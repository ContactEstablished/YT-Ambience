"""Dumps a material's (or material function's) expression graph:
inspect_graph.py /Game/Path/M_or_MF [--function]"""
import sys
import unreal

mel = unreal.MaterialEditingLibrary
asset = unreal.load_asset(sys.argv[1])
is_func = isinstance(asset, unreal.MaterialFunction)
exprs = mel.get_material_function_expressions(asset) if is_func else mel.get_material_expressions(asset)
ids = {e.get_name(): i for i, e in enumerate(exprs)}


def label(e):
    cls = e.get_class().get_name().replace("MaterialExpression", "")
    extra = ""
    for prop in ("parameter_name", "input_name", "output_name", "function_input_type"):
        try:
            extra += f" {prop}={e.get_editor_property(prop)}"
        except Exception:
            pass
    if isinstance(e, unreal.MaterialExpressionMaterialFunctionCall):
        f = e.get_editor_property("material_function")
        extra += f" fn={f.get_name() if f else None}"
    if isinstance(e, unreal.MaterialExpressionCollectionParameter):
        extra += f" coll={e.get_editor_property('collection').get_name()} param={e.get_editor_property('parameter_name')}"
    return f"[{ids[e.get_name()]}] {cls}{extra}"


for e in exprs:
    line = label(e)
    try:
        names = mel.get_material_expression_input_names(e)
        ins = mel.get_inputs_for_material_function_expression(asset, e) if is_func else mel.get_inputs_for_material_expression(asset, e)
        links = [f"{n}<-{ids.get(i.get_name(), '?') if i else '-'}" for n, i in zip(names, ins) if i]
        if links:
            line += "  IN: " + ", ".join(links)
    except Exception as ex:
        line += f"  (inputs: {ex})"
    print(line)
if not is_func:
    for prop in ("MP_MATERIAL_ATTRIBUTES", "MP_BASE_COLOR", "MP_NORMAL", "MP_ROUGHNESS", "MP_SPECULAR", "MP_METALLIC", "MP_EMISSIVE_COLOR", "MP_WORLD_POSITION_OFFSET", "MP_DISPLACEMENT"):
        try:
            n = mel.get_material_property_input_node(asset, getattr(unreal.MaterialProperty, prop))
            if n:
                print(f"{prop} <- [{ids.get(n.get_name())}] out={mel.get_material_property_input_node_output_name(asset, getattr(unreal.MaterialProperty, prop))}")
        except Exception as ex:
            print(prop, "?", ex)
    print("use_material_attributes", asset.get_editor_property("use_material_attributes"))
