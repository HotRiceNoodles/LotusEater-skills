# 动画制作环节（编排设计 + 注入 + 校验）

读本文的时机：用户要"带动画"（L3）或要做 MP4（L4 前置）时，在 L2 可编辑版上编排进入动画。

## 1. 编排原则

- **什么动**：只动前景内容（文本框、面板、圆环、进度点等原生形状）；
  背景剧照保持静态（Type=13 msoPicture 跳过）。
- **什么效果**：宽形状（>360pt，面板/横幅/黑边）用擦入 Wipe(22)，文字和
  小元素用淡入 Fade(10)。克制——一套课件只用 2~3 种效果，电影感靠"少而准"。
- **顺序**：按 z-order 注入 = 生成顺序 = 视觉层级（底→面、标题→内容）。
- **节奏**：首形状 0.5s 淡入做"开场"，其余 0.35s 级联、间隔 0.12s（封顶 2.5s），
  整页 2~3 秒内完成，不拖沓。
- **触发**：默认首形状 AfterPrevious(3)——翻到该页自动播放，其余 WithPrevious(2)。
  若教学需要"先提问后答案"，把答案组形状改为 OnPageClick(1)，由教师点击控制。

## 2. 注入实现

python-pptx **不暴露动画 API**，但支持 lxml 级操作。两条路：

**(a) 跨平台：纯 XML 注入（首选）**
按 PowerPoint 自己的 `<p:timing>` 规范直接写出 XML 树到每页 slide XML：

```python
# 核心结构：mainSeq > par > cTn(nodeType=afterEffect/withEffect/clickEffect)
# > childTnLst > [set(visible), animEffect(filter="fade"/"wipe(down)")]
# 全部实现见 scripts/add_animations.py（已验证 610 个动画）
```

预设 ID 表（presetID）：fade=10 / wipe=22 / fly=2 / zoom=23 / appear=1；触发
nodeType：clickEffect=点击 / withEffect=与上一项同时 / afterEffect=上一项之后；
duration 与 TriggerDelayTime 单位毫秒。

**(b) Windows：PowerPoint COM（效果类型最全）**

```powershell
$eff = $seq.AddEffect($sh, $fx, 0, $trigger)   # $seq = $slide.TimeLine.MainSequence
$eff.Timing.Duration = 0.35                    # 时长（秒）
$eff.Timing.TriggerDelayTime = 0.12            # WithPrevious 时的级联延迟
```

枚举：MsoAnimEffect Appear=1 / Fly=2 / Fade=10 / Wipe=22 / Zoom=23；
MsoAnimTrigger OnPageClick=1 / WithPrevious=2 / AfterPrevious=3。
完整可跑实现见 `scripts/add_animations.ps1`。

## 3. 校验

- **回读校验**：重开文件统计每页 `MainSequence.Count`，与注入日志比对
  （17 页课件应为 610 个左右，平均每页 30~50 个）。
- **渲染目检**：`export_qa.ps1` 导出的 PNG 是动画播完后的终态，可确认版面
  没被动画副作用破坏，但**看不到动画过程本身**——动画节奏只能在 PowerPoint
  放映里人工确认，交付时提醒用户 F5/Shift+F5 检查。
- 单页想改触发方式或顺序：告诉页码，按形状名/位置定位该页 MainSequence
  里的效果，改 `Timing.TriggerType` 或删掉重挂。
