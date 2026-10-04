"""Lists assets under a content path with their classes: inspect_assets.py /Game/EasyRain"""
import sys
import unreal

path = sys.argv[1] if len(sys.argv) > 1 else "/Game"
reg = unreal.AssetRegistryHelpers.get_asset_registry()
for a in sorted(reg.get_assets_by_path(path, recursive=True), key=lambda a: str(a.package_name)):
    print(f"{str(a.asset_class_path.asset_name):32} {a.package_name}")
