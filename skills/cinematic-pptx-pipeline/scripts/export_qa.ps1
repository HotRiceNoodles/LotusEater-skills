# 用本机 PowerPoint 把 PPTX 每页渲染成 PNG（目检 QA 用——COM 渲染 = 最终放映效果）
# 用法:
#   powershell -File export_qa.ps1 -Src "deck.pptx" -OutDir "qa_dir" [-W 1280] [-H 720]
# 注意:
#   - 输出文件名为 "幻灯片N.PNG"（跟随系统语言）
#   - 目检前先清空 OutDir 旧 PNG，防止缓存错觉
param(
    [Parameter(Mandatory=$true)][string]$Src,
    [Parameter(Mandatory=$true)][string]$OutDir,
    [int]$W = 1280,
    [int]$H = 720
)

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$pp = $null
try {
    $pp = New-Object -ComObject PowerPoint.Application
    $pres = $pp.Presentations.Open($Src, $true, $false, $false)   # ReadOnly 打开即可
    $pres.Export($OutDir, "PNG", $W, $H)
    $pres.Close()
    Write-Output ("EXPORTED to " + $OutDir)
} catch {
    Write-Output ("FAIL: " + $_.Exception.Message)
} finally {
    if ($pp) { $pp.Quit() }
}
