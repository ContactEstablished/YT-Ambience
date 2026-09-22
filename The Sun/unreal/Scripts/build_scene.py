"""Run inside Unreal Editor with -ExecutePythonScript. Builds only /Game/Solar.
Creates materials, imports mesh sources, saves a level and sequence, then renders.
"""
import unreal as u
import json, traceback
from pathlib import Path

ROOT=Path(u.Paths.project_dir())
TOOLS=u.AssetToolsHelpers.get_asset_tools()
LIB=u.MaterialEditingLibrary
ELA=u.EditorAssetLibrary
SUB=u.get_editor_subsystem(u.UnrealEditorSubsystem)
ACTORS=u.get_editor_subsystem(u.EditorActorSubsystem)
LEVELS=u.get_editor_subsystem(u.LevelEditorSubsystem)
COMMON=(ROOT/'Shaders'/'Common.hlsl').read_text()
FOLDER='/Game/Solar'
PARAMETERS={'SolarTime':8.,'RotationSpeed':1.,'SurfaceFlow':1.,'Sunspots':1.,'FlareActivity':1.5,'FlareIntensity':1.,'CoronaGlow':1.,'SunSize':1.,'Stars':1.}

def struct(cls,**props):
    value=cls()
    for key,val in props.items():value.set_editor_property(key,val)
    return value

def asset(name,cls,factory):
    old=ELA.load_asset(FOLDER+'/'+name) if ELA.does_asset_exist(FOLDER+'/'+name) else None
    return old or TOOLS.create_asset(name,FOLDER,cls,factory)

def node(mat,cls,**props):
    n=LIB.create_material_expression(mat,cls)
    for key,value in props.items():n.set_editor_property(key,value)
    return n

def make_material(name,shader,mpc,additive=False,wpo=None):
    mat=asset(name,u.Material,u.MaterialFactoryNew())
    LIB.delete_all_material_expressions(mat)
    mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('blend_mode',u.BlendMode.BLEND_ADDITIVE if additive else u.BlendMode.BLEND_OPAQUE)
    if additive:
        mat.set_editor_property('translucency_pass',u.MaterialTranslucencyPass.MTP_BEFORE_DOF)
    inputs={}
    for key in PARAMETERS:
        inputs[key]=node(mat,u.MaterialExpressionCollectionParameter,collection=mpc,parameter_name=key)
    inputs['World']=node(mat,u.MaterialExpressionWorldPosition)
    inputs['UV']=node(mat,u.MaterialExpressionTextureCoordinate)
    def custom(code,typ):
        expr=node(mat,u.MaterialExpressionCustom,code=COMMON+code,output_type=typ,description=name+' / native solar shader')
        expr.set_editor_property('inputs',[struct(u.CustomInput,input_name=k) for k in inputs])
        for k,v in inputs.items():
            assert LIB.connect_material_expressions(v,'',expr,k), 'Custom input connection failed: '+k
        return expr
    expr=custom((ROOT/'Shaders'/shader).read_text(),u.CustomMaterialOutputType.CMOT_FLOAT4)
    mask=node(mat,u.MaterialExpressionComponentMask,r=True,g=True,b=True,a=False)
    assert LIB.connect_material_expressions(expr,'',mask,''), 'RGB mask connection failed'
    LIB.connect_material_property(mask,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    if additive:
        opacity=node(mat,u.MaterialExpressionConstant,r=1.)
        LIB.connect_material_property(opacity,'',u.MaterialProperty.MP_OPACITY)
    if wpo:
        expr=custom((ROOT/'Shaders'/wpo).read_text(),u.CustomMaterialOutputType.CMOT_FLOAT3)
        LIB.connect_material_property(expr,'',u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    elif name in ('M_Photosphere','M_Corona'):
        expr=custom('return World*(SunSize-1.);',u.CustomMaterialOutputType.CMOT_FLOAT3)
        LIB.connect_material_property(expr,'',u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    LIB.layout_material_expressions(mat)
    LIB.recompile_material(mat)
    ELA.save_loaded_asset(mat)
    return mat

def import_mesh(name):
    existing=ELA.load_asset(FOLDER+'/'+name) if ELA.does_asset_exist(FOLDER+'/'+name) else None
    source=ROOT/'Assets'/(name+'.obj')
    destination=ROOT/'Content'/'Solar'/(name+'.uasset')
    if existing and destination.stat().st_mtime>=source.stat().st_mtime:
        full_precision(existing)
        return existing
    task=u.AssetImportTask()
    task.filename=str(ROOT/'Assets'/(name+'.obj'))
    task.destination_path=FOLDER
    task.destination_name=name
    task.automated=True;task.replace_existing=True;task.save=True
    options=u.FbxImportUI()
    options.import_mesh=True;options.import_materials=False;options.import_textures=False
    options.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    options.static_mesh_import_data.combine_meshes=True
    options.static_mesh_import_data.generate_lightmap_u_vs=False
    options.static_mesh_import_data.auto_generate_collision=False
    task.options=options
    TOOLS.import_asset_tasks([task])
    mesh=ELA.load_asset(FOLDER+'/'+name)
    if not mesh:raise RuntimeError('Mesh import failed: '+name)
    mesh.set_editor_property('positive_bounds_extension',u.Vector(250,250,250))
    mesh.set_editor_property('negative_bounds_extension',u.Vector(250,250,250))
    full_precision(mesh)
    ELA.save_loaded_asset(mesh)
    u.log('SOLAR_MESH '+name+' '+str(mesh.get_bounding_box()))
    return mesh

def full_precision(mesh):
    subsystem=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    settings=subsystem.get_lod_build_settings(mesh,0)
    if not settings.get_editor_property('use_full_precision_u_vs'):
        settings.set_editor_property('use_full_precision_u_vs',True)
        subsystem.set_lod_build_settings(mesh,0,settings)
        ELA.save_loaded_asset(mesh)

def actor(name,mesh,mat,location=(0,0,0),scale=(1,1,1),rotation=(0,0,0)):
    a=ACTORS.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*location),u.Rotator(*rotation))
    a.set_actor_label(name)
    c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,mat)
    c.set_editor_property('cast_shadow',False)
    c.set_editor_property('bounds_scale',5.)
    c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    a.set_actor_scale3d(u.Vector(*scale))
    return a

def build():
    (ROOT/'Renders'/'build_error.txt').unlink(missing_ok=True)
    if ELA.does_asset_exist('/Game/Solar/SolarScene'):
        LEVELS.load_level('/Game/Solar/SolarScene')
        for old in ACTORS.get_all_level_actors():
            if isinstance(old,(u.StaticMeshActor,u.CameraActor,u.LevelSequenceActor)):
                ACTORS.destroy_actor(old)
    else:
        assert LEVELS.new_level('/Game/Solar/SolarScene'), 'Failed to create solar level'
    mpc=asset('SolarControls',u.MaterialParameterCollection,u.MaterialParameterCollectionFactoryNew())
    mpc.set_editor_property('scalar_parameters',[struct(u.CollectionScalarParameter,parameter_name=k,default_value=v) for k,v in PARAMETERS.items()])
    ELA.save_loaded_asset(mpc)
    surface=make_material('M_Photosphere','Surface.hlsl',mpc)
    corona=make_material('M_Corona','Corona.hlsl',mpc,True)
    loops=make_material('M_MagneticLoops','Loop.hlsl',mpc,True,'LoopPosition.hlsl')
    plume=make_material('M_PlasmaEjections','Plume.hlsl',mpc,True,'PlumePosition.hlsl')
    stars=make_material('M_Stars','Stars.hlsl',mpc,True)
    particles=make_material('M_EjectaParticles','Particles.hlsl',mpc,True,'ParticlePosition.hlsl')
    actor('Sun - flowing photosphere',ELA.load_asset('/Engine/BasicShapes/Sphere'),surface,scale=(2,2,2))
    actor('Magnetic ribbons - 72 independent loops',import_mesh('MagneticLoops'),loops)
    actor('Random broad plasma ejections',import_mesh('PlasmaEjections'),plume)
    actor('Fine plasma and detached ejection particles',import_mesh('EjectaParticles'),particles)
    plane=import_mesh('CoronaPlane');starfield=import_mesh('StarField')
    actor('Breathing corona',plane,corona,location=(-115,0,0))
    actor('Distant warm stars',starfield,stars,location=(-300,0,0))
    camera=ACTORS.spawn_actor_from_class(u.CameraActor,u.Vector(700,0,0),u.Rotator(0,180,0))
    camera.set_actor_label('Solar camera')
    cc=camera.camera_component
    cc.set_editor_property('field_of_view',50.)
    cc.set_editor_property('aspect_ratio',16/9)
    cc.set_editor_property('constrain_aspect_ratio',True)
    pp=cc.get_editor_property('post_process_settings')
    for key,val in {'override_auto_exposure_method':True,'auto_exposure_method':u.AutoExposureMethod.AEM_MANUAL,
                    'override_auto_exposure_bias':True,'auto_exposure_bias':0.,
                    'override_auto_exposure_apply_physical_camera_exposure':True,'auto_exposure_apply_physical_camera_exposure':False,
                    'override_bloom_intensity':True,'bloom_intensity':.23,
                    'override_bloom_threshold':True,'bloom_threshold':1.35,
                    'override_motion_blur_amount':True,'motion_blur_amount':0.,
                    'override_vignette_intensity':True,'vignette_intensity':0.}.items():
        pp.set_editor_property(key,val)
    cc.set_editor_property('post_process_settings',pp)
    cc.set_editor_property('post_process_blend_weight',1.)
    seq=asset('SolarFilm',u.LevelSequence,u.LevelSequenceFactoryNew())
    for track in seq.get_tracks():seq.remove_track(track)
    for binding in seq.get_bindings():binding.remove()
    seq.set_display_rate(u.FrameRate(30,1));seq.set_tick_resolution_directly(u.FrameRate(30000,1))
    seq.set_playback_start(0);seq.set_playback_end(360)
    binding=seq.add_possessable(camera)
    cut=seq.add_track(u.MovieSceneCameraCutTrack).add_section();cut.set_range(0,360)
    cut.set_camera_binding_id(struct(u.MovieSceneObjectBindingID,guid=binding.get_id()))
    track=seq.add_track(u.MovieSceneMaterialParameterCollectionTrack)
    track.set_editor_property('mpc',mpc)
    section=track.add_section();section.set_range(0,360)
    section.add_scalar_parameter_key('SolarTime',u.FrameNumber(0),0.,u.MovieSceneKeyInterpolation.LINEAR)
    section.add_scalar_parameter_key('SolarTime',u.FrameNumber(360000),12.,u.MovieSceneKeyInterpolation.LINEAR)
    ELA.save_loaded_asset(seq)
    LEVELS.save_current_level()
    ELA.save_directory(FOLDER,only_if_is_dirty=True,recursive=True)
    u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(700,0,0),u.Rotator(0,180,0))
    (ROOT/'Assets'/'build_manifest.json').write_text(json.dumps({'engine':u.SystemLibrary.get_engine_version(),'controls':PARAMETERS,'sequence_seconds':12,'fps':30,'events':len(json.loads((ROOT/'Assets'/'events.json').read_text()))},indent=2))
    u.log('SOLAR_BUILD_COMPLETE')

if __name__=='__main__':
    try:
        build()
        exec(compile((ROOT/'Scripts'/'render_movie.py').read_text(),str(ROOT/'Scripts'/'render_movie.py'),'exec'),globals())
    except Exception:
        (ROOT/'Renders'/'build_error.txt').write_text(traceback.format_exc())
        u.log_error(traceback.format_exc())
        u.SystemLibrary.quit_editor()
