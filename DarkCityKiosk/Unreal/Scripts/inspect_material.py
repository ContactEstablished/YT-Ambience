"""Prints a material's parameters and its expression graph: inspect_material.py /Game/Path/M_Name"""
import sys
import unreal

mel = unreal.MaterialEditingLibrary
path = sys.argv[1]
m = unreal.load_asset(path)
print("class", m.get_class().get_name())
base = m
if isinstance(m, unreal.MaterialInstance):
    base = m.get_base_material()
    print("parent", m.get_editor_property("parent").get_path_name())
    for p in m.get_editor_property("scalar_parameter_values"):
        print("  MI scalar", p.parameter_info.name, p.parameter_value)
    for p in m.get_editor_property("vector_parameter_values"):
        print("  MI vector", p.parameter_info.name, p.parameter_value)
    for p in m.get_editor_property("texture_parameter_values"):
        print("  MI texture", p.parameter_info.name, p.parameter_value.get_path_name() if p.parameter_value else None)
print("scalars", [str(n) for n in mel.get_scalar_parameter_names(base)])
print("vectors", [str(n) for n in mel.get_vector_parameter_names(base)])
print("textures", [str(n) for n in mel.get_texture_parameter_names(base)])
print("statics", [str(n) for n in mel.get_static_switch_parameter_names(base)])
if isinstance(base, unreal.Material):
    for prop in ("MP_BASE_COLOR", "MP_ROUGHNESS", "MP_NORMAL", "MP_METALLIC", "MP_SPECULAR", "MP_EMISSIVE_COLOR", "MP_OPACITY"):
        node = mel.get_material_property_input_node(base, getattr(unreal.MaterialProperty, prop))
        print(prop, "<-", node.get_class().get_name() if node else None,
              (node.get_editor_property("material_function").get_path_name() if node and isinstance(node, unreal.MaterialExpressionMaterialFunctionCall) else ""))
    print("blend", base.get_editor_property("blend_mode"), "shading", base.get_editor_property("shading_model"))
    funcs = set()
    for e in unreal.MaterialEditingLibrary.get_material_expressions(base) if hasattr(mel, "get_material_expressions") else []:
        if isinstance(e, unreal.MaterialExpressionMaterialFunctionCall):
            funcs.add(e.get_editor_property("material_function").get_path_name())
    print("function calls", sorted(funcs))
