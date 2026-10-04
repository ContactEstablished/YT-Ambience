import importlib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck; dck = importlib.reload(dck)
import unreal

dck.ensure_map()
rain = dck.find_actor("EasyRain")
names = """rainSize RainSize globalScale rainSpeed fallingSpeed volumetricMaskingAmount volumetricMaskSpeed VolumetricMaskTiling maskSpeed maskTiling gustsContrast gustsSpeed gustsTiling gustBreakupAmount detailStrength midStrength baseStrength DetailStrength curtainColor CurtainFallingSpeed CurtainGlobalSpeed curtainGlobalStrengthMultiplier CurtainGlobalWindStrength curtainWindDirection rainCurtainGlobalScale globalCurtainSpeed customSpeed cameraAffectsDirection cameraImpactsDirection CameraFadeDistance driftsSizeMax driftsSizeMin driftsSpawnRate driftOpacity spriteDynamicMaterial systemTickRatePerSecond GlimmerIntensity backlightingTint BacklightSpread splashSpreadRadius splashScaleVariationSpeed Preset rainState""".split()
for n in names:
    try:
        print(f"  {n} = {rain.get_editor_property(n)}")
    except Exception:
        pass
# Which properties can Sequencer animate? (CPF_Interp = 'Expose to Cinematics')
cls = rain.get_class()
print("class", cls.get_name())
