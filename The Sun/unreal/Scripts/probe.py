import unreal, json
from pathlib import Path
root=Path(unreal.Paths.project_dir())
names=['MaterialExpressionCustom','CustomInput','MovieSceneMaterialParameterCollectionTrack','MovieSceneParameterSection','MaterialParameterCollection','CollectionScalarParameter','MoviePipelinePIEExecutor','MoviePipelineInProcessExecutor','MoviePipelineQueueSubsystem','EditorLevelLibrary','MovieSceneCameraCutSection']
out={name:str(getattr(unreal,name,None).__doc__) for name in names}
(root/'Assets'/'api_probe.json').write_text(json.dumps(out,indent=2))
unreal.log('SOLAR_PROBE_COMPLETE')
