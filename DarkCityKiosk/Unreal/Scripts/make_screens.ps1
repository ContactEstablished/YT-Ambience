# Builds the screen images for the city's LED screens and neon signs from screens.json.
#   pwsh -NoProfile -File make_screens.ps1
# Ads: the user's art from DarkCityKiosk/_ads/<image> (cover-cropped to the screen's shape), or a
#      stand-in if it isn't there yet, plus the headline / Japanese line / logo in exact type.
# Neon: vertical Japanese lettering with a soft glow, drawn entirely from type.
# Writes Unreal/RawContent/screens/T_Screen_<name>_<slide>.png and screen_colors.json (average
# colour per screen, linear, used to tint each screen's glow light in Unreal).
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here "..\..")
$adsDir = Join-Path $root "_ads"
$outDir = Join-Path $root "Unreal\RawContent\screens"
New-Item -ItemType Directory -Force $outDir | Out-Null
$cfg = Get-Content (Join-Path $here "screens.json") -Raw -Encoding UTF8 | ConvertFrom-Json

$EN = "Bahnschrift"; $JP = "Yu Gothic"
function C([double[]]$rgb, [int]$a = 255) {
  [System.Drawing.Color]::FromArgb($a, [int](255 * [math]::Min(1, $rgb[0])), [int](255 * [math]::Min(1, $rgb[1])), [int](255 * [math]::Min(1, $rgb[2])))
}
function NewG($bmp) {
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = "AntiAlias"; $g.InterpolationMode = "HighQualityBicubic"; $g.TextRenderingHint = "AntiAliasGridFit"
  $g
}
function Blur($bmp, [int]$factor) {
  # cheap wide blur: shrink then enlarge with bicubic filtering
  $w = [math]::Max(2, [int]($bmp.Width / $factor)); $h = [math]::Max(2, [int]($bmp.Height / $factor))
  $small = New-Object System.Drawing.Bitmap $w, $h
  $g = NewG $small; $g.DrawImage($bmp, 0, 0, $w, $h); $g.Dispose()
  $big = New-Object System.Drawing.Bitmap $bmp.Width, $bmp.Height
  $g = NewG $big; $g.DrawImage($small, 0, 0, $bmp.Width, $bmp.Height); $g.Dispose(); $small.Dispose()
  $big
}
function TextPath([string]$text, [string]$family, [System.Drawing.FontStyle]$style, [double]$size) {
  $p = New-Object System.Drawing.Drawing2D.GraphicsPath
  $fmt = [System.Drawing.StringFormat]::GenericTypographic
  $p.AddString($text, (New-Object System.Drawing.FontFamily $family), [int]$style, [single]$size, (New-Object System.Drawing.PointF 0, 0), $fmt)
  $p.FillMode = "Winding"  # some glyphs overlap their own contours; alternate fill would punch holes
  $p
}
function FitPath([string]$text, [string]$family, [System.Drawing.FontStyle]$style, [double]$maxW, [double]$maxH) {
  $p = TextPath $text $family $style 100
  $b = $p.GetBounds()
  $s = [math]::Min($maxW / [math]::Max(1, $b.Width), $maxH / [math]::Max(1, $b.Height))
  $p.Dispose()
  TextPath $text $family $style (100 * $s)
}
function PlacePath($path, [double]$cx, [double]$top) {
  $b = $path.GetBounds()
  $m = New-Object System.Drawing.Drawing2D.Matrix
  $m.Translate([single]($cx - $b.X - $b.Width / 2), [single]($top - $b.Y))
  $path.Transform($m)
  $path.GetBounds()
}
function GlowText($bmp, $paths, [double[]]$tint, [double]$glowStrength = 0.9) {
  # soft coloured glow behind crisp near-white type
  $mask = New-Object System.Drawing.Bitmap $bmp.Width, $bmp.Height
  $g = NewG $mask
  foreach ($p in $paths) { $g.FillPath((New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)), $p) }
  $g.Dispose()
  $glow = Blur $mask 12
  $g = NewG $bmp
  $ia = New-Object System.Drawing.Imaging.ImageAttributes
  $cm = New-Object System.Drawing.Imaging.ColorMatrix
  $cm.Matrix00 = [single]$tint[0]; $cm.Matrix11 = [single]$tint[1]; $cm.Matrix22 = [single]$tint[2]; $cm.Matrix33 = [single]$glowStrength
  $ia.SetColorMatrix($cm)
  $rect = New-Object System.Drawing.Rectangle 0, 0, $bmp.Width, $bmp.Height
  $g.DrawImage($glow, $rect, 0, 0, $bmp.Width, $bmp.Height, [System.Drawing.GraphicsUnit]::Pixel, $ia)
  $core = C @((0.85 + 0.15 * $tint[0]), (0.85 + 0.15 * $tint[1]), (0.85 + 0.15 * $tint[2]))
  foreach ($p in $paths) { $g.FillPath((New-Object System.Drawing.SolidBrush $core), $p) }
  $g.Dispose(); $mask.Dispose(); $glow.Dispose()
}
function Background($bmp, $slide) {
  $g = NewG $bmp
  $W = $bmp.Width; $H = $bmp.Height
  $file = Join-Path $adsDir $slide.image
  if (Test-Path $file) {
    $img = [System.Drawing.Image]::FromFile($file)
    $s = [math]::Max($W / $img.Width, $H / $img.Height)  # cover
    $dw = $img.Width * $s; $dh = $img.Height * $s
    $g.DrawImage($img, [single](($W - $dw) / 2), [single](($H - $dh) / 2), [single]$dw, [single]$dh)
    $img.Dispose(); $real = $true
  } else {
    # stand-in: dark tinted gradient + a soft glowing shape where the subject will be
    $t = $slide.tint
    $lg = New-Object System.Drawing.Drawing2D.LinearGradientBrush((New-Object System.Drawing.Point 0, 0), (New-Object System.Drawing.Point 0, $H),
      (C @(($t[0] * 0.18), ($t[1] * 0.18), ($t[2] * 0.22))), (C @(0.01, 0.012, 0.02)))
    $g.FillRectangle($lg, 0, 0, $W, $H)
    $ep = New-Object System.Drawing.Drawing2D.GraphicsPath
    if ($H -gt $W) { $ep.AddEllipse([single]($W * 0.2), [single]($H * 0.12), [single]($W * 0.6), [single]($H * 0.45)) }
    else { $ep.AddEllipse([single]($W * 0.45), [single]($H * 0.2), [single]($W * 0.4), [single]($H * 0.6)) }
    $pg = New-Object System.Drawing.Drawing2D.PathGradientBrush $ep
    $pg.CenterColor = C @(($t[0] * 0.9), ($t[1] * 0.9), ($t[2] * 0.9))
    $pg.SurroundColors = @([System.Drawing.Color]::FromArgb(0, 0, 0, 0))
    $g.FillPath($pg, $ep)
    $real = $false
  }
  $g.Dispose()
  $real
}
function Shade($bmp, [string]$layout) {
  # darken the text area so the type reads
  $g = NewG $bmp; $W = $bmp.Width; $H = $bmp.Height
  switch ($layout) {
    "bottom" { $r = New-Object System.Drawing.Rectangle 0, ([int]($H * 0.55)), $W, ([int]($H * 0.45) + 1)
               $b = New-Object System.Drawing.Drawing2D.LinearGradientBrush($r, [System.Drawing.Color]::FromArgb(0, 0, 0, 0), [System.Drawing.Color]::FromArgb(215, 0, 0, 0), 90.0) }
    "top"    { $r = New-Object System.Drawing.Rectangle 0, 0, $W, ([int]($H * 0.45))
               $b = New-Object System.Drawing.Drawing2D.LinearGradientBrush($r, [System.Drawing.Color]::FromArgb(200, 0, 0, 0), [System.Drawing.Color]::FromArgb(0, 0, 0, 0), 90.0) }
    "left"   { $r = New-Object System.Drawing.Rectangle 0, 0, ([int]($W * 0.5)), $H
               $b = New-Object System.Drawing.Drawing2D.LinearGradientBrush($r, [System.Drawing.Color]::FromArgb(210, 0, 0, 0), [System.Drawing.Color]::FromArgb(0, 0, 0, 0), 0.0) }
    default  { $r = New-Object System.Drawing.Rectangle 0, 0, $W, $H
               $b = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(70, 0, 0, 0)) }
  }
  $g.FillRectangle($b, $r); $g.Dispose()
}
function KazeLogo([double]$cx, [double]$cy, [double]$r) {
  # circle with a stylised 'A' whose crossbar is a wind wave (after the reference's KAZE mark)
  # returns two paths: the ring (alternate fill = hole in the middle) and the letter (winding fill)
  $ring = New-Object System.Drawing.Drawing2D.GraphicsPath
  $ring.AddEllipse([single]($cx - $r), [single]($cy - $r), [single](2 * $r), [single](2 * $r))
  $ring.AddEllipse([single]($cx - $r * 0.86), [single]($cy - $r * 0.86), [single](1.72 * $r), [single](1.72 * $r))
  $p = New-Object System.Drawing.Drawing2D.GraphicsPath
  $w = $r * 0.11
  $p.AddPolygon([System.Drawing.PointF[]]@((New-Object System.Drawing.PointF ($cx - $w), ($cy - $r * 0.62)), (New-Object System.Drawing.PointF ($cx + $w), ($cy - $r * 0.62)),
    (New-Object System.Drawing.PointF ($cx + $r * 0.52), ($cy + $r * 0.55)), (New-Object System.Drawing.PointF ($cx + $r * 0.52 - 2 * $w), ($cy + $r * 0.55)),
    (New-Object System.Drawing.PointF $cx, ($cy - $r * 0.35))))
  $p.AddPolygon([System.Drawing.PointF[]]@((New-Object System.Drawing.PointF ($cx - $w), ($cy - $r * 0.62)), (New-Object System.Drawing.PointF $cx, ($cy - $r * 0.35)),
    (New-Object System.Drawing.PointF ($cx - $r * 0.52 + 2 * $w), ($cy + $r * 0.55)), (New-Object System.Drawing.PointF ($cx - $r * 0.52), ($cy + $r * 0.55))))
  $pts = for ($k = 0; $k -le 20; $k++) { $x = $cx - $r * 0.55 + $k * $r * 1.1 / 20; New-Object System.Drawing.PointF $x, ($cy + $r * 0.12 + [math]::Sin($k / 20 * 2 * [math]::PI) * $r * 0.07) }
  $wave = New-Object System.Drawing.Drawing2D.GraphicsPath; $wave.AddCurve([System.Drawing.PointF[]]$pts)
  $wave.Widen((New-Object System.Drawing.Pen ([System.Drawing.Color]::White), ([single]($w * 1.4))))
  $p.AddPath($wave, $false)
  $p.FillMode = "Winding"
  @($ring, $p)
}
function Lum($bmp) {
  $s = New-Object System.Drawing.Bitmap 8, 8
  $g = NewG $s; $g.DrawImage($bmp, 0, 0, 8, 8); $g.Dispose()
  $acc = @(0.0, 0.0, 0.0)
  for ($y = 0; $y -lt 8; $y++) { for ($x = 0; $x -lt 8; $x++) { $c = $s.GetPixel($x, $y)
    $acc[0] += [math]::Pow($c.R / 255, 2.2); $acc[1] += [math]::Pow($c.G / 255, 2.2); $acc[2] += [math]::Pow($c.B / 255, 2.2) } }
  $s.Dispose()
  @(($acc[0] / 64), ($acc[1] / 64), ($acc[2] / 64))
}

$colors = [ordered]@{}
$report = @()
foreach ($prop in $cfg.screens.PSObject.Properties) {
  $name = $prop.Name; $sc = $prop.Value
  $W = [int]$sc.size[0]; $H = [int]$sc.size[1]
  $sum = @(0.0, 0.0, 0.0); $n = 0
  if ($sc.type -eq "ad") {
    $k = 0
    foreach ($slide in $sc.slides) {
      $bmp = New-Object System.Drawing.Bitmap $W, $H
      $real = Background $bmp $slide
      Shade $bmp $slide.layout
      $paths = @()
      $tw = if ($slide.layout -eq "left") { $W * 0.42 } else { $W * 0.84 }
      $cx = if ($slide.layout -eq "left") { $W * 0.24 } else { $W / 2 }
      $lineH = if ($H -gt $W) { $H * 0.075 } else { $H * 0.17 }
      switch ($slide.layout) { "bottom" { $y = $H * 0.70 } "top" { $y = $H * 0.07 } "left" { $y = $H * 0.25 } default { $y = $H * 0.56 } }
      if ($slide.logo -eq "kaze") {
        $paths += KazeLogo ($W / 2) ($H * 0.2) ($W * 0.22); $y = $H * 0.34
      }
      foreach ($line in $slide.lines) {
        $p = FitPath $line $EN ([System.Drawing.FontStyle]::Bold) $tw $lineH
        $b = PlacePath $p $cx $y; $paths += $p; $y = $b.Bottom + $lineH * 0.25
      }
      if ($slide.jp) {
        $p = FitPath $slide.jp $JP ([System.Drawing.FontStyle]::Bold) ($tw * 0.8) ($lineH * 0.72)
        $b = PlacePath $p $cx ($y + $lineH * 0.1); $paths += $p; $y = $b.Bottom + $lineH * 0.3
      }
      if ($slide.sub) {
        $p = FitPath $slide.sub $EN ([System.Drawing.FontStyle]::Regular) ($tw * 0.85) ($lineH * 0.32)
        $sy = if ($slide.layout -eq "logo") { $H * 0.9 } else { $y + $lineH * 0.15 }
        $null = PlacePath $p $cx $sy; $paths += $p
      }
      GlowText $bmp $paths $slide.tint 0.8
      $file = Join-Path $outDir "T_Screen_${name}_$k.png"
      $bmp.Save($file, [System.Drawing.Imaging.ImageFormat]::Png)
      $l = Lum $bmp; for ($i = 0; $i -lt 3; $i++) { $sum[$i] += $l[$i] }; $n++
      $report += "$name slide $k : " + $(if ($real) { "art " + $slide.image } else { "STAND-IN (no _ads/" + $slide.image + ")" })
      $bmp.Dispose(); $k++
    }
  } else {
    # neon: columns of vertical lettering read right-to-left, optional latin word and frame
    $bmp = New-Object System.Drawing.Bitmap $W, $H
    $g = NewG $bmp; $g.Clear([System.Drawing.Color]::Black); $g.Dispose()
    $paths = @()
    $cols = @($sc.columns); $nc = $cols.Count
    $colW = ($W * 0.82) / $nc
    $latinH = if ($sc.latin) { $H * 0.08 } else { 0 }
    $top = $H * 0.05; $avail = $H * 0.88 - $latinH
    # one cell size for every column, so later columns (which start a little lower) still fit
    $maxChars = ($cols | ForEach-Object { $_.Length } | Measure-Object -Maximum).Maximum
    $cell = [math]::Min($colW * 0.95, $avail / [math]::Max(4, $maxChars + 0.6 * ($nc - 1)))
    for ($ci = 0; $ci -lt $nc; $ci++) {
      $chars = $cols[$ci].ToCharArray()
      $cx = $W * 0.91 - $colW * ($ci + 0.5)
      $yy = $top + ($ci * $cell * 0.6)
      foreach ($ch in $chars) {
        if ("、。，．".Contains([string]$ch)) {
          # vertical-writing punctuation: small, in the top-right of its cell, and only half a cell tall
          $p = FitPath ([string]$ch) $JP ([System.Drawing.FontStyle]::Bold) ($cell * 0.28) ($cell * 0.28)
          $b = $p.GetBounds(); $m = New-Object System.Drawing.Drawing2D.Matrix
          $m.Translate([single]($cx + $cell * 0.12 - $b.X), [single]($yy + $cell * 0.02 - $b.Y)); $p.Transform($m)
          $paths += $p; $yy += $cell * 0.5
          continue
        }
        $p = FitPath ([string]$ch) $JP ([System.Drawing.FontStyle]::Bold) ($cell * 0.86) ($cell * 0.86)
        $null = PlacePath $p $cx ($yy + $cell * 0.07); $paths += $p; $yy += $cell
      }
    }
    if ($sc.latin) {
      $p = FitPath $sc.latin $EN ([System.Drawing.FontStyle]::Bold) ($W * 0.8) ($latinH * 0.8)
      $null = PlacePath $p ($W / 2) ($H * 0.93 - $latinH); $paths += $p
    }
    if ($sc.frame) {
      $fp = New-Object System.Drawing.Drawing2D.GraphicsPath
      $fp.AddRectangle((New-Object System.Drawing.RectangleF ([single]($W * 0.04)), ([single]($H * 0.012)), ([single]($W * 0.92)), ([single]($H * 0.976))))
      $fp.Widen((New-Object System.Drawing.Pen ([System.Drawing.Color]::White), ([single]($W * 0.025))))
      $paths += $fp
    }
    GlowText $bmp $paths $sc.color 1.0
    $bmp.Save((Join-Path $outDir "T_Screen_${name}_0.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    $l = Lum $bmp; for ($i = 0; $i -lt 3; $i++) { $sum[$i] += $l[$i] }; $n++
    $report += "$name neon"
    $bmp.Dispose()
  }
  $colors[$name] = @([math]::Round($sum[0] / $n, 4), [math]::Round($sum[1] / $n, 4), [math]::Round($sum[2] / $n, 4))
}
$colors | ConvertTo-Json | Set-Content (Join-Path $outDir "screen_colors.json") -Encoding UTF8
$report | ForEach-Object { Write-Output $_ }
