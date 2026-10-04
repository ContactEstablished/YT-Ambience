# The MIRAI landmark's sign: "MIRAI" over 未来, near-white type with a soft cyan glow on black
# (the sign material is additive, so black is invisible).
#   pwsh -NoProfile -File make_landmark_sign.ps1
# Writes Unreal/RawContent/signs/T_Sign_MIRAI.png. setup_city_bg.py runs this itself.
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here "..\..")
$outDir = Join-Path $root "Unreal\RawContent\signs"
New-Item -ItemType Directory -Force $outDir | Out-Null

$EN = "Bahnschrift"; $JP = "Yu Gothic"
$W = 1024; $H = 768
$tint = @(0.55, 0.85, 1.0)
$mirai = "MIRAI"
$kanji = [string][char]0x672A + [string][char]0x6765  # 未来

function NewG($bmp) {
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = "AntiAlias"; $g.InterpolationMode = "HighQualityBicubic"; $g.TextRenderingHint = "AntiAliasGridFit"
  $g
}
function Blur($bmp, [int]$factor) {
  $w = [math]::Max(2, [int]($bmp.Width / $factor)); $h = [math]::Max(2, [int]($bmp.Height / $factor))
  $small = New-Object System.Drawing.Bitmap $w, $h
  $g = NewG $small; $g.DrawImage($bmp, 0, 0, $w, $h); $g.Dispose()
  $big = New-Object System.Drawing.Bitmap $bmp.Width, $bmp.Height
  $g = NewG $big; $g.DrawImage($small, 0, 0, $bmp.Width, $bmp.Height); $g.Dispose(); $small.Dispose()
  $big
}
function TextPath([string]$text, [string]$family, [System.Drawing.FontStyle]$style, [double]$size) {
  $p = New-Object System.Drawing.Drawing2D.GraphicsPath
  $p.AddString($text, (New-Object System.Drawing.FontFamily $family), [int]$style, [single]$size, (New-Object System.Drawing.PointF 0, 0),
               [System.Drawing.StringFormat]::GenericTypographic)
  $p.FillMode = "Winding"
  $p
}
function Fit($p, [double]$cx, [double]$top, [double]$maxW, [double]$maxH) {
  $b = $p.GetBounds()
  $s = [math]::Min($maxW / $b.Width, $maxH / $b.Height)
  $m = New-Object System.Drawing.Drawing2D.Matrix
  $m.Translate([single]$cx, [single]$top); $m.Scale([single]$s, [single]$s); $m.Translate([single](-$b.X - $b.Width / 2), [single](-$b.Y))
  $p.Transform($m)
}

# MIRAI with wide letter spacing: every letter at one size, laid out left to right, then the
# whole word scaled to fit
$paths = @()
$letters = @(); $widths = @()
for ($i = 0; $i -lt 5; $i++) {
  $p = TextPath $mirai.Substring($i, 1) $EN ([System.Drawing.FontStyle]::Regular) 200
  $letters += $p; $widths += $p.GetBounds().Width
}
$cell = ($widths | Measure-Object -Maximum).Maximum * 1.25  # tracked caps: each letter centred in an equal cell
$capH = $letters[0].GetBounds().Height
$s = [math]::Min(($W * 0.86) / (5 * $cell), ($H * 0.3) / $capH)
$x = ($W - 5 * $cell * $s) / 2
for ($i = 0; $i -lt 5; $i++) {
  $b = $letters[$i].GetBounds()
  $m = New-Object System.Drawing.Drawing2D.Matrix
  $m.Translate([single]($x + ($i + 0.5) * $cell * $s), [single]($H * 0.1)); $m.Scale([single]$s, [single]$s)
  $m.Translate([single](-$b.X - $b.Width / 2), [single](-$b.Y))
  $letters[$i].Transform($m)
  $paths += $letters[$i]
}
$l = $letters[0].GetBounds().X; $r = $letters[4].GetBounds().Right  # centre the word on its drawn extent
$m = New-Object System.Drawing.Drawing2D.Matrix; $m.Translate([single]($W / 2 - ($l + $r) / 2), 0)
foreach ($p in $letters) { $p.Transform($m) }
$p = TextPath $kanji $JP ([System.Drawing.FontStyle]::Bold) 200
Fit $p ($W / 2) ($H * 0.52) ($W * 0.5) ($H * 0.36)
$paths += $p

$bmp = New-Object System.Drawing.Bitmap $W, $H
$g = NewG $bmp; $g.Clear([System.Drawing.Color]::Black); $g.Dispose()
$mask = New-Object System.Drawing.Bitmap $W, $H
$g = NewG $mask
foreach ($p in $paths) { $g.FillPath([System.Drawing.Brushes]::White, $p) }
$g.Dispose()
$g = NewG $bmp
foreach ($pass in @(@(16, 0.9), @(6, 0.7))) {  # wide soft glow + a tighter halo
  $glow = Blur $mask $pass[0]
  $ia = New-Object System.Drawing.Imaging.ImageAttributes
  $cm = New-Object System.Drawing.Imaging.ColorMatrix
  $cm.Matrix00 = [single]$tint[0]; $cm.Matrix11 = [single]$tint[1]; $cm.Matrix22 = [single]$tint[2]; $cm.Matrix33 = [single]$pass[1]
  $ia.SetColorMatrix($cm)
  $g.DrawImage($glow, (New-Object System.Drawing.Rectangle 0, 0, $W, $H), 0, 0, $W, $H, [System.Drawing.GraphicsUnit]::Pixel, $ia)
  $glow.Dispose()
}
$core = [System.Drawing.Color]::FromArgb(255, 225, 242, 255)
foreach ($p in $paths) { $g.FillPath((New-Object System.Drawing.SolidBrush $core), $p) }
$g.Dispose(); $mask.Dispose()
$out = Join-Path $outDir "T_Sign_MIRAI.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
"sign: $out"
