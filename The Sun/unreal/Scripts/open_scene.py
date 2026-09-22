"""Open the native solar sequence for interactive viewing in Unreal Editor."""
import unreal as u
u.EditorPythonScripting.set_keep_python_script_alive(True)
u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Solar/SolarScene')
sequence=u.EditorAssetLibrary.load_asset('/Game/Solar/SolarFilm')
u.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
u.LevelSequenceEditorBlueprintLibrary.set_current_time(180)
u.EditorLevelLibrary.set_level_viewport_camera_info(u.Vector(700,0,0),u.Rotator(0,180,0))
