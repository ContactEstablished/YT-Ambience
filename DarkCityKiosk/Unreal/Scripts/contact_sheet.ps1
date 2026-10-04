# Stacks images into one labelled sheet (each tile scaled to -TileW wide, 16:9).
#   pwsh -File contact_sheet.ps1 -Out sheet.png -Cols 2 -TileW 960 img1.png img2.png ...
param([string]$Out, [int]$Cols = 2, [int]$TileW = 960, [Parameter(ValueFromRemainingArguments = $true)][string[]]$Images)
Add-Type -AssemblyName System.Drawing
$th = [int]($TileW * 9 / 16)
$rows = [math]::Ceiling($Images.Count / $Cols)
$sheet = New-Object System.Drawing.Bitmap ($TileW * $Cols), ($th * $rows)
$g = [System.Drawing.Graphics]::FromImage($sheet)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$font = New-Object System.Drawing.Font "Segoe UI", 14, ([System.Drawing.FontStyle]::Bold)
$bg = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(160, 0, 0, 0))
for ($i = 0; $i -lt $Images.Count; $i++) {
  $img = [System.Drawing.Image]::FromFile((Resolve-Path $Images[$i]))
  $x = ($i % $Cols) * $TileW; $y = [math]::Floor($i / $Cols) * $th
  $g.DrawImage($img, $x, $y, $TileW, $th)
  $label = [System.IO.Path]::GetFileNameWithoutExtension($Images[$i])
  $sz = $g.MeasureString($label, $font)
  $g.FillRectangle($bg, $x, $y, $sz.Width + 12, $sz.Height + 4)
  $g.DrawString($label, $font, [System.Drawing.Brushes]::White, $x + 6, $y + 2)
  $img.Dispose()
}
$g.Dispose(); $sheet.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png); $sheet.Dispose()
