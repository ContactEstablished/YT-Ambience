"""Kitchen pass (2026-10-09, prompt 7): the working ramen / coffee kitchen behind the service opening,
the order terminal, the customer counter's surface and things on it, and the storage under it.

Built on its own (build_kitchen.py -> Unreal/RawContent/kiosk_kitchen.glb) so the kiosk export and its
weathering bake stay untouched; Unreal trims the old step-2 interior out of copies of the kiosk's
ServiceSide and Body meshes (Unreal/Scripts/kiosk_kitchen.py). Numbers: kiosk_config.KITCHEN / POS /
UNDER_COUNTER; small props are sized here.

What the glb holds:
  SM_Kiosk_Kitchen         the room (deeper and taller than the old recess), worktops, cabinets, sink,
                           hood, noodle boiler, stock pot, shelves, rails, coffee brewer + grinder, the
                           order terminal, the under-counter fridge and drawers: one-off parts
  SM_Kiosk_KitchenCounter  a stainless top sheet on the customer counter, with UV1 = 0..1 over the
                           counter for its own wear map (polish, scratches, rings, seams)
  SM_Kiosk_KitchenCards    printed things from the Kitchen atlas: the terminal's screen and labels,
                           order tickets, tape labels, packaging prints, paperwork (M_KioskGraphic)
  SM_KP_<name>             small repeated props at the origin (bowls, cups, bottles, tubs, tools),
                           placed in Unreal as instances from kitchen_props.json
Layering seen through the opening: customer counter -> heavy frame -> pass + prep worktop -> the
cooking line under the hood -> shelves on the back wall -> the darker back corners.
"""
import math

from mathutils import Matrix, Vector

import kiosk_config as C
from . import geo

K, P, U = C.KITCHEN, C.POS, C.UNDER_COUNTER
Y0, PH = C.Y0, C.PLATFORM_H
SW, CO = C.SERVICE_WINDOW, C.COUNTER
XA, XB = K["x0"], K["x1"]
YF = K["front"]
YB = YF + K["depth"]
CZ = K["ceiling"]
FT, BT = K["front_top"], K["back_top"]
YFW = YF + K["front_d"]  # back edge of the pass / prep worktop
YBC = YB - K["back_d"]  # front edge of the back counter
HX0, HX1 = K["hood"]
YCF = Y0 - CO["projection"]  # customer counter's front edge

# (rgb linear, roughness, metallic, emission). Unreal builds its own instances of M_Kitchen from
# scene_config.KITCHEN_LOOK; these only drive Blender's review renders.
MATERIALS = {
    "KK_Steel": ((0.60, 0.60, 0.58), 0.30, 1.0, 0.0),  # stainless: worktops, cladding, pots
    "KK_SteelWorn": ((0.46, 0.45, 0.43), 0.42, 1.0, 0.0),  # older, duller stainless: shelves, inserts, hood
    "KK_SteelCounter": ((0.55, 0.55, 0.53), 0.32, 1.0, 0.0),  # the customer counter's top sheet
    "KK_Chrome": ((0.75, 0.75, 0.74), 0.12, 1.0, 0.0),  # faucet, rails, ladle bowls
    "KK_Mesh": ((0.20, 0.20, 0.19), 0.45, 0.8, 0.0),  # wire mesh (tebo baskets, strainer, baffle filters)
    "KK_Tile": ((0.74, 0.72, 0.66), 0.16, 0.0, 0.0),
    "KK_TileOld": ((0.66, 0.66, 0.60), 0.22, 0.0, 0.0),  # a replaced tile, a shade off
    "KK_Grout": ((0.17, 0.15, 0.12), 0.9, 0.0, 0.0),
    "KK_Ceiling": ((0.075, 0.075, 0.072), 0.75, 0.0, 0.0),  # dark painted ceiling, structure
    "KK_WallPaint": ((0.50, 0.45, 0.36), 0.55, 0.0, 0.0),  # warm cream enamel on the walls above the tiles: the glow seen from the street
    "KK_Floor": ((0.05, 0.05, 0.05), 0.8, 0.0, 0.0),
    "KK_Cabinet": ((0.13, 0.15, 0.14), 0.5, 0.2, 0.0),  # painted steel cabinet fronts (dark green-grey)
    "KK_Rubber": ((0.025, 0.025, 0.025), 0.75, 0.0, 0.0),
    "KK_PlasticBlack": ((0.022, 0.022, 0.024), 0.35, 0.0, 0.0),
    "KK_PlasticGrey": ((0.30, 0.30, 0.29), 0.55, 0.0, 0.0),  # terminal keys
    "KK_POS": ((0.33, 0.32, 0.29), 0.45, 0.0, 0.0),  # terminal housing, warm grey paint
    "KK_POSDark": ((0.05, 0.05, 0.055), 0.40, 0.5, 0.0),  # terminal pedestal, visor, bumpers
    "KK_CeramicWhite": ((0.80, 0.78, 0.74), 0.10, 0.0, 0.0),
    "KK_CeramicRed": ((0.45, 0.035, 0.025), 0.12, 0.0, 0.0),
    "KK_CeramicBlack": ((0.02, 0.02, 0.02), 0.10, 0.0, 0.0),
    "KK_PlasticRed": ((0.55, 0.03, 0.02), 0.30, 0.0, 0.0),
    "KK_PlasticYellow": ((0.80, 0.52, 0.04), 0.30, 0.0, 0.0),
    "KK_PlasticGreen": ((0.05, 0.26, 0.09), 0.35, 0.0, 0.0),
    "KK_PlasticCream": ((0.78, 0.76, 0.68), 0.40, 0.0, 0.0),
    "KK_PlasticBlue": ((0.11, 0.18, 0.28), 0.50, 0.0, 0.0),  # muted blue crates and packaging
    "KK_PaperCream": ((0.84, 0.79, 0.66), 0.60, 0.0, 0.0),  # paper cups, receipts
    "KK_Kraft": ((0.40, 0.26, 0.14), 0.80, 0.0, 0.0),
    "KK_Cardboard": ((0.34, 0.24, 0.14), 0.85, 0.0, 0.0),
    "KK_Wood": ((0.50, 0.36, 0.22), 0.60, 0.0, 0.0),  # cutting board
    "KK_WoodDark": ((0.16, 0.09, 0.05), 0.50, 0.0, 0.0),  # handles, chopstick pot
    "KK_GlassDark": ((0.03, 0.02, 0.012), 0.05, 0.0, 0.0),  # soy bottles
    "KK_Soy": ((0.035, 0.014, 0.006), 0.04, 0.0, 0.0),
    "KK_Broth": ((0.32, 0.17, 0.06), 0.06, 0.0, 0.0),
    "KK_Water": ((0.035, 0.035, 0.03), 0.02, 0.0, 0.0),
    "KK_Scallion": ((0.12, 0.38, 0.05), 0.5, 0.0, 0.0),
    "KK_Chashu": ((0.38, 0.18, 0.09), 0.45, 0.0, 0.0),
    "KK_Menma": ((0.52, 0.34, 0.12), 0.45, 0.0, 0.0),
    "KK_Egg": ((0.85, 0.48, 0.08), 0.35, 0.0, 0.0),
    "KK_Nori": ((0.015, 0.03, 0.015), 0.6, 0.0, 0.0),
    "KK_Onion": ((0.50, 0.30, 0.12), 0.55, 0.0, 0.0),
    "KK_Beans": ((0.07, 0.035, 0.015), 0.35, 0.0, 0.0),
    "KK_Cloth": ((0.72, 0.70, 0.62), 0.95, 0.0, 0.0),
    "KK_ClothBlue": ((0.09, 0.16, 0.27), 0.95, 0.0, 0.0),
    # glowing parts (Unreal: KITCHEN_LOOK emissive)
    "KK_Lamp": ((1.0, 0.86, 0.66), 0.4, 0.0, 6.0),  # the rear ceiling tube
    "KK_LampHood": ((1.0, 0.74, 0.45), 0.3, 0.0, 5.0),  # hood lamp lenses
    "KK_LampShelf": ((1.0, 0.70, 0.40), 0.3, 0.0, 3.0),  # LED strip under the top shelf
    "KK_LED_Green": ((0.25, 1.0, 0.4), 0.3, 0.0, 6.0),
    "KK_LED_Amber": ((1.0, 0.55, 0.08), 0.3, 0.0, 6.0),
    "KK_LED_Red": ((0.5, 0.03, 0.02), 0.3, 0.0, 0.0),  # the terminal's unlit red LED
    "KK_LED_Blue": ((0.15, 0.45, 1.0), 0.3, 0.0, 4.0),
}


def ensure_materials(B):
    import bpy
    for name, (rgb, rough, metal, emit) in MATERIALS.items():
        m = B.mat(name, rgb, emit)
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return bpy.data.materials


# ---- helpers ----------------------------------------------------------------------------------------

def merge(dst, src, matrix):
    """Append geo.Mesh `src` into `dst` through a 4x4 matrix (for tilted parts)."""
    off = len(dst.verts)
    dst.verts.extend(matrix @ Vector(v) for v in src.verts)
    for f, mi, sm in zip(src.faces, src.face_mat, src.face_smooth):
        dst.faces.append(tuple(off + i for i in f))
        dst.face_mat.append(dst._mat(src.mats[mi]))
        dst.face_smooth.append(sm)


def part(dst, matrix, builder, *args, **kw):
    tmp = geo.Mesh("tmp")
    builder(tmp, *args, **kw)
    merge(dst, tmp, matrix)


def at(x, y, z, yaw=0.0, pitch=0.0, roll=0.0):
    """Matrix: translate to (x, y, z), then yaw about Z, pitch about X, roll about Y (degrees)."""
    return (Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
            @ Matrix.Rotation(math.radians(pitch), 4, "X") @ Matrix.Rotation(math.radians(roll), 4, "Y"))


def bx(m, cx, cy, cz, sx, sy, sz, mat, bevel=0.0, seg=1):
    """Box from centre + size (bottom-centre if cz is the base: pass cz + sz / 2)."""
    geo.box(m, cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2, mat, bevel, seg)


def ring(m, center, r, tube, mat, segments=24, tube_seg=6, axis="Z"):
    """Torus (rims, rails bent into rings)."""
    cx, cy, cz = center
    verts, faces = [], []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        for j in range(tube_seg):
            b = 2 * math.pi * j / tube_seg
            rr = r + tube * math.cos(b)
            p = Vector((rr * math.cos(a), rr * math.sin(a), tube * math.sin(b)))
            if axis == "Y":
                p = Vector((p.x, p.z, p.y))
            elif axis == "X":
                p = Vector((p.z, p.y, p.x))
            verts.append(Vector((cx, cy, cz)) + p)
    for i in range(segments):
        for j in range(tube_seg):
            a, b = i * tube_seg + j, i * tube_seg + (j + 1) % tube_seg
            c, d = ((i + 1) % segments) * tube_seg + (j + 1) % tube_seg, ((i + 1) % segments) * tube_seg + j
            faces.append((a, b, c, d))
    m.add_raw(verts, faces, mat, True)


def polyline(m, pts, r, mat, seg=8):
    for a, b in zip(pts, pts[1:]):
        geo.pipe(m, a, b, r, mat, seg)


# ---- printed cards (Kitchen atlas) -----------------------------------------------------------------

class Cards:
    """Quads (and bent strips) textured from the Kitchen atlas; UV1 is (0, 0) and the vertex colour
    is (random, age, 0, 0): M_KioskGraphic then shows the print with no kiosk weathering over it."""

    def __init__(self, manifest):
        self.man = manifest
        self.verts, self.faces, self.uv, self.col, self.mat = [], [], [], [], []
        self.n = 0

    def size(self, item):
        return self.man["items"][item]["size_m"]

    def card(self, item, center, right, up, w=None, h=None, age=0.3, flip_u=False, bend=None):
        """A card centred at `center`, facing right x up. w/h default to the art's own size (m).
        bend = (axis_point, radius): wrap around a vertical cylinder (labels on bottles and pots)."""
        it = self.man["items"][item]
        u0, v0, u1, v1 = it["uv"]
        W, H = w or it["size_m"][0], h or it["size_m"][1]
        c, r, up = Vector(center), Vector(right).normalized(), Vector(up).normalized()
        nu = 8 if bend else 1
        rnd = ((sum(map(ord, item)) * 37 + self.n * 101) % 997) / 997.0
        self.n += 1
        base = len(self.verts)
        for j in (0, 1):
            for i in range(nu + 1):
                fu = i / nu
                if bend:
                    ax, rad = Vector(bend[0]), bend[1]
                    n0 = (c - Vector((ax.x, ax.y, c.z)))
                    n0.z = 0
                    n0.normalize()
                    t = Vector((-n0.y, n0.x, 0.0))
                    ang = (fu - 0.5) * W / rad
                    p = Vector((ax.x, ax.y, c.z)) + (n0 * math.cos(ang) + t * math.sin(ang)) * rad
                else:
                    p = c + r * ((fu - 0.5) * W)
                p = p + up * ((j - 0.5) * H)
                self.verts.append(p)
                uu = u1 - fu * (u1 - u0) if flip_u else u0 + fu * (u1 - u0)
                self.uv.append((uu, 1.0 - (v1 - j * (v1 - v0))))
                self.col.append((rnd, age, 0.0, 0.0))
        for i in range(nu):
            a, b = base + i, base + i + 1
            self.faces.append((a, b, b + nu + 1, a + nu + 1))
            self.mat.append(0)

    def build(self, coll, materials, name="SM_Kiosk_KitchenCards", mat="KG_Kitchen"):
        import bpy
        import numpy as np
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.verts], [], self.faces)
        me.update()
        me.materials.append(materials[mat])
        me.polygons.foreach_set("use_smooth", [True] * len(self.faces))
        uv_per_loop, uv1 = [], []
        for f in me.polygons:
            for li in f.loop_indices:
                vi = me.loops[li].vertex_index
                uv_per_loop.append(self.uv[vi])
                uv1.append((0.0, 0.0))
        for nm, data in (("UVMap", uv_per_loop), ("WeatherUV", uv1)):
            layer = me.uv_layers.new(name=nm)
            layer.data.foreach_set("uv", np.array(data, np.float32).ravel())
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        ca.data.foreach_set("color", np.array(self.col, np.float32).ravel())
        me.color_attributes.active_color = ca
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        return ob


FWD, BACKW = Vector((0, -1, 0)), Vector((0, 1, 0))  # facing the customer / facing into the kitchen
RIGHT, UP = Vector((1, 0, 0)), Vector((0, 0, 1))


# ---- prototypes: small repeated props (local frame: base at z = 0, front toward -Y) --------------

def bowl_profile(r, h):
    """Ramen bowl: foot ring, flaring wall, lip, back down the inside."""
    return ([(r * 0.40, 0.0), (r * 0.44, 0.0), (r * 0.44, h * 0.10), (r * 0.55, h * 0.15), (r * 0.80, h * 0.45),
             (r * 0.95, h * 0.78), (r, h)],
            [(r * 0.955, h * 1.005), (r * 0.91, h * 0.80), (r * 0.76, h * 0.50), (r * 0.48, h * 0.20), (r * 0.15, h * 0.16)])


def p_bowl(m, r=0.095, h=0.082, outer="KK_CeramicWhite", inner="KK_CeramicWhite", band="KK_CeramicRed"):
    o, i = bowl_profile(r, h)
    geo.lathe(m, (0, 0, 0), o, outer, 28, cap_bottom=True, cap_top=False)
    geo.lathe(m, (0, 0, 0), [o[-1]] + i, inner, 28, cap_bottom=False, cap_top=True)
    if band:
        geo.lathe(m, (0, 0, 0), [(r * 0.958 + 0.0012, h * 0.80), (r * 0.995 + 0.0012, h * 0.95)], band, 28, cap_bottom=False, cap_top=False)
        geo.lathe(m, (0, 0, 0), [(r * 0.62 + 0.001, h * 0.30), (r * 0.66 + 0.001, h * 0.34)], band, 28, cap_bottom=False, cap_top=False)


def p_cup(m, lid=False):
    prof = [(0.026, 0.0), (0.028, 0.004), (0.041, 0.106), (0.0435, 0.108), (0.0435, 0.112), (0.040, 0.111), (0.027, 0.012)]
    geo.lathe(m, (0, 0, 0), prof, "KK_PaperCream", 24, cap_bottom=True, cap_top=True)
    geo.lathe(m, (0, 0, 0), [(0.0345 + 0.0012, 0.035), (0.0395 + 0.0012, 0.085)], "KK_Kraft", 24, cap_bottom=False, cap_top=False)  # sleeve
    if lid:
        geo.lathe(m, (0, 0, 0), [(0.0445, 0.106), (0.046, 0.112), (0.042, 0.118), (0.038, 0.122), (0.0, 0.123)], "KK_PlasticBlack", 24,
                  cap_bottom=True, cap_top=False)


def p_cupstack(m, n=28):
    h = 0.112 + (n - 1) * 0.0065
    geo.lathe(m, (0, 0, 0), [(0.026, 0.0), (0.028, 0.004), (0.041, 0.106), (0.0435, h), (0.040, h), (0.027, h - 0.10)], "KK_PaperCream", 24,
              cap_bottom=True, cap_top=True)
    for k in range(n - 1):  # the rolled rims of the nested cups
        geo.lathe(m, (0, 0, 0), [(0.0438, 0.108 + k * 0.0065), (0.0442, 0.110 + k * 0.0065)], "KK_PaperCream", 20, cap_bottom=False, cap_top=False)


def p_lidstack(m, n=24):
    for k in range(n):
        z = k * 0.0042
        geo.lathe(m, (0, 0, 0), [(0.044, z), (0.046, z + 0.006), (0.040, z + 0.012), (0.0, z + 0.013)], "KK_PlasticBlack", 20,
                  cap_bottom=k == 0, cap_top=False)


def p_squeeze(m, mat="KK_PlasticRed"):
    geo.lathe(m, (0, 0, 0), [(0.026, 0.0), (0.029, 0.006), (0.029, 0.14), (0.024, 0.158), (0.014, 0.164), (0.0, 0.165)], mat, 18,
              cap_bottom=True, cap_top=False)
    geo.lathe(m, (0, 0, 0), [(0.016, 0.160), (0.016, 0.178), (0.006, 0.19), (0.002, 0.215), (0.0, 0.216)], "KK_PlasticCream", 14,
              cap_bottom=True, cap_top=False)


def p_soy(m):
    geo.lathe(m, (0, 0, 0), [(0.024, 0.0), (0.026, 0.004), (0.026, 0.07), (0.016, 0.09), (0.012, 0.10), (0.0, 0.10)], "KK_GlassDark", 18,
              cap_bottom=True, cap_top=False)
    geo.lathe(m, (0, 0, 0), [(0.016, 0.092), (0.017, 0.112), (0.014, 0.12), (0.0, 0.121)], "KK_PlasticRed", 14, cap_bottom=True, cap_top=False)
    geo.pipe(m, (0.008, 0, 0.112), (0.024, 0, 0.122), 0.0035, "KK_PlasticRed", 6)


def p_tare(m):
    geo.lathe(m, (0, 0, 0), [(0.046, 0.0), (0.05, 0.008), (0.05, 0.22), (0.04, 0.26), (0.018, 0.285), (0.016, 0.30), (0.0, 0.30)],
              "KK_GlassDark", 20, cap_bottom=True, cap_top=False)
    geo.lathe(m, (0, 0, 0), [(0.019, 0.288), (0.019, 0.312), (0.0, 0.313)], "KK_PlasticRed", 14, cap_bottom=True, cap_top=False)


def p_jar(m, mat="KK_PlasticRed", lid="KK_PlasticBlack"):
    geo.lathe(m, (0, 0, 0), [(0.022, 0.0), (0.025, 0.004), (0.025, 0.058), (0.021, 0.064), (0.0, 0.064)], mat, 16, cap_bottom=True, cap_top=False)
    geo.lathe(m, (0, 0, 0), [(0.023, 0.06), (0.023, 0.078), (0.0, 0.079)], lid, 16, cap_bottom=True, cap_top=False)


def p_tub(m, lid="KK_PlasticGreen"):
    geo.lathe(m, (0, 0, 0), [(0.046, 0.0), (0.048, 0.003), (0.056, 0.085), (0.0, 0.085)], "KK_PlasticCream", 22, cap_bottom=True, cap_top=False)
    geo.lathe(m, (0, 0, 0), [(0.058, 0.082), (0.06, 0.09), (0.057, 0.094), (0.0, 0.095)], lid, 22, cap_bottom=True, cap_top=False)


def p_tubstack(m, n=6, lid="KK_PlasticCream"):
    for k in range(n):
        z = k * 0.02
        geo.lathe(m, (0, 0, 0), [(0.046, z), (0.056, z + 0.085), (0.058, z + 0.088)], "KK_PlasticCream", 20, cap_bottom=k == 0, cap_top=False)
    geo.lathe(m, (0, 0, 0), [(0.058, 0.085 + (n - 1) * 0.02), (0.06, 0.093 + (n - 1) * 0.02), (0.0, 0.095 + (n - 1) * 0.02)], lid, 20,
              cap_bottom=True, cap_top=False)


def p_insert(m, fill="KK_Scallion", lid=False):
    """1/6 gastronorm pan sunk in the topping rail: rim + filling (or a lid)."""
    w, d = 0.176, 0.162
    geo.box(m, -w / 2, w / 2, -d / 2, d / 2, -0.004, 0.0, "KK_SteelWorn", 0.002)  # rim flange
    geo.box(m, -w / 2 + 0.012, w / 2 - 0.012, -d / 2 + 0.012, d / 2 - 0.012, -0.10, -0.004, "KK_SteelWorn", 0.01)
    if lid:
        geo.box(m, -w / 2 + 0.004, w / 2 - 0.004, -d / 2 + 0.004, d / 2 - 0.004, 0.0, 0.006, "KK_SteelWorn", 0.004)
        geo.box(m, -0.03, 0.03, -0.006, 0.006, 0.006, 0.018, "KK_SteelWorn", 0.004)
    else:
        geo.box(m, -w / 2 + 0.014, w / 2 - 0.014, -d / 2 + 0.014, d / 2 - 0.014, -0.025, -0.012, fill, 0.004)
        rng = geo.RNG
        for _ in range(14):  # a lumpy surface: pieces piled in the pan
            x, y = rng.uniform(-w / 2 + 0.025, w / 2 - 0.025), rng.uniform(-d / 2 + 0.025, d / 2 - 0.025)
            s = rng.uniform(0.012, 0.024)
            geo.box(m, x - s, x + s, y - s * 0.7, y + s * 0.7, -0.016, -0.016 + s * 0.6, fill, s * 0.25)


def p_ladle(m, r=0.042):
    """Hanging ladle: origin at the hook, handle down, bowl at the bottom opening outward (-Y)."""
    geo.pipe(m, (0, 0, 0), (0, 0, -0.012), 0.004, "KK_Chrome", 8)
    ring(m, (0, 0, -0.022), 0.009, 0.0025, "KK_Chrome", 12, 6, axis="Y")
    geo.pipe(m, (0, 0, -0.03), (0, -0.004, -0.30), 0.0045, "KK_Chrome", 8)
    bowl = geo.Mesh("b")
    geo.lathe(bowl, (0, 0, 0), [(0.0, -r), (r * 0.6, -r * 0.8), (r * 0.92, -r * 0.4), (r, 0.0), (r * 0.96, 0.002), (r * 0.88, -r * 0.35),
                                (r * 0.55, -r * 0.72), (0.0, -r * 0.9)], "KK_Chrome", 20, cap_bottom=False, cap_top=False)
    merge(m, bowl, at(0, -0.004 - r * 0.17, -0.30 - r * 0.98, pitch=80))


def p_strainer(m, r=0.07):
    """Hanging fine strainer (hira-zaru): rim, mesh disc, handle up to the hook."""
    geo.pipe(m, (0, 0, 0), (0, 0, -0.012), 0.004, "KK_Chrome", 8)
    ring(m, (0, 0, -0.022), 0.009, 0.0025, "KK_Chrome", 12, 6, axis="Y")
    geo.pipe(m, (0, 0, -0.03), (0, 0, -0.24), 0.005, "KK_WoodDark", 8)
    cz = -0.24 - r
    ring(m, (0, 0, cz), r, 0.003, "KK_Chrome", 28, 6, axis="Y")
    geo.cylinder(m, (0, 0.006, cz), r, 0.002, "KK_Mesh", axis="Y", segments=28)


def p_tebo(m, hang=True):
    """Noodle basket: mesh cylinder with a rim and a long handle. hang: origin at the handle's hook,
    basket below; else origin at the basket bottom with the handle raking up toward -Y (in a well)."""
    def basket(mm):
        geo.cylinder(mm, (0, 0, 0.075), 0.062, 0.15, "KK_Mesh", segments=20, cap=False)
        geo.cylinder(mm, (0, 0, 0.002), 0.062, 0.004, "KK_Mesh", segments=20)
        ring(mm, (0, 0, 0.15), 0.064, 0.003, "KK_Chrome", 24, 6)
        geo.pipe(mm, (0, -0.064, 0.15), (0, -0.30, 0.15 + 0.20), 0.006, "KK_Chrome", 8)
        geo.pipe(mm, (0, -0.30, 0.35), (0, -0.33, 0.37), 0.006, "KK_Chrome", 8)
    if hang:
        tmp = geo.Mesh("t")
        basket(tmp)
        # rotate so the handle points straight up from the hook
        ang = math.atan2(0.20, 0.236)
        mat = at(0, 0, 0, pitch=-(90 - math.degrees(ang))) @ Matrix.Translation((0, 0.33, -0.37))
        merge(m, tmp, mat)
    else:
        basket(m)


def p_tongs(m):
    for s in (-1, 1):
        polyline(m, [(0, 0, 0), (s * 0.006, -0.002, -0.05), (s * 0.014, -0.004, -0.22), (s * 0.012, -0.006, -0.25)], 0.0035, "KK_Chrome", 6)
    ring(m, (0, 0, 0.004), 0.008, 0.002, "KK_Chrome", 12, 6, axis="Y")


def p_pan(m):
    """Yukihira pan hanging by its handle: the pan below, base toward the wall (+Y)."""
    ring(m, (0, 0, -0.008), 0.007, 0.002, "KK_Chrome", 12, 6, axis="Y")
    geo.pipe(m, (0, 0.004, -0.015), (0, 0.004, -0.17), 0.011, "KK_WoodDark", 10)
    geo.pipe(m, (0, 0.004, -0.17), (0, 0.004, -0.20), 0.008, "KK_SteelWorn", 8)
    pan = geo.Mesh("p")
    geo.lathe(pan, (0, 0, 0), [(0.0, 0.0), (0.07, 0.0), (0.085, 0.01), (0.09, 0.06), (0.087, 0.061), (0.082, 0.012), (0.068, 0.004), (0.0, 0.004)],
              "KK_SteelWorn", 28, cap_bottom=False, cap_top=False)
    merge(m, pan, at(0, 0.03, -0.29, pitch=90))


def p_towel_hang(m, w=0.20, drop=0.26):
    for s, d in ((-1, drop), (1, drop * 0.8)):
        geo.box(m, -w / 2, w / 2, s * 0.007 - 0.0025, s * 0.007 + 0.0025, -d, 0.0, "KK_Cloth", 0.002)
    geo.cylinder(m, (0, 0, 0.0), 0.0095, w, "KK_Cloth", axis="X", segments=10)  # folded over the rail
    for k in range(3):  # a blue stripe near each hem
        z = -drop + 0.03 + k * 0.006
        geo.box(m, -w / 2, w / 2, -0.0098, -0.0094, z, z + 0.004, "KK_ClothBlue")


def p_towel_fold(m):
    geo.box(m, -0.11, 0.11, -0.065, 0.065, 0.0, 0.022, "KK_Cloth", 0.008, 2)
    geo.box(m, -0.112, 0.112, -0.058, -0.052, 0.004, 0.018, "KK_ClothBlue", 0.002)


def p_napkins(m):
    geo.box(m, -0.07, 0.07, -0.045, 0.045, 0.0, 0.012, "KK_Steel", 0.003)
    for s in (-1, 1):
        geo.box(m, -0.07, 0.07, s * 0.045 - 0.0015, s * 0.045 + 0.0015, 0.0, 0.13, "KK_Steel", 0.001)
    geo.box(m, -0.062, 0.062, -0.042, 0.042, 0.012, 0.115, "KK_PaperCream", 0.002)


def p_chopsticks(m):
    geo.lathe(m, (0, 0, 0), [(0.034, 0.0), (0.036, 0.004), (0.036, 0.12), (0.032, 0.122), (0.032, 0.02), (0.0, 0.02)], "KK_WoodDark", 20,
              cap_bottom=True, cap_top=True)
    rng = geo.RNG
    for k in range(22):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0.0, 0.024)
        x, y = r * math.cos(a), r * math.sin(a)
        lean = Vector((x, y, 0)) * 0.35
        geo.box(m, x - 0.0035, x + 0.0035, y - 0.0025, y + 0.0025, 0.02, 0.025, "KK_Wood")
        geo.pipe(m, (x, y, 0.02), (x + lean.x, y + lean.y, 0.225 + rng.uniform(-0.01, 0.01)), 0.0032, "KK_Wood", 4)


def p_traystack(m, n=5):
    for k in range(n):
        z = k * 0.011
        geo.box(m, -0.18, 0.18, -0.13, 0.13, z, z + 0.004, "KK_PlasticBlack", 0.002)
        for s in (-1, 1):
            geo.box(m, -0.18, 0.18, s * 0.13 - 0.004, s * 0.13 + 0.004, z, z + 0.014, "KK_PlasticBlack", 0.002)
            geo.box(m, s * 0.18 - 0.004, s * 0.18 + 0.004, -0.13, 0.13, z, z + 0.014, "KK_PlasticBlack", 0.002)


def p_takeout(m, n=7):
    for k in range(n):
        z = k * 0.013
        geo.box(m, -0.075, 0.075, -0.058, 0.058, z, z + 0.006, "KK_PlasticCream", 0.004)
        geo.box(m, -0.08, 0.08, -0.063, 0.063, z + 0.04, z + 0.046, "KK_PlasticCream", 0.004)


def p_airpot(m):
    geo.lathe(m, (0, 0, 0), [(0.07, 0.0), (0.075, 0.01), (0.075, 0.30), (0.065, 0.31), (0.0, 0.31)], "KK_Steel", 24, cap_bottom=True, cap_top=False)
    geo.lathe(m, (0, 0, 0), [(0.066, 0.30), (0.066, 0.335), (0.05, 0.36), (0.0, 0.362)], "KK_PlasticBlack", 24, cap_bottom=True, cap_top=False)
    geo.box(m, -0.02, 0.02, -0.06, 0.03, 0.352, 0.37, "KK_PlasticBlack", 0.006)  # pump lever
    geo.pipe(m, (0, -0.066, 0.31), (0, -0.10, 0.29), 0.008, "KK_PlasticBlack", 8)  # spout
    geo.box(m, -0.03, 0.03, 0.06, 0.08, 0.20, 0.33, "KK_PlasticBlack", 0.008)  # handle


def p_bags(m):
    """Cup sleeves in plastic bags, a stack of three lying on their side."""
    for k in range(3):
        geo.cylinder(m, (0, 0, 0.045 + k * 0.09), 0.046, 0.22, "KK_PaperCream", axis="X", segments=14)


def p_box(m, sx=0.30, sy=0.20, sz=0.17, mat="KK_Cardboard"):
    geo.box(m, -sx / 2, sx / 2, -sy / 2, sy / 2, 0.0, sz, mat, 0.004)
    geo.box(m, -sx / 2 - 0.001, sx / 2 + 0.001, -0.025, 0.025, sz - 0.001, sz + 0.0008, "KK_Kraft")  # tape


def p_crate(m):
    """Plastic crate (muted blue) with onions, open top."""
    w, d, h, t = 0.40, 0.30, 0.22, 0.012
    geo.box(m, -w / 2, w / 2, -d / 2, d / 2, 0.0, 0.012, "KK_PlasticBlue", 0.003)
    for s in (-1, 1):
        geo.box(m, -w / 2, w / 2, s * d / 2 - t / 2, s * d / 2 + t / 2, 0.0, h, "KK_PlasticBlue", 0.003)
        geo.box(m, s * w / 2 - t / 2, s * w / 2 + t / 2, -d / 2, d / 2, 0.0, h, "KK_PlasticBlue", 0.003)
        geo.box(m, s * w / 2 - t, s * w / 2 + t, -0.05, 0.05, h - 0.06, h - 0.035, "KK_Rubber", 0.004)  # hand holes
    rng = geo.RNG
    for k in range(18):
        x, y = rng.uniform(-w / 2 + 0.05, w / 2 - 0.05), rng.uniform(-d / 2 + 0.05, d / 2 - 0.05)
        z = h - 0.05 + rng.uniform(-0.03, 0.02)
        geo.lathe(m, (x, y, z), [(0.0, -0.035), (0.028, -0.025), (0.036, 0.0), (0.026, 0.026), (0.006, 0.042), (0.0, 0.05)], "KK_Onion", 10,
                  cap_bottom=False, cap_top=False)


PROTOS = {
    "bowl_white": lambda m: p_bowl(m),
    "bowl_black": lambda m: p_bowl(m, outer="KK_CeramicBlack", inner="KK_CeramicRed", band=None),
    "bowl_small": lambda m: p_bowl(m, r=0.062, h=0.055, band="KK_PlasticBlue"),
    "cup": lambda m: p_cup(m),
    "cup_lid": lambda m: p_cup(m, lid=True),
    "cupstack": lambda m: p_cupstack(m),
    "cupstack_short": lambda m: p_cupstack(m, 14),
    "lidstack": lambda m: p_lidstack(m),
    "squeeze_red": lambda m: p_squeeze(m, "KK_PlasticRed"),
    "squeeze_yellow": lambda m: p_squeeze(m, "KK_PlasticYellow"),
    "squeeze_white": lambda m: p_squeeze(m, "KK_PlasticCream"),
    "soy": p_soy,
    "tare": p_tare,
    "jar_red": lambda m: p_jar(m, "KK_PlasticRed"),
    "jar_black": lambda m: p_jar(m, "KK_PlasticBlack", "KK_PlasticRed"),
    "jar_white": lambda m: p_jar(m, "KK_PlasticCream", "KK_PlasticGreen"),
    "tub_green": lambda m: p_tub(m, "KK_PlasticGreen"),
    "tub_cream": lambda m: p_tub(m, "KK_PlasticCream"),
    "tubstack": lambda m: p_tubstack(m),
    "insert_negi": lambda m: p_insert(m, "KK_Scallion"),
    "insert_chashu": lambda m: p_insert(m, "KK_Chashu"),
    "insert_menma": lambda m: p_insert(m, "KK_Menma"),
    "insert_egg": lambda m: p_insert(m, "KK_Egg"),
    "insert_lid": lambda m: p_insert(m, lid=True),
    "ladle": lambda m: p_ladle(m),
    "ladle_small": lambda m: p_ladle(m, 0.03),
    "strainer": p_strainer,
    "tebo_hang": lambda m: p_tebo(m, True),
    "tebo_well": lambda m: p_tebo(m, False),
    "tongs": p_tongs,
    "pan": p_pan,
    "towel_hang": lambda m: p_towel_hang(m),
    "towel_fold": p_towel_fold,
    "napkins": p_napkins,
    "chopsticks": p_chopsticks,
    "traystack": p_traystack,
    "takeout": p_takeout,
    "airpot": p_airpot,
    "bags": p_bags,
    "box_blue": lambda m: p_box(m, mat="KK_PlasticBlue"),
    "box_kraft": lambda m: p_box(m, mat="KK_Cardboard"),
    "box_small": lambda m: p_box(m, 0.20, 0.14, 0.12, "KK_Cardboard"),
    "crate": p_crate,
}


class Props:
    """Placements of the prototypes: (name, (x, y, z), yaw deg, scale). Unreal instances them."""

    def __init__(self):
        self.items = []

    def put(self, name, x, y, z, yaw=0.0, s=1.0):
        assert name in PROTOS, name
        self.items.append((name, (x, y, z), yaw, s))

    def stack(self, name, x, y, z, n, step, yaw=0.0, jitter=0.002):
        for k in range(n):
            self.put(name, x + geo.jitter(jitter), y + geo.jitter(jitter), z + k * step, yaw + geo.jitter(8.0))


# ---- 1. the room -----------------------------------------------------------------------------------

def room(m):
    t = 0.04
    # structure (closes the room so its lights stay in; the old recess lining is trimmed in Unreal)
    geo.box(m, XA - t, XB + t, YB, YB + t, PH - 0.02, CZ + t, "KK_Ceiling")
    geo.box(m, XA - t, XA, YF, YB, PH - 0.02, CZ + t, "KK_Ceiling")
    geo.box(m, XB, XB + t, YF, YB, PH - 0.02, CZ + t, "KK_Ceiling")
    geo.box(m, XA, XB, YF + K["bulkhead_d"], YB, CZ, CZ + t, "KK_Ceiling")
    geo.box(m, XA, XB, YF, YF + K["bulkhead_d"], SW["z1"], CZ + t, "KK_Ceiling", 0.004)  # bulkhead over the opening
    geo.box(m, XA, XB, YF, YB, PH - 0.02, PH, "KK_Floor")
    for r in geo.subtract_rects((XA - t, XB + t, PH - 0.02, CZ + t), [(SW["x0"], SW["x1"], SW["z0"] - 0.06, SW["z1"])]):
        geo.box(m, r[0], r[1], YF - t, YF, r[2], r[3], "KK_Ceiling")
    # back wall: subway-tile splashback (bevelled, one replaced tile), stainless sheets above and behind the hood
    tw, th, gap = 0.15, 0.075, 0.003
    tt = K["tile_top"]
    geo.box(m, XA, XB, YB - 0.004, YB, BT, tt, "KK_Grout")
    rows = int((tt - BT - 0.10) / (th + gap))
    z_start = tt - rows * (th + gap)
    geo.box(m, XA, XB, YB - 0.012, YB, BT, z_start, "KK_Steel", 0.002)  # stainless upstand strip under the tiles
    for r in range(rows):
        z = z_start + r * (th + gap)
        off = (r % 2) * (tw + gap) / 2
        x = XA - off
        while x < XB:
            a, b = max(x, XA), min(x + tw, XB)
            if b - a > 0.02 and not (HX0 - 0.02 < (a + b) / 2 < HX1 + 0.02):
                mat = "KK_TileOld" if (r, int((x - XA) / tw)) in ((2, 5), (4, 13)) else "KK_Tile"
                geo.box(m, a + gap / 2, b - gap / 2, YB - 0.011 + geo.jitter(0.0006), YB - 0.003, z + gap / 2, z + th + gap / 2, mat, 0.003)
            x += tw + gap
    geo.box(m, HX0 - 0.02, HX1 + 0.02, YB - 0.006, YB, BT, CZ, "KK_SteelWorn")  # behind the cooking line
    # stainless sheets above the tiles and on the side walls, with folded seam strips
    geo.box(m, XA, XB, YB - 0.004, YB, tt, CZ, "KK_WallPaint")
    for x in (XA + 0.62, XA + 1.25, HX1 + 0.32):  # painted steel panels: cover strips over the joints
        geo.box(m, x - 0.012, x + 0.012, YB - 0.008, YB - 0.004, tt, CZ, "KK_WallPaint", 0.002)
    for xs, sgn in ((XA, 1), (XB, -1)):
        geo.box(m, xs if sgn > 0 else xs - 0.004, xs + 0.004 if sgn > 0 else xs, YF, YB, PH, CZ, "KK_WallPaint")
        for y in (YF + 0.55, YF + 1.05):
            geo.box(m, xs + sgn * 0.004 - 0.002, xs + sgn * 0.008, y - 0.012, y + 0.012, tt, CZ, "KK_WallPaint", 0.002)
    # the right wall (the one the orbit sees most) carries the tile splashback too
    xr = XB - 0.004
    geo.box(m, xr - 0.004, xr, YF, YB, BT, tt, "KK_Grout")
    for r in range(rows):
        z = z_start + r * (th + gap)
        y = YF - (r % 2) * (tw + gap) / 2
        while y < YB:
            a, b = max(y, YF), min(y + tw, YB)
            if b - a > 0.02:
                mat = "KK_TileOld" if (r, int((y - YF) / tw)) in ((1, 3), (5, 7)) else "KK_Tile"
                geo.box(m, xr - 0.011 + geo.jitter(0.0006), xr - 0.003, a + gap / 2, b - gap / 2, z + gap / 2, z + th + gap / 2, mat, 0.003)
            y += tw + gap
    geo.box(m, xr - 0.012, xr, YF, YB, BT, z_start, "KK_Steel", 0.002)
    # ceiling: conduit, a junction box, the rear fluorescent batten (the room's dim fill light)
    cy = YF + K["bulkhead_d"] + 0.12
    geo.pipe(m, (XA + 0.1, cy, CZ - 0.018), (XB - 0.1, cy, CZ - 0.018), 0.011, "KK_SteelWorn", 10)
    geo.box(m, -0.62, -0.50, cy - 0.06, cy + 0.06, CZ - 0.06, CZ, "KK_SteelWorn", 0.005)
    by = YB - 0.85
    geo.box(m, -1.70, -0.40, by - 0.045, by + 0.045, CZ - 0.05, CZ, "KK_SteelWorn", 0.006)
    geo.cylinder(m, (-1.05, by, CZ - 0.062), 0.014, 1.20, "KK_Lamp", axis="X", segments=12)
    for x in (-1.66, -0.44):
        geo.box(m, x - 0.015, x + 0.015, by - 0.02, by + 0.02, CZ - 0.08, CZ - 0.05, "KK_PlasticBlack", 0.003)
    # a shorter batten over the coffee corner and the right wall
    rx0, rx1, ry = -0.05, 0.50, YB - 0.62
    geo.box(m, rx0, rx1, ry - 0.045, ry + 0.045, CZ - 0.05, CZ, "KK_SteelWorn", 0.006)
    geo.cylinder(m, ((rx0 + rx1) / 2, ry, CZ - 0.062), 0.014, rx1 - rx0 - 0.06, "KK_Lamp", axis="X", segments=12)
    for x in (rx0 + 0.03, rx1 - 0.03):
        geo.box(m, x - 0.015, x + 0.015, ry - 0.02, ry + 0.02, CZ - 0.08, CZ - 0.05, "KK_PlasticBlack", 0.003)
    return {"rear_tube": ((-1.05, by, CZ - 0.07), 1.20), "right_tube": (((rx0 + rx1) / 2, ry, CZ - 0.07), rx1 - rx0 - 0.06)}


# ---- 2. worktops, cabinets, sink -------------------------------------------------------------------

def worktops(m):
    # the pass sill through the wall's thickness and the front worktop (pass + prep), stainless, rolled edge
    geo.box(m, SW["x0"], SW["x1"], Y0 - 0.026, YF + 0.01, FT - 0.06, FT, "KK_Steel", 0.004)
    geo.box(m, SW["x0"], SW["x1"], Y0 - 0.032, Y0 - 0.018, FT - 0.035, FT + 0.002, "KK_Steel", 0.005)  # front nosing
    geo.box(m, XA, XB, YF, YFW, FT - 0.035, FT, "KK_Steel", 0.004)
    geo.box(m, XA, XB, YFW - 0.012, YFW + 0.004, FT - 0.06, FT + 0.002, "KK_Steel", 0.005)  # rolled back edge
    geo.box(m, XA, XB, YF + 0.02, YFW - 0.02, PH, FT - 0.035, "KK_Cabinet")
    # back counter: top, upstand, cabinet doors with bar handles, toe kick
    geo.box(m, XA, XB, YBC, YB, BT - 0.03, BT, "KK_Steel", 0.004)
    geo.box(m, XA, XB, YBC - 0.012, YBC + 0.004, BT - 0.05, BT + 0.002, "KK_Steel", 0.005)
    geo.box(m, XA, XB, YBC + 0.03, YB, PH + 0.09, BT - 0.03, "KK_Cabinet")
    x = XA + 0.02
    while x < XB - 0.3:
        w = min(0.46, XB - 0.02 - x)
        geo.box(m, x + 0.004, x + w - 0.004, YBC + 0.018, YBC + 0.03, PH + 0.1, BT - 0.05, "KK_Steel", 0.004)
        hx = x + w - 0.05 if int((x - XA) / 0.46) % 2 == 0 else x + 0.05
        geo.pipe(m, (hx, YBC + 0.004, BT - 0.12), (hx, YBC + 0.004, BT - 0.36), 0.006, "KK_Chrome", 8)
        for zz in (BT - 0.12, BT - 0.36):
            geo.pipe(m, (hx, YBC + 0.004, zz), (hx, YBC + 0.018, zz), 0.004, "KK_Chrome", 6)
        x += w
    geo.box(m, XA, XB, YBC + 0.06, YB, PH, PH + 0.09, "KK_PlasticBlack")
    # prep sink in the back counter (left part) with a gooseneck faucet
    sx0, sx1 = -1.98, -1.58
    geo.box(m, sx0, sx1, YBC + 0.06, YB - 0.10, BT - 0.003, BT + 0.001, "KK_Water")  # the basin's dark opening
    for (a0, a1, b0, b1) in ((sx0 - 0.01, sx1 + 0.01, YBC + 0.05, YBC + 0.06), (sx0 - 0.01, sx1 + 0.01, YB - 0.10, YB - 0.09),
                             (sx0 - 0.01, sx0, YBC + 0.05, YB - 0.09), (sx1, sx1 + 0.01, YBC + 0.05, YB - 0.09)):
        geo.box(m, a0, a1, b0, b1, BT, BT + 0.004, "KK_Steel", 0.002)
    fx, fy = (sx0 + sx1) / 2, YB - 0.055
    geo.cylinder(m, (fx, fy, BT + 0.02), 0.022, 0.04, "KK_Chrome", segments=16)
    pts = [(fx, fy, BT + 0.04), (fx, fy, BT + 0.34)]
    for k in range(1, 9):
        a = math.pi * k / 8
        pts.append((fx, fy - 0.11 * (1 - math.cos(a)) / 2 * 2, BT + 0.34 + 0.09 * math.sin(a)))
    pts.append((fx, fy - 0.22, BT + 0.27))
    polyline(m, pts, 0.011, "KK_Chrome", 10)
    for s in (-1, 1):  # wrist-action taps
        geo.pipe(m, (fx + s * 0.02, fy, BT + 0.1), (fx + s * 0.11, fy - 0.02, BT + 0.13), 0.006, "KK_Chrome", 8)


# ---- 3. the cooking line: noodle boiler, stock pot, hood ---------------------------------------------

def cooking_line(m, props):
    b0, b1 = K["boiler"]
    yb0, yb1 = YBC + 0.03, YB - 0.05
    top = BT + 0.025
    geo.box(m, b0, b1, yb0, yb1, BT - 0.03, top - 0.006, "KK_SteelWorn", 0.006)  # tank body
    geo.box(m, b0 + 0.01, b1 - 0.01, yb0 - 0.006, yb0, PH + 0.12, BT - 0.04, "KK_SteelWorn", 0.004)  # front panel
    for k, x in enumerate((b0 + 0.08, b0 + 0.16)):  # control knobs + pilot lamp
        geo.cylinder(m, (x, yb0 - 0.015, BT - 0.10), 0.016, 0.022, "KK_PlasticBlack", axis="Y", segments=14)
    geo.cylinder(m, (b0 + 0.24, yb0 - 0.008, BT - 0.10), 0.006, 0.006, "KK_LED_Amber", axis="Y", segments=10)
    nx, ny = 3, 2
    wells = []
    for i in range(nx):
        for j in range(ny):
            cx = b0 + (i + 0.5) * (b1 - b0) / nx
            cy = yb0 + (j + 0.5) * (yb1 - yb0) / ny
            wells.append((cx, cy))
    r = 0.072
    # top plate: strips between the wells, round rims, dark water inside
    xs = [b0] + [b0 + (i + 1) * (b1 - b0) / nx for i in range(nx - 1)] + [b1]
    for i in range(nx):
        cx = (xs[i] + xs[i + 1]) / 2
        geo.box(m, xs[i], cx - r, yb0, yb1, top - 0.006, top, "KK_SteelWorn")
        geo.box(m, cx + r, xs[i + 1], yb0, yb1, top - 0.006, top, "KK_SteelWorn")
        for (ya, yc) in ((yb0, wells[i * ny][1] - r), (wells[i * ny][1] + r, wells[i * ny + 1][1] - r), (wells[i * ny + 1][1] + r, yb1)):
            geo.box(m, cx - r, cx + r, ya, yc, top - 0.006, top, "KK_SteelWorn")
    for k, (cx, cy) in enumerate(wells):
        ring(m, (cx, cy, top), r, 0.004, "KK_Steel", 28, 6)
        geo.cylinder(m, (cx, cy, top - 0.03), r - 0.002, 0.003, "KK_Water", segments=28)
        geo.cylinder(m, (cx, cy, top - 0.008), r - 0.002, 0.044, "KK_SteelWorn", segments=28, cap=False)
    # baskets in four wells (one per order on the rail), handles raking toward the pass
    for k, yaw in ((0, -6), (1, 4), (2, 10), (4, -3)):
        cx, cy = wells[k]
        props.put("tebo_well", cx, cy, top - 0.13, yaw)
    # stock-pot burner and the pot (ladle resting in it, lid leaning against the upstand)
    u0, u1 = K["burner"]
    geo.box(m, u0, u1, yb0, yb1, BT - 0.02, BT + 0.06, "KK_PlasticBlack", 0.006)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        cx, cy = (u0 + u1) / 2, (yb0 + yb1) / 2
        geo.pipe(m, (cx, cy, BT + 0.07), (cx + 0.16 * math.cos(a), cy + 0.16 * math.sin(a), BT + 0.07), 0.008, "KK_Rubber", 6)
    geo.cylinder(m, (u0 + 0.06, yb0 - 0.012, BT - 0.01), 0.018, 0.024, "KK_PlasticBlack", axis="Y", segments=14)
    px, py, pz = (u0 + u1) / 2, (yb0 + yb1) / 2, BT + 0.075
    pr, ph = 0.16, 0.34
    geo.lathe(m, (px, py, pz), [(0.0, 0.0), (pr - 0.01, 0.0), (pr, 0.012), (pr, ph - 0.006), (pr + 0.006, ph), (pr - 0.004, ph + 0.002),
                                (pr - 0.006, 0.02), (0.0, 0.02)], "KK_SteelWorn", 36, cap_bottom=False, cap_top=False)
    geo.cylinder(m, (px, py, pz + ph - 0.055), pr - 0.007, 0.004, "KK_Broth", segments=36)
    for s in (-1, 1):
        geo.box(m, px + s * (pr + 0.025) - 0.02, px + s * (pr + 0.025) + 0.02, py - 0.03, py + 0.03, pz + ph - 0.07, pz + ph - 0.05, "KK_SteelWorn", 0.006)
    part(m, at(px + 0.02, py - 0.16, pz + ph + 0.19, yaw=10, pitch=28), p_ladle, 0.05)  # bowl in the broth, handle out front
    geo.cylinder(m, (u1 + 0.005, YB - 0.04, BT + 0.19), 0.15, 0.012, "KK_SteelWorn", axis="Y", segments=28)  # lid against the upstand
    # the hood: sloped front, lip, baffle filters inside, two lamps, a rail of tools along the lip
    hy0, hy1 = YB - 0.64, YB
    lipz = 1.70  # low enough that the lip and its lamps show under the opening's head
    sides = []
    for x in (HX0, HX1):
        sides.append([(x, hy1, CZ), (x, hy0 + 0.08, CZ), (x, hy0, lipz + 0.08), (x, hy0, lipz), (x, hy0 + 0.03, lipz), (x, hy1, lipz + 0.30)])
    geo.prism(m, ([Vector(p) for p in sides[0]], [Vector(p) + Vector((0.012, 0, 0)) for p in sides[0]]), "KK_SteelWorn")
    geo.prism(m, ([Vector(p) for p in sides[1]], [Vector(p) - Vector((0.012, 0, 0)) for p in sides[1]]), "KK_SteelWorn")
    front = [(hy0 + 0.08, CZ), (hy0, lipz + 0.08), (hy0, lipz), (hy0 + 0.012, lipz), (hy0 + 0.012, lipz + 0.08), (hy0 + 0.09, CZ - 0.012)]
    geo.prism(m, ([Vector((HX0, y, z)) for y, z in front], [Vector((HX1, y, z)) for y, z in front]), "KK_SteelWorn")
    geo.box(m, HX0, HX1, hy0 + 0.012, hy0 + 0.05, lipz, lipz + 0.012, "KK_SteelWorn")  # grease gutter
    # baffle filters on the inclined plane behind the lip
    f0, f1 = Vector((0, hy0 + 0.06, lipz + 0.02)), Vector((0, hy1 - 0.02, lipz + 0.26))
    nf = 3
    for k in range(nf):
        xa = HX0 + 0.03 + k * (HX1 - HX0 - 0.06) / nf
        xb = xa + (HX1 - HX0 - 0.06) / nf - 0.01
        for j in range(9):
            xx = xa + (j + 0.5) * (xb - xa) / 9
            geo.pipe(m, (xx, f0.y, f0.z), (xx, f1.y, f1.z), 0.009, "KK_Mesh", 4)
        polyline(m, [(xa, f0.y, f0.z), (xb, f0.y, f0.z), (xb, f1.y, f1.z), (xa, f1.y, f1.z), (xa, f0.y, f0.z)], 0.006, "KK_SteelWorn", 6)
    lamps = []
    for x in (HX0 + 0.25, HX1 - 0.25):  # under the gutter, in front of the filters
        geo.cylinder(m, (x, hy0 + 0.035, lipz - 0.002), 0.04, 0.02, "KK_SteelWorn", segments=20)
        geo.cylinder(m, (x, hy0 + 0.035, lipz - 0.013), 0.032, 0.006, "KK_LampHood", segments=20)
        lamps.append((x, hy0 + 0.035, lipz - 0.035))
    # a kitchen timer on the back wall between the boiler and the pot (red display), a thermometer clipped to the pot
    tx = -0.38
    geo.box(m, tx - 0.05, tx + 0.05, YB - 0.035, YB - 0.006, 1.40, 1.47, "KK_PlasticBlack", 0.008)
    geo.box(m, tx - 0.036, tx + 0.036, YB - 0.0365, YB - 0.034, 1.43, 1.458, "KK_LED_Red")
    for k in range(3):
        geo.cylinder(m, (tx - 0.025 + k * 0.025, YB - 0.037, 1.414), 0.006, 0.004, "KK_PlasticGrey", axis="Y", segments=10)
    geo.pipe(m, (px + pr * 0.7, py - pr * 0.7, pz + ph + 0.02), (px + pr * 0.55, py - pr * 0.55, pz + ph - 0.18), 0.0025, "KK_Chrome", 6)
    geo.cylinder(m, (px + pr * 0.7, py - pr * 0.7, pz + ph + 0.035), 0.018, 0.01, "KK_PlasticBlack", segments=14)
    # a short duct up through the ceiling, to the extract outside
    geo.box(m, -0.62, -0.28, YB - 0.38, YB - 0.10, CZ - 0.01, CZ + 0.04, "KK_SteelWorn", 0.004)
    # rail in front of the lip with tebo, ladles, tongs; the cleaning sticker on the lip
    ry, rz = hy0 - 0.03, lipz - 0.02
    geo.pipe(m, (HX0 + 0.03, ry, rz), (HX1 - 0.03, ry, rz), 0.006, "KK_Chrome", 8)
    for x in (HX0 + 0.03, HX1 - 0.03):
        geo.pipe(m, (x, ry, rz), (x, hy0, rz), 0.005, "KK_Chrome", 6)
    for x, name, yaw in ((HX0 + 0.16, "strainer", 0), (HX0 + 0.40, "ladle_small", 0), (HX0 + 0.50, "ladle", -8), (HX0 + 0.62, "tongs", 10)):  # slim tools only: the opening stays readable
        props.put(name, x, ry - 0.003, rz - 0.004, yaw)
    return {"hood_lamps": lamps, "hood_note": ((HX0 + 0.82, hy0 - 0.001, lipz + 0.035), "hood_note")}


# ---- 4. shelves, rails, wall stock ----------------------------------------------------------------

def shelves(m, props, cards):
    (z1, z2), (d1, d2) = K["shelves"], K["shelf_d"]
    spans = [(XA + 0.03, HX0 - 0.03), (HX1 + 0.03, XB - 0.03)]
    strips = []
    for z, d in ((z1, d1), (z2, d2)):
        for a, b in (spans if z == z2 else spans[:1]):  # the batch brewer stands where the right middle shelf would be
            geo.box(m, a, b, YB - d, YB - 0.004, z - 0.025, z, "KK_SteelWorn", 0.003)
            geo.box(m, a, b, YB - d - 0.004, YB - d + 0.012, z - 0.045, z + 0.012, "KK_SteelWorn", 0.003)  # turned-down front lip
            for x in (a + 0.06, (a + b) / 2, b - 0.06):  # brackets
                geo.prism(m, ([Vector((x - 0.004, YB - 0.004, z - 0.025)), Vector((x - 0.004, YB - d + 0.03, z - 0.025)),
                                Vector((x - 0.004, YB - 0.004, z - 0.20))],
                               [Vector((x + 0.004, YB - 0.004, z - 0.025)), Vector((x + 0.004, YB - d + 0.03, z - 0.025)),
                                Vector((x + 0.004, YB - 0.004, z - 0.20))]), "KK_SteelWorn")
            if z == z2:  # warm LED strip under the top shelf's lip, lighting the middle shelf
                geo.box(m, a + 0.05, b - 0.05, YB - d + 0.02, YB - d + 0.035, z - 0.034, z - 0.026, "KK_LampShelf")
                strips.append(((a + b) / 2, YB - d + 0.03, z - 0.04, b - a - 0.1))
    # tools rail under the middle shelf (left span): ladles, a pan, a towel; a magnetic strip with knives
    rz = z1 - 0.07
    ra, rb = -1.56, -1.20
    geo.pipe(m, (ra, YB - 0.05, rz), (rb, YB - 0.05, rz), 0.006, "KK_Chrome", 8)
    for x in (ra, rb):
        geo.pipe(m, (x, YB - 0.05, rz), (x, YB, rz), 0.005, "KK_Chrome", 6)
    for x, name, yaw in ((ra + 0.06, "ladle", 0), (ra + 0.14, "ladle_small", 4), (ra + 0.26, "pan", 0)):
        props.put(name, x, YB - 0.05, rz, yaw)
    kx0, kx1 = XA + 0.08, XA + 0.48
    geo.box(m, kx0, kx1, YB - 0.016, YB - 0.004, rz - 0.02, rz + 0.02, "KK_PlasticBlack", 0.003)
    for k, x in enumerate((kx0 + 0.06, kx0 + 0.15, kx0 + 0.25, kx0 + 0.33)):
        L = (0.21, 0.18, 0.24, 0.15)[k]
        geo.box(m, x - 0.011, x + 0.011, YB - 0.02, YB - 0.016, rz - L + 0.1, rz + 0.04, "KK_Chrome", 0.001)
        geo.box(m, x - 0.012, x + 0.012, YB - 0.026, YB - 0.016, rz + 0.04, rz + 0.15, "KK_WoodDark", 0.004)

    # top shelf (z2): backup stock and packaging, grouped, uneven
    zs = z2
    L = spans[0]
    props.put("box_blue", L[0] + 0.19, YB - 0.14, zs, 0)
    props.put("box_blue", L[0] + 0.21, YB - 0.15, zs + 0.17, -4)
    cards.card("box_noodle", (L[0] + 0.19 + 0.003, YB - 0.14 - 0.101, zs + 0.085), RIGHT, UP, 0.29, 0.16, age=0.4)
    props.put("takeout", L[0] + 0.48, YB - 0.15, zs, 0)
    props.put("takeout", L[0] + 0.48, YB - 0.15, zs + 0.092, 3)
    props.put("tubstack", L[0] + 0.64, YB - 0.12, zs, 0)
    props.put("tubstack", L[0] + 0.77, YB - 0.10, zs, 0)
    props.put("bags", L[0] + 0.93, YB - 0.16, zs, 0)
    props.put("box_small", L[1] - 0.10, YB - 0.12, zs, -6)
    R = spans[1]
    props.put("box_kraft", R[0] + 0.17, YB - 0.15, zs, 0)
    cards.card("box_cups", (R[0] + 0.17, YB - 0.15 - 0.102, zs + 0.085), RIGHT, UP, 0.28, 0.16, age=0.35)
    geo.box(m, R[0] + 0.36, R[0] + 0.46, YB - 0.20, YB - 0.04, zs, zs + 0.14, "KK_Beans", 0.02)  # bean bag
    cards.card("bag_beans", (R[0] + 0.41, YB - 0.2015, zs + 0.072), RIGHT, UP, 0.085, 0.11, age=0.2)
    # middle shelf (z1): seasonings, ingredients, bowls
    zm = z1
    props.stack("bowl_small", L[0] + 0.10, YB - 0.12, zm, 5, 0.022)
    props.stack("bowl_small", L[0] + 0.24, YB - 0.12, zm, 3, 0.022)
    for k, (n, dx) in enumerate((("jar_red", 0.40), ("jar_red", 0.455), ("jar_black", 0.51), ("jar_white", 0.57), ("jar_white", 0.625))):
        props.put(n, L[0] + dx, YB - 0.10 - 0.03 * (k % 2), zm, k * 37)
    props.put("tare", L[0] + 0.76, YB - 0.10, zm, 20)
    cards.card("label_tare", (L[0] + 0.76, YB - 0.10 - 0.0505, zm + 0.13), RIGHT, UP, 0.06, 0.08, age=0.5,
               bend=((L[0] + 0.76, YB - 0.10, 0), 0.0505))
    props.put("tare", L[0] + 0.87, YB - 0.12, zm, -30)
    props.put("tub_green", L[0] + 1.00, YB - 0.10, zm, 0)
    props.put("tub_cream", L[0] + 1.00, YB - 0.10, zm + 0.095, 40)
    cards.card("tape_negi", (L[0] + 1.00, YB - 0.10 - 0.0525, zm + 0.05), RIGHT, UP, 0.046, 0.014, age=0.4, bend=((L[0] + 1.00, YB - 0.10, 0), 0.0525))
    props.put("tub_cream", L[0] + 1.13, YB - 0.12, zm, 0)
    cards.card("tape_menma", (L[0] + 1.13, YB - 0.12 - 0.0525, zm + 0.05), RIGHT, UP, 0.046, 0.014, age=0.3, bend=((L[0] + 1.13, YB - 0.12, 0), 0.0525))
    return {"shelf_strips": strips}


# ---- 5. the work surfaces: pass + prep (front), coffee corner -------------------------------------

def prep_and_pass(m, props, cards):
    z = FT
    # bowls stacked at the pass's left (white with a red band, and black/red), a stack of trays behind the jamb
    for x, n, kind in ((-1.79, 5, "bowl_white"), (-1.60, 4, "bowl_white"), (-1.42, 3, "bowl_black")):
        props.stack(kind, x, YF + 0.16, z, n, 0.024)
    props.put("traystack", -2.12, YF + 0.20, z, 2)
    props.put("towel_fold", -2.15, YF + 0.20, z + 0.07, -8)
    # cutting board with a knife and chopped scallions; the topping rail behind it
    geo.box(m, -1.30, -0.96, YF + 0.04, YF + 0.24, z, z + 0.022, "KK_Wood", 0.004)
    geo.box(m, -1.27, -1.08, YF + 0.10, YF + 0.125, z + 0.022, z + 0.025, "KK_Chrome", 0.001)  # blade
    geo.box(m, -1.08, -0.98, YF + 0.105, YF + 0.12, z + 0.022, z + 0.036, "KK_WoodDark", 0.005)
    rng = geo.RNG
    for _ in range(40):
        x, y = rng.uniform(-1.22, -1.06), rng.uniform(YF + 0.15, YF + 0.21)
        geo.lathe(m, (x, y, z + 0.022), [(0.0035, 0.0), (0.0055, 0.0), (0.0055, 0.0022), (0.0035, 0.0022)], "KK_Scallion", 8,
                  cap_bottom=False, cap_top=False)  # sliced rings, lying flat
    rail_y = YF + 0.34
    geo.box(m, -1.40, -0.66, rail_y - 0.09, rail_y + 0.09, z, z + 0.012, "KK_SteelWorn", 0.004)
    for k, n in enumerate(("insert_negi", "insert_chashu", "insert_menma", "insert_egg")):
        props.put(n, -1.31 + k * 0.18, rail_y, z + 0.012 + 0.004, 0)
    # two bowls set out for the next order (tare in the bottom), a ladle resting on a dish
    for x in (-0.86, -0.66):
        props.put("bowl_white", x, YF + 0.14, z, 15)
        geo.cylinder(m, (x, YF + 0.14, z + 0.016), 0.03, 0.002, "KK_Soy", segments=16)
    geo.lathe(m, (-0.50, YF + 0.10, z), [(0.0, 0.0), (0.05, 0.0), (0.07, 0.012), (0.066, 0.013), (0.0, 0.004)], "KK_CeramicWhite", 20,
              cap_bottom=False, cap_top=False)
    part(m, at(-0.53, YF + 0.38, z + 0.17, yaw=-12, pitch=-62), p_ladle, 0.042)  # bowl on the dish, handle back
    # seasoning and sauce on the right of the pass
    props.put("squeeze_red", -0.42, YF + 0.30, z, 0)
    props.put("squeeze_yellow", -0.36, YF + 0.31, z, 30)
    props.put("tub_cream", -0.30, YF + 0.16, z, 0)
    cards.card("tape_chashu", (-0.30, YF + 0.16 - 0.0525, z + 0.05), RIGHT, UP, 0.046, 0.014, age=0.3, bend=((-0.30, YF + 0.16, 0), 0.0525))
    props.put("jar_red", -0.22, YF + 0.28, z, 0)
    props.put("jar_black", -0.17, YF + 0.30, z, 0)
    # the coffee corner (front worktop right of the opening): cup stacks, lids, sugar caddy, the grinder
    cx = K["coffee_x"]
    props.put("cupstack", cx - 0.12, YF + 0.10, z, 0)
    props.put("cupstack", cx - 0.02, YF + 0.12, z, 0)
    props.put("cupstack_short", cx + 0.08, YF + 0.09, z, 0)
    props.put("lidstack", cx + 0.08, YF + 0.22, z, 0)
    geo.box(m, cx - 0.17, cx - 0.04, YF + 0.22, YF + 0.33, z, z + 0.06, "KK_Steel", 0.004)  # sugar / creamer caddy
    for k in range(9):
        geo.box(m, cx - 0.16 + k * 0.012, cx - 0.155 + k * 0.012, YF + 0.235, YF + 0.29, z + 0.03, z + 0.11, "KK_PaperCream", 0.001)
    for k in range(5):
        geo.cylinder(m, (cx - 0.075 + (k % 3) * 0.018, YF + 0.30 - (k // 3) * 0.02, z + 0.07), 0.008, 0.016, "KK_PlasticCream", segments=8)
    gx = cx + 0.30
    geo.box(m, gx - 0.08, gx + 0.08, YF + 0.16, YF + 0.36, z, z + 0.05, "KK_PlasticBlack", 0.01)  # grinder base
    geo.box(m, gx - 0.065, gx + 0.065, YF + 0.24, YF + 0.36, z + 0.05, z + 0.30, "KK_PlasticBlack", 0.02)
    geo.box(m, gx - 0.03, gx + 0.03, YF + 0.20, YF + 0.24, z + 0.17, z + 0.24, "KK_Steel", 0.006)  # spout
    geo.lathe(m, (gx, YF + 0.30, z + 0.30), [(0.035, 0.0), (0.075, 0.13), (0.075, 0.16), (0.0, 0.16)], "KK_Beans", 20, cap_bottom=True, cap_top=False)
    geo.lathe(m, (gx, YF + 0.30, z + 0.46), [(0.078, 0.0), (0.078, 0.012), (0.0, 0.03)], "KK_PlasticBlack", 20, cap_bottom=True, cap_top=False)
    cards.card("tape_beans", (gx, YF + 0.2395, z + 0.12), RIGHT, UP, 0.046, 0.014, age=0.3)


def back_counter(m, props, cards):
    """The back counter away from the boiler: prep side (left: sink, rice cooker, tare) and the
    coffee side (right: batch brewer over an airpot, a second airpot, the beans)."""
    z = BT
    # rice cooker at the far left, the tare bottles and a soup tub by the hood
    rx, ry = XA + 0.165, YB - 0.24
    geo.lathe(m, (rx, ry, z), [(0.0, 0.0), (0.13, 0.0), (0.14, 0.02), (0.14, 0.18), (0.13, 0.20), (0.0, 0.20)], "KK_PlasticCream", 28, cap_bottom=False, cap_top=False)
    geo.lathe(m, (rx, ry, z + 0.20), [(0.13, 0.0), (0.12, 0.04), (0.06, 0.07), (0.0, 0.075)], "KK_PlasticCream", 28, cap_bottom=False, cap_top=False)
    geo.box(m, rx - 0.05, rx + 0.05, ry - 0.145, ry - 0.125, z + 0.08, z + 0.14, "KK_PlasticBlack", 0.006)
    geo.box(m, rx + 0.015, rx + 0.035, ry - 0.147, ry - 0.145, z + 0.12, z + 0.13, "KK_LED_Amber")
    geo.box(m, rx - 0.07, rx + 0.07, ry - 0.02, ry + 0.02, z + 0.27, z + 0.29, "KK_PlasticBlack", 0.008)
    for k, (dx, dy) in enumerate(((-1.48, YB - 0.21), (-1.37, YB - 0.19))):  # in front of the hanging tools
        props.put("tare", dx, dy, z, 10 * k)
    cards.card("tape_shoyu", (-1.48, YB - 0.21 - 0.0505, z + 0.16), RIGHT, UP, 0.05, 0.015, age=0.5, bend=((-1.48, YB - 0.21, 0), 0.0505))
    cards.card("tape_shio", (-1.37, YB - 0.19 - 0.0505, z + 0.16), RIGHT, UP, 0.05, 0.015, age=0.4, bend=((-1.37, YB - 0.19, 0), 0.0505))
    props.put("squeeze_white", -1.27, YB - 0.33, z, 0)
    props.put("tub_green", -1.18, YB - 0.22, z, 0)
    cards.card("tape_miso", (-1.18, YB - 0.22 - 0.0525, z + 0.05), RIGHT, UP, 0.046, 0.014, age=0.35, bend=((-1.18, YB - 0.22, 0), 0.0525))
    # coffee side: batch brewer (brew basket over an airpot), its display, a second airpot
    cx0 = HX1 + 0.08
    bx0, bx1 = cx0, cx0 + 0.24
    by1 = YB - 0.04
    geo.box(m, bx0, bx1, by1 - 0.40, by1, z, z + 0.03, "KK_Steel", 0.006)  # drip base
    geo.box(m, bx0, bx1, by1 - 0.16, by1, z, z + 0.62, "KK_Steel", 0.012)  # tower
    geo.box(m, bx0, bx1, by1 - 0.40, by1 - 0.16, z + 0.44, z + 0.62, "KK_Steel", 0.012)  # head
    geo.box(m, bx0 + 0.03, bx1 - 0.03, by1 - 0.402, by1 - 0.398, z + 0.47, z + 0.58, "KK_PlasticBlack", 0.004)  # panel
    geo.box(m, bx0 + 0.035, bx1 - 0.035, by1 - 0.39, by1 - 0.17, z + 0.38, z + 0.44, "KK_PlasticBlack", 0.008)  # brew basket
    geo.box(m, (bx0 + bx1) / 2 - 0.012, (bx0 + bx1) / 2 + 0.012, by1 - 0.48, by1 - 0.39, z + 0.40, z + 0.42, "KK_PlasticBlack", 0.005)  # handle
    cards.card("brewer_panel", ((bx0 + bx1) / 2, by1 - 0.4035, z + 0.545), RIGHT, UP, 0.07, 0.03, age=0.3)
    for k, x in enumerate((bx0 + 0.06, bx0 + 0.10, bx1 - 0.06)):
        geo.cylinder(m, (x, by1 - 0.404, z + 0.495), 0.008, 0.006, "KK_LED_Green" if k == 0 else "KK_PlasticGrey", axis="Y", segments=10)
    props.put("airpot", (bx0 + bx1) / 2, by1 - 0.26, z + 0.03, 0)
    props.put("airpot", bx1 + 0.10, YB - 0.22, z, -20)
    cards.card("tape_hot", (bx1 + 0.10, YB - 0.22 - 0.0755, z + 0.22), RIGHT, UP, 0.046, 0.014, age=0.3, bend=((bx1 + 0.10, YB - 0.22, 0), 0.0755))


def right_wall(m, props, cards):
    """The kitchen's right wall, the surface the orbit looks at most: a wire rack with stock over
    the aisle, the calendar and the temperature log, a towel on a hook."""
    x = XB - 0.004
    ya, yb = YFW + 0.06, YBC - 0.06
    for zr in (1.34, 1.66):
        geo.box(m, x - 0.25, x, ya, yb, zr - 0.006, zr, "KK_Mesh")
        geo.pipe(m, (x - 0.25, ya, zr), (x - 0.25, yb, zr), 0.004, "KK_Chrome", 6)
        for yy in (ya + 0.02, yb - 0.02):
            geo.pipe(m, (x, yy, zr - 0.14), (x - 0.24, yy, zr - 0.002), 0.004, "KK_Chrome", 6)
    props.stack("bowl_white", x - 0.13, ya + 0.12, 1.34, 6, 0.024)
    props.stack("bowl_black", x - 0.13, ya + 0.33, 1.34, 4, 0.024)
    props.put("box_blue", x - 0.15, yb - 0.17, 1.66, 90)
    props.put("bags", x - 0.12, ya + 0.15, 1.66, 90)
    # paperwork near the front (seen first through the opening)
    cards.card("calendar", (x - 0.002, YF + 0.20, 1.52), Vector((0, -1, 0)), UP, 0.17, 0.25, age=0.5)
    ty = YF + 0.395
    cards.card("temp_log", (x - 0.0045, ty, 1.355), Vector((0, -1, 0)), UP, 0.15, 0.21, age=0.6)
    geo.box(m, x - 0.004, x - 0.002, ty - 0.08, ty + 0.08, 1.24, 1.48, "KK_Wood", 0.002)  # clipboard
    geo.box(m, x - 0.012, x - 0.004, ty - 0.05, ty + 0.05, 1.455, 1.485, "KK_PlasticBlack", 0.004)  # its clip
    props.put("towel_hang", x - 0.03, YF + 0.62, 1.30, 90)
    geo.pipe(m, (x, YF + 0.62, 1.30), (x - 0.03, YF + 0.62, 1.30), 0.004, "KK_Chrome", 6)


# ---- 6. the pass rail of order tickets ------------------------------------------------------------

def ticket_rail(m, cards):
    """A ticket rail hung from the bulkhead, just inside the inner frame: the tickets face the cook;
    the customer sees their backs glowing in the prep light."""
    y, z = YF + 0.06, 1.69
    x0, x1 = -1.66, -0.62
    geo.box(m, x0, x1, y - 0.012, y + 0.012, z - 0.006, z + 0.016, "KK_Steel", 0.003)
    for x in (x0 + 0.03, x1 - 0.03):
        geo.box(m, x - 0.006, x + 0.006, y - 0.004, y + 0.004, z + 0.016, SW["z1"], "KK_Steel", 0.001)
    for k, (tx, rot) in enumerate(((-1.56, 2.0), (-1.47, -3.0), (-1.38, 1.0), (-1.06, -2.0), (-0.97, 4.0))):
        w, h = 0.058, 0.084
        c = Vector((tx, y + 0.0, z - h / 2 + 0.004))
        a = math.radians(rot)
        r = Vector((math.cos(a), 0, math.sin(a)))
        up = Vector((-math.sin(a), 0, math.cos(a)))
        cards.card(f"ticket_{k}", c + Vector((0, 0.0015, 0)), r * -1, up, w, h, age=0.2)  # face toward the kitchen
        cards.card("ticket_back", c - Vector((0, 0.0015, 0)), r, up, w, h, age=0.2)
    # one more spiked on the pass by the bowls
    geo.box(m, -0.73, -0.69, YF + 0.29, YF + 0.33, FT, FT + 0.008, "KK_PlasticBlack", 0.003)
    geo.pipe(m, (-0.71, YF + 0.31, FT + 0.008), (-0.71, YF + 0.31, FT + 0.13), 0.0018, "KK_Chrome", 6)
    cards.card("ticket_5", (-0.71, YF + 0.312, FT + 0.07), Vector((-1, 0, 0)), Vector((0, -0.3, 1)), 0.058, 0.084, age=0.25)


# ---- 7. the order terminal ------------------------------------------------------------------------

def terminal(m, cards):
    x0, x1, z0 = P["x0"], P["x1"], P["z0"]
    xc = (x0 + x1) / 2
    pd = P["pedestal_d"]
    dk_out, dk_lo, dk_hi = P["deck"]
    pz0, pz1 = P["pod"]
    pf0, pf1 = P["pod_d"]
    # pedestal on the wall (covers the old machine's footprint), bolted, flex conduit up into the wall
    geo.box(m, x0, x1, Y0 - pd, Y0 + 0.002, z0, pz1 + 0.02, "KK_POSDark", 0.012, 2)
    geo.bolts(m, [(x, Y0 - pd, z) for x in (x0 + 0.03, x1 - 0.03) for z in (z0 + 0.25, pz1 - 0.02)], "-Y", "KK_Chrome", 0.009)
    polyline(m, [(x1 - 0.06, Y0 - 0.05, pz1 + 0.02), (x1 - 0.06, Y0 - 0.05, pz1 + 0.09), (x1 - 0.06, Y0 - 0.02, pz1 + 0.14),
                 (x1 - 0.06, Y0 + 0.01, pz1 + 0.15)], 0.011, "KK_Rubber", 10)
    # payment unit: a sloped keypad deck facing the customer
    ux0, ux1 = x0 + 0.012, x1 - 0.012
    yo, yi = Y0 - dk_out, Y0 - pd
    side = [(yi, z0), (yo, z0), (yo, z0 + dk_lo), (yi, z0 + dk_hi)]
    geo.prism(m, ([Vector((ux0, y, zz)) for y, zz in side], [Vector((ux1, y, zz)) for y, zz in side]), "KK_POS")
    for x in (ux0 - 0.004, ux1 - 0.002):  # rubber bumpers on the front corners
        geo.box(m, x, x + 0.006, yo - 0.006, yo + 0.04, z0 + 0.005, z0 + dk_lo + 0.004, "KK_POSDark", 0.003)
    geo.box(m, ux0 + 0.01, ux1 - 0.01, yo - 0.008, yo + 0.01, z0, z0 + 0.012, "KK_Rubber", 0.003)  # foot strip
    slope = math.atan2(dk_hi - dk_lo, dk_out - pd)  # deck angle
    n_deck = Vector((0, -math.sin(slope), math.cos(slope)))
    d_up = Vector((0, math.cos(slope), math.sin(slope)))  # up the deck, toward the wall

    def deck(u, v):  # point on the deck surface: u along x, v metres up the slope from the front edge
        return Vector((u, yo, z0 + dk_lo)) + d_up * v

    # keypad 3 x 4 (26 mm pitch), function keys, legends
    kp0 = xc - 0.035
    for i in range(3):
        for j in range(4):
            c = deck(kp0 + (i - 1) * 0.026, 0.026 + (3 - j) * 0.026)
            part(m, Matrix.Translation(c) @ Matrix.Rotation(slope, 4, "X"), lambda mm: geo.box(mm, -0.011, 0.011, -0.009, 0.009, 0.0, 0.008,
                                                                                                "KK_PlasticGrey", 0.003))
    for j, mat in enumerate(("KK_PlasticRed", "KK_PlasticYellow", "KK_PlasticGreen")):
        c = deck(kp0 + 0.062, 0.026 + (2 - j) * 0.026 + 0.013)
        part(m, Matrix.Translation(c) @ Matrix.Rotation(slope, 4, "X"), lambda mm, mt=mat: geo.box(mm, -0.011, 0.011, -0.011, 0.011, 0.0, 0.009, mt, 0.003))
    cards.card("pos_keys", deck(kp0, 0.065) + n_deck * 0.0085, RIGHT, d_up, 0.078, 0.104, age=0.6)
    cards.card("pos_fkeys", deck(kp0 + 0.062, 0.065) + n_deck * 0.0095, RIGHT, d_up, 0.026, 0.078, age=0.5)
    # contactless pad (raised glossy plate + the ring of LEDs above it), the amber display
    tc = deck(x0 + 0.075, 0.075)
    part(m, Matrix.Translation(tc) @ Matrix.Rotation(slope, 4, "X"), lambda mm: geo.box(mm, -0.036, 0.036, -0.03, 0.03, 0.0, 0.006, "KK_PlasticBlack", 0.004))
    cards.card("pos_tap", tc + n_deck * 0.0065, RIGHT, d_up, 0.064, 0.052, age=0.3)
    for k in range(4):
        c = deck(x0 + 0.05 + k * 0.016, 0.125)
        part(m, Matrix.Translation(c) @ Matrix.Rotation(slope, 4, "X"), lambda mm: geo.cylinder(mm, (0, 0, 0.002), 0.0035, 0.004, "KK_LED_Green", segments=8))
    cards.card("pos_lcd", deck(xc + 0.035, 0.150) + n_deck * 0.001, RIGHT, d_up, 0.056, 0.016, age=0.4)
    # card slot + receipt slot on the front face, a curled receipt hanging out
    geo.box(m, xc - 0.045, xc + 0.045, yo - 0.004, yo + 0.002, z0 + 0.035, z0 + 0.045, "KK_PlasticBlack", 0.002)
    geo.box(m, xc - 0.04, xc + 0.04, yo - 0.003, yo + 0.002, z0 + 0.062, z0 + 0.068, "KK_Rubber", 0.001)
    pts = [Vector((0, yo - 0.002, z0 + 0.065))]
    for k in range(1, 10):
        a = k / 9 * math.pi * 0.8
        pts.append(Vector((0, yo - 0.002 - 0.045 * math.sin(a), z0 + 0.065 - 0.05 * (1 - math.cos(a)) + 0.012 * math.sin(a))))
    for p, q in zip(pts, pts[1:]):
        geo.prism(m, ([Vector((xc - 0.029, p.y, p.z)), Vector((xc - 0.029, q.y, q.z)), Vector((xc - 0.029, q.y + 0.0008, q.z + 0.0008))],
                      [Vector((xc + 0.029, p.y, p.z)), Vector((xc + 0.029, q.y, q.z)), Vector((xc + 0.029, q.y + 0.0008, q.z + 0.0008))]),
                  "KK_PaperCream")
    # screen pod: hooded housing, face tilted back, deep bezel, the screen, status LEDs on the visor
    side = [(Y0 - pd, pz0 - 0.02), (Y0 - pf0 - 0.01, pz0 - 0.02), (Y0 - pf0, pz0), (Y0 - pf1, pz1), (Y0 - pd, pz1 + 0.01)]
    geo.prism(m, ([Vector((x0 + 0.004, y, zz)) for y, zz in side], [Vector((x1 - 0.004, y, zz)) for y, zz in side]), "KK_POS")
    tilt = math.atan2(pf0 - pf1, pz1 - pz0)
    n_face = Vector((0, -math.cos(tilt), math.sin(tilt)))
    f_up = Vector((0, math.sin(tilt), math.cos(tilt)))
    fc = Vector((xc, Y0 - (pf0 + pf1) / 2, (pz0 + pz1) / 2))
    rot_face = Matrix.Rotation(-tilt, 4, "X")
    def bezel(mm):  # a deep frame round the screen opening, the dark glass recessed behind it
        for (a0, a1, b0, b1) in ((-0.17, 0.17, 0.094, 0.155), (-0.17, 0.17, -0.155, -0.07), (-0.17, -0.116, -0.07, 0.094),
                                 (0.116, 0.17, -0.07, 0.094)):
            geo.box(mm, a0, a1, -0.016, 0.0, b0, b1, "KK_POSDark", 0.004, 2)
        geo.box(mm, -0.118, 0.118, -0.004, 0.0, -0.072, 0.096, "KK_PlasticBlack", 0.002)
    part(m, Matrix.Translation(fc) @ rot_face, bezel)
    cards.card("pos_screen", fc + n_face * 0.0045 + f_up * 0.012, RIGHT, f_up, 0.226, 0.163, age=0.3)
    cards.card("pos_brand", fc + n_face * 0.0165 - f_up * 0.112, RIGHT, f_up, 0.054, 0.009, age=0.3)
    cards.card("pos_nocash", fc + n_face * 0.0165 + RIGHT * -0.115 - f_up * 0.128, RIGHT, f_up, 0.04, 0.015, age=0.6)
    # visor over the top and the side cheeks (as the reference's hooded frame)
    vz = pz1 + 0.012
    geo.box(m, x0 - 0.004, x1 + 0.004, Y0 - pf1 - P["visor"], Y0 - pd + 0.005, vz, vz + 0.016, "KK_POSDark", 0.004)
    for x in (x0 - 0.004, x1 - 0.008):
        geo.prism(m, ([Vector((x, Y0 - pd, pz0 + 0.06)), Vector((x, Y0 - pf0 - 0.012, pz0 + 0.02)), Vector((x, Y0 - pf1 - P["visor"], vz)),
                       Vector((x, Y0 - pd, vz))],
                      [Vector((x + 0.012, Y0 - pd, pz0 + 0.06)), Vector((x + 0.012, Y0 - pf0 - 0.012, pz0 + 0.02)),
                       Vector((x + 0.012, Y0 - pf1 - P["visor"], vz)), Vector((x + 0.012, Y0 - pd, vz))]), "KK_POSDark")
    for k, mat in enumerate(("KK_LED_Green", "KK_LED_Amber", "KK_LED_Red")):
        geo.cylinder(m, (x1 - 0.04 - k * 0.018, Y0 - pf1 - P["visor"] + 0.004, vz + 0.008), 0.0045, 0.008, mat, axis="Y", segments=10)
    for x in (x0 + 0.012, x1 - 0.012):  # corner bumpers at the pod's lower corners
        geo.box(m, x - 0.014, x + 0.014, Y0 - pf0 - 0.018, Y0 - pf0 + 0.02, pz0 - 0.022, pz0 + 0.02, "KK_Rubber", 0.006)
    # the maintenance sticker and asset tag on the pod's side, a speaker grille
    cards.card("pos_service", (x1 + 0.0065, Y0 - 0.15, pz0 + 0.12), Vector((0, 1, 0)), UP, 0.042, 0.027, age=0.5)
    cards.card("pos_asset", (x1 - 0.0115, Y0 - 0.19, z0 + 0.06), Vector((0, 1, 0)), UP, 0.04, 0.014, age=0.6)
    for k in range(6):
        geo.box(m, x0 + 0.03 + k * 0.008, x0 + 0.034 + k * 0.008, Y0 - pd - 0.002, Y0 - pd, pz0 - 0.12, pz0 - 0.07, "KK_PlasticBlack")
    return {"screen": (tuple(fc - n_face * 0.06), tuple(-n_face))}


# ---- 8. the customer counter: top sheet + things on it --------------------------------------------

def counter_top(m_counter):
    """Stainless top sheet on the customer counter, in pieces round the jambs, posts and the terminal,
    with the sheet seams where the pieces meet. UV1 (0..1 over the counter) is set by the builder."""
    zt = CO["z"]
    jw, jp = C.MASSING["service_jamb_w"], C.MASSING["service_jamb_proud"]
    fw = C.SHELL["frame_w"]
    pw, pp = C.SERVICE_POSTS["w"], C.SERVICE_POSTS["proud"]
    holes = [(P["x0"] - 0.006, P["x1"] + 0.006, Y0 - P["deck"][0] - 0.01, Y0 + 0.01),
             (SW["x0"] - fw - jw - pw - 0.03, SW["x0"] - fw + 0.025, Y0 - jp - 0.02, Y0 + 0.01),
             (SW["x1"] + fw - 0.025, SW["x1"] + fw + jw + pw + 0.03, Y0 - jp - 0.02, Y0 + 0.01),
             (SW["x0"] - 0.01, SW["x1"] + 0.01, Y0 - 0.03, Y0 + 0.01)]
    seams = (-1.15, -0.62)
    pieces = []
    for r in geo.subtract_rects((CO["x0"] + 0.004, CO["x1"] - 0.004, YCF - 0.002, Y0 - 0.004), holes):
        cuts = [r[0]] + [s for s in seams if r[0] < s < r[1]] + [r[1]]
        for a, b in zip(cuts, cuts[1:]):
            pieces.append((a + (0.0012 if a in seams else 0), b - (0.0012 if b in seams else 0), r[2], r[3]))
    for a, b, c, d in pieces:
        geo.box(m_counter, a, b, c, d, zt + 0.0004, zt + 0.0032, "KK_SteelCounter", 0.0012)
    # rolled front nose over the old edge
    for a, b, c, d in pieces:
        if c < YCF + 0.01:
            geo.box(m_counter, a, b, YCF - 0.008, YCF + 0.004, zt - 0.03, zt + 0.0032, "KK_SteelCounter", 0.003)
    return pieces


def counter_items(m, props, cards):
    zt = CO["z"] + 0.0032
    y = Y0 - 0.20
    # napkins + chopsticks just left of the opening, in front of the jamb
    props.put("napkins", -1.83, YCF + 0.10, zt, 4)
    props.put("chopsticks", -1.69, YCF + 0.09, zt, 0)
    # condiment caddy: chili oil, soy, vinegar, shichimi, pepper
    cx, cy = -1.12, YCF + 0.12
    geo.box(m, cx - 0.12, cx + 0.12, cy - 0.06, cy + 0.06, zt, zt + 0.006, "KK_Steel", 0.003)
    for s in (-1, 1):
        geo.box(m, cx - 0.12, cx + 0.12, cy + s * 0.06 - 0.002, cy + s * 0.06 + 0.002, zt, zt + 0.035, "KK_Steel", 0.001)
    geo.pipe(m, (cx, cy, zt + 0.006), (cx, cy, zt + 0.17), 0.005, "KK_Chrome", 8)
    ring(m, (cx, cy, zt + 0.17), 0.018, 0.004, "KK_Chrome", 16, 6, axis="Y")
    props.put("soy", cx - 0.085, cy - 0.02, zt + 0.006, 30)
    props.put("squeeze_red", cx - 0.035, cy + 0.02, zt + 0.006, 0)
    props.put("soy", cx + 0.035, cy + 0.02, zt + 0.006, 200)
    props.put("jar_red", cx + 0.07, cy - 0.025, zt + 0.006, 0)
    props.put("jar_black", cx + 0.095, cy + 0.025, zt + 0.006, 0)
    # the pickup spot: a tray with a lidded coffee and a covered bowl, by the right of the opening
    tx, ty = -0.52, YCF + 0.17
    geo.box(m, tx - 0.17, tx + 0.17, ty - 0.12, ty + 0.12, zt, zt + 0.006, "KK_PlasticBlack", 0.003)
    for s in (-1, 1):
        geo.box(m, tx - 0.17, tx + 0.17, ty + s * 0.12 - 0.004, ty + s * 0.12 + 0.004, zt, zt + 0.016, "KK_PlasticBlack", 0.002)
        geo.box(m, tx + s * 0.17 - 0.004, tx + s * 0.17 + 0.004, ty - 0.12, ty + 0.12, zt, zt + 0.016, "KK_PlasticBlack", 0.002)
    props.put("cup_lid", tx + 0.09, ty + 0.02, zt + 0.006, 0)
    props.put("bowl_black", tx - 0.06, ty, zt + 0.006, 0)
    geo.lathe(m, (tx - 0.06, ty, zt + 0.006 + 0.084), [(0.0, 0.016), (0.06, 0.012), (0.094, 0.0), (0.096, -0.004)], "KK_CeramicBlack", 28,
              cap_bottom=False, cap_top=False)  # its lid
    geo.box(m, tx - 0.07, tx - 0.05, ty - 0.11, ty - 0.03, zt + 0.006, zt + 0.012, "KK_PaperCream")  # chopsticks in paper
    # a ticket spike with receipts by the terminal; a stack of trays and the menu stand at the right
    sx = P["x1"] + 0.08
    geo.cylinder(m, (sx, YCF + 0.08, zt + 0.004), 0.03, 0.008, "KK_PlasticBlack", segments=16)
    geo.pipe(m, (sx, YCF + 0.08, zt + 0.008), (sx, YCF + 0.08, zt + 0.13), 0.0018, "KK_Chrome", 6)
    for k in range(3):
        cards.card(f"ticket_{(k + 2) % 5}", (sx + 0.003 * k, YCF + 0.08 + 0.002 * k, zt + 0.055 + k * 0.01),
                   Vector((math.cos(0.5 * k), math.sin(0.5 * k), 0)), Vector((0, 0.15, 1)), 0.058, 0.084, age=0.35)
    props.put("traystack", 0.30, YCF + 0.20, zt, 3)
    geo.box(m, 0.52, 0.66, YCF + 0.06, YCF + 0.12, zt, zt + 0.01, "KK_PlasticBlack", 0.003)
    part(m, at(0.59, YCF + 0.09, zt + 0.01, pitch=-12), lambda mm: geo.box(mm, -0.062, 0.062, -0.003, 0.003, 0.0, 0.165, "KK_PlasticCream", 0.002))
    cards.card("k_menu", (0.59, YCF + 0.09 - 0.004 - 0.0175, zt + 0.01 + 0.081), RIGHT, Vector((0, 0.21, 0.98)), 0.12, 0.16, age=0.3)


# ---- 9. under the counter -------------------------------------------------------------------------

def under_counter(m, props, cards):
    yf = Y0 - C.MASSING["base_proud"] - 0.012  # in front of the base frame
    zc = CO["z"] - CO["thickness"] - 0.01
    # under-counter fridge (stainless), vent grille, handles, temperature display. Exterior pass (2026-10-09):
    # one door (was two) between the right stool and the gusset at 0.53, hinged on the side away from the stool
    fx0, fx1, ftop = U["fridge"]
    fd = 0.26  # slim: the stools' back legs stand just in front
    geo.box(m, fx0, fx1, yf - fd, yf, PH + 0.04, ftop, "KK_SteelWorn", 0.008)
    for k in range(4):  # adjustable feet
        geo.cylinder(m, (fx0 + 0.04 + (k % 2) * (fx1 - fx0 - 0.08), yf - fd + 0.04 + (k // 2) * (fd - 0.08), PH + 0.02), 0.014, 0.04, "KK_PlasticBlack", segments=10)
    xm = (fx0 + fx1) / 2
    doors = ((fx0 + 0.005, fx1 - 0.005),) if U.get("fridge_hinge") else ((fx0 + 0.005, xm - 0.002), (xm + 0.002, fx1 - 0.005))
    for a, b in doors:
        geo.box(m, a, b, yf - fd - 0.02, yf - fd + 0.002, PH + 0.14, ftop - 0.015, "KK_SteelWorn", 0.006)
        if len(doors) == 1:  # handle on the free edge, hinge knuckles on the hinge side
            right = U["fridge_hinge"] == "right"
            hx = a + 0.03 if right else b - 0.03
            for z in (PH + 0.18, ftop - 0.06):
                geo.cylinder(m, (b - 0.004 if right else a + 0.004, yf - fd - 0.021, z), 0.006, 0.045, "KK_Chrome", segments=8)
        else:
            hx = b - 0.03 if a < xm else a + 0.03
        geo.box(m, hx - 0.008, hx + 0.008, yf - fd - 0.045, yf - fd - 0.02, ftop - 0.24, ftop - 0.05, "KK_Chrome", 0.004)
        geo.box(m, a + 0.02, b - 0.02, yf - fd - 0.0205, yf - fd - 0.019, ftop - 0.03, ftop - 0.022, "KK_Rubber")  # gasket line
    for k in range(8):
        z = PH + 0.06 + k * 0.009
        geo.box(m, fx0 + 0.03, fx1 - 0.03, yf - fd - 0.004, yf - fd + 0.002, z, z + 0.004, "KK_PlasticBlack")
    cards.card("fridge_display", (xm, yf - fd - 0.0215, ftop - 0.012 - 0.03), RIGHT, UP, 0.04, 0.014, age=0.3)
    geo.box(m, xm - 0.025, xm + 0.025, yf - fd - 0.021, yf - fd - 0.019, ftop - 0.058, ftop - 0.024, "KK_PlasticBlack")
    props.put("crate", xm - 0.04, yf - 0.135, ftop + 0.002, 3)  # a crate of onions on top, under the counter
    # drawers under the terminal end: a three-drawer steel unit, padlock hasp on the top drawer
    dx0, dx1, dtop = U["drawers"]
    dd = 0.34
    geo.box(m, dx0, dx1, yf - dd, yf, PH + 0.03, dtop, "KK_Cabinet", 0.008)
    hs = (dtop - PH - 0.06) / 3
    for k in range(3):
        z0 = PH + 0.05 + k * hs
        geo.box(m, dx0 + 0.012, dx1 - 0.012, yf - dd - 0.016, yf - dd + 0.002, z0 + 0.006, z0 + hs - 0.006, "KK_Cabinet", 0.005)
        geo.box(m, (dx0 + dx1) / 2 - 0.06, (dx0 + dx1) / 2 + 0.06, yf - dd - 0.035, yf - dd - 0.016, z0 + hs - 0.05, z0 + hs - 0.035, "KK_Chrome", 0.004)
        geo.box(m, (dx0 + dx1) / 2 - 0.03, (dx0 + dx1) / 2 + 0.03, yf - dd - 0.0165, yf - dd - 0.015, z0 + hs * 0.35, z0 + hs * 0.6,
                "KK_PaperCream")  # card holder label
    geo.box(m, dx1 - 0.05, dx1 - 0.03, yf - dd - 0.03, yf - dd - 0.016, dtop - 0.09, dtop - 0.04, "KK_Chrome", 0.002)
    ring(m, (dx1 - 0.04, yf - dd - 0.04, dtop - 0.10), 0.014, 0.004, "KK_Steel", 14, 6, axis="X")
    # Exterior pass (2026-10-09): nothing in front of the gas / water entry or in the left stool's knee space
    # any more: the noodle boxes and the spare stock pot are gone (the cartons now wait behind the back-left
    # corner, under the canopy, kiosk/exterior.py)
    _ = zc
    return {"fridge_display": (xm, yf - fd - 0.06, ftop - 0.04)}


# ---- lights for Unreal -----------------------------------------------------------------------------

def light_rig(info):
    """Positions/directions/sizes for Unreal's kitchen lights (intensities: scene_config.KITCHEN_LIGHTS)."""
    sw = SW
    lights = {
        # the bright prep light under the bulkhead at the opening (the old Interior_Light fixture)
        # aimed down and a little toward the customer: the pass and the counter brightest, the back falling off
        "L_Kitchen_Prep": {"type": "rect", "pos": ((sw["x0"] + sw["x1"]) / 2, YF + 0.13, sw["z1"] - 0.05),
                           "x_dir": (0.0, -0.30, -0.954), "y_dir": (1.0, 0.0, 0.0), "w": sw["x1"] - sw["x0"] - 0.3, "h": 0.12},
        # rear fluorescent batten: the room's dim fill (the old L_Interior, so kiosk_look / kiosk_refresh still drive it;
        # scene_config.INTERIOR holds the same position)
        "L_Interior": {"type": "point", "pos": info["rear_tube"][0], "radius_cm": 6.0},
        "L_Kitchen_CeilingR": {"type": "rect", "pos": info["right_tube"][0], "x_dir": (0.0, 0.0, -1.0), "y_dir": (1.0, 0.0, 0.0),
                               "w": info["right_tube"][1], "h": 0.04},
    }
    for k, p in enumerate(info["hood_lamps"]):
        lights[f"L_Kitchen_Hood_{k}"] = {"type": "spot", "pos": p, "dir": (0.0, -0.25, -0.97), "cone": 55.0}
    for k, (x, y, z, w) in enumerate(info["shelf_strips"]):
        lights[f"L_Kitchen_Shelf_{k}"] = {"type": "rect", "pos": (x, y, z), "x_dir": (0.0, -0.2, -0.98), "y_dir": (1.0, 0.0, 0.0), "w": w, "h": 0.02}
    lights["L_Kitchen_POS"] = {"type": "point", "pos": info["screen"][0], "radius_cm": 8.0}
    return lights


def build(B, coll, manifest):
    """Builds everything; returns (unique objects, prototype meshes {name: geo.Mesh}, placements, lights)."""
    import bpy
    geo.reseed(707)
    materials = bpy.data.materials
    props = Props()
    cards = Cards(manifest)
    m = geo.Mesh("SM_Kiosk_Kitchen")
    info = room(m)
    worktops(m)
    info.update(cooking_line(m, props))
    info.update(shelves(m, props, cards))
    prep_and_pass(m, props, cards)
    back_counter(m, props, cards)
    right_wall(m, props, cards)
    ticket_rail(m, cards)
    info.update(terminal(m, cards))
    counter_items(m, props, cards)
    info.update(under_counter(m, props, cards))
    pos, item = info["hood_note"]
    cards.card(item, pos, RIGHT, UP, 0.066, 0.044, age=0.7)
    mc = geo.Mesh("SM_Kiosk_KitchenCounter")
    pieces = counter_top(mc)
    objs = {"kitchen": m.build(coll, materials), "counter": mc.build(coll, materials), "cards": cards.build(coll, materials)}
    protos = {}
    for name in sorted({p[0] for p in props.items}):
        pm = geo.Mesh(f"SM_KP_{name}")
        PROTOS[name](pm)
        protos[name] = pm
    return objs, protos, props.items, light_rig(info), pieces
