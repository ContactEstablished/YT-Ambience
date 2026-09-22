@echo off
set "SOLAR_BLENDER=C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
if not exist "%SOLAR_BLENDER%" (
    echo Blender 5.2 was not found at the expected installation path.
    echo Open solar_observatory.blend directly, or use Open-Sun.ps1 with -BlenderExe.
    pause
    exit /b 1
)
start "Solar Observatory" "%SOLAR_BLENDER%" "%~dp0solar_observatory.blend" --python "%~dp0scripts\sun_controls.py"
