import importlib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck; dck = importlib.reload(dck)
import unreal

dck.ensure_map()
print("world", dck.world().get_path_name())
cls = unreal.EditorAssetLibrary.load_blueprint_class("/Game/EasyRain/Blueprints/BP_EasyRain")
rain = dck.get_or_spawn(cls, "EasyRain", folder="Weather")
names = """Preset rainState RainState cameraCentric spawnRate spawnAmount spawnRadius spawnRadiusHeight spawnZOffset rainAmount rainfallSpeed rainSpread rainLifetime rainColor rainAlpha rainEmissiveIntensity rainBacklighting rainGlimmerIntensity globalScale GlobalStrengthMultiplier globalWindStrength windStrength windDirection windUpdraftStrength gustAmount gustSpeed gustTiling enableRainCurtains rainCurtainsColor CurtainOpacity CurtainSpawnRate CurtainSpriteSize curtainsHeightOffset driftsEnable driftsSpawnRate driftOpacity splashAmount splashColor splashScale splashAlpha splashHeightOffset shelterHeightLimit fakeDoFDistance NearParticleSizeMin NearParticleSizeMax distantParticleScale motionScaling systemTickRatePerSecond UpdateRainValuesTickRate puddleCoverage puddleColor puddleOpacity puddleMaskScale puddleTransitionSharpness puddleWetnessFalloff surfaceWetnessAmount wetSurfaceDarkening rainRipplesAmount rainRipplesSpeed rainRipplesTiling rainRipplesNormalIntensity puddleWindSpeed puddleWindNormalIntensity puddleWindRippleTiling ambientColorSaturation backlightingTint BacklightSpread""".split()
for n in names:
    try:
        v = rain.get_editor_property(n)
        print(f"  {n} = {v}")
    except Exception as e:
        print(f"  {n}: -- ({str(e).splitlines()[0][:60]})")
