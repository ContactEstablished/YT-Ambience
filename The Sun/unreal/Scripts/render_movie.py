"""Render the saved native sequence using Unreal Movie Render Queue."""
import unreal as u
import json
from pathlib import Path
ROOT=Path(u.Paths.project_dir())
u.EditorPythonScripting.set_keep_python_script_alive(True)
request=json.loads((ROOT/'render_request.json').read_text())
queue_subsystem=u.get_editor_subsystem(u.MoviePipelineQueueSubsystem)
queue=queue_subsystem.get_queue()
queue.delete_all_jobs()
job=queue.allocate_new_job(u.MoviePipelineExecutorJob)
job.job_name='Solar native Unreal rendering'
job.map=u.SoftObjectPath('/Game/Solar/SolarScene.SolarScene')
job.sequence=u.SoftObjectPath('/Game/Solar/SolarFilm.SolarFilm')
config=job.get_configuration()
out=config.find_or_add_setting_by_class(u.MoviePipelineOutputSetting)
out.output_directory=u.DirectoryPath(str(ROOT/'Renders'/request.get('directory','Frames')))
out.output_resolution=u.IntPoint(request.get('width',1920),request.get('height',1080))
out.file_name_format='Sun_{frame_number}';out.zero_pad_frame_numbers=4
out.use_custom_playback_range=True;out.custom_start_frame=request.get('start',0);out.custom_end_frame=request.get('end',360)
out.override_existing_output=True
out.use_custom_frame_rate=True;out.output_frame_rate=u.FrameRate(30,1)
config.find_or_add_setting_by_class(u.MoviePipelineDeferredPassBase)
config.find_or_add_setting_by_class(u.MoviePipelineImageSequenceOutput_PNG)
aa=config.find_or_add_setting_by_class(u.MoviePipelineAntiAliasingSetting)
aa.spatial_sample_count=request.get('samples',8);aa.temporal_sample_count=1
aa.override_anti_aliasing=True;aa.anti_aliasing_method=u.AntiAliasingMethod.AAM_NONE
aa.engine_warm_up_count=16;aa.render_warm_up_count=16
settings=config.find_or_add_setting_by_class(u.MoviePipelineConsoleVariableSetting)
for name,value in {'r.MotionBlurQuality':0.,'r.EyeAdaptationQuality':0.,'r.BloomQuality':5.,'r.Tonemapper.Sharpen':.2,'r.ScreenPercentage':100.}.items():
    settings.add_or_update_console_variable(name,value)
EXECUTOR=u.MoviePipelinePIEExecutor(queue_subsystem)
def finished(executor,success):
    (ROOT/'Renders'/'render_result.json').write_text(json.dumps({'success':success,'request':request},indent=2))
    u.log('SOLAR_RENDER_FINISHED '+str(success))
    u.SystemLibrary.quit_editor()
def error(executor,pipeline,fatal,message):
    with (ROOT/'Renders'/'render_errors.txt').open('a') as f:f.write(str(fatal)+' '+str(message)+'\n')
EXECUTOR.on_executor_finished_delegate.add_callable_unique(finished)
EXECUTOR.on_executor_errored_delegate.add_callable_unique(error)
queue_subsystem.render_queue_with_executor_instance(EXECUTOR)
