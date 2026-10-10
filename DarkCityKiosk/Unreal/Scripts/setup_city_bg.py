"""Builds the instanced city background from city_bg_layout.py into L_DarkCity.

    node Scripts/ue.mjs Scripts/setup_city_bg.py              # (re)build, show the new city, hide the old
    node Scripts/ue.mjs Scripts/setup_city_bg.py --show old   # flip back to the Blender fill towers (no rebuild)
    node Scripts/ue.mjs Scripts/setup_city_bg.py --show new   # and forward again
    node Scripts/ue.mjs Scripts/setup_city_bg.py --materials  # rebuild the two materials in place only

Everything goes in the outliner folder City_Background (scene_config.CITY_BG["folder"]): one actor
per group (Band1..Band4, Anchors, Landmark, Details) holding hierarchical instanced static mesh
components (unit cube / cylinder instances), the re-hosted ad screens, and shop glow lights.
Replaced actors are hidden, never deleted: City_Mid*, City_Far_*, City_Landmark, the three anchor
towers, and the shop lights of the hidden fill towers.

Materials (/Game/DarkCity/CityBG/Materials):
  M_CityBG_Facade  window grid in real metres: each instance carries its size in per-instance custom
                   data, so a scaled cube gets correctly sized windows on every face; rows follow
                   world height so floors line up across setbacks. Lit windows cluster by floor and
                   block; the grid blends into its average glow once a window is under ~3 px.
  M_CityBG_Light   emissive with per-instance colour/intensity; beacons blink (1.5 s), neon pulses
                   (7.5 s); both divide the 30 s and 300 s loops, on the sequence's loop clock (prompt 10).
After building it checks the flying cars against the new towers (traffic_lanes.City).
"""
import importlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import matkit as mk  # noqa: E402
import scene_config as S  # noqa: E402
import city_bg_layout as LAY  # noqa: E402
import traffic_lanes as TL  # noqa: E402
import traffic_plan as TP  # noqa: E402
import wetfx_hlsl as W  # noqa: E402

dck, mk, S, LAY, TL, TP, W = (importlib.reload(m) for m in (dck, mk, S, LAY, TL, TP, W))
import unreal  # noqa: E402

C = S.CITY_BG
FOLDER = C["folder"]
BG = f"{dck.GAME}/CityBG"
MATS = f"{BG}/Materials"
MESH = {"box": unreal.load_asset("/Engine/BasicShapes/Cube"), "cyl": unreal.load_asset("/Engine/BasicShapes/Cylinder"),
        "plane": unreal.load_asset("/Engine/BasicShapes/Plane")}
GROUPS = ("Band1", "Band2", "Band3", "Band4", "Anchors", "Landmark", "Details")
SHADOWS = {g: C["bands"][g]["shadows"] if g in C["bands"] else True for g in GROUPS}
SHADOWS["Landmark"] = False

args = sys.argv[1:]
show = args[args.index("--show") + 1] if "--show" in args else None

FACADE_HLSL = r"""
struct FCityBG
{
    float Hash(float2 p) { float3 p3 = frac(float3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return frac((p3.x + p3.y) * p3.z); }
    float PulseInt(float x, float w) { float f = floor(x); return f * w + clamp(x - f - 0.5 * (1.0 - w), 0.0, w); }
    float Pulse(float x, float w, float fw) { return (PulseInt(x + 0.5 * fw, w) - PulseInt(x - 0.5 * fw, w)) / fw; }
};
FCityBG F;
float3 s = max(Sz, float3(0.01, 0.01, 0.01));
float3 lp = LP / 100.0;
float roof = step(0.497, abs(lp.z));
float u = (D2.y > 0.5) ? atan2(lp.y, lp.x) * 0.5 * s.x : ((abs(lp.x) > abs(lp.y)) ? lp.y * s.y : lp.x * s.x);
float fh = (D2.z > 0.5) ? D2.z : FloorH;
float bw = (Bay > 0.3) ? Bay : BayW;
float2 g = float2(u / bw, WP.z * 0.01 / fh);
float2 fw = max(fwidth(g), float2(1e-4, 1e-4));
float pane = F.Pulse(g.x, PaneW, fw.x) * F.Pulse(g.y, PaneH, fw.y);
float seed = D2.x;
float2 cell = floor(g);
float2 blk = floor(cell / float2(CX, CY));
float lit = saturate(D1.x);
float hb = F.Hash(blk + seed * 0.731);
float hf = F.Hash(float2(cell.y, seed * 1.37 + 5.0));
float hc = F.Hash(float2(cell.x, seed * 2.71 + 9.0));       // vertical stacks
float blkLit = saturate(lit * (0.15 + 1.7 * hb) * (0.6 + 0.8 * hf) * (0.55 + 0.9 * hc));
float h1 = F.Hash(cell + seed);
float h2 = F.Hash(cell * 1.31 + seed * 2.1 + 17.0);
float h3 = F.Hash(cell * 0.77 + seed * 3.3 + 41.0);
float on = step(h1, blkLit);
float ws = saturate(D1.y);
float3 c = (h2 < ws) ? WarmC.rgb : ((h2 < 1.0 - TealShare) ? CoolC.rgb : TealC.rgb);
float3 cMean = WarmC.rgb * ws + CoolC.rgb * max(1.0 - ws - TealShare, 0.0) + TealC.rgb * TealShare;
float br = max(D1.z, 0.0) * Intensity;
float paneMean = PaneW * PaneH;
float3 eCell = c * on * (0.45 + 1.1 * h3) * pane;
float3 eBlk = cMean * blkLit * paneMean;
float3 eTwr = cMean * lit * paneMean;
float m = max(fw.x, fw.y);
float k1 = saturate((m - LodStart) / max(LodEnd - LodStart, 1e-3));
float k2 = saturate((m * min(CX, CY) - LodStart) / max(LodEnd - LodStart, 1e-3));
float paneF = lerp(pane, paneMean, k1);
float3 e = lerp(eCell, lerp(eBlk, eTwr, k2), k1) + CoolC.rgb * UnlitGlow * paneF;
float wall = (1.0 - roof) * Windows;
return float4(e * br * wall, paneF * wall);
"""

LIGHT_HLSL = r"""
float tb = frac(T / BlinkPeriod + Ph);
float on = smoothstep(0.0, 0.04, tb) * (1.0 - smoothstep(BlinkDuty, BlinkDuty + 0.08, tb));
float mb = lerp(1.0, 0.04 + 0.96 * on, saturate(Bl));
float tp = frac(T / PulsePeriod + Ph * 3.7);
float mp = 1.0 - saturate(Pu) * (0.5 - 0.5 * cos(6.2831853 * tp));
return Col * I * Scale * mb * mp;
"""


def custom_data(m, index, x, y, vec=False):
    cls = unreal.MaterialExpressionPerInstanceCustomData3Vector if vec else unreal.MaterialExpressionPerInstanceCustomData
    return mk.expr(m, cls, x, y, data_index=index)


def build_facade_material():
    m = mk.material(MATS, "M_CityBG_Facade")
    mk.setp(m, used_with_instanced_static_meshes=True)
    lp = mk.expr(m, unreal.MaterialExpressionLocalPosition, -1600, -300)
    wp = mk.expr(m, unreal.MaterialExpressionWorldPosition, -1600, -200)
    ins = {"LP": lp, "WP": wp, "Sz": custom_data(m, 0, -1600, -100, True), "D1": custom_data(m, 3, -1600, 0, True),
           "D2": custom_data(m, 6, -1600, 100, True), "Bay": custom_data(m, 9, -1600, 200)}
    common = C["windows"]["common"]
    scal = {"FloorH": ("FloorH", 3.8), "BayW": ("BayW", 1.8), "PaneW": ("PaneW", common["PaneW"]), "PaneH": ("PaneH", common["PaneH"]),
            "CX": ("ClusterX", common["ClusterX"]), "CY": ("ClusterY", common["ClusterY"]), "Intensity": ("Intensity", 2.4),
            "UnlitGlow": ("UnlitGlow", common["UnlitGlow"]), "LodStart": ("LodStart", common["LodStart"]),
            "LodEnd": ("LodEnd", common["LodEnd"]), "Windows": ("Windows", 1.0), "TealShare": ("TealShare", common["TealShare"])}
    for i, (inp, (pname, val)) in enumerate(scal.items()):
        ins[inp] = mk.scalar(m, pname, val, -1600, 320 + i * 80)
    cc = C["colors"]
    for i, (inp, pname, key) in enumerate((("WarmC", "WarmColor", "warm"), ("CoolC", "CoolColor", "cool"), ("TealC", "TealColor", "teal"))):
        ins[inp] = mk.vector(m, pname, cc[key], -1600, 1300 + i * 120)
    c = mk.custom(m, FACADE_HLSL, list(ins), unreal.CustomMaterialOutputType.CMOT_FLOAT4, -1000, 0, "City windows")
    for k, e in ins.items():
        mk.link(e, "", c, k)
    rgb = mk.expr(m, unreal.MaterialExpressionComponentMask, -700, 0, r=True, g=True, b=True, a=False)
    mk.link(c, "", rgb, "")
    a = mk.expr(m, unreal.MaterialExpressionComponentMask, -700, 150, r=False, g=False, b=False, a=True)
    mk.link(c, "", a, "")
    wall = mk.vector(m, "WallColor", cc["wall"], -700, 300)
    glass = mk.vector(m, "GlassColor", cc["glass"], -700, 420)
    base = mk.expr(m, unreal.MaterialExpressionLinearInterpolate, -400, 300)
    mk.link(wall, "", base, "A")
    mk.link(glass, "", base, "B")
    mk.link(a, "", base, "Alpha")
    wr, gr = mk.scalar(m, "WallRough", common["WallRough"], -700, 560), mk.scalar(m, "GlassRough", common["GlassRough"], -700, 650)
    rough = mk.expr(m, unreal.MaterialExpressionLinearInterpolate, -400, 560)
    mk.link(wr, "", rough, "A")
    mk.link(gr, "", rough, "B")
    mk.link(a, "", rough, "Alpha")
    mk.out(m, rgb, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.out(m, base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.finish(m)
    return m


def build_light_material():
    m = mk.material(MATS, "M_CityBG_Light")
    mk.setp(m, used_with_instanced_static_meshes=True)
    ins = {"Col": custom_data(m, 0, -1200, 0, True), "I": custom_data(m, 3, -1200, 100), "Bl": custom_data(m, 4, -1200, 200),
           "Ph": custom_data(m, 5, -1200, 300), "Pu": custom_data(m, 6, -1200, 400),
           "T": W.loop_time(m, -1200, 500)}  # the sequence's loop clock (prompt 10), not engine Time
    for i, (k, v) in enumerate((("BlinkPeriod", 1.5), ("BlinkDuty", 0.3), ("PulsePeriod", 7.5), ("Scale", 1.0))):
        ins[k] = mk.scalar(m, k, v, -1200, 600 + i * 80)
    c = mk.custom(m, LIGHT_HLSL, list(ins), unreal.CustomMaterialOutputType.CMOT_FLOAT3, -800, 0, "Beacon / neon")
    for k, e in ins.items():
        mk.link(e, "", c, k)
    mk.out(m, c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.out(m, mk.expr(m, unreal.MaterialExpressionConstant3Vector, -500, 200, constant=unreal.LinearColor(0.02, 0.02, 0.02, 1.0)), "",
           unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, mk.expr(m, unreal.MaterialExpressionConstant, -500, 320, r=0.4), "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.finish(m)
    return m


def build_materials():
    facade, lightm = build_facade_material(), build_light_material()
    W = C["windows"]
    mis = {}
    for name in ("Band1", "Band2", "Band3", "Band4", "Shop", "Plain"):
        mis[name] = mk.instance(MATS, f"MI_CityBG_{name}", facade, W[name])
    mis["Anchors"] = mis["Band1"]
    mis["Landmark"] = mis["Band3"]
    mis["Details"] = mis["Band2"]
    return mis, lightm


# ---- Actors ---------------------------------------------------------------------------------
def destroy_previous():
    n = 0
    for a in dck.ACTORS.get_all_level_actors():
        if str(a.get_folder_path()).startswith(FOLDER):
            a.destroy_actor()
            n += 1
    return n


def add_hism(actor, name, mesh, material, n_floats, shadows):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    root = sds.k2_gather_subobject_data_for_instance(actor)[0]
    h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.HierarchicalInstancedStaticMeshComponent,
                                                                 blueprint_context=None))
    if not str(fail).strip() == "":
        print("   add_new_subobject:", fail)
    sds.rename_subobject(h, unreal.Text(name))
    comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))
    comp.set_static_mesh(mesh)
    comp.set_material(0, material)
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    comp.set_cast_shadow(shadows)
    comp.set_num_custom_data_floats(n_floats)
    return comp


def transform(p):
    x, y, z = p["c"]
    sx, sy, sz = p["size"]
    return unreal.Transform(location=dck.to_ue(x, y, z), rotation=unreal.Rotator(roll=0.0, pitch=0.0, yaw=dck.heading_to_ue_yaw(p["yaw"])),
                            scale=unreal.Vector(sx, sy, sz))


def build_group(group, parts, mis, light_mat):
    actor = dck.ACTORS.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    actor.set_actor_label(f"BG_{group}")
    actor.set_folder_path(FOLDER)
    buckets = {}
    for p in parts:
        buckets.setdefault((p["kind"], p["shape"]), []).append(p)
    n = 0
    for (kind, shape), ps in sorted(buckets.items()):
        if kind == "light":
            mat, floats = light_mat, LAY.LIGHT_FLOATS
        elif kind == "podium":
            mat, floats = mis["Shop"], LAY.FACADE_FLOATS
        elif kind == "plain":
            mat, floats = mis["Plain"], 0
        else:
            mat, floats = mis[group], LAY.FACADE_FLOATS
        comp = add_hism(actor, f"{kind.title()}_{shape.title()}", MESH[shape], mat, floats, SHADOWS[group] and kind != "light")
        comp.add_instances([transform(p) for p in ps], False, True)
        if floats:
            for i, p in enumerate(ps):
                for k, v in enumerate(p["data"]):
                    comp.set_custom_data_value(i, k, float(v), False)
            comp.set_custom_data_value(len(ps) - 1, 0, float(ps[-1]["data"][0]), True)
        n += len(ps)
    return actor, n


def build_screens(screens):
    """The anchors' ad screens on planes, exactly where the Blender towers had them (same materials)."""
    out = []
    for s in screens:
        mi = unreal.load_asset(f"{dck.GAME}/City/Screens/Instances/MI_Screen_{s['name']}")
        if mi is None:
            print(f"   (no MI_Screen_{s['name']})")
            continue
        n = unreal.Vector(s["normal"][0], -s["normal"][1], 0.0)  # Blender -> Unreal
        right = n.cross(unreal.Vector(0, 0, 1))  # the viewer's right, looking at the screen
        rot = unreal.MathLibrary.make_rot_from_xz(right, n)  # plane X = right (U), Y = down (V), Z = out of the screen
        a = dck.ACTORS.spawn_actor_from_class(unreal.StaticMeshActor, dck.to_ue(*s["center"]), rot)
        a.set_actor_label(f"BG_Screen_{s['name']}")
        a.set_folder_path(f"{FOLDER}/Screens")
        a.set_actor_scale3d(unreal.Vector(s["width"], s["height"], 1.0))
        c = a.static_mesh_component
        c.set_static_mesh(MESH["plane"])
        c.set_material(0, mi)
        c.set_cast_shadow(False)
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        out.append(a)
    return out


SIGN_DIR = f"{BG}/Signs"


def build_sign_material():
    m = mk.material(MATS, "M_CityBG_Sign")
    mk.setp(m, blend_mode=unreal.BlendMode.BLEND_ADDITIVE, shading_model=unreal.MaterialShadingModel.MSM_UNLIT)
    tex = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0, parameter_name="Sign")
    mul = mk.expr(m, unreal.MaterialExpressionMultiply, -350, 0)
    mk.link(tex, "RGB", mul, "A")
    mk.link(mk.scalar(m, "Intensity", 6.0, -700, 250), "", mul, "B")
    mk.out(m, mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.finish(m)
    return m


def build_signs(signs):
    """Glowing signs (the landmark's MIRAI): an additive plane, black = invisible, facing the Mid camera."""
    import subprocess
    r = subprocess.run(["pwsh", "-NoProfile", "-File", os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_landmark_sign.ps1")],
                       capture_output=True, text=True, encoding="utf-8")
    print(" ", (r.stdout or r.stderr).strip())
    mat = build_sign_material()
    for s in signs:
        task = mk.setp(unreal.AssetImportTask(), filename=os.path.join(dck.RAW, "signs", f"{s['texture']}.png"), destination_path=SIGN_DIR,
                       automated=True, replace_existing=True, save=True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.load_asset(f"{SIGN_DIR}/{s['texture']}")
        mk.setp(tex, srgb=True, never_stream=True)
        mk.EAL.save_loaded_asset(tex)
        mi = mk.instance(MATS, f"MI_CityBG_Sign_{s['name']}", mat, {"Intensity": s["intensity"]})
        mk.MEL.set_material_instance_texture_parameter_value(mi, "Sign", tex)
        mk.MEL.update_material_instance(mi)
        mk.EAL.save_loaded_asset(mi)
        n = unreal.Vector(s["normal"][0], -s["normal"][1], 0.0)
        right = n.cross(unreal.Vector(0, 0, 1))
        a = dck.ACTORS.spawn_actor_from_class(unreal.StaticMeshActor, dck.to_ue(*s["center"]), unreal.MathLibrary.make_rot_from_xz(right, n))
        a.set_actor_label(f"BG_Sign_{s['name']}")
        a.set_folder_path(f"{FOLDER}/Screens")
        a.set_actor_scale3d(unreal.Vector(s["width"], s["height"], 1.0))
        c = a.static_mesh_component
        c.set_static_mesh(MESH["plane"])
        c.set_material(0, mi)
        c.set_cast_shadow(False)
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)


def build_shop_lights(shops):
    sl = C["shop_light"]
    for s in shops:
        a = dck.ACTORS.spawn_actor_from_class(unreal.PointLight, dck.to_ue(*s["pos"]), unreal.Rotator(0, 0, 0))
        a.set_actor_label(f"L_ShopBG_{s['name']}")
        a.set_folder_path(f"{FOLDER}/Lights")
        c = a.get_component_by_class(unreal.PointLightComponent)
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        mk.setp(c, intensity_units=unreal.LightUnits.CANDELAS, attenuation_radius=sl["radius_m"] * 100, cast_shadows=False,
                volumetric_scattering_intensity=sl["volumetric_scattering"], source_radius=200.0)
        c.set_intensity(sl["intensity_cd"])
        c.set_light_color(unreal.LinearColor(*s["colour"], 1.0))


# ---- Old / new visibility -------------------------------------------------------------------
def old_labels():
    anchors = {f"City_{n}" for n in C["anchors"]}
    fill = ("City_Mid", "City_Far_")
    out = set()
    for a in dck.ACTORS.get_all_level_actors():
        lab = a.get_actor_label()
        if lab.startswith(fill) or lab == "City_Landmark" or lab in anchors:
            out.add(lab)
        elif lab.startswith("L_Shop_") and lab[len("L_Shop_"):].startswith(("Mid", "Far")):
            out.add(lab)
    return out


def set_visible(actor, visible):
    actor.modify()
    root = actor.get_editor_property("root_component")
    if root:
        root.modify()
        root.set_visibility(visible, True)
    actor.set_actor_hidden_in_game(not visible)


def show_set(which):
    old = old_labels()
    n_old = n_new = 0
    for a in dck.ACTORS.get_all_level_actors():
        if a.get_actor_label() in old:
            set_visible(a, which == "old")
            n_old += 1
        elif str(a.get_folder_path()).startswith(FOLDER):
            set_visible(a, which == "new")
            n_new += 1
    print(f"showing the {which} city: {n_old} Blender actors {'shown' if which == 'old' else 'hidden'}, "
          f"{n_new} background actors {'shown' if which == 'new' else 'hidden'}")


# ---- Traffic check --------------------------------------------------------------------------
def check_traffic(layout):
    """Every flying-traffic corridor (traffic_routes.json) still clears the rebuilt city."""
    path = os.path.join(dck.RAW, "traffic_routes.json")
    if not os.path.exists(path):
        print("traffic check: no traffic_routes.json yet (run setup_traffic.py)")
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    city = TL.City(TL.load_city(), S.TRAFFIC["routes"])  # reads the city_bg.json just written
    lines = [(f"{r['layer']}{i}", r["points"]) for recs in data["layers"].values() for i, r in enumerate(recs)]
    if data.get("hero"):
        lines.append(("hero", data["hero"]["points"]))
    bad = []
    for name, pts in lines:
        hits = sum(1 for p in pts if city.blocked(p, tight=True))
        if hits:
            bad.append(f"{name}: {hits} points inside a tower (re-run setup_traffic.py --replan)")
    print(f"traffic check: {len(lines) - len(bad)}/{len(lines)} corridors clear" + "".join("\n   " + b for b in bad))
    return bad


# ---- Main -----------------------------------------------------------------------------------
dck.ensure_map()
if show:
    show_set(show)
elif "--materials" in args:
    build_materials()
    print("setup_city_bg: materials rebuilt")
else:
    layout = LAY.build_layout(log=lambda s: print(s))
    with open(os.path.join(dck.RAW, "city_bg.json"), "w", encoding="utf-8") as f:
        json.dump(layout, f)
    mis, light_mat = build_materials()
    print(f"removed {destroy_previous()} previous background actors")
    total = 0
    for g in GROUPS:
        ps = [p for p in layout["parts"] if p["group"] == g]
        if ps:
            _, n = build_group(g, ps, mis, light_mat)
            total += n
    build_screens(layout["screens"])
    build_signs(layout.get("signs", []))
    build_shop_lights(layout["shop_lights"])
    show_set("new")
    check_traffic(layout)
    TP.remask(log=print)  # the corridors' visibility in this city (re-run setup_traffic.py + make_sweep.py to use it)
    print(f"setup_city_bg: {total} instances in {len(GROUPS)} groups")
dck.LEVELS.save_current_level()
