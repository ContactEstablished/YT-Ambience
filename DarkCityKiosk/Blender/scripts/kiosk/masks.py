"""Step 5: texture prep. Bakes surfacing masks into a vertex-colour attribute "Masks", exported
with the glTF so Unreal's kiosk materials can place wear and grime procedurally:

  R = edges     convex edges and corners (paint chips, rubbed bare metal)
  G = occlusion ambient occlusion from the whole kiosk (grime in recesses, under the canopy)
  B = cavity    concave creases (dirt and rust collecting in seams)

Large faces are subdivided first so the masks have enough vertices to vary across a panel.
Values are linear 0..1 (FLOAT_COLOR), so Unreal receives them unchanged.
"""
import bmesh
import bpy

MAX_EDGE = 0.18  # metres; longer edges are split so masks can vary across big panels
AO_DISTANCE = 0.6  # metres; how far occlusion looks for nearby geometry
AO_SAMPLES = 48
EDGE_GAIN, CAVITY_GAIN = 3.0, 3.0  # stretch the dirt-map contrast into usable 0..1 masks


def subdivide_long_edges(ob, max_edge=MAX_EDGE, passes=5):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for _ in range(passes):
        long_edges = [e for e in bm.edges if e.calc_length() > max_edge]
        if not long_edges:
            break
        bmesh.ops.subdivide_edges(bm, edges=long_edges, cuts=1, use_grid_fill=True)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def _color_layer(ob, name):
    attrs = ob.data.color_attributes
    if name in attrs:
        attrs.remove(attrs[name])
    layer = attrs.new(name, "FLOAT_COLOR", "POINT")
    attrs.active_color = layer
    return layer


def _select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def bake_masks(objects):
    scene = bpy.context.scene
    for ob in objects:
        subdivide_long_edges(ob)

    # Edges/cavity from Blender's dirty-vertex-colours (concave dark, convex bright), per object
    for ob in objects:
        _color_layer(ob, "Dirt")
        _select_only([ob])
        bpy.ops.object.mode_set(mode="VERTEX_PAINT")
        bpy.ops.paint.vertex_color_dirt(blur_strength=1.0, blur_iterations=1, clean_angle=3.14159, dirt_angle=0.0,
                                        dirt_only=False, normalize=True)
        bpy.ops.object.mode_set(mode="OBJECT")

    # Occlusion: one Cycles AO bake across all objects (they occlude each other)
    for ob in objects:
        _color_layer(ob, "AO")
    scene.render.engine = "CYCLES"
    scene.cycles.samples = AO_SAMPLES
    if scene.world is None:
        scene.world = bpy.data.worlds.new("BakeWorld")
    scene.world.light_settings.distance = AO_DISTANCE
    _select_only(objects)
    bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")

    # Pack into Masks (R edge, G occlusion, B cavity)
    for ob in objects:
        attrs = ob.data.color_attributes
        dirt, ao = attrs["Dirt"].data, attrs["AO"].data
        n = len(dirt)
        d = [0.0] * (n * 4)
        a = [0.0] * (n * 4)
        dirt.foreach_get("color", d)
        ao.foreach_get("color", a)
        out = [0.0] * (n * 4)
        for i in range(n):
            v = d[4 * i]
            out[4 * i] = min(max((v - 0.5) * EDGE_GAIN, 0.0), 1.0)
            out[4 * i + 1] = a[4 * i]
            out[4 * i + 2] = min(max((0.5 - v) * CAVITY_GAIN, 0.0), 1.0)
            out[4 * i + 3] = 1.0
        masks = _color_layer(ob, "Masks")
        masks.data.foreach_set("color", out)
        attrs.remove(attrs["Dirt"])
        attrs.remove(attrs["AO"])
        attrs.active_color = attrs["Masks"]
        attrs.render_color_index = attrs.active_color_index
        r = out[0::4]
        g = out[1::4]
        print(f"masks {ob.name}: {n} verts, edge mean {sum(r) / n:.2f}, occlusion mean {sum(g) / n:.2f}")
