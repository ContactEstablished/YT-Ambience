param([switch]$Rebuild)
$ErrorActionPreference = 'Stop'
$SolarScript = if ($Rebuild) { 'build_scene.py' } else { 'render_movie.py' }
$SolarResultPath = Join-Path $PSScriptRoot 'Renders\render_result.json'
if (Test-Path -LiteralPath $SolarResultPath) { Remove-Item -LiteralPath $SolarResultPath }
$SolarProcessId = & (Join-Path $PSScriptRoot 'Scripts\Run-Unreal.ps1') -Script $SolarScript -Log 'render-final.log'
Write-Host ('Rendering with Unreal (process ' + $SolarProcessId + '). Output: unreal/Renders/')
Wait-Process -Id $SolarProcessId
if (-not (Test-Path -LiteralPath $SolarResultPath)) { throw 'No render completion report. See Renders/render-final.log.' }
$SolarResult = Get-Content -LiteralPath $SolarResultPath -Raw | ConvertFrom-Json
if (-not $SolarResult.success) { throw 'Unreal reported a failed render. See Renders/render-final.log.' }
$SolarRequest = $SolarResult.request
$SolarFrames = Join-Path $PSScriptRoot ('Renders\' + $SolarRequest.directory + '\Sun_%04d.png')
$SolarVideo = Join-Path $PSScriptRoot 'Renders\Sun-Unreal.mp4'
$SolarFrameCount = $SolarRequest.end - $SolarRequest.start
& ffmpeg -y -hide_banner -loglevel error -framerate 30 -start_number $SolarRequest.start -i $SolarFrames -frames:v $SolarFrameCount -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -movflags +faststart $SolarVideo
if ($LASTEXITCODE -ne 0) { throw 'MP4 encoding failed. The rendered PNG sequence is still available.' }
Write-Host ('Finished: ' + $SolarVideo)
