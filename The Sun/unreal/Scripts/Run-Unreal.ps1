param(
    [string]$Script = 'build_scene.py',
    [string]$Log = 'build.log'
)
$ErrorActionPreference = 'Stop'
$SolarRoot = Split-Path -Parent $PSScriptRoot
$SolarProject = Join-Path $SolarRoot 'SolarObservatory.uproject'
$SolarScript = Join-Path $PSScriptRoot $Script
$SolarLog = Join-Path $SolarRoot ('Renders\' + $Log)
$SolarProcess = Start-Process -FilePath 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' -ArgumentList @(('"'+$SolarProject+'"'),'-unattended','-nosplash','-nosound','-RenderOffscreen','-windowed','-ResX=960','-ResY=540',('-ExecutePythonScript="'+$SolarScript+'"'),('-abslog="'+$SolarLog+'"')) -WindowStyle Hidden -PassThru
$SolarProcess.Id
