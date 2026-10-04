import unreal
rain = None
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label() == "EasyRain":
        rain = a
cands = ["Rain Size", "rainSize", "RainSize", "Near Particle Size Min", "NearParticleSizeMin", "nearParticleSizeMin",
         "Near Particle Size Max", "distantParticleScale", "Distant Particle Scale", "rainfallSpeed", "rainSpread",
         "motionScaling", "spawnRadius", "spawnRadiusHeight", "rainLifetime", "rainAmount", "GlobalFallingSpeed",
         "globalFallingSpeed", "Primary Spawn Rate", "primarySpawnRate", "Fake DOF Distance", "Fading Distance",
         "Geometry Fade Distance", "Environment Glow", "Glow Spread", "Ambient Intensity", "Ambient Color", "AmbientSaturation"]
for n in cands:
    try:
        print(f"  {n!r} = {rain.get_editor_property(n)}")
    except Exception:
        pass
# Niagara user parameters on the rain component
nc = rain.get_component_by_class(unreal.NiagaraComponent)
print("niagara asset:", nc.get_asset().get_path_name() if nc else None)
