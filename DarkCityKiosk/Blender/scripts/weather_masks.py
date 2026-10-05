"""Recomputes the kiosk weathering masks from the bake cache (no re-export, no re-bake):

    blender -b --factory-startup -P weather_masks.py [-- --detail]   (--detail: only the tiling T_WearDetail)

The cache (Blender/weather_cache/) is written by export_kiosk_glb.py (kiosk/weather.py bake()).
Re-run that export after any geometry change: the cache matches one WeatherUV layout. Then, in
Unreal: node Scripts/ue.mjs Scripts/kiosk_weather.py --textures
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kiosk import weather  # noqa: E402

if "--detail" in sys.argv:
    weather.make_detail()
else:
    weather.compute()
