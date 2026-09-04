param(
  [Parameter(Mandatory)][string]$Src,
  [Parameter(Mandatory)][string]$OutDir,
  [Parameter(Mandatory)][string]$InfoPath,
  [string]$LogPath = "",
  [int]$Width = 1280,
  [int]$Height = 720,
  [string]$Prefix = "slide"
)
# Export per-slide staged frames from an animated PPTX by toggling non-picture
# shape visibility. PowerPoint COM, Windows only. One PowerPoint instance per
# slide for resilience (long sessions risk RPC crashes).
# All paths must be ASCII; non-ASCII source path will trigger 0x8007007B on Open.
if (-not $LogPath) { $LogPath = Join-Path $OutDir "stage_export.log" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$lines = @()
$meta = @()
# detect slide count by opening once briefly
$pp = $null
$cnt = 0
try {
  $pp = New-Object -ComObject PowerPoint.Application
  $pres = $pp.Presentations.Open($Src, $false, $false, $false)
  $cnt = $pres.Slides.Count
  try { $pres.Close() } catch {}
} catch {
  $lines += ("count FAIL: " + $_.Exception.Message)
  $lines | Set-Content -Path $LogPath -Encoding UTF8
  if ($pp) { try { $pp.Quit() } catch {} }
  exit 1
} finally { if ($pp) { try { $pp.Quit() } catch {} } }
$lines += ("slides=" + $cnt)
for ($si = 1; $si -le $cnt; $si++) {
  $firstFrame = "{0}{1:00}_000.png" -f $Prefix, $si
  $pp = $null
  try {
    $pp = New-Object -ComObject PowerPoint.Application
    $pres = $pp.Presentations.Open($Src, $false, $false, $false)
    $sl = $pres.Slides.Item($si)
    $np = @()
    for ($i = 1; $i -le $sl.Shapes.Count; $i++) {
      $sh = $sl.Shapes.Item($i)
      if ($sh.Type -eq 13) { try { $sh.Visible = 1 } catch {}; continue }
      try { $sh.Visible = 0 } catch {}
      $np += $sh
    }
    $N = $np.Count
    $lastFrame = "{0}{1:00}_{2:000}.png" -f $Prefix, $si, $N
    $fFirst = Join-Path $OutDir $firstFrame
    $fLast = Join-Path $OutDir $lastFrame
    if ((Test-Path $fFirst) -and (Test-Path $fLast)) {
      $lines += ("slide {0:00} resume-skip (N={1})" -f $si, $N)
      $meta += ("{0:00}={1}" -f $si, $N)
      try { $pres.Close() } catch {}
      continue
    }
    $sl.Export($fFirst, "PNG", $Width, $Height)
    for ($k = 1; $k -le $N; $k++) {
      try { $np[$k-1].Visible = 1 } catch {}
      $fk = "{0}{1:00}_{2:000}.png" -f $Prefix, $si, $k
      $f = Join-Path $OutDir $fk
      $sl.Export($f, "PNG", $Width, $Height)
    }
    foreach ($sh in $np) { try { $sh.Visible = 1 } catch {} }
    $meta += ("{0:00}={1}" -f $si, $N)
    $lines += ("slide {0:00} ok nonpic={1}" -f $si, $N)
    try { $pres.Close() } catch {}
  } catch {
    $lines += ("slide {0:00} FAIL: {1}" -f $si, $_.Exception.Message)
  } finally {
    if ($pp) { try { $pp.Quit() } catch {} }
  }
}
$meta | Set-Content -Path $InfoPath -Encoding UTF8
$lines += "ALL_DONE"
$lines | Set-Content -Path $LogPath -Encoding UTF8