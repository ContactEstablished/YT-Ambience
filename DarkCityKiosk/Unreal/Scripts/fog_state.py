"""Sets the height fog to one look state for testing (the sweep keys these over time).
    node Scripts/ue.mjs Scripts/fog_state.py density extinction inscatter_r,g,b emissive_r,g,b"""
import importlib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck; dck = importlib.reload(dck)
import unreal
density, ext = float(sys.argv[1]), float(sys.argv[2])
ins = [float(v) for v in sys.argv[3].split(",")]
emi = [float(v) for v in sys.argv[4].split(",")]
dck.ensure_map()
unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
fc = dck.find_actor("HeightFog").get_component_by_class(unreal.ExponentialHeightFogComponent)
fc.modify()
fc.set_fog_density(density)
fc.set_volumetric_fog_extinction_scale(ext)
fc.set_fog_inscattering_color(unreal.LinearColor(*ins, 1.0))
fc.set_volumetric_fog_emissive(unreal.LinearColor(*emi, 1.0))
print("fog:", density, ext, ins, emi)
