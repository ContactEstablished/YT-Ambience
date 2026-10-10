"""Shader code shared by the rain contact pass (prompt 9): ground.py, kiosk_weather.py, kiosk_exterior.py, wet_fx.py.

Every animated water / steam effect runs on one loop clock, the MPC_WetFX scalar LoopTime, which make_sweep.py keys
linearly from 0 to the loop length over LS_Sweep. Each effect completes a whole number of cycles per loop (rates are
rounded to LoopLength), and random choices are hashed on the slot index modulo the slots in one loop, so the last frame
leads into the first exactly. A fixed seed alone would not do that.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import matkit as mk  # noqa: E402
import unreal  # noqa: E402

MPC = f"{dck.GAME}/WetFX/MPC_WetFX"
MPC_SCALARS = {"LoopTime": 0.0, "LoopLength": 30.0, "WaterAmount": 1.0, "SteamAmount": 1.0}
ER_TEX = "/Game/EasyRain/System/SystemTextures/Puddles"
RIPPLE_TEX = {"TT": f"{ER_TEX}/T_puddleRainRippleTemporal_01_Mask", "TG": f"{ER_TEX}/T_puddleRainRippleGradient_01_D",
              "TN": f"{ER_TEX}/T_puddleRainRipple_01_N"}

# EasyRain's MF_EasyRain_ripplesRain (four layers of MF_EasyRain_ripple, the same textures and constants), on the
# loop clock: each layer's rate is rounded to whole cycles per loop, so the rings repeat exactly at the seam.
# P: world xy (cm). -> float4(normal xy * Intensity, 1, ring mask)
RIPPLE_HLSL = r"""
float2 uv = P * (Tiling / 100.0);
float L = max(Len, 1.0);
float4 rate = round(float4(1.0, 0.85, 0.95, 0.7) * Speed * L) / L;
float4 tt = frac(Time * rate + float4(0.0, 0.4, 0.45, 0.7) * Speed);
float2 q[4] = { uv * 1.2, (uv + float2(0.7, 0.2)) * 0.8, (uv + float2(0.5, 0.9)) * 2.0, uv + float2(0.8, 0.88) };
float2 n = 0.0;
float ms = 0.0;
for (int i = 0; i < 4; i++)
{
    float2 p = q[i] + 1.0;
    float t0 = Texture2DSample(TT, TTSampler, p).r;
    float g = Texture2DSample(TG, TGSampler, p).r;
    float2 nn = Texture2DSample(TN, TNSampler, p).rg * 2.0 - 1.0;
    float f = frac(tt[i] + t0);
    float c = clamp((f - 1.0 + g) * 25.0, 1.0, 5.0);
    float m = saturate(1.0 - f) * sin(c * 3.14159265);
    n += nn * m;
    ms += saturate(m);
}
return float4(n * Intensity, 1.0, ms);
"""

# One drip source's falling-drop events. Slots: K = LoopLength / Period (rounded), so the pattern repeats each loop.
# Slot k drips unless hash(k) < Skip; its drop lets go at a hashed moment in the slot, falls Fall metres under gravity
# (t = sqrt(2 Fall / g)) and splashes. Paste inside a loop over j = 0..2 (the three most recent slots); needs t (loop
# time), T (loop length), Period, Skip, Seed, Fall in scope; gives rel (release time), s (seconds since release,
# wrapped), tf (fall time), sz (size scale), ok (this slot drips).
DRIP_EVENT = r"""
float K = max(1.0, round(T / max(Period, 0.05)));
float Pq = T / K;
float kk = floor(t / Pq) - j;
kk -= K * floor(kk / K);
uint h_ok_u = uint(kk) * 747796405u + uint(Seed * 1000.0 + 0.5) * 2891336453u + 11u;
h_ok_u = ((h_ok_u >> ((h_ok_u >> 28u) + 4u)) ^ h_ok_u) * 277803737u;
float h_ok = float((h_ok_u >> 22u) ^ h_ok_u) * 2.3283064e-10;
bool ok = h_ok >= Skip;
uint h_rel_u = uint(kk) * 747796405u + uint(Seed * 1000.0 + 0.5) * 2891336453u + 23u;
h_rel_u = ((h_rel_u >> ((h_rel_u >> 28u) + 4u)) ^ h_rel_u) * 277803737u;
float h_rel = float((h_rel_u >> 22u) ^ h_rel_u) * 2.3283064e-10;
float rel = (kk + 0.08 + 0.55 * h_rel) * Pq;
float s = t - rel;
s -= T * floor(s / T);
float tf = sqrt(2.0 * Fall / 9.81);
uint h_sz_u = uint(kk) * 747796405u + uint(Seed * 1000.0 + 0.5) * 2891336453u + 37u;
h_sz_u = ((h_sz_u >> ((h_sz_u >> 28u) + 4u)) ^ h_sz_u) * 277803737u;
float h_sz = float((h_sz_u >> 22u) ^ h_sz_u) * 2.3283064e-10;
float sz = lerp(0.75, 1.25, h_sz);
"""

# The drip strip (M_FX_Water), pixel side. X: metres across the strip (0 = its axis), Y: metres down from the source,
# H: strip length (= fall), W: strip width, px: metres per pixel. Mode 0: canopy drip events (falling streak, hanging
# bead, landing splash); Mode 1: a short continuous trickle (beads streaming down, loop-exact) with a small splash.
# -> float2(opacity before the global amounts, across-the-streak coordinate for the normal)
WATER_HLSL = r"""
float t = Time;
float T = max(Len, 1.0);
float a = 0.0;
float pw = max(px, 1e-5);
float yUp = H - Y;  // metres above the landing point
if (Mode < 0.5)
{
    for (int j = 0; j < 3; j++)
    {
""" + DRIP_EVENT + r"""
        if (!ok) continue;
        float rr = 0.5 * Size * sz;
        if (s < tf)
        {
            // falling: a streak as long as the drop travels in half a frame (180 deg shutter at 24 fps)
            float yd = 4.905 * s * s;
            float L = max(2.0 * rr, 9.81 * s / 48.0);
            float yc = clamp(Y, yd - L, yd);
            float d = length(float2(X, Y - yc));
            float re = max(rr, 0.6 * pw);  // never thinner than a pixel: no shimmer; the opacity keeps the energy
            float cov = smoothstep(re + 0.5 * pw, re - 0.5 * pw, d) * (rr / re);
            float head = lerp(0.35, 1.0, saturate((Y - (yd - L)) / max(L, 1e-4)));
            a = max(a, cov * head * saturate(Streak * (2.0 * rr / L + 0.6)));  // a smeared drop still catches the light along its path
        }
        else if (s < tf + SplashDur)
        {
            // landing: a few droplets thrown out and up, falling back; gone in a fraction of a second
            float tau = s - tf;
            float fade = 1.0 - tau / SplashDur;
            for (int i = 0; i < 5; i++)
            {
uint hi_u = uint(kk * 5.0 + i) * 747796405u + uint(Seed * 1000.0 + 0.5) * 2891336453u + 51u;
hi_u = ((hi_u >> ((hi_u >> 28u) + 4u)) ^ hi_u) * 277803737u;
float hi = float((hi_u >> 22u) ^ hi_u) * 2.3283064e-10;
                float th = (i / 4.0 - 0.5) * 2.3 + (hi - 0.5) * 0.6;
                float v = SplashV * lerp(0.55, 1.15, frac(hi * 7.31));
                float2 p = float2(sin(th) * v * tau, cos(th) * v * tau - 4.905 * tau * tau);
                if (p.y < -0.002) continue;
                float r2 = rr * lerp(0.25, 0.45, frac(hi * 3.17));
                float re2 = max(r2, 0.6 * pw);
                float d = length(float2(X, yUp) - p);
                a = max(a, smoothstep(re2 + 0.5 * pw, re2 - 0.5 * pw, d) * (r2 / re2) * fade);
            }
        }
    }
    // the next drop swelling at the source before it lets go
    for (int j = -1; j <= 0; j++)
    {
""" + DRIP_EVENT + r"""
        if (!ok) continue;
        float ahead = T - s;  // seconds until this slot's release
        if (ahead > 0.0 && ahead < Grow)
        {
            float rb = 0.5 * Size * sz * lerp(0.35, 1.0, 1.0 - ahead / Grow);
            float re = max(rb, 0.6 * pw);
            float d = length(float2(X, Y - rb * 0.9));
            a = max(a, smoothstep(re + 0.5 * pw, re - 0.5 * pw, d) * (rb / re) * 0.9);
        }
    }
}
else
{
    // trickle: beads streaming down the strip at Flow m/s, some gaps; whole bead counts per loop (loop-exact)
    float sp = 0.016;
    float rate = round(Flow / sp * T) / T;
    float nb = max(1.0, rate * T);
    float ph = Y / sp - t * rate;
    float bi = floor(ph);
    float bk = bi - nb * floor(bi / nb);
uint h_on_u = uint(bk) * 747796405u + uint(Seed * 1000.0 + 0.5) * 2891336453u + 11u;
h_on_u = ((h_on_u >> ((h_on_u >> 28u) + 4u)) ^ h_on_u) * 277803737u;
float h_on = float((h_on_u >> 22u) ^ h_on_u) * 2.3283064e-10;
    float on = step(Skip, h_on);
    float f = frac(ph);
uint h_rr_u = uint(bk) * 747796405u + uint(Seed * 1000.0 + 0.5) * 2891336453u + 23u;
h_rr_u = ((h_rr_u >> ((h_rr_u >> 28u) + 4u)) ^ h_rr_u) * 277803737u;
float h_rr = float((h_rr_u >> 22u) ^ h_rr_u) * 2.3283064e-10;
    float rr = 0.5 * Size * lerp(0.7, 1.2, h_rr);
    float re = max(rr, 0.6 * pw);
    float d = length(float2(X, (f - 0.5) * sp * 1.6));
    a = smoothstep(re + 0.5 * pw, re - 0.5 * pw, d) * (rr / re) * on * Streak;
    // a thin continuous film along the axis, fainter
    a = max(a, smoothstep(0.5 * re + 0.5 * pw, 0.5 * re - 0.5 * pw, abs(X)) * 0.07 * Streak);
    // small splashes where it lands
    float P2 = T / max(1.0, round(T / 0.22));
    float k2 = floor(t / P2);
    float kn = max(1.0, round(T / P2));
    float k2w = k2 - kn * floor(k2 / kn);
    float tau = t - k2 * P2;
    for (int i = 0; i < 3; i++)
    {
uint hi_u = uint(k2w * 3.0 + i) * 747796405u + uint(Seed * 1000.0 + 0.5) * 2891336453u + 51u;
hi_u = ((hi_u >> ((hi_u >> 28u) + 4u)) ^ hi_u) * 277803737u;
float hi = float((hi_u >> 22u) ^ hi_u) * 2.3283064e-10;
        float th = (hi - 0.5) * 2.4;
        float v = SplashV * lerp(0.4, 0.9, frac(hi * 7.31));
        float2 p = float2(sin(th) * v * tau, cos(th) * v * tau - 4.905 * tau * tau);
        if (p.y < -0.002 || tau > SplashDur) continue;
        float r2 = 0.5 * Size * 0.35;
        float re2 = max(r2, 0.6 * pw);
        a = max(a, smoothstep(re2 + 0.5 * pw, re2 - 0.5 * pw, length(float2(X, yUp) - p)) * (r2 / re2) * (1.0 - tau / SplashDur));
    }
}
// across-the-streak coordinate (-1..1) for a rounded normal: the drop glints like a small cylinder
float un = clamp(X / max(0.6 * Size, 0.6 * pw), -1.0, 1.0);
return float2(a, un);
"""

# The drip strip's world normal: rounded across the streak (un -1..1), facing the camera in the middle, so lights to
# either side put a thin glint on the falling drop. AY: the strip's axis (world), CD: camera minus object.
WATER_NORMAL_HLSL = r"""
float3 ay = normalize(AY);
float3 c = normalize(CD - ay * dot(CD, ay) + float3(1e-4, 0.0, 0.0));
float3 right = normalize(cross(ay, c));
float u = clamp(UN, -0.98, 0.98);
return normalize(right * u + c * sqrt(1.0 - u * u));
"""

# Cylindrical billboard (vertex side): the quad (engine Plane, local X across, local Y along its axis) turns about
# its axis to face the camera. LP: local position (cm, without offsets), AX / AY: the local X / Y axes in world
# space (scaled), CD: camera minus object position (world). Lean: the top drifts along Wind by Lean * (y/len)^2 metres.
BILLBOARD_HLSL = r"""
float3 ay = normalize(AY);
float3 c = CD - ay * dot(CD, ay);
c = normalize(c + float3(1e-4, 0.0, 0.0));
float3 right = normalize(cross(ay, c));
float lx = LP.x / 100.0;
float3 o = AX * LP.x;
float3 n = right * length(AX) * LP.x;
float v = saturate(LP.y / 100.0 + 0.5);
float3 lean = float3(Wind, 0.0) * Lean * 100.0 * v * v;
return n - o + lean;
"""

# Steam (M_FX_Steam), pixel side. U: 0..1 across, V: 0..1 up the card; AX / AY: the card's scaled axes (their lengths
# are its width / height in metres). Prompt 10: the noise is laid out in METRES (it was in card units, so a tall card
# stretched every eddy into a vertical streak) and carried up at Rise m/s (whole texture tiles per loop). The column
# meanders (two slow waves climbing it), widens by Spread m per m of rise, thins as it spreads (sqrt(Base / width)),
# and breaks into wisps higher up (the threshold climbs by Breakup); its sides are eaten by the noise rather than cut
# by a profile, and it fades out well inside the card's edges and top, so no card outline can show.
# The noise texture (StarterContent T_Perlin_Noise_M, 2048 px fBm down to ~1 px = 1 mm here) is read at FIXED low mips
# (5-6: 32-64 texels a tile, SampleLevel), so the grain that read as streaks is gone, only soft billows are left, and the
# plume looks the same from the wide video camera and a close lens (a mip bias would follow the view). The fine eddies climb 1.35x faster than the billows and the warp 0.7x, so the pattern churns instead of scrolling.
# Base, Spread: m; Rise: m/s; Sway: cycles/s; SwayAmp: m of meander per m of rise; Scale: eddy frequency (1 = ~0.5 m).
# -> float density
STEAM_HLSL = r"""
float t = Time;
float L = max(Len, 1.0);
float W = max(length(AX), 0.01);
float H = max(length(AY), 0.01);
float y = V * H;
float xc = (U - 0.5) * W;
float sw1 = round(Sway * L) / L;
float sw2 = round(Sway * 1.7 * L) / L;
float mead = (0.65 * sin(6.2831853 * (sw1 * t - y * 0.35 + Seed)) + 0.35 * sin(6.2831853 * (sw2 * t - y * 0.8 + Seed * 2.3))) * SwayAmp * y;
float hw = Base + Spread * y;
float x = xc - mead;
float k = Scale;
float g = 1.0 / (1.0 + 0.3 * y);
float r0 = round(Rise * 0.7 * 0.25 * k * L) / L;
float r1 = round(Rise * 0.5 * k * L) / L;
float r2 = round(Rise * 1.35 * 1.15 * k * L) / L;
float2 wq = float2(x * 0.25 * k * g + Seed, y * 0.25 * k - t * r0);
float2 w = (float2(Texture2DSampleLevel(Noise, NoiseSampler, wq, 6.0).r, Texture2DSampleLevel(Noise, NoiseSampler, wq + float2(0.37, 0.61), 6.0).r) - 0.5) * 0.5;
float n1 = Texture2DSampleLevel(Noise, NoiseSampler, float2(x * 0.5 * k * g + Seed * 1.7, y * 0.5 * k - t * r1) + w, 5.5).r;
float n2 = Texture2DSampleLevel(Noise, NoiseSampler, float2(x * 1.15 * k * g - Seed, y * 1.15 * k - t * r2) + w * 1.8, 5.0).r;
float n = n1 * 0.62 + n2 * 0.38;
float r = abs(x) / max(hw, 1e-3);
float core = exp(-r * r * 1.8);
float th = Thresh + Breakup * saturate(V) + (1.0 - core) * 0.15;
float wisp = smoothstep(th, th + Soft, n);
float dens = core * wisp * sqrt(Base / hw);
dens *= smoothstep(0.0, 0.12, V) * (1.0 - smoothstep(0.5, 0.92, V));
dens *= 1.0 - smoothstep(0.36, 0.48, abs(U - 0.5));
return dens;
"""


def collection():
    """MPC_WetFX: the loop clock and the master amounts (water, steam)."""
    path = MPC
    folder, name = path.rsplit("/", 1)
    mk.ensure_dir(folder)
    if not dck.EAL.does_asset_exist(path):
        unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
    mpc = unreal.load_asset(path)
    have = {str(p.get_editor_property("parameter_name")) for p in mpc.get_editor_property("scalar_parameters")}
    params = list(mpc.get_editor_property("scalar_parameters"))
    for n, v in MPC_SCALARS.items():
        if n not in have:
            p = unreal.CollectionScalarParameter()
            p.set_editor_property("parameter_name", n)
            p.set_editor_property("default_value", v)
            params.append(p)
    mpc.set_editor_property("scalar_parameters", params)
    dck.EAL.save_loaded_asset(mpc)
    return mpc


def set_mpc_default(name, value):
    mpc = unreal.load_asset(MPC)
    params = list(mpc.get_editor_property("scalar_parameters"))
    for p in params:
        if str(p.get_editor_property("parameter_name")) == name:
            p.set_editor_property("default_value", float(value))
    mpc.set_editor_property("scalar_parameters", params)
    dck.EAL.save_loaded_asset(mpc)


def mpc_param(m, name, x, y):
    return mk.expr(m, unreal.MaterialExpressionCollectionParameter, x, y, collection=unreal.load_asset(MPC), parameter_name=name)


def loop_time(m, x, y):
    """The loop clock for the city's looping materials (prompt 10: LED screens, neon, beacons, nav lights), in place of
    the engine's Time node, which starts wherever each render process starts: fmod(LoopTime, LoopLength). The sequence
    keys LoopTime, so every render process (and every chunk of a long render) sees the same moment at the same frame,
    and past the loop end (the crossfade tail, make_sweep.py) it wraps to the loop's start."""
    f = mk.expr(m, unreal.MaterialExpressionFmod, x, y)
    mk.link(mpc_param(m, "LoopTime", x - 250, y - 40), "", f, "A")
    mk.link(mpc_param(m, "LoopLength", x - 250, y + 40), "", f, "B")
    return f


def texobj(m, path, x, y):
    return mk.expr(m, unreal.MaterialExpressionTextureObject, x, y, texture=unreal.load_asset(path))


def ripple_node(m, P, x, y, speed, tiling, intensity):
    """The loop-clock ripple normal: a custom node fed by P (world xy, cm). -> float4(nx, ny, 1, mask)."""
    c = mk.custom(m, RIPPLE_HLSL, ["P", "Time", "Len", "Speed", "Tiling", "Intensity", "TT", "TG", "TN"],
                  unreal.CustomMaterialOutputType.CMOT_FLOAT4, x, y, "Rain ripples (loop clock)")
    mk.link(P, "", c, "P")
    mk.link(mpc_param(m, "LoopTime", x - 300, y), "", c, "Time")
    mk.link(mpc_param(m, "LoopLength", x - 300, y + 60), "", c, "Len")
    for k, v, dy in (("Speed", speed, 120), ("Tiling", tiling, 180), ("Intensity", intensity, 240)):
        node = v if not isinstance(v, (int, float)) else mk.expr(m, unreal.MaterialExpressionConstant, x - 300, y + dy, r=float(v))
        mk.link(node, "", c, k)
    for k, path in RIPPLE_TEX.items():
        mk.link(texobj(m, path, x - 500, y + 300 + 80 * len(k) * (1 if k == "TT" else 2 if k == "TG" else 3)), "", c, k)
    return c

# The platform's wet layer (M_KioskWeathered, UseRainContact branch). Base: the weathered (colour, roughness);
# WP: world position (cm); N: world normal; Map: T_RainContact (R damp, G standing water, B rain exposure, A 1 - contact),
# top-down in the kiosk frame; Conc: concrete albedo (world-mapped detail); Noise: tiling noise; Rip: the loop-clock
# ripple normal; D0..D4 / Q0..Q4: the canopy drips' landing spots (x, y cm) + (period, skip) / (seed, fall m).
# Mode 0 -> float4(colour, roughness); mode 1 -> float4(world normal, 0).
RAIN_CONTACT_HLSL = r"""
float vert = 1.0 - saturate(abs(N.z) * 2.0);  // 1 on the slab's sides
float top = saturate(N.z * 2.0 - 1.0);
float2 pk = float2(WP.x, -WP.y) * 0.01;  // kiosk frame, metres
float2 nk = float2(N.x, -N.y);
float2 ps = pk - nk * 0.015 * vert;  // the sides read the map just inside the edge
float4 mp = Texture2DSample(Map, MapSampler, (ps + Half) / (2.0 * Half));
float damp = mp.r, film = mp.g, expo = mp.b, cont = 1.0 - mp.a;  // alpha stores 1 - contact (see build_rain_contact.py)
float zl = WP.z * 0.01;
if (zl > 0.6) { damp = 0.8; film = 0.0; expo = 1.0; cont = 0.0; }  // the same concrete on the roof: plainly exposed
// the slab's sides: soaked a few cm up from the street, wet runoff streaks below where water spills over the lip
float along = dot(pk, float2(-nk.y, nk.x));
float sn = Texture2DSample(Noise, NoiseSampler, float2(along * 2.6, zl * 0.7)).r;
float wick = smoothstep(0.03 + 0.03 * sn, 0.005, zl);
float streak = smoothstep(0.52, 0.78, sn) * saturate(film * 2.5 + damp * 0.6) * EdgeStreak;
damp = lerp(damp, max(max(damp, wick), streak), vert);
film = lerp(film, streak * 0.5, vert);
float D = saturate(damp * Amount);
float F = saturate(film * Amount);
float C = saturate(cont * Amount);
float E = saturate(expo * Amount);
if (Mode < 0.5 && DebugMap > 0.5) return float4(mp.r, mp.g, mp.b, 0.5);  // DebugMap: the wet map as colour (R damp, G water, B rain)
if (Mode < 0.5)
{
    float3 cd = Texture2DSample(Conc, ConcSampler, pk / DetailTile).rgb;
    float lum = dot(cd, float3(0.3, 0.59, 0.11));
    float k = clamp(1.0 + (lum - DetailAvg) / max(DetailAvg, 1e-3) * 0.35 * DetailAmt, 0.75, 1.25);
    float3 col = Base.rgb * k;
    float r = saturate(Base.a + (DetailAvg - lum) * 0.6 * DetailAmt);
    col *= 1.0 - WetDark * D;
    r = lerp(r, WetRough, D);
    col *= 1.0 - ContactDark * C;
    r = lerp(r, r * 0.8, C * D);
    col *= 1.0 - PoolDark * F;
    r = lerp(r, PoolRough, smoothstep(0.1, 0.6, F));
    return float4(col, clamp(r, 0.03, 1.0));
}
// normal: raindrop rings where rain lands on water or wet concrete, rings where each canopy drip lands (tops only)
float2 g = Rip.xy * RippleAmt * E * saturate(F + 0.3 * D);
float4 dp[5] = { D0, D1, D2, D3, D4 };
float4 dq[5] = { Q0, Q1, Q2, Q3, Q4 };
float t = Time;
float T = max(Len, 1.0);
for (int i = 0; i < 5; i++)
{
    float2 dv = (WP.xy - dp[i].xy) * 0.01;
    float dd = length(dv);
    if (dd > 0.35 || dp[i].z <= 0.0) continue;
    float Period = dp[i].z, Skip = dp[i].w, Seed = dq[i].x, Fall = dq[i].y;
    for (int j = 0; j < 3; j++)
    {
""" + DRIP_EVENT + r"""
        if (!ok) continue;
        float tau = s - tf;
        if (tau < 0.0 || tau > RingDur) continue;
        float R = 0.012 + RingSpeed * tau;
        float w = 0.008 + 0.02 * tau;
        float x = (dd - R) / w;
        float amp = RingAmt * sz * (1.0 - tau / RingDur) * (1.0 - tau / RingDur) * exp(-x * x);
        g += dv / max(dd, 1e-4) * amp * sin(x * 2.4) * saturate(F * 1.5 + D * 0.6);
    }
}
float3 n = normalize(N + float3(g * top, 0.0));
return float4(n, 0.0);
"""
RAIN_CONTACT_SCALARS = ["Amount", "WetDark", "WetRough", "PoolRough", "PoolDark", "ContactDark", "DetailAmt", "DetailTile",
                        "DetailAvg", "RippleAmt", "RingAmt", "RingSpeed", "RingDur", "EdgeStreak", "DebugMap"]
RAIN_MAP = f"{dck.GAME}/WetFX/Textures/T_RainContact"
NOISE_TEX = "/Game/StarterContent/Textures/T_Perlin_Noise_M"
CONC_TEX = "/Game/StarterContent/Textures/T_Concrete_Poured_D"


def rain_contact_branch(m, base, x, y, defaults):
    """Adds the platform's wet layer to a material: base = the float4(colour, roughness) node. Returns the two
    custom nodes (mode 0: colour + roughness, mode 1: world normal). Parameters named as RAIN_CONTACT_SCALARS
    (ContactAmount -> Amount), D0..D4 / Q0..Q4 for the drips, the map half-size from rain_contact.json."""
    wp = mk.expr(m, unreal.MaterialExpressionWorldPosition, x - 900, y)
    if hasattr(unreal, "MaterialExpressionTruncateLWC"):
        tr = mk.expr(m, unreal.MaterialExpressionTruncateLWC, x - 750, y)
        mk.link(wp, "", tr, "")
        wp = tr
    nrm = mk.expr(m, unreal.MaterialExpressionVertexNormalWS, x - 750, y + 80)
    xy = mk.expr(m, unreal.MaterialExpressionComponentMask, x - 600, y + 160, r=True, g=True, b=False, a=False)
    mk.link(wp, "", xy, "")
    c = defaults
    rip = ripple_node(m, xy, x - 400, y + 1400, mk.scalar(m, "RippleSpeed", c.get("RippleSpeed", 1.0), x - 900, y + 1500),
                      mk.scalar(m, "RippleTiling", c.get("RippleTiling", 1.4), x - 900, y + 1560), 1.0)
    names = ["Base", "WP", "N", "Map", "Conc", "Noise", "Rip", "Time", "Len", "Half", "Mode"] + RAIN_CONTACT_SCALARS + \
        [f"D{i}" for i in range(5)] + [f"Q{i}" for i in range(5)]
    params = {}
    for i, n in enumerate(RAIN_CONTACT_SCALARS):
        key = "ContactAmount" if n == "Amount" else n
        params[n] = mk.scalar(m, key, c.get(key, 0.0), x - 600, y + 300 + i * 60)
    for i in range(5):
        params[f"D{i}"] = mk.vector(m, f"DripSpot{i}", (0.0, 0.0, 0.0), x - 900, y + 300 + i * 120)
        params[f"Q{i}"] = mk.vector(m, f"DripInfo{i}", (0.0, 0.0, 0.0), x - 900, y + 900 + i * 120)
    half = mk.scalar(m, "MapHalf", c.get("MapHalf", 4.096), x - 600, y + 1200)
    outs = []
    for k, mode in enumerate((0.0, 1.0)):
        cn = mk.custom(m, RAIN_CONTACT_HLSL, names, unreal.CustomMaterialOutputType.CMOT_FLOAT4, x, y + k * 700,
                       "Rain contact" + (" (normal)" if mode else ""))
        mk.link(base, "", cn, "Base")
        mk.link(wp, "", cn, "WP")
        mk.link(nrm, "", cn, "N")
        mk.link(mk.expr(m, unreal.MaterialExpressionTextureObjectParameter, x - 400, y - 300 + k * 700, parameter_name="RainContactMap",
                        texture=unreal.load_asset(RAIN_MAP)), "", cn, "Map")
        mk.link(texobj(m, CONC_TEX, x - 400, y - 200 + k * 700), "", cn, "Conc")
        mk.link(texobj(m, NOISE_TEX, x - 400, y - 100 + k * 700), "", cn, "Noise")
        mk.link(rip, "", cn, "Rip")
        mk.link(mpc_param(m, "LoopTime", x - 300, y + 60 + k * 700), "", cn, "Time")
        mk.link(mpc_param(m, "LoopLength", x - 300, y + 120 + k * 700), "", cn, "Len")
        mk.link(half, "", cn, "Half")
        mk.link(mk.expr(m, unreal.MaterialExpressionConstant, x - 300, y + 180 + k * 700, r=mode), "", cn, "Mode")
        for n, p in params.items():
            mk.link(p, "RGBA" if n[0] in "DQ" and n[1:].isdigit() else "", cn, n)  # the drips' vectors carry 4 numbers
        outs.append(cn)
    return outs
