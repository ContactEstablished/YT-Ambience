"""Material-building helpers for the Dark City Kiosk editor scripts."""
import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()


def setp(obj, **props):
    for k, v in props.items():
        try:
            obj.set_editor_property(k, v)
        except Exception as e:  # noqa: BLE001
            print(f"  (skip {type(obj).__name__}.{k}: {str(e).splitlines()[0][:90]})")
    return obj


def ensure_dir(path):
    if not EAL.does_directory_exist(path):
        EAL.make_directory(path)


def material(folder, name):
    """Load and clear the material, or create it."""
    path = f"{folder}/{name}"
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path)
        MEL.delete_all_material_expressions(m)
        for _ in range(3):
            left = list(MEL.get_material_expressions(m))
            if not left:
                break
            for e in left:
                MEL.delete_material_expression(m, e)
        return m
    ensure_dir(folder)
    return TOOLS.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())


def expr(m, cls, x, y, **props):
    return setp(MEL.create_material_expression(m, cls, x, y), **props)


def link(a, a_out, b, b_in):
    if not MEL.connect_material_expressions(a, a_out, b, b_in):
        print(f"  !! link failed: {a.get_name()}.{a_out} -> {b.get_name()}.{b_in}")


def out(m, e, e_out, prop):
    if not MEL.connect_material_property(e, e_out, prop):
        print(f"  !! output failed: {e.get_name()}.{e_out} -> {prop}")


def scalar(m, name, value, x, y):
    return expr(m, unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=float(value))


def vector(m, name, rgb, x, y):
    return expr(m, unreal.MaterialExpressionVectorParameter, x, y, parameter_name=name,
                default_value=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))


def custom(m, code, inputs, out_type, x, y, desc=""):
    c = expr(m, unreal.MaterialExpressionCustom, x, y, code=code, output_type=out_type, description=desc)
    ins = []
    for n in inputs:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        ins.append(ci)
    c.set_editor_property("inputs", ins)
    return c


def finish(m):
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)


def instance(folder, name, parent, scalars=None, vectors=None):
    path = f"{folder}/{name}"
    ensure_dir(folder)
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset(
        name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, parent)
    for k, v in (scalars or {}).items():
        MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
    for k, v in (vectors or {}).items():
        MEL.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(v[0], v[1], v[2], 1.0))
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    return mi
