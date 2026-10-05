"""Surfacing pass (2026-10-04, brief 5): weathering masks baked from the kiosk's own geometry.

Every mark has a physical driver rather than a grunge overlay:
  water   rain-flow streaks: each camera-facing side (-X, -Y) is turned into a 2.5D relief (up to
          three surface layers per cell); water runs down it, continues over attached surfaces and
          drips off edges. Every rivet, bolt, bracket, lap, sill and box bottom starts a streak on the
          surface below it; ledges and part tops start a dirt streak down the face beneath them.
  rust    at fasteners (and a halo round them), seams, panel bottom edges, the lowest 40 cm, under
          roof equipment, the drain outlet and shoe; rusty streaks below rusty fasteners.
  edges   paint chips on exposed convex edges, far more where crates, feet and passers-by hit
          (kiosk_config.WEATHER_TOUCH "abrade"); some sheets and units barely chipped at all.
  grime   in cavities and recesses, under protrusions and the canopy, the splash band at the base.
  heat    grease and soot round the service opening, the kitchen extract and the roof exhausts.
  hands   polished, cleaner touch points (door lever, counter nose, latches, buttons).
  age     paint generations per sheet (original / faded / darker amber / newer repaint), newer sheets
          with less wear.
The masks are potentials. Unreal's weathered master material decides per material instance how
much of each shows (Unreal/Scripts/scene_config.KIOSK_WEATHER), so the roof units can differ.

Pipeline, called by export_kiosk_glb.py after the sections are joined:
  prepare()  per-face island/material ids, the WeatherUV channel (TEXCOORD_1) on the weathered
             faces; faces no video/review viewpoint sees are packed smaller;
  bake()     Cycles bakes per-texel position, normal, ids, cavity / edge / occlusion, cached in
             Blender/weather_cache/ (the geometry is locked, so the look iterates on the cache:
             blender -b --factory-startup -P weather_masks.py);
  compute()  numpy turns the cache into Unreal/RawContent/weather/T_KioskWear_{A,B,C,D}.png:
             A = edge wear, rust, grime, dark streaks      B = rust streaks, soot, touch, wetness
             C = paint variation, newness, splash, grease
             D (half resolution, brief 5B) = dried spatter, sun fade, zinc oxide, light scuffs
Brief 5B (refine(), kiosk_config WEATHER_FASCIA / RUNOFF / SERVICE / ROOF_UNITS) is a targeted pass
on top: the lit fascia, the service-window frame, per-unit roof histories and long runs that start
at named sources. Every texel outside those zones keeps its 5A values.
"""
import math
import os
import time

import bmesh  # noqa: F401  (kept for interactive use)
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import kiosk_config as C

WX = C.WEATHER
SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLENDER_DIR = os.path.dirname(SCRIPTS)
CACHE = os.path.join(BLENDER_DIR, "weather_cache")
OUT_DIR = os.path.join(os.path.dirname(BLENDER_DIR), "Unreal", "RawContent", "weather")
UV_NAME = "WeatherUV"
MATS = WX["materials"]
MAT_ID = {m: i + 1 for i, m in enumerate(MATS)}  # 0 = not weathered
YELLOW = {MAT_ID[m] for m in ("Kiosk_YellowPaint", "Kiosk_YellowPaint_Dark", "Kiosk_YellowPaint_Faded")}
_T0 = [time.time()]


def log(msg):
    print(f"weather [{time.time() - _T0[0]:6.1f}s] {msg}", flush=True)


# ---- 1. Prepare: ids and the WeatherUV channel ---------------------------------------------------

def _arrays(me):
    nv, nf, nl = len(me.vertices), len(me.polygons), len(me.loops)
    co = np.empty(nv * 3, np.float32)
    me.vertices.foreach_get("co", co)
    lv = np.empty(nl, np.int32)
    me.loops.foreach_get("vertex_index", lv)
    ls = np.empty(nf, np.int32)
    me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32)
    me.polygons.foreach_get("loop_total", lt)
    mi = np.empty(nf, np.int32)
    me.polygons.foreach_get("material_index", mi)
    ctr = np.empty(nf * 3, np.float32)
    me.polygons.foreach_get("center", ctr)
    nrm = np.empty(nf * 3, np.float32)
    me.polygons.foreach_get("normal", nrm)
    area = np.empty(nf, np.float32)
    me.polygons.foreach_get("area", area)
    lf = np.repeat(np.arange(nf, dtype=np.int32), lt)
    return dict(co=co.reshape(-1, 3), lv=lv, ls=ls, lt=lt, lf=lf, mi=mi, ctr=ctr.reshape(-1, 3), nrm=nrm.reshape(-1, 3), area=area)


def _components(nv, lv, lf, nf):
    """Connected parts (faces sharing vertices): every primitive the build scripts add is one part."""
    lab = np.arange(nv, dtype=np.int64)
    for _ in range(200):
        fmin = np.full(nf, np.iinfo(np.int64).max, np.int64)
        np.minimum.at(fmin, lf, lab[lv])
        new = lab.copy()
        np.minimum.at(new, lv, fmin[lf])
        new = new[new]
        if np.array_equal(new, lab):
            break
        lab = new
    face_lab = np.empty(nf, np.int64)
    face_lab[lf] = lab[lv]  # any loop of the face
    _, inv = np.unique(face_lab, return_inverse=True)
    return inv.astype(np.int64)


def _viewpoints():
    """Every place a camera of this project looks from: the video orbit (floor and eye height), the
    review close-ups and the reference camera."""
    vc, hc = C.VIDEO_CAM, C.HERO_CAM
    pts = []
    for th in range(-45, 46, 15):
        t = math.radians(th)
        dx, dy = hc["pos_xy"][0] * vc["distance_scale"], hc["pos_xy"][1] * vc["distance_scale"]
        x, y = dx * math.cos(t) - dy * math.sin(t), dx * math.sin(t) + dy * math.cos(t)
        for z in (vc["height_m"], 1.7, 5.0):
            pts.append(Vector((x, y, z)))
        pts.append(Vector((x * 0.45, y * 0.45, 0.3)))  # closer, low: under the canopy
        pts.append(Vector((x * 0.45, y * 0.45, 1.6)))
    pts += [Vector(loc) for loc, _, _ in C.REVIEW_CAMS.values()]
    pts.append(Vector((hc["pos_xy"][0], hc["pos_xy"][1], 0.05)))
    return pts


def _visible_faces(objects, data, bvh, views):
    """Per object, a bool per face: some viewpoint sees the face (centre or near a corner)."""
    vp = np.array([tuple(v) for v in views], np.float32)
    out = []
    for ob, d in zip(objects, data):
        wmask = d["wmat"] > 0
        vis = np.zeros(len(d["mi"]), bool)
        idx = np.nonzero(wmask)[0]
        ctr, nrm = d["ctr"][idx], d["nrm"][idx]
        # facing test, vectorised: which viewpoints are in front of the face
        to = vp[None, :, :] - ctr[:, None, :]
        facing = np.einsum("fvk,fk->fv", to, nrm) > 0.01
        for j, f in enumerate(idx):
            cand = np.nonzero(facing[j])[0]
            if not len(cand):
                continue
            pts = [Vector(ctr[j])]
            if d["area"][f] > 0.004:
                s, n = d["ls"][f], d["lt"][f]
                for v in d["lv"][s:s + n]:
                    pts.append(Vector(0.75 * d["co"][v] + 0.25 * ctr[j]))
            nv = Vector(nrm[j])
            hit = False
            for c in cand:
                cv = Vector(vp[c])
                for p in pts:
                    o = p + nv * 0.003
                    dv = cv - o
                    dist = dv.length
                    loc, _, _, _ = bvh.ray_cast(o, dv / dist, dist)
                    if loc is None:
                        hit = True
                        break
                if hit:
                    break
            vis[f] = hit
        out.append(vis)
        log(f"visibility {ob.name}: {int(vis.sum())}/{len(idx)} weathered faces seen")
    return out


def _select_faces(objects, masks):
    for ob, m in zip(objects, masks):
        ob.data.polygons.foreach_set("select", m)
        ob.data.vertices.foreach_set("select", np.zeros(len(ob.data.vertices), bool))
        ob.data.edges.foreach_set("select", np.zeros(len(ob.data.edges), bool))
        ob.data.update()


def _edit(objects, fn):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="FACE")
    try:
        fn()
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def prepare(objects):
    """Island + material ids (face attributes), visibility, WeatherUV."""
    data, island_off = [], 0
    allv, allp = [], []
    voff = 0
    tables = []
    for ob in objects:
        me = ob.data
        d = _arrays(me)
        names = [m.name if m else "" for m in me.materials]
        lut = np.array([MAT_ID.get(n, 0) for n in names] or [0], np.int32)
        d["wmat"] = lut[d["mi"]]
        comp = _components(len(d["co"]), d["lv"], d["lf"], len(d["mi"]))
        d["island"] = comp + island_off
        # per-part table: bbox, area, dominant material
        n_isl = int(comp.max()) + 1 if len(comp) else 0
        lo = np.full((n_isl, 3), 1e9, np.float32)
        hi = np.full((n_isl, 3), -1e9, np.float32)
        vpart = np.empty(len(d["co"]), np.int64)
        vpart[d["lv"]] = comp[d["lf"]]
        np.minimum.at(lo, vpart, d["co"])
        np.maximum.at(hi, vpart, d["co"])
        parea = np.bincount(comp, weights=d["area"], minlength=n_isl)
        pmat = np.zeros(n_isl, np.int32)
        order = np.argsort(d["area"])  # the largest face's material wins
        pmat[comp[order]] = d["wmat"][order]
        tables.append(np.column_stack([lo, hi, parea, pmat, np.full(n_isl, len(tables))]))
        island_off += n_isl
        for name, vals in (("wx_island", d["island"].astype(np.float32)), ("wx_mat", d["wmat"].astype(np.float32))):
            if name in me.attributes:
                me.attributes.remove(me.attributes[name])
            me.attributes.new(name, "FLOAT", "FACE").data.foreach_set("value", vals)
        allv.append(d["co"])
        polys = np.split(d["lv"] + voff, np.cumsum(d["lt"])[:-1])
        allp.extend(p.tolist() for p in polys)
        voff += len(d["co"])
        data.append(d)
        log(f"prepare {ob.name}: {len(d['mi'])} faces, {n_isl} parts, {int((d['wmat'] > 0).sum())} weathered faces")
    # occluders: the weathered sections plus the props standing round the kiosk
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name.startswith("SM_Kiosk_") and ob not in objects:
            d = _arrays(ob.data)
            allv.append(d["co"])
            allp.extend((p + voff).tolist() for p in np.split(d["lv"], np.cumsum(d["lt"])[:-1]))
            voff += len(d["co"])
    bvh = BVHTree.FromPolygons([tuple(v) for v in np.concatenate(allv)], allp, epsilon=0.0)
    vis = _visible_faces(objects, data, bvh, _viewpoints())

    # WeatherUV: seen faces unwrapped at full density, unseen ones smaller, then packed together
    for ob in objects:
        uvl = ob.data.uv_layers
        if UV_NAME in uvl:
            uvl.remove(uvl[UV_NAME])
        layer = uvl.new(name=UV_NAME, do_init=False)
        layer.data.foreach_set("uv", np.zeros(len(ob.data.loops) * 2, np.float32))
        uvl.active = layer
    for group, scale in ((True, 1.0), (False, WX["hidden_scale"])):
        masks = [(d["wmat"] > 0) & (v == group) for d, v in zip(data, vis)]
        if not any(m.any() for m in masks):
            continue
        _select_faces(objects, masks)
        _edit(objects, lambda: bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0,
                                                         correct_aspect=True, scale_to_bounds=False))
        if scale != 1.0:
            for ob, m in zip(objects, masks):
                uv = np.empty(len(ob.data.loops) * 2, np.float32)
                ob.data.uv_layers[UV_NAME].data.foreach_get("uv", uv)
                lm = np.repeat(m, [p.loop_total for p in ob.data.polygons])
                uv = uv.reshape(-1, 2)
                uv[lm] *= scale
                ob.data.uv_layers[UV_NAME].data.foreach_set("uv", uv.ravel())
        log(f"unwrapped {'seen' if group else 'unseen'} faces")
    _select_faces(objects, [d["wmat"] > 0 for d in data])
    margin = 3.0 / WX["res"]

    def pack():
        bpy.ops.uv.select_all(action="SELECT")
        bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", rotate=True, scale=True, margin_method="FRACTION",
                                margin=margin, shape_method="AABB")
    _edit(objects, pack)
    for ob in objects:  # UVMap stays first (TEXCOORD_0, the metre-scale UVs); WeatherUV is TEXCOORD_1
        ob.data.uv_layers.active = ob.data.uv_layers[0]
        ob.data.uv_layers[0].active_render = True
    log("packed WeatherUV")
    os.makedirs(CACHE, exist_ok=True)
    np.save(os.path.join(CACHE, "parts.npy"), np.concatenate(tables).astype(np.float32))
    return data


# ---- 2. Bake ------------------------------------------------------------------------------------

def _gpu(scene):
    scene.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                devs = [d for d in prefs.devices if d.type == kind]
                if devs:
                    for d in prefs.devices:
                        d.use = d.type == kind
                    scene.cycles.device = "GPU"
                    log(f"bake on {kind}: {', '.join(d.name for d in devs)}")
                    return
            except TypeError:
                continue
    except KeyError:
        pass
    log("bake on CPU")


def _bake_material(lo, size):
    m = bpy.data.materials.get("WX_Bake") or bpy.data.materials.new("WX_Bake")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    out = N("ShaderNodeOutputMaterial")
    emit = N("ShaderNodeEmission")
    nt.links.new(emit.outputs[0], out.inputs["Surface"])
    img_node = N("ShaderNodeTexImage")
    nt.nodes.active = img_node
    geo = N("ShaderNodeNewGeometry")
    passes = {}

    def combine(r, g, b):
        c = N("ShaderNodeCombineXYZ")
        for i, s in enumerate((r, g, b)):
            if s is not None:
                nt.links.new(s, c.inputs[i])
        return c.outputs[0]

    # position, normalised to the kiosk bounds
    sub = N("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = lo
    nt.links.new(geo.outputs["Position"], sub.inputs[0])
    div = N("ShaderNodeVectorMath")
    div.operation = "DIVIDE"
    div.inputs[1].default_value = size
    nt.links.new(sub.outputs[0], div.inputs[0])
    passes["pos"] = div.outputs[0]
    # true (flat) normal, 0..1
    mad = N("ShaderNodeVectorMath")
    mad.operation = "MULTIPLY_ADD"
    mad.inputs[1].default_value = (0.5, 0.5, 0.5)
    mad.inputs[2].default_value = (0.5, 0.5, 0.5)
    nt.links.new(geo.outputs["True Normal"], mad.inputs[0])
    passes["nrm"] = mad.outputs[0]
    # ids
    a_isl = N("ShaderNodeAttribute")
    a_isl.attribute_name, a_isl.attribute_type = "wx_island", "GEOMETRY"
    a_mat = N("ShaderNodeAttribute")
    a_mat.attribute_name, a_mat.attribute_type = "wx_mat", "GEOMETRY"
    passes["ids"] = combine(a_isl.outputs["Fac"], a_mat.outputs["Fac"], None)
    # cavity (short occlusion), convex/concave edges (bevel vs flat normal), recess (long occlusion)
    ao_s = N("ShaderNodeAmbientOcclusion")
    ao_s.samples, ao_s.inputs["Distance"].default_value = 16, 0.035
    ao_m = N("ShaderNodeAmbientOcclusion")
    ao_m.samples, ao_m.inputs["Distance"].default_value = 16, 0.45
    bev = N("ShaderNodeBevel")
    bev.samples, bev.inputs["Radius"].default_value = 8, 0.012
    dot = N("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(bev.outputs[0], dot.inputs[0])
    nt.links.new(geo.outputs["Normal"], dot.inputs[1])
    passes["shade"] = combine(ao_s.outputs["AO"], dot.outputs["Value"], ao_m.outputs["AO"])
    return m, img_node, emit, passes


def bake(objects):
    scene = bpy.context.scene
    res = WX["res"]
    _gpu(scene)
    pts = np.concatenate([np.array([v.co[:] for v in ob.data.vertices], np.float32) for ob in objects])
    lo = pts.min(0) - 0.01
    size = (pts.max(0) + 0.01) - lo
    mat, img_node, emit, passes = _bake_material(tuple(lo), tuple(size))
    saved = [[s.material for s in ob.material_slots] for ob in objects]
    for ob in objects:
        for s in ob.material_slots:
            s.material = mat
        if not ob.material_slots:
            ob.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    scene.render.bake.margin = 0
    scene.render.bake.use_clear = True
    scene.render.bake.target = "IMAGE_TEXTURES"
    os.makedirs(CACHE, exist_ok=True)
    valid = None
    for name, samples in (("ids", 1), ("pos", 1), ("nrm", 1), ("shade", 24)):
        img = bpy.data.images.new(f"WX_{name}", res, res, alpha=True, float_buffer=True)
        img.colorspace_settings.name = "Non-Color"
        img.generated_color = (0, 0, 0, 0)
        img_node.image = img
        mat.node_tree.links.new(passes[name], emit.inputs["Color"])
        scene.cycles.samples = samples
        bpy.ops.object.bake(type="EMIT", margin=0, use_clear=True, uv_layer=UV_NAME)
        px = np.empty(res * res * 4, np.float32)
        img.pixels.foreach_get(px)
        px = px.reshape(-1, 4)
        if valid is None:
            valid = np.nonzero(px[:, 3] > 0.5)[0]
            np.save(os.path.join(CACHE, "texels.npy"), valid.astype(np.int64))
        v = px[valid, :3]
        if name == "pos":
            v = v * size + lo
        elif name == "nrm":
            v = v * 2.0 - 1.0
            v /= np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-6)
        np.save(os.path.join(CACHE, f"{name}.npy"), v.astype(np.float32))
        bpy.data.images.remove(img)
        log(f"baked {name}: {len(valid)} texels")
    for ob, mats in zip(objects, saved):
        for s, m in zip(ob.material_slots, mats):
            s.material = m
    bpy.data.materials.remove(mat)
    np.save(os.path.join(CACHE, "meta.npy"), np.array([res], np.int64))


# ---- 3. Compute: masks from the cache -------------------------------------------------------------

_LAT = np.random.default_rng(7).random((64, 64, 64)).astype(np.float32)


def vnoise(p, scale, seed=0):
    """Smooth 3D value noise (0..1) at world points p (n,3), feature size `scale` metres."""
    q = p / scale + seed * 17.13
    i = np.floor(q).astype(np.int64)
    f = (q - i).astype(np.float32)
    f = f * f * (3 - 2 * f)
    out = np.zeros(len(p), np.float32)
    for dx in (0, 1):
        wx = f[:, 0] if dx else 1 - f[:, 0]
        for dy in (0, 1):
            wy = f[:, 1] if dy else 1 - f[:, 1]
            for dz in (0, 1):
                wz = f[:, 2] if dz else 1 - f[:, 2]
                out += wx * wy * wz * _LAT[(i[:, 0] + dx) & 63, (i[:, 1] + dy) & 63, (i[:, 2] + dz) & 63]
    return out


def fbm(p, scale, octaves=3, seed=0):
    out, amp, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        out = out + amp * vnoise(p, scale / (2 ** o), seed + o)
        tot += amp
        amp *= 0.5
    return out / tot


def hash01(ids, seed=0):
    x = (ids.astype(np.uint64) * np.uint64(2654435761) + np.uint64(seed * 97 + 13)) & np.uint64(0xFFFFFFFF)
    x ^= x >> np.uint64(15)
    x = (x * np.uint64(2246822519)) & np.uint64(0xFFFFFFFF)
    x ^= x >> np.uint64(13)
    return (x & np.uint64(0xFFFFFF)).astype(np.float32) / float(0xFFFFFF)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def capsule_dist(p, a, b):
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    ab = b - a
    t = np.clip(((p - a) @ ab) / max(float(ab @ ab), 1e-9), 0.0, 1.0)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


def _zones(P, zones, kinds):
    out = {k: np.zeros(len(P), np.float32) for k in kinds}
    for z in zones:
        kind, a, b, r, s = z
        lo = np.minimum(a, b) - r
        hi = np.maximum(a, b) + r
        m = np.all((P >= lo) & (P <= hi), axis=1)
        if not m.any():
            continue
        d = capsule_dist(P[m], a, b)
        out[kind][m] = np.maximum(out[kind][m], s * smooth(r, r * 0.35, d))
    return out


class Relief:
    """One camera-facing side (-X or -Y) as a 2.5D relief: up to `L` surface layers per cell, rain
    flowing down it. Texels facing that side are rasterised into cells (lateral u, height z) with
    their outward depth; surfaces in the same cell more than 1.5 cm apart are separate layers."""
    L = 3

    def __init__(self, P, sel, axis, cell):
        self.idx = np.nonzero(sel)[0]
        p = P[self.idx]
        if axis == "-Y":
            u, out = p[:, 0], -p[:, 1]
        else:
            u, out = -p[:, 1], -p[:, 0]
        self.cell = cell
        self.u0, self.z0 = u.min() - 2 * cell, p[:, 2].min() - 2 * cell
        self.nu = int((u.max() - self.u0) / cell) + 3
        self.nz = int((p[:, 2].max() - self.z0) / cell) + 3
        cu = ((u - self.u0) / cell).astype(np.int64)
        cz = ((p[:, 2] - self.z0) / cell).astype(np.int64)
        flat = cz * self.nu + cu
        order = np.lexsort((-out, flat))
        fs, os_ = flat[order], out[order]
        newc = np.ones(len(fs), bool)
        newc[1:] = fs[1:] != fs[:-1]
        gap = np.zeros(len(fs), bool)
        gap[1:] = (os_[:-1] - os_[1:]) > 0.015
        start = newc | gap
        k = np.cumsum(start) - 1
        first = np.maximum.accumulate(np.where(newc, k, 0))
        rank = k - first
        keep = rank < self.L
        self.t_layer = np.full(len(self.idx), -1, np.int64)
        self.t_layer[order[keep]] = rank[keep]
        self.t_flat = flat
        D = np.full(self.L * self.nz * self.nu, -np.inf, np.float32)
        np.maximum.at(D, rank[keep] * (self.nz * self.nu) + fs[keep], os_[keep])
        self.D = D.reshape(self.L, self.nz, self.nu)
        self._fill_holes()

    def _fill_holes(self):
        """A missing cell between two cells of the same surface (grazing texels) is filled, so water
        keeps running."""
        D = self.D
        for _ in range(2):
            up, dn = D[:, 2:, :], D[:, :-2, :]
            mid = D[:, 1:-1, :]
            hole = ~np.isfinite(mid) & np.isfinite(up) & np.isfinite(dn) & (np.abs(up - dn) < 0.008)
            mid[hole] = up[hole]

    def lookup(self, grid):
        """Per texel value of a (L, nz, nu, ...) grid; texels beyond the third layer get 0."""
        out = np.zeros((len(self.idx),) + grid.shape[3:], np.float32)
        ok = self.t_layer >= 0
        g = grid.reshape((-1,) + grid.shape[3:])
        out[ok] = g[self.t_layer[ok] * (self.nz * self.nu) + self.t_flat[ok]]
        return out

    def splat(self, values, reduce=np.maximum):
        """Texel values -> (L, nz, nu) grid (max per cell)."""
        g = np.zeros(self.L * self.nz * self.nu, np.float32)
        ok = self.t_layer >= 0
        reduce.at(g, self.t_layer[ok] * (self.nz * self.nu) + self.t_flat[ok], values[ok])
        return g.reshape(self.L, self.nz, self.nu)

    def flow(self, src_edge, src_top, src_carry, rng, ch=3, lam=None):
        """Rain runs down every layer from the top row. A cell continues the streak of the cell above
        on the same surface (depth within 8 mm). Where a surface ends, its water drips onto the
        surface below if that surface lies at most `attach` behind it (rivets, laps, sills, brackets
        flush to the wall); further back only a weak stain reaches it (water wicking back along the
        underside). src_edge (L,nz,nu,ch): dirt a drip edge adds; src_top: dirt a face picks up at its
        top edge; src_carry: dirt picked up anywhere (heat zones). lam: per column run length (m);
        by default random between WEATHER streak_len. Returns streaks (L,nz,nu,ch) plus each cell's
        distance (m) to the bottom and top edges of its surface."""
        L, nz, nu, cell = self.L, self.nz, self.nu, self.cell
        D = self.D
        lo_len, hi_len = WX["streak_len"]
        # per column run length (lognormal-ish) and an intermittent along-the-run modulation
        if lam is None:
            lam = lo_len * (hi_len / lo_len) ** _urand(nu, cell, 0.02, int(rng.integers(1000)))
        decay = np.exp(-cell / lam).astype(np.float32)
        S = np.zeros((L, nz, nu, ch), np.float32)
        top_d = np.zeros((L, nz, nu), np.float32)
        attach, cont = 0.03, 0.008
        lidx = np.arange(nu)
        for z in range(nz - 2, -1, -1):
            d_here, d_up = D[:, z, :], D[:, z + 1, :]  # (L, nu)
            s_up = S[:, z + 1, :, :]
            ex_h, ex_u = np.isfinite(d_here), np.isfinite(d_up)
            # continuity matrix (L_here, L_up, nu)
            diff = np.abs(d_here[:, None, :] - d_up[None, :, :])
            same = (diff < cont) & ex_h[:, None, :] & ex_u[None, :, :]
            carried = np.where(same[..., None], s_up[None, :, :, :], 0.0).max(axis=1) * decay[None, :, None]
            has_up = same.any(axis=1)
            # surfaces above that end here drip; find where each lands
            ends = ex_u & ~same.any(axis=0)  # (L_up, nu)
            drip = np.zeros((L, nu, ch), np.float32)
            if ends.any():
                for lu in range(L):
                    e = ends[lu]
                    if not e.any():
                        continue
                    dd = d_up[lu]  # drip depth
                    # candidate landing layers: at or behind the drip, the nearest one
                    behind = ex_h & (d_here <= dd[None, :] + 0.004)
                    gapd = np.where(behind, dd[None, :] - d_here, np.inf)
                    land = np.argmin(gapd, axis=0)
                    g = gapd[land, lidx]
                    okk = e & np.isfinite(g)
                    w_att = np.where(g < attach, 1.0, 0.55).astype(np.float32)
                    amount = (s_up[lu] * np.where(g < attach, 1.0, 0.3)[:, None] + src_edge[lu, z + 1] * w_att[:, None])
                    amount[~okk] = 0.0
                    np.maximum.at(drip, (land[okk], lidx[okk]), amount[okk])
            new = np.maximum(carried, drip)
            # a face starting here picks up dirt at its top edge
            starts = ex_h & ~has_up
            new += np.where(starts[..., None], src_top[:, z, :, :], 0.0)
            new += src_carry[:, z, :, :]
            new[~ex_h] = 0.0
            S[:, z, :, :] = np.minimum(new, 1.5)
            top_d[:, z, :] = np.where(starts | ~ex_h, 0.0, np.where(same, top_d[None, :, z + 1, :], 0).max(axis=1) + cell)
        # distance to the bottom edge, bottom-up
        bot_d = np.zeros((L, nz, nu), np.float32)
        for z in range(1, nz):
            d_here, d_dn = D[:, z, :], D[:, z - 1, :]
            same = (np.abs(d_here[:, None, :] - d_dn[None, :, :]) < cont) & np.isfinite(d_here)[:, None, :] & np.isfinite(d_dn)[None, :, :]
            bot_d[:, z, :] = np.where(same, bot_d[None, :, z - 1, :], -cell).max(axis=1) + cell
        return S, bot_d, top_d


def _box(a, k, axis):
    pad = [(0, 0)] * a.ndim
    pad[axis] = (k + 1, k)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    n = a.shape[axis]
    return ((np.take(c, np.arange(2 * k + 1, 2 * k + 1 + n), axis=axis) - np.take(c, np.arange(n), axis=axis)) / (2 * k + 1)).astype(np.float32)


def _gauss_blur2(a, rz, ru=None):
    """~Gaussian blur (three box passes) over the last two axes (z, u) of a relief grid."""
    ru = rz if ru is None else ru
    out = a
    for axis, k in ((a.ndim - 2, rz), (a.ndim - 1, ru)):
        if k >= 1:
            for _ in range(3):
                out = _box(out, int(k), axis)
    return out


def _noise1(n, cell, feature, seed):
    """1D smooth noise along a relief row (n cells), feature size in metres."""
    x = np.arange(n, dtype=np.float32) * cell
    p = np.stack([x, np.full(n, 0.37, np.float32), np.full(n, 0.11 * seed, np.float32)], 1)
    return fbm(p, feature, 2, seed)


def _urand(n, cell, feature, seed):
    """Spatially coherent uniform 0..1 values along a relief row: neighbouring cells within about
    `feature` metres share their randomness, so streaks stay a few cells wide instead of a barcode."""
    v = _noise1(n, cell, feature, seed)
    out = np.empty(n, np.float32)
    out[np.argsort(v, kind="stable")] = np.linspace(0, 1, n, dtype=np.float32)
    return out


# ---- 5B: targeted refinement (kiosk_config WEATHER_FASCIA / RUNOFF / SERVICE / ROOF_UNITS) ------------

def _fascia_faces():
    """The two lit fascia faces: (side, relief axis, u0, u1 of the face, lit span i0..i1, panels)."""
    rh = C.CANOPY_DETAIL["rail_h"]
    out = []
    for side, axis, (u0, u1) in (("front", "-Y", (C.CANOPY_X0, C.CANOPY_X1)), ("left", "-X", (C.CANOPY_Y0, C.CANOPY_Y1))):
        i0, i1 = u0 + rh, u1 - rh
        out.append((side, axis, u0, u1, i0, i1, max(1, round((i1 - i0) / C.CANOPY_DETAIL["mullion_every"]))))
    return out


def _run_sources():
    """Every long-run source in relief terms: kiosk_config.WEATHER_RUNOFF plus the fascia's own (both
    sides of each mullion, the stile ends, and the top-rail rivets that weep rust)."""
    lit_top = C.FACE_Z1 - C.CANOPY_DETAIL["rail_h"]
    pitch = C.CANOPY_DETAIL["rail_rivet_pitch"]
    src = list(C.WEATHER_RUNOFF)
    for side, axis, u0, u1, i0, i1, n in _fascia_faces():
        pw = (i1 - i0) / n
        for k in range(1, n):
            m = i0 + k * pw
            src += [(side, m - 0.016, lit_top, 0.012, 0.44, 0.30, 1, "dark", "lit"),
                    (side, m + 0.016, lit_top, 0.012, 0.40, 0.26, 1, "dark", "lit")]
        src += [(side, i0 + 0.014, lit_top, 0.014, 0.44, 0.30, 1, "dark", "lit"),
                (side, i1 - 0.014, lit_top, 0.014, 0.36, 0.24, 1, "dark", "lit")]
        off = 0 if side == "front" else 1000
        for j in range(int((u1 - u0 - 0.1) / pitch) + 1):
            u = u0 + 0.05 + j * pitch
            if hash01(np.array([j + off]), 5)[0] < C.WEATHER_FASCIA["rivet_rust_odds"] and i0 + 0.02 < u < i1 - 0.02:
                src.append((side, u, lit_top, 0.014, 0.10 + 0.22 * hash01(np.array([j + off]), 6)[0], 0.35, 1, "rust", "lit"))
    return [dict(axis="-Y" if side == "front" else "-X", u=u if side == "front" else -u, z=zz, w=w, len=ln, s=s, n=ns,
                 kind=kind, mats=mats) for side, u, zz, w, ln, s, ns, kind, mats in src]


def _source_runs(R, axis, p, m, sources, i0, fr):
    """Long runs from named sources on one relief side. Each source marks the first surface of its
    materials just below it; the water then follows the relief with the source's run length (same
    meander as the other streaks, its own intermittency). Per texel (dark, rust), or None."""
    srcs = [s for s in sources if s["axis"] == axis]
    if not srcs:
        return None
    u_t = p[:, 0] if axis == "-Y" else -p[:, 1]
    z_t = p[:, 2]
    yellow_t = np.isin(m, list(YELLOW))
    lit_t = m == MAT_ID["Lightbox_Yellow"]
    nu, cell = R.nu, R.cell
    cols = R.u0 + (np.arange(nu, dtype=np.float32) + 0.5) * cell
    lam = np.full(nu, 0.02, np.float32)
    val = np.zeros((len(p), 2), np.float32)
    for k, s in enumerate(srcs):
        half = s["w"] / 2
        sel = (np.abs(u_t - s["u"]) < half + 0.006) & (z_t <= s["z"] + 0.004) & (z_t > s["z"] - 0.06)
        sel &= {"lit": lit_t, "yellow": yellow_t}.get(s["mats"], True)
        if not sel.any():
            log(f"  source {axis} u={s['u']:.3f} z={s['z']:.3f}: no {s['mats']} surface below")
            continue
        rr = np.random.default_rng(4000 + k + (0 if axis == "-Y" else 500))
        offs = (rr.random(s["n"]) - 0.5) * max(s["w"] - 0.008, 0.0)  # sub-streaks across the source
        amps = 0.55 + 0.45 * rr.random(s["n"])
        wid = 0.0035 + 0.004 * rr.random(s["n"])
        du = u_t[sel] - s["u"]
        prof = np.max(amps[None, :] * np.exp(-((du[:, None] - offs[None, :]) / wid[None, :]) ** 2), axis=1)
        ch = 1 if s["kind"] == "rust" else 0
        val[sel, ch] = np.maximum(val[sel, ch], s["s"] * prof)
        inw = np.abs(cols - s["u"]) < half + 0.012
        lam[inw] = np.maximum(lam[inw], s["len"])
    if not val.any():
        return None
    g = np.stack([R.splat(val[:, 0]), R.splat(val[:, 1])], axis=-1)
    pos = (g > 0).any(axis=-1)
    above = np.flip(np.cumsum(np.flip(pos, axis=1), axis=1), axis=1)  # marked cells at or above, per column
    g = np.where((pos & (above == 1))[..., None], g, 0.0).astype(np.float32)  # a source, not a band
    zero = np.zeros_like(g)
    S, _, _ = R.flow(zero, zero, g, None, ch=2, lam=lam)
    S = (np.take_along_axis(S, np.broadcast_to(i0[None, :, :, None], S.shape), axis=2) * (1 - fr)
         + np.take_along_axis(S, np.broadcast_to(i0[None, :, :, None] + 1, S.shape), axis=2) * fr)
    S = _box(S, 1, 2)
    zn = _gauss_blur2(np.random.default_rng(91 if axis == "-Y" else 92).random((1, R.nz, nu)).astype(np.float32), 8, 3)
    zn = (zn - zn.mean()) / max(float(zn.std()), 1e-6)
    S *= np.clip(1.0 + 0.35 * zn, 0.35, 1.6)[..., None]
    return R.lookup(S)


def _halo3d(P, src, dst_idx, cell=0.015, k=2):
    """Smooth 3D proximity to the src texels (a blurred voxel splat, ~4 cm reach) at dst_idx; 0..1."""
    ps, pd = P[src], P[dst_idx]
    lo = np.minimum(ps.min(0), pd.min(0)) - 0.05
    hi = np.maximum(ps.max(0), pd.max(0)) + 0.05
    g = np.zeros(tuple(np.ceil((hi - lo) / cell).astype(np.int64) + 1), np.float32)
    q = ((ps - lo) / cell).astype(np.int64)
    g[q[:, 0], q[:, 1], q[:, 2]] = 1.0
    for axis in range(3):
        for _ in range(3):
            g = _box(g, k, axis)
    ref = float(np.median(g[q[:, 0], q[:, 1], q[:, 2]]))
    qd = ((pd - lo) / cell).astype(np.int64)
    return np.clip(g[qd[:, 0], qd[:, 1], qd[:, 2]] / max(ref, 1e-6) * 0.9, 0, 1)


def refine(v):
    """Brief 5B on top of the 5A masks, in four zones only (the source runs were added to the streaks
    in the relief pass). Returns the replaced layers and X, a fourth mask (n, 4): dried spatter, sun
    fade, zinc oxide, light scuffs. Every texel outside the zones keeps its 5A values."""
    P, Nn, z, mat, isl = v["P"], v["Nn"], v["z"], v["mat"], v["isl"]
    up, down, side = v["up"], v["down"], v["side"]
    cavity, edge, streak = v["cavity"], v["edge"], v["streak"]  # streak is changed in place
    E, Rr, G = v["E"].copy(), v["Rr"].copy(), v["G"].copy()
    soot, grease, pvar, newness = v["soot"].copy(), v["grease"].copy(), v["pvar"].copy(), v["newness"].copy()
    plo, phi, pdiag, r_part3 = v["plo"], v["phi"], v["pdiag"], v["r_part3"]
    X = np.zeros((len(P), 4), np.float32)
    TOP = C.CANOPY_TOP

    # 1 the lit fascia: per-panel diffuser age, dirt where water stops or creeps, chips on the frame,
    #   spatter; the runs from the roof, joints and rivets came from the relief
    WF = C.WEATHER_FASCIA
    rh = C.CANOPY_DETAIL["rail_h"]
    cx0, cy0 = C.CANOPY_X0, C.CANOPY_Y0
    lit_bot, lit_top = C.FACE_Z0 + rh, C.FACE_Z1 - rh
    fas = (z > C.FASCIA_Z0 - 0.02) & (z < TOP + 0.03) & (v["to_edge"] < C.FASCIA["depth"] - 0.005)
    near_front = (P[:, 1] - cy0) <= (P[:, 0] - cx0)
    lit = mat == MAT_ID["Lightbox_Yellow"]
    frame_mat = np.isin(mat, list(YELLOW))
    gen_val = {"orig": (0.50, 0.08), "amber": (0.25, 0.06), "bleach": (0.72, 0.05), "new": (0.50, 0.78)}  # pvar, newness
    grime_k = {"orig": 1.0, "amber": 1.25, "bleach": 1.0, "new": 0.6}
    for fside, axis, u0, u1, i0, i1, nn in _fascia_faces():
        if fside == "front":
            sel = fas & near_front & (P[:, 1] < cy0 + 0.4)
        else:
            sel = fas & ~near_front & (P[:, 0] < cx0 + 0.4)
        idx = np.nonzero(sel)[0]
        if not len(idx):
            continue
        p = P[idx]
        u = p[:, 0] if fside == "front" else p[:, 1]
        zz = p[:, 2]
        pw = (i1 - i0) / nn
        k = np.clip(np.floor((u - i0) / pw).astype(np.int64), 0, nn - 1)
        joints = i0 + np.arange(nn + 1) * pw
        dj = np.min(np.abs(u[:, None] - joints[None, :]), axis=1)
        dc = u - u0  # from the canopy corner both lit faces share
        gens = WF["panels"][fside]
        pv = np.array([gen_val[g][0] for g in gens], np.float32)[k]
        nw = np.array([gen_val[g][1] for g in gens], np.float32)[k]
        gk = np.where(lit[idx], np.array([grime_k[g] for g in gens], np.float32)[k], 1.0)
        li = lit[idx]
        pvar[idx[li]] = np.clip(pv + 0.10 * (fbm(p, 0.35, 2, seed=111) - 0.5), 0, 1)[li]
        newness[idx[li]] = nw[li]
        h = zz - lit_bot
        edge_n = fbm(p * np.array([1, 1, 0], np.float32), 0.06, 2, seed=113)
        band = smooth(WF["bottom_band"], 0.0, h - 0.04 * (edge_n - 0.5)) * (0.45 + 0.55 * fbm(p, 0.04, 2, seed=115))
        streaky = fbm(p * np.array([1, 1, 0.15], np.float32), 0.012, 2, seed=117)  # narrow across, long down
        joint = smooth(WF["joint_band"], 0.006, dj) * (0.35 + 0.65 * streaky)
        under_top = smooth(0.035, 0.0, lit_top - zz) * (0.4 + 0.6 * streaky)
        corner = smooth(WF["corner_reach"], 0.0, dc) * (0.5 + 0.5 * fbm(p, 0.08, 2, seed=119))
        add = (0.7 * band + 0.55 * joint + 0.35 * under_top) * li + 0.4 * corner
        G[idx] = np.clip((G[idx] + add) * gk, 0, 1)
        # rust round the corner posts and the frame ends there; occasional small chips on the frame
        Rr[idx] = np.maximum(Rr[idx], ~li * smooth(WF["corner_reach"] * 0.6, 0.0, dc) * 0.22
                             * smooth(0.35, 0.7, fbm(p, 0.05, 2, seed=121)))
        fr_ = frame_mat[idx]
        E[idx[fr_]] = np.clip(E[idx[fr_]] * WF["chip_boost"], 0, 1)
        # dried rain spatter: more toward the bottom, the corner and beside the runs; less on the new panel
        spk = (0.35 + 0.45 * smooth(0.18, 0.0, h) + 0.25 * corner + 0.3 * np.clip(streak[idx, 0] * 2.0, 0, 1)) \
            * (0.55 + 0.9 * fbm(p, 0.25, 2, seed=123))
        spk *= np.where(li, np.where(nw > 0.5, 0.5, 1.0), 0.8)
        spk *= ((Nn[idx, 1] < -0.5) if fside == "front" else (Nn[idx, 0] < -0.5)) | up[idx]  # where rain lands, not the soffit
        X[idx, 0] = np.clip(spk, 0, 1)
        log(f"refine fascia {fside}: {len(idx)} texels, {int(li.sum())} lit")

    # 2 the service-window frame: grime where sections overlap, grease and heat at the head and jamb
    #   tops, worn counter edges; the working surfaces are wiped
    WS = C.WEATHER_SERVICE
    x0, x1, z0, z1, ymax = WS["zone"]
    zs = np.nonzero((P[:, 0] > x0) & (P[:, 0] < x1) & (z > z0) & (z < z1) & (P[:, 1] < ymax))[0]
    p = P[zs]
    soft = (smooth(x0, x0 + 0.12, p[:, 0]) * smooth(x1, x1 - 0.12, p[:, 0]) * smooth(z0, z0 + 0.08, p[:, 2])
            * smooth(z1, z1 - 0.08, p[:, 2]) * smooth(ymax, ymax - 0.08, p[:, 1]))
    co = C.COUNTER
    work = (up[zs] & (np.abs(p[:, 2] - co["z"]) < 0.012) & (p[:, 1] > C.Y0 - co["projection"] - 0.01)
            & (p[:, 0] > co["x0"] - 0.01) & (p[:, 0] < co["x1"] + 0.01))
    # overlaps: the grime layer is already full in these cavities, so the extra dark accumulation goes
    # into the runs channel (only real overlaps: tight cavities)
    lap = WS["overlap_dirt"] * smooth(0.35, 0.85, cavity[zs]) * soft * ~work * (1 - 0.8 * v["touch"][zs])
    streak[zs, 0] = np.maximum(streak[zs, 0], lap * (0.6 + 0.4 * fbm(p, 0.03, 2, seed=129)))
    # grease and heat: patchy plumes that rise from the opening (streaky upward)
    hz2 = _zones(p, WS["heat"], ("grease", "soot"))
    plume = 0.55 + 0.45 * smooth(0.3, 0.7, fbm(p * np.array([1, 1, 0.35], np.float32), 0.05, 2, seed=131))
    grease[zs] = np.maximum(grease[zs], np.clip(hz2["grease"] * (0.6 + 0.4 * cavity[zs] + 0.3 * down[zs]) * plume, 0, 1))
    soot[zs] = np.maximum(soot[zs], np.clip(hz2["soot"] * (0.6 + 0.4 * fbm(p, 0.15, 2, seed=91)), 0, 1))
    az = _zones(p, WS["abrade"], ("abrade",))["abrade"]
    Ev = edge[zs] * v["p_wear"][zs] * (0.35 + 0.9 * v["vary"][zs]) * (v["abr"][zs] + 1.5 * az) * (1 - 0.75 * newness[zs])
    Ev = np.maximum(Ev, az * 0.6 * smooth(0.6, 0.85, fbm(p, 0.02, 2, seed=133)))  # dings and scrapes along the nose
    E[zs] = np.maximum(E[zs], np.clip(Ev, 0, 1) * (az > 0))
    w = zs[work]
    c = WS["clean"]
    G[w] *= c
    streak[w] *= c
    grease[w] *= c
    soot[w] *= c
    Rr[w] *= 0.55 + 0.45 * c
    log(f"refine service window: {len(zs)} texels, {len(w)} on working surfaces")

    # 3 roof units with their own histories; a faint rust halo round every roof fastener and flange
    roof_t = np.nonzero(z > TOP - 0.03)[0]
    roof_part = plo[:, 2] > TOP - 0.05
    pmat = np.rint(v["parts"][:, 7]).astype(np.int64)
    pext = (phi - plo).min(axis=1)
    flange_part = roof_part & (pmat == MAT_ID["Steel_Dark"]) & (pext < 0.05) & (pdiag > 0.12) & (pdiag < 0.95)
    halo3 = _halo3d(P, v["fast"] & (z > TOP - 0.03), roof_t)
    Rr[roof_t] = np.maximum(Rr[roof_t], halo3 * 0.45 * ~v["fast"][roof_t])
    isl_r = isl[roof_t]
    ids = lambda names: [MAT_ID[nm] for nm in names]  # noqa: E731
    for name, (bx0, bx1, by0, by1), mods in C.WEATHER_ROOF_UNITS:
        inside_part = roof_part & (plo[:, 0] > bx0 - 0.05) & (phi[:, 0] < bx1 + 0.05) & (plo[:, 1] > by0 - 0.05) & (phi[:, 1] < by1 + 0.05)
        sel = roof_t[inside_part[isl_r]]
        if not len(sel):
            log(f"refine roof {name}: nothing in the box")
            continue
        p, m = P[sel], mat[sel]
        if "grime" in mods:
            G[sel] = np.clip(G[sel] * mods["grime"], 0, 1)
        if "streak" in mods:
            streak[sel, 0] *= mods["streak"]
        if "rust" in mods:
            Rr[sel] = np.clip(Rr[sel] * mods["rust"], 0, 1)
        if "fade" in mods:  # sun-chalked paint: broad blotches, a little streaky, most on the tops
            s, mats = mods["fade"]
            f = s * (0.55 + 0.45 * fbm(p, 0.22, 3, seed=141)) * (0.8 + 0.4 * fbm(p * np.array([1, 1, 0.25], np.float32), 0.03, 2, seed=143))
            f *= 1.0 + 0.25 * up[sel]
            X[sel, 1] = np.where(np.isin(m, ids(mats)), np.clip(f, 0, 1), X[sel, 1])
        if "oxide" in mods:  # white rust: patches, where water sits (bottoms) and on the tops
            s, mats = mods["oxide"]
            pl = (p[:, 2] - plo[isl[sel], 2]) / np.maximum(phi[isl[sel], 2] - plo[isl[sel], 2], 0.05)
            o = s * (smooth(0.42, 0.72, fbm(p, 0.12, 3, seed=145)) + 0.5 * smooth(0.3, 0.0, pl) * side[sel]
                     + 0.35 * up[sel] * fbm(p, 0.05, 2, seed=147))
            X[sel, 2] = np.where(np.isin(m, ids(mats)), np.clip(o, 0, 1), X[sel, 2])
        if "scuff" in mods:  # light abrasion on the upper curve, along the axis, where things rest and slide
            s, mats = mods["scuff"]
            nzs = Nn[sel, 2]
            sc = s * smooth(0.1, 0.6, nzs) * smooth(0.42, 0.72, fbm(p * np.array([0.35, 1, 1], np.float32), 0.08, 3, seed=149))
            sc = np.maximum(sc, s * 0.5 * smooth(0.55, 0.9, nzs))
            X[sel, 3] = np.where(np.isin(m, ids(mats)), np.clip(sc, 0, 1), X[sel, 3])
        if "base" in mods:  # dark water staining wicking up from the base
            s, hgt, mats = mods["base"]
            mm = np.isin(m, ids(mats)) & side[sel]
            if mm.any():
                hb = p[:, 2] - np.percentile(p[mm, 2], 0.5)
                wob = fbm(p * np.array([1, 1, 0], np.float32), 0.05, 2, seed=151)
                st = s * smooth(hgt * (0.65 + 0.7 * wob), 0.0, hb) * (0.7 + 0.3 * fbm(p, 0.03, 2, seed=153))
                st = np.maximum(st, s * 0.35 * smooth(0.025, 0.0, hb))
                streak[sel, 0] = np.where(mm, np.maximum(streak[sel, 0], st), streak[sel, 0])
        if "flange_rust" in mods:
            fl = flange_part[isl[sel]]
            fru = fl * (0.55 * edge[sel] + 0.25 * smooth(0.4, 0.8, fbm(p, 0.04, 2, seed=155))) * (0.6 + 0.4 * r_part3[sel])
            Rr[sel] = np.maximum(Rr[sel], np.clip(fru * mods["flange_rust"], 0, 1))
        log(f"refine roof {name}: {len(sel)} texels")
    # dark rings on the skid top round the upright vessels' bases
    sk = roof_t[up[roof_t] & (np.abs(z[roof_t] - (TOP + C.ROOF_SKIDS[0][5])) < 0.02)]
    if len(sk):
        p = P[sk]
        ring = np.zeros(len(sk), np.float32)
        for cx, cy, r, reach, s in C.WEATHER_BASE_RINGS:
            d = np.hypot(p[:, 0] - cx, p[:, 1] - cy) - r
            ring = np.maximum(ring, s * smooth(reach, 0.0, d) * (0.6 + 0.4 * fbm(p, 0.04, 2, seed=157)))
        streak[sk, 0] = np.maximum(streak[sk, 0], ring)
    log("refine roof: done")
    return dict(E=E, Rr=Rr, G=G, soot=soot, grease=grease, pvar=pvar, newness=newness, X=X)


def compute(write=True):
    t0 = time.time()
    _T0[0] = t0
    res = int(np.load(os.path.join(CACHE, "meta.npy"))[0])
    texels = np.load(os.path.join(CACHE, "texels.npy"))
    P = np.load(os.path.join(CACHE, "pos.npy"))
    Nn = np.load(os.path.join(CACHE, "nrm.npy"))
    ids = np.load(os.path.join(CACHE, "ids.npy"))
    shade = np.load(os.path.join(CACHE, "shade.npy"))
    parts = np.load(os.path.join(CACHE, "parts.npy"))  # lo xyz, hi xyz, area, mat, object
    isl = np.rint(ids[:, 0]).astype(np.int64)
    mat = np.rint(ids[:, 1]).astype(np.int64)
    n = len(P)
    log(f"compute: {n} texels at {res}px")
    rng = np.random.default_rng(1979)
    z = P[:, 2]
    nz_ = Nn[:, 2]
    up, down = nz_ > 0.6, nz_ < -0.6
    side = ~up & ~down
    ao_s = np.clip(shade[:, 0], 0, 1)
    bevel = np.clip(shade[:, 1], -1, 1)
    ao_m = np.clip(shade[:, 2], 0, 1)
    cavity = smooth(0.92, 0.55, ao_s)
    recess = smooth(0.95, 0.45, ao_m)
    edge = smooth(0.995, 0.93, bevel) * smooth(0.80, 0.97, ao_s)  # convex: the normal bends, nothing occludes
    PH, TOP = C.PLATFORM_H, C.CANOPY_TOP

    # parts: fasteners, per-part randomness (history), paint generations
    plo, phi = parts[:, 0:3], parts[:, 3:6]
    pdiag = np.linalg.norm(phi - plo, axis=1)
    fastener_part = pdiag < WX["fastener_diag"]
    fast = fastener_part[isl]
    r_part = hash01(isl, 1)
    r_part2 = hash01(isl, 2)
    r_part3 = hash01(isl, 3)
    yellow = np.isin(mat, list(YELLOW))
    odds = np.cumsum(WX["paint_odds"])
    gen = np.searchsorted(odds, r_part * odds[-1])  # 0 original, 1 faded, 2 amber, 3 newer
    newness = np.where(gen == 3, 0.65 + 0.35 * r_part2, 0.15 * r_part2).astype(np.float32)
    newness[~yellow] = (0.5 * r_part2[~yellow] ** 3).astype(np.float32)  # a few newer steel parts
    pvar = np.select([gen == 0, gen == 1, gen == 2, gen == 3],
                     [0.5 + 0.08 * (r_part2 - 0.5), 0.72 + 0.18 * r_part3, 0.12 + 0.16 * r_part3, 0.45 + 0.12 * r_part3]).astype(np.float32)
    # big soft blotches of fading inside a sheet (sun and rain on old paint)
    blot = fbm(P, 0.55, 3, seed=11)
    pvar = np.clip(pvar + (blot - 0.5) * 0.25 * (1 - newness), 0, 1)
    log("parts and paint generations")

    # rain exposure: under the canopy only wind-driven rain reaches the low walls
    cx0, cx1, cy0, cy1 = C.CANOPY_X0, C.CANOPY_X1, C.CANOPY_Y0, C.CANOPY_Y1
    inside = (P[:, 0] > cx0) & (P[:, 0] < cx1) & (P[:, 1] > cy0) & (P[:, 1] < cy1) & (z < C.CANOPY_BOTTOM + 0.02)
    to_edge = np.minimum.reduce([P[:, 0] - cx0, cx1 - P[:, 0], P[:, 1] - cy0, cy1 - P[:, 1]])
    reach = (C.CANOPY_BOTTOM - z) * math.tan(math.radians(WX["rain_angle_deg"]))
    exposure = np.where(inside, smooth(-0.15, 0.25, reach - to_edge), 1.0).astype(np.float32)
    exposure[down] *= 0.15
    low = smooth(0.75, PH + 0.02, z)  # the lowest ~60 cm of the walls
    wall_noise = fbm(P, 0.35, 3, seed=5)
    splash_top = WX["splash_top"][0] + (WX["splash_top"][1] - WX["splash_top"][0]) * fbm(P * np.array([1, 1, 0], np.float32), 0.45, 2, seed=9)
    splash = smooth(splash_top + PH, splash_top + PH - 0.22, z) * (z > PH - 0.01) * side
    log("exposure, splash")

    # hands and heat
    tz = _zones(P, C.WEATHER_TOUCH, ("touch", "abrade"))
    hz = _zones(P, C.WEATHER_HEAT, ("soot", "grease", "heat"))
    wz = _zones(P, [(k, p, p, r, s) for k, p, r, s in C.WEATHER_WATER], ("rust",))
    run_sources = _run_sources()
    log(f"zones, {len(run_sources)} runoff sources")

    # rain-flow streaks on the two camera-facing sides
    streak = np.zeros((n, 3), np.float32)  # dark grime, rust, grease
    halo = np.zeros(n, np.float32)
    bot_dist = np.full(n, 1.0, np.float32)
    top_dist = np.full(n, 1.0, np.float32)
    nx, ny = Nn[:, 0], Nn[:, 1]
    for axis, sel in (("-Y", side & (-ny >= np.abs(nx))), ("-X", side & (-nx > np.abs(ny)))):
        R = Relief(P, sel, axis, WX["cell"])
        ix = R.idx
        nu = R.nu
        # dirt each drip edge carries: rivets and bolts (rusty ones run orange), brackets, laps, sills
        col_rand = _urand(nu, R.cell, 0.015, 3)
        is_f = fast[ix].astype(np.float32)
        rusty = (r_part3[ix] < 0.45).astype(np.float32) * (1 - newness[ix])
        e_dark = (0.35 + 0.65 * r_part[ix]) * (0.55 + 0.45 * is_f)
        e_rust = rusty * (0.4 + 0.6 * r_part2[ix]) * (0.35 + 0.65 * is_f)
        steel_bare = ~yellow[ix]
        e_rust = np.where(steel_bare, e_rust * 0.8, e_rust)
        e_grease = hz["grease"][ix]
        src_edge = np.stack([R.splat(e_dark), R.splat(e_rust), R.splat(e_grease)], axis=-1)
        # long drip edges (laps, sills, box bottoms) release water in clusters, not as an even curtain;
        # fasteners always do
        gate = smooth(0.32, 0.72, _noise1(nu, R.cell, 0.018, 7)) * (0.5 + 0.5 * col_rand)
        fgrid = R.splat(is_f)
        src_edge *= np.maximum(fgrid, gate[None, None, :])[..., None]
        # top edges of faces collect dirt that streaks down: stronger outdoors and on old parts
        t_dark = (0.2 + 0.3 * r_part2[ix]) * (0.5 + 0.5 * exposure[ix]) * (1 - 0.6 * newness[ix])
        src_top = np.stack([R.splat(t_dark), R.splat(t_dark * 0.25 * rusty), R.splat(e_grease * 0.5)], axis=-1)
        # only some columns carry a run from a face's top edge (dirt washes off in clusters)
        gate_top = smooth(0.45, 0.8, _noise1(nu, R.cell, 0.03, 13)) * _urand(nu, R.cell, 0.012, 17) ** 1.3
        src_top *= gate_top[None, None, :, None] * 1.6
        carry = np.zeros_like(src_edge)
        carry[..., 2] = R.splat(hz["grease"][ix]) * 0.01  # grease film keeps feeding drips
        carry[..., 0] = R.splat(wz["rust"][ix]) * 0.0
        carry[..., 1] = R.splat(wz["rust"][ix]) * 0.03  # the drain keeps feeding rust
        S, bot, top = R.flow(src_edge, src_top, carry, rng)
        # meander: each streak wanders a cell or two sideways as it runs down
        uu, zg = np.meshgrid(np.arange(nu, dtype=np.float32) * R.cell, np.arange(R.nz, dtype=np.float32) * R.cell)
        wob = fbm(np.stack([uu.ravel() * 0.15, zg.ravel(), np.full(uu.size, 3.3, np.float32)], 1), 0.22, 2, seed=21)
        pos = np.arange(nu, dtype=np.float32)[None, :] - (wob.reshape(R.nz, nu) - 0.5) * 5.0  # sub-cell, no steps
        i0 = np.clip(np.floor(pos).astype(np.int64), 0, nu - 2)
        fr = np.clip(pos - i0, 0, 1)[None, :, :, None]
        S = (np.take_along_axis(S, np.broadcast_to(i0[None, :, :, None], S.shape), axis=2) * (1 - fr)
             + np.take_along_axis(S, np.broadcast_to(i0[None, :, :, None] + 1, S.shape), axis=2) * fr)
        S = _box(S, 1, 2)  # soften the 4 mm cell edges sideways
        # intermittency along the run (water doesn't wet a streak evenly)
        zz_noise = _gauss_blur2(rng.random((1, R.nz, nu)).astype(np.float32), 6, 3)
        zz_noise = (zz_noise - zz_noise.mean()) / max(zz_noise.std(), 1e-6)
        S *= np.clip(1.0 + 0.45 * zz_noise, 0.2, 1.8)[..., None]
        streak[ix] = R.lookup(S)
        bot_dist[ix] = R.lookup(bot)
        top_dist[ix] = R.lookup(top)
        # rust halo round fasteners on this side (blurred fastener mask)
        fm = R.splat(fast[ix].astype(np.float32) * (0.3 + 0.7 * rusty))
        halo[ix] = R.lookup(np.clip(_gauss_blur2(fm, 4) * 3.0, 0, 1))
        # 5B: long runs that start at a named source (WEATHER_RUNOFF, the fascia joints and rivets)
        runs = _source_runs(R, axis, P[ix], mat[ix], run_sources, i0, fr)
        if runs is not None:
            streak[ix, 0] += runs[:, 0]
            streak[ix, 1] += runs[:, 1]
            log(f"source runs {axis}: mean {runs.mean(0)}, max {runs.max(0)}")
        del S, src_edge, src_top, carry
        log(f"relief {axis}: {R.nu}x{R.nz} cells, {len(ix)} texels, streak mean {streak[ix].mean(0)}")

    # other sides (never in camera): streaks from part tops, cheap stand-in
    other = side & ~((-ny >= np.abs(nx)) | (-nx > np.abs(ny)))
    if other.any():
        ptop = phi[isl[other], 2]
        streak[other, 0] = 0.25 * smooth(0.4, 0.0, ptop - z[other]) * fbm(P[other] * np.array([4, 4, 0.3], np.float32), 0.1, 2, seed=4)

    # ---- edge wear (chips) ----
    p_wear = np.clip(0.15 + 1.7 * (r_part ** 3), 0.1, 1.8)  # some parts barely chipped, a few heavily
    vary = smooth(0.25, 0.75, fbm(P, 0.6, 3, seed=31))
    abr = 1.0 + 1.4 * low + 1.5 * tz["abrade"] + 0.6 * tz["touch"] + 0.4 * exposure
    E = edge * p_wear * (0.35 + 0.9 * vary) * abr * (1 - 0.75 * newness)
    E = np.maximum(E, fast * (0.25 + 0.6 * r_part2) * (1 - newness))  # bolt heads: wrenched, rubbed
    # dings away from edges where crates and feet hit
    E = np.maximum(E, (low * 0.45 + tz["abrade"] * 0.7) * smooth(0.64, 0.86, fbm(P, 0.025, 2, seed=41)) * side)
    E = np.clip(E, 0, 1)
    log("edge wear")

    # ---- rust ----
    wet_bias = 0.55 + 0.45 * exposure
    Rr = np.zeros(n, np.float32)
    Rr = np.maximum(Rr, fast * smooth(0.55, 0.1, r_part3) * (0.5 + 0.5 * r_part2))  # rusty bolts
    Rr = np.maximum(Rr, halo * 0.8)
    Rr = np.maximum(Rr, cavity * (0.25 + 0.5 * low) * wet_bias * smooth(0.3, 0.8, wall_noise))  # seams
    Rr = np.maximum(Rr, side * smooth(0.035, 0.0, bot_dist) * (0.25 + 0.6 * r_part) * wet_bias)  # bottom edges
    Rr = np.maximum(Rr, smooth(PH + 0.32, PH, z) * (0.3 + 0.7 * smooth(0.35, 0.75, fbm(P, 0.12, 3, seed=51))) * ~up)  # lowest band
    roof_deck = up & (np.abs(z - TOP) < 0.06)
    Rr = np.maximum(Rr, roof_deck * recess * 0.9 * smooth(0.3, 0.7, fbm(P, 0.25, 3, seed=61)))  # under equipment
    part_low = (z - plo[isl, 2]) / np.maximum(phi[isl, 2] - plo[isl, 2], 0.05)
    roofp = plo[isl, 2] > TOP - 0.05
    Rr = np.maximum(Rr, roofp * side * smooth(0.25, 0.0, part_low) * (0.3 + 0.7 * r_part3))  # unit bottoms
    Rr = np.maximum(Rr, wz["rust"])
    Rr = np.maximum(Rr, E * 0.5 * smooth(0.3, 0.8, fbm(P, 0.08, 2, seed=71)))  # old chips go brown
    Rr *= (1 - 0.7 * newness)
    Rr = np.clip(Rr, 0, 1)
    log("rust")

    # ---- grime ----
    G = 0.75 * cavity + 0.55 * recess
    G += down * (0.35 + 0.35 * inside)  # under-sides, the soffit
    G += up * (0.35 * recess + 0.25 * (1 - exposure) + 0.2 * smooth(0.4, 0.8, fbm(P, 0.3, 3, seed=81)))  # ledges collect dirt
    G += low * 0.35 * (0.5 + wall_noise)
    G += side * smooth(0.06, 0.0, bot_dist) * 0.25  # dirt line along the bottom of every sheet
    G *= (1 - 0.45 * edge) * (1 - 0.8 * tz["touch"])  # rubbed clean
    G = np.clip(G * (0.75 + 0.5 * r_part2), 0, 1)
    log("grime")

    # ---- heat, hands, wet ----
    soot = np.clip(hz["soot"] * (0.6 + 0.4 * smooth(0.3, 0.7, fbm(P, 0.15, 2, seed=91))) + hz["heat"] * 0.4, 0, 1)
    grease = np.clip(hz["grease"] * (0.5 + 0.5 * cavity + 0.3 * down) + streak[:, 2], 0, 1)
    touch = np.clip(tz["touch"] * (0.7 + 0.3 * edge), 0, 1)
    wet = np.clip(exposure * (0.55 + 0.45 * up) + 0.6 * splash + 0.35 * streak[:, 0], 0, 1)
    heat = hz["heat"]
    soot = np.maximum(soot, heat * 0.5)

    # brief 5B: the targeted refinement (fascia, service-window frame, roof units) and the fourth mask
    rf = refine(locals())
    E, Rr, G, soot, grease, pvar, newness, X = (rf[k] for k in ("E", "Rr", "G", "soot", "grease", "pvar", "newness", "X"))
    del rf

    if not write:
        return locals()
    A = np.stack([E, Rr, G, np.clip(streak[:, 0], 0, 1)], 1)
    B = np.stack([np.clip(streak[:, 1], 0, 1), soot, touch, wet], 1)
    Cc = np.stack([pvar, newness, np.clip(splash * (0.6 + 0.4 * wall_noise), 0, 1), grease], 1)
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, arr in (("A", A), ("B", B), ("C", Cc)):
        write_png(os.path.join(OUT_DIR, f"T_KioskWear_{name}.png"), texels, arr, res)
    # D (half resolution; smooth zone masks): dried spatter, sun fade, zinc oxide, light scuffs
    write_png(os.path.join(OUT_DIR, "T_KioskWear_D.png"), texels, X, res, out_res=res // 2)
    log(f"compute done in {time.time() - t0:.0f}s")
    return None


def _dilate(img, filled, iters):
    """Grow island edges into the empty gutter so filtering and mips don't pull in black."""
    for _ in range(iters):
        if filled.all():
            break
        new = filled.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = np.roll(filled, (dy, dx), axis=(0, 1)) & ~new
            if nb.any():
                img[nb] = np.roll(img, (dy, dx), axis=(0, 1))[nb]
                new |= nb
        filled = new
    return img


def write_png(path, texels, values, res, out_res=None):
    """Mask values at the atlas texels -> PNG (gutters dilated). out_res < res box-filters it down."""
    img = np.zeros((res * res, 4), np.uint8)
    img[texels] = np.rint(np.clip(values, 0, 1) * 255).astype(np.uint8)
    filled = np.zeros(res * res, bool)
    filled[texels] = True
    img = _dilate(img.reshape(res, res, 4), filled.reshape(res, res), 8)
    if out_res and out_res != res:
        f = res // out_res
        img = np.rint(img.reshape(out_res, f, out_res, f, 4).mean(axis=(1, 3), dtype=np.float32)).astype(np.uint8)
        res = out_res
    name = os.path.splitext(os.path.basename(path))[0]
    bimg = bpy.data.images.get(name) or bpy.data.images.new(name, res, res, alpha=True)
    if bimg.size[0] != res:
        bimg.scale(res, res)
    bimg.colorspace_settings.name = "Non-Color"
    bimg.alpha_mode = "STRAIGHT"
    bimg.pixels.foreach_set((img.reshape(-1) / np.float32(255)).astype(np.float32))
    bimg.filepath_raw = path
    bimg.file_format = "PNG"
    bimg.save()
    log(f"wrote {os.path.basename(path)}")


# ---- 4. Tiling detail (T_WearDetail): what the baked potentials are thresholded with --------------

DETAIL_TILE_M = 0.5  # one tile per 0.5 m of the metre-scale UVMap (TEXCOORD_0); 2048 px -> 0.24 mm/px


def _pnoise(res, feature_px, rng):
    """Periodic (tileable) band-limited noise, zero mean, unit std."""
    f = np.fft.fftfreq(res).astype(np.float32)
    k = np.sqrt(f[None, :] ** 2 + f[:, None] ** 2)
    filt = np.exp(-(k * feature_px) ** 2)
    n = np.real(np.fft.ifft2(np.fft.fft2(rng.standard_normal((res, res)).astype(np.float32)) * filt)).astype(np.float32)
    return (n - n.mean()) / max(float(n.std()), 1e-9)


def _equalise(a):
    """Rank-transform to a uniform 0..1 distribution (so thresholds mean coverage)."""
    flat = a.ravel()
    out = np.empty(flat.size, np.float32)
    out[np.argsort(flat, kind="stable")] = np.linspace(0, 1, flat.size, dtype=np.float32)
    return out.reshape(a.shape)


def make_detail(res=2048):
    """R chip noise (3 mm - 3 cm clusters), G scratches (mostly horizontal, 1-12 cm), B water spots and
    splash speckle (0.5-6 mm), A paint mottling (5-15 cm). Tileable, linear."""
    rng = np.random.default_rng(42)
    px = DETAIL_TILE_M / res
    cm = 0.01 / px
    chips = _equalise(0.5 * _pnoise(res, 3.0 * cm, rng) + 0.3 * _pnoise(res, 1.0 * cm, rng) + 0.2 * _pnoise(res, 0.3 * cm, rng))
    scr = np.zeros((res, res), np.float32)
    for _ in range(900):
        length = rng.uniform(1, 12) * cm
        ang = rng.normal(0, 0.35) if rng.random() < 0.65 else rng.uniform(0, math.pi)
        x0, y0 = rng.uniform(0, res, 2)
        t = np.arange(0, length, 0.5, dtype=np.float32)
        xs = np.rint(x0 + t * math.cos(ang)).astype(np.int64) % res
        ys = np.rint(y0 + t * math.sin(ang)).astype(np.int64) % res
        inten = rng.uniform(0.35, 1.0) * np.clip(np.sin(np.linspace(0, math.pi, len(t))) * 1.6, 0, 1)
        w = 1 if rng.random() < 0.7 else 2
        for oy in range(w):
            np.maximum.at(scr, ((ys + oy) % res, xs), inten)
    scr = np.maximum(scr, np.roll(scr, 1, 0) * 0.5)
    spots = np.zeros((res, res), np.float32)
    yy, xx = np.mgrid[-26:27, -26:27]
    rr = np.sqrt(xx ** 2 + yy ** 2).astype(np.float32)
    for _ in range(1500):
        r = rng.uniform(2, 12) * (rng.random() ** 2) + 1.5
        cx, cy = rng.integers(0, res, 2)
        disc = np.clip((r - rr) / 1.5, 0, 1) * rng.uniform(0.3, 1.0)
        disc = np.maximum(disc, np.clip(1 - np.abs(rr - r) / 1.2, 0, 1) * 0.6 * (disc.max()))  # dried ring
        ys = (cy + yy) % res
        xs = (cx + xx) % res
        spots[ys, xs] = np.maximum(spots[ys, xs], disc)
    spots = np.maximum(spots, np.clip(_pnoise(res, 0.12 * cm, rng) - 2.2, 0, 1))  # fine speckle
    mott = _equalise(0.6 * _pnoise(res, 5 * cm, rng) + 0.4 * _pnoise(res, 15 * cm, rng))
    img = np.stack([chips, np.clip(scr, 0, 1), np.clip(spots, 0, 1), mott], -1)[::-1]  # Blender images are bottom-up
    os.makedirs(OUT_DIR, exist_ok=True)
    texels = np.arange(res * res)
    write_png(os.path.join(OUT_DIR, "T_WearDetail.png"), texels, img.reshape(-1, 4), res)


def build(objects):
    """Called by export_kiosk_glb.py: ids + WeatherUV + bake + masks."""
    _T0[0] = time.time()
    prepare(objects)
    bake(objects)
    compute()
    make_detail()
