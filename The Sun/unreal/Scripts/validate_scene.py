"""Read-only native asset checks. Run in the editor via -ExecutePythonScript.
StaticMeshEditorSubsystem is unavailable in the minimal Python commandlet.
"""
import unreal as u
import json
from pathlib import Path
root=Path(u.Paths.project_dir())
ela=u.EditorAssetLibrary
u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Solar/SolarScene')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
solar=[a for a in actors if isinstance(a,u.StaticMeshActor)]
cameras=[a for a in actors if isinstance(a,u.CameraActor)]
assert len(solar)==6, 'Duplicate or missing solar mesh actors'
assert len(cameras)==1, 'Duplicate or missing camera'
settings={str(p.get_editor_property('parameter_name')):p.get_editor_property('default_value') for p in ela.load_asset('/Game/Solar/SolarControls').get_editor_property('scalar_parameters')}
assert settings['FlareActivity']==1.5 and settings['SurfaceFlow']==1 and settings['Sunspots']==1
mesh_sub=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
meshes=['MagneticLoops','PlasmaEjections','EjectaParticles','CoronaPlane','StarField']
for name in meshes:
    mesh=ela.load_asset('/Game/Solar/'+name)
    assert mesh and mesh_sub.get_lod_build_settings(mesh,0).get_editor_property('use_full_precision_u_vs'), name
materials=['M_Photosphere','M_Corona','M_MagneticLoops','M_PlasmaEjections','M_EjectaParticles','M_Stars']
for name in materials:
    mat=ela.load_asset('/Game/Solar/'+name)
    assert mat.get_editor_property('shading_model')==u.MaterialShadingModel.MSM_UNLIT
    assert u.MaterialEditingLibrary.get_material_property_input_node(mat,u.MaterialProperty.MP_EMISSIVE_COLOR), name
seq=ela.load_asset('/Game/Solar/SolarFilm')
assert seq.get_display_rate().numerator==30
assert seq.get_playback_start()==0 and seq.get_playback_end()==360
assert len(seq.get_tracks())==2
report={'engine':u.SystemLibrary.get_engine_version(),'mesh_actors':len(solar),'cameras':len(cameras),
        'native_materials':materials,'full_precision_meshes':meshes,'controls':settings,
        'fps':30,'frame_range':[0,360],'passed':True,
        'scope':'Saved asset structure, material output links, precision, controls, and sequence; no desktop UI automation.'}
(root/'Assets'/'validation.json').write_text(json.dumps(report,indent=2))
u.log('SOLAR_VALIDATION_PASSED')
