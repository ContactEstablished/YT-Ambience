param(
    [string]$BlenderExe = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $BlenderExe)) {
    throw 'Blender was not found. Run this script with -BlenderExe followed by the path to blender.exe.'
}
$SolarScene = Join-Path $PSScriptRoot 'solar_observatory.blend'
$SolarPanel = Join-Path $PSScriptRoot 'scripts\sun_controls.py'
# Opens the interactive app requested by the user. No preferences are installed or saved.
& $BlenderExe $SolarScene --python $SolarPanel
