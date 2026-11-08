# Native Windows text overlay, offline; requires System.Drawing/GDI+.
# Inputs are generated JSON paths in the caller's output directory.
param(
    [Parameter(Mandatory=$true, Position=0)][string]$Manifest,
    [Parameter(Mandatory=$true, Position=1)][string]$BboxOutput
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$info=Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8 | ConvertFrom-Json
if((Test-Path -LiteralPath $info.png) -or (Test-Path -LiteralPath $BboxOutput)){
    throw 'Refusing to overwrite PNG or bounding-box report'
}
$bitmap=[System.Drawing.Bitmap]::new([string]$info.image)
$graphics=[System.Drawing.Graphics]::FromImage($bitmap)
$graphics.TextRenderingHint=[System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$graphics.SmoothingMode=[System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$format=[System.Drawing.StringFormat]::GenericTypographic
$format.FormatFlags=$format.FormatFlags -bor [System.Drawing.StringFormatFlags]::MeasureTrailingSpaces
$fontName=[string]$info.font
$family=[System.Drawing.FontFamily]::new($fontName)
$boxes=@()
try {
    foreach($entry in $info.texts){
        $size=[single]([double]$(if($entry.size){$entry.size}else{36}) * [double]$info.scale)
        if($size -le 0){throw 'Invalid font size'}
        $style=if($entry.bold){[System.Drawing.FontStyle]::Bold}else{[System.Drawing.FontStyle]::Regular}
        $font=[System.Drawing.Font]::new($family,$size,$style,[System.Drawing.GraphicsUnit]::Pixel)
        $value=[string]$entry.value
        $sizeObj=$graphics.MeasureString($value,$font,[System.Drawing.PointF]::new(0,0),$format)
        $x=[double]$entry.x*[double]$info.scale
        $y=([double]$entry.y - ([double]$size / [double]$info.scale)*1.12)*[double]$info.scale
        if($entry.anchor -eq 'middle'){$x-=$sizeObj.Width/2}
        if($entry.anchor -eq 'end'){$x-=$sizeObj.Width}
        $c=if($entry.color){[string]$entry.color}else{'#13223B'}
        $brush=[System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml($c))
        try {
            $graphics.DrawString($value,$font,$brush,[System.Drawing.PointF]::new([single]$x,[single]$y),$format)
            $boxes+=([pscustomobject]@{
              text=$value
              x=[math]::Round($x/[double]$info.scale,2)
              y=[math]::Round($y/[double]$info.scale,2)
              width=[math]::Round([double]$sizeObj.Width/[double]$info.scale,2)
              height=[math]::Round([double]$sizeObj.Height/[double]$info.scale,2)
            })
        } finally {$brush.Dispose();$font.Dispose()}
    }
    $graphics.Flush()
    $bitmap.Save([string]$info.png,[System.Drawing.Imaging.ImageFormat]::Png)
    $json=[pscustomobject]@{renderer='Windows GDI+ DrawString';font=$fontName;boxes=@($boxes)}
    [System.IO.File]::WriteAllText($BboxOutput,($json|ConvertTo-Json -Depth 6),[System.Text.UTF8Encoding]::new($false))
} finally {
    $graphics.Dispose()
    $bitmap.Dispose()
    $family.Dispose()
}
Write-Output "PNG=$($info.png); LABELS=$($boxes.Count)"
