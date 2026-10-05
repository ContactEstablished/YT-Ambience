"""Render LS_Sweep with Movie Render Queue.
    node Scripts/ue.mjs Scripts/render.py [--tag preview] [--res 1920x1080] [--frames 0-720]
                                          [--spatial 1] [--temporal 1] [--warmup 48] [--fog-clear]
                                          [--sequence LS_Sweep]
--sequence: which level sequence to render (LS_Review: the close-up review cameras, make_review.py).
--frames: one contiguous range per call, e.g. '0-720' (full sweep) or '180-181' (one still).
Never queue several jobs: EasyRain's GPU particles crashed the editor at the MRQ job hand-over.
Frames go to DarkCityKiosk/Renders/frames/<tag>/LS_Sweep.<frame>.png; encode a range with
`node Scripts/encode.mjs <tag>`. Returns immediately: MRQ renders in a SEPARATE editor process
(new-process executor) and logs 'render.py: done' when that process exits.
Why a separate process: when an MRQ Play-In-Editor session ends, EasyRain's GPU particles crash
the RHI thread (UE 5.8, NiagaraGpuComputeDispatch). In its own process that crash happens after
every frame is written and can't take the editor down. Unsaved changes are saved first.
Notes: MRQ steps time at exactly 1/24 s per frame (repeatable). Warm-up frames let
Lumen, volumetric fog history, TSR and the rain particles settle before the first frame.
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402

dck = importlib.reload(dck)
import unreal  # noqa: E402

args = sys.argv[1:]


def opt(name, default, conv=str):
    if name in args:
        i = args.index(name)
        v = conv(args[i + 1])
        del args[i:i + 2]
        return v
    return default


# --fog-clear: switch off LS_Sweep's mist-wave keys for this render (the fog holds its clear-phase
# component values), so the Mid pose, which sits on a mist peak, can be judged clear. The keys are
# switched back on when the render finishes; make_sweep.py also rebuilds them.
fog_clear = "--fog-clear" in args
if fog_clear:
    args.remove("--fog-clear")
tag = opt("--tag", "preview")
SEQ = f"{dck.GAME}/Sequences/{opt('--sequence', 'LS_Sweep')}"
res = tuple(int(v) for v in opt("--res", "1920x1080").split("x"))
frames_arg = opt("--frames", "0-720")
spatial = opt("--spatial", 1, int)
temporal = opt("--temporal", 1, int)
warmup = opt("--warmup", 48, int)
# Rain sprites stay out of the ray-tracing scene (not needed in reflections; a Niagara GPU crash
# hit the RHI thread on PIE teardown with them in). Finer volumetric fog for final-quality haze.
RENDER_CVARS = {
    "r.RayTracing.Geometry.NiagaraSprites": 0,
    "r.RayTracing.Geometry.NiagaraRibbons": 0,
    "r.RayTracing.Geometry.NiagaraMeshes": 0,
    "r.VolumetricFog.GridPixelSize": 4,
    "r.VolumetricFog.GridSizeZ": 128,
}
if "-" in frames_arg:
    ranges = [tuple(int(v) for v in part.split("-")) for part in frames_arg.split(",")]
else:
    ranges = [(int(f), int(f) + 1) for f in frames_arg.split(",")]

dck.ensure_map()
unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
out_dir = os.path.join(dck.ROOT_DIR, "Renders", "frames", tag)
os.makedirs(out_dir, exist_ok=True)

subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
if subsystem.is_rendering():
    raise RuntimeError("a Movie Render Queue render is already running")
queue = subsystem.get_queue()
queue.delete_all_jobs()
seq_path = unreal.SoftObjectPath(f"{SEQ}.{SEQ.rsplit('/', 1)[1]}")
map_path = unreal.SoftObjectPath(dck.world().get_path_name())

if len(ranges) > 1:
    # Each MRQ job tears down and restarts Play-In-Editor; EasyRain's GPU particles crashed the
    # RHI thread at that hand-over. Render one contiguous range per call instead.
    raise RuntimeError("render.py: one range per call (multi-job queues crash on PIE hand-over)")
for f0, f1 in ranges:
    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    dck.setp(job, job_name=f"{tag}_{f0}", sequence=seq_path, map=map_path)
    config = job.get_configuration()
    out = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    dck.setp(out, output_directory=unreal.DirectoryPath(out_dir.replace("\\", "/")),
             file_name_format="{sequence_name}.{frame_number}", output_resolution=unreal.IntPoint(res[0], res[1]),
             use_custom_playback_range=True, custom_start_frame=f0, custom_end_frame=f1,
             zero_pad_frame_numbers=5, override_existing_output=True)
    config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    config.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    aa = config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    dck.setp(aa, spatial_sample_count=spatial, temporal_sample_count=temporal, override_anti_aliasing=True,
             anti_aliasing_method=unreal.AntiAliasingMethod.AAM_TSR, engine_warm_up_count=warmup,
             render_warm_up_count=warmup, render_warm_up_frames=True)
    game = config.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
    dck.setp(game, cinematic_quality_settings=True, flush_streaming_managers=True)
    cvars = config.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
    for name, value in RENDER_CVARS.items():
        cvars.add_or_update_console_variable(name, value)


FOG_WAVE_PROPS = ("FogDensity", "VolumetricFogExtinctionScale", "VolumetricFogEmissive")


def set_fog_waves(active):
    seq = unreal.load_asset(SEQ)
    n = 0
    for b in seq.get_bindings():
        for tr in b.get_tracks():
            if isinstance(tr, unreal.MovieScenePropertyTrack) and str(tr.get_property_name()) in FOG_WAVE_PROPS:
                for s in tr.get_sections():
                    s.set_is_active(active)
                    n += 1
    dck.EAL.save_loaded_asset(seq)
    return n


def on_finished(executor, success):
    if fog_clear:
        set_fog_waves(True)
    unreal.log(f"render.py: done ({'ok' if success else 'FAILED'}) -> {out_dir}")


if fog_clear:
    print(f"fog waves off for this render ({set_fog_waves(False)} sections)")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)  # the render process loads from disk
# The render process loads this project's ini, which turns on Python remote execution; ue.mjs would
# then see two "DarkCityKiosk" editors and might run scripts in the render process. Switch it off there.
# -nocrashreports: the render process hits EasyRain's GPU-particle teardown crash on exit (after
# every frame is written); don't launch the crash reporter or leave a popup for it.
EXTRA_ARGS = ["-ini:Engine:[/Script/PythonScriptPlugin.PythonScriptPluginSettings]:bRemoteExecution=False", "-nocrashreports"]
proc = unreal.get_default_object(unreal.MoviePipelineInProcessExecutorSettings)
extra = proc.get_editor_property("additional_command_line_arguments")
for arg in EXTRA_ARGS:
    if arg not in extra:
        extra = f"{extra} {arg}".strip()
proc.set_editor_property("additional_command_line_arguments", extra)
executor = subsystem.render_queue_with_executor(unreal.MoviePipelineNewProcessExecutor)
executor.on_executor_finished_delegate.add_callable_unique(on_finished)
unreal._dck_render_callback = on_finished  # keep the callback alive after this namespace goes away
total = sum(b - a for a, b in ranges)
print(f"rendering {tag}: {len(ranges)} job(s), {total} frame(s) at {res[0]}x{res[1]}, {spatial}x{temporal} samples -> {out_dir}")
