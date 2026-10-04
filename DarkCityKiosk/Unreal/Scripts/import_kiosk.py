"""Imports RawContent/<dck.KIOSK_GLB>.glb into dck.KIOSK_MESHES (replacing in place)
and prints each mesh's bounds so the axis mapping can be checked."""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402

dck = importlib.reload(dck)
import unreal  # noqa: E402

src = os.path.join(dck.RAW, f"{dck.KIOSK_GLB}.glb")
task = dck.setp(unreal.AssetImportTask(), filename=src, destination_path=dck.KIOSK_MESHES,
                automated=True, replace_existing=True, save=True)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
print("imported:", len(task.get_editor_property("imported_object_paths")), "objects")

reg = unreal.AssetRegistryHelpers.get_asset_registry()
for a in sorted(reg.get_assets_by_path(dck.KIOSK_MESHES, recursive=True), key=lambda a: str(a.asset_name)):
    if str(a.asset_class_path.asset_name) == "StaticMesh":
        sm = unreal.load_asset(str(a.package_name))
        b = sm.get_bounding_box()
        print(f"{str(a.asset_name):28} {str(a.package_name):70} min ({b.min.x:.0f},{b.min.y:.0f},{b.min.z:.0f}) max ({b.max.x:.0f},{b.max.y:.0f},{b.max.z:.0f})")
