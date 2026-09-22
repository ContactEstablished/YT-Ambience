@echo off
set "SOLAR_UNREAL=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
if not exist "%SOLAR_UNREAL%" (
    echo Unreal Engine 5.8 was not found at the expected installation path.
    echo Open SolarObservatory.uproject with your installed Unreal Editor.
    pause
    exit /b 1
)
start "Solar Observatory" "%SOLAR_UNREAL%" "%~dp0SolarObservatory.uproject" -ExecutePythonScript="%~dp0Scripts\open_scene.py"
