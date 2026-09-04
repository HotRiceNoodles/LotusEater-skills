# 给 PPTX 注入进入动画（PowerPoint COM；要求本机装有 PowerPoint）
# 用法:
#   powershell -File add_animations.ps1 -Src "a.pptx" -Dst "b.pptx" [-Log "check.txt"]
#
# 方案（已验证）:
#   - 按 z-order（= 生成顺序 ≈ 视觉层级）给每个非图片形状挂进入动画
#   - 首个形状: 淡入 0.5s, AfterPrevious —— 翻到该页自动播放
#   - 其余形状: 淡入 0.35s, WithPrevious, 延迟 k*0.12s（上限 2.5s）级联
#   - 宽形状(>360pt)用擦入(Wipe)替代淡入；背景图(Type=13)保持静态
#   - 动画枚举: MsoAnimEffect Fade=10/Wipe=22; MsoAnimTrigger OnPageClick=1/WithPrevious=2/AfterPrevious=3
param(
    [Parameter(Mandatory=$true)][string]$Src,
    [Parameter(Mandatory=$true)][string]$Dst,
    [string]$Log = ""
)

Copy-Item $Src $Dst -Force
$logLines = @()
$pp = $null
try {
    $pp = New-Object -ComObject PowerPoint.Application
    # Open(FileName, ReadOnly:=false, Untitled:=false, WithWindow:=false)
    $pres = $pp.Presentations.Open($dst, $false, $false, $false)
    foreach ($slide in $pres.Slides) {
        $seq = $slide.TimeLine.MainSequence
        $k = 0
        for ($i = 1; $i -le $slide.Shapes.Count; $i++) {
            $sh = $slide.Shapes.Item($i)
            if ($sh.Type -eq 13) { continue }   # msoPicture: 背景图不动画
            $fx = 10                            # msoAnimEffectFade
            if ($sh.Width -gt 360) { $fx = 22 } # msoAnimEffectWipe（宽面板）
            try {
                if ($k -eq 0) {
                    $eff = $seq.AddEffect($sh, $fx, 0, 3)      # AfterPrevious
                    $eff.Timing.Duration = 0.5
                } else {
                    $eff = $seq.AddEffect($sh, $fx, 0, 2)      # WithPrevious
                    $eff.Timing.Duration = 0.35
                    $eff.Timing.TriggerDelayTime = [math]::Min(2.5, $k * 0.12)
                }
                $k++
            } catch { }
        }
        $logLines += ("Slide " + $slide.SlideIndex + ": " + $k + " effects")
    }
    $pres.Save()
    $pres.Close()
    $logLines += "SAVED: $Dst"
} catch {
    $logLines += ("FAIL: " + $_.Exception.Message)
} finally {
    if ($pp) { $pp.Quit() }
}

if ($Log -ne "") { $logLines | Set-Content -Path $Log -Encoding UTF8 }
$logLines
