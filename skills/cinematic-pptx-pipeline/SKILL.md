---
name: cinematic-pptx-pipeline
description: 多风格 PPT/课件制作全流水线：按风格模块（电影质感 / 手绘涂鸦——马克笔涂鸦·蜡笔童绘·粉笔黑板 / 国潮——敦煌重彩·新中式海报·釉彩潮玩 / 玻璃拟态——极光玻璃·暗夜霓虹·晨雾轻拟态）生成 AI 插图 → 1280×720 HTML 页面（Python 生成器 + 构件库）→ Chrome headless 逐页截图 QA → 三级 PPTX 交付（位图版 / 可编辑原生版 / 带动画版）→ L4 MP4 视频版。当用户要求"电影级 PPT""手绘/涂鸦/绘本/黑板风 PPT""国潮/新中式/敦煌风 PPT""玻璃拟态/毛玻璃/Glassmorphism PPT""做一套课件/幻灯片并转成 PPT""可编辑 PPTX""带动画的 PPT""把动画 PPT 转成视频 / MP4 / 短视频"，或要把已有 HTML 幻灯片转为 PowerPoint / MP4 格式时使用本 skill。
---

# Cinematic PPTX Pipeline

从零产出一套电影级、手绘风、国潮风或玻璃拟态的演示文稿，并按需交付 PPTX
（L1/L2/L3）和 MP4 视频（L4）。全流水线已在七年级语文《春》17 页课件上完整
完整验证（10 张 AI 剧照 + 610 个动画效果 + 102s MP4）。

## 风格模块（第 0 步：先定风格，再走总流程）

| 模块 | 参考文档 | 视觉语言一句话 |
|---|---|---|
| 电影质感 | `references/cinematic-image-prompts.md` | 宽银幕黑边 + 暗底金/米白字 + 体积光剧照 + 胶片颗粒 |
| 手绘/涂鸦 | `references/handdrawn-style.md` | 三个子方向：马克笔涂鸦（默认）/ 蜡笔童绘 / 粉笔黑板；纸底深字 + 抖动手绘线 + 胶带贴纸 |
| 国潮 / 新中式 | `references/guochao-style.md` | 三个子方向：敦煌重彩（默认）/ 新中式海报 / 釉彩潮玩；传统纹样 + 高饱和撞色 + 烫金 + 印章 + 竖排 |
| 玻璃拟态 | `references/glassmorphism-style.md` | 三个子方向：极光玻璃（默认）/ 暗夜霓虹 / 晨雾轻拟态；三层景深 + 磨砂卡片（半透明+模糊+细亮边+长投影） |

- 四模块共用同一条流水线和全部脚本；差异只在**生图 prompt、色板、字体、
  构件库、底图处理方向**（电影=压暗亮字，手绘=压亮深字，国潮=压暗金红 /
  新中式浅底深字，玻璃拟态=深色方向不压暗、浅色方向不压暗只做渐变）。
- 各 reference 末尾都有"与其他模块关键差异对照表"，动手前对照执行。
- **风险排序（两条独立维度，选材时对照）**：
  - 字体回退风险：玻璃拟态（无衬线系统自带）≈ 国潮（宋体/黑体）< 电影
    （黑体/楷体）< 手绘（手写体需内嵌，最高）。
  - 可编辑版还原难度：手绘 / 国潮（中等，纹样与手绘感需并进背景图）< 电影
    （较低）< **玻璃拟态（最高，PPT 不支持 backdrop-filter，必须预模糊背景）**。
- 新风格扩展：仿照四份 reference 的结构（prompt 模板/色板/字体/构件/版式
  法则/PPT 落点/交付注意事项）新增一份文档并在上表登记即可，不改脚本。

## 总流程（六步）

0. **选定风格模块**（电影质感 / 手绘涂鸦 / 国潮 / 玻璃拟态，各含 3 个子方向），
   后续第 1~3 步按该模块的 reference 执行；第 4~6 步与风格无关。
1. **规划页序与场景清单**：先定页面数与每页内容，再规划 8~12 张插图的复用
   矩阵（哪些页共用哪张图、用什么处理方向）。prompt 规范见所选风格模块的
   reference（电影版 `cinematic-image-prompts.md` / 手绘版 `handdrawn-style.md`
   / 国潮版 `guochao-style.md` / 玻璃版 `glassmorphism-style.md`）。
2. **生成插图**（ImageGen）：所选风格统一 prompt 模板并行生成，硬规则 =
   画面不带文字（文字全由版式层负责）。
3. **生成 HTML 页面**（1280×720 画布）：Python 生成器架构 = `lib`（公共构件
   库 + 风格构件：电影版 letterbox/场记板/面板，手绘版手绘框/荧光笔/胶带/
   贴纸/涂鸦箭头，国潮版回纹边框/印章/烫金标题/竖排题签/海水江崖纹脚，
   玻璃版磨砂卡/光斑/玻璃胶囊标签/浮动玻璃条）+ 分段 `pages_*.py`
   （每文件管几页）。色板、字体、底图处理方向严格按风格模块的 reference。
4. **截图 QA**：Chrome headless 逐页截图目检，出框/遮挡/重叠当轮修掉。
   路径用绝对路径，截图前删旧 PNG 防缓存。
5. **PPTX 交付**：按用户需求选一级或逐级做（L1→L3，见下）。
6. **动画制作**（要"带动画"时，L3 环节）：在 L2 可编辑版上编排进入动画，
   详见下方「动画制作环节」。

## PPTX 三级交付

| 级别 | 产物 | 用途 | 路径 |
|---|---|---|---|
| L1 位图版 | 每页截图整幅嵌入 16:9 | 快速、画面 100% 还原 | `scripts/make_pptx_bitmap.py` |
| L2 可编辑版 | 原生文本框 + 原生形状，剧照预合成做底图 | 用户要"可编辑"时 | `scripts/bg_compose.py` + `references/editable-pptx-notes.md` |
| L3 动画版 | 在 L2 上注入进入动画，翻页自动播放 | 用户要"带动画"时 | `scripts/add_animations.py`（跨平台，默认）+ `scripts/add_animations.ps1`（Windows COM 备用） |
| L4 MP4 视频版 | 按元素级联 + 页间交叉过渡拼成 1280×720 MP4 | 用户要"做成视频"时 | `scripts/stage_export_frames.ps1`（Windows COM）+ `scripts/frames_to_video.py`（跨平台 ffmpeg） |

### L1 位图版

```bash
python scripts/make_pptx_bitmap.py <截图目录> <输出.pptx> --missing "p00,p02-p17"
```

页名缺失时也可省略 `--missing`，按目录内 PNG 自然排序。依赖 python-pptx。

### L2 可编辑版

关键策略：**把压暗（或压亮）/渐变/暗角烤进背景图**（`bg_compose.py` 的
Compositor；方向按风格模块：电影=压暗+黑 scrim，手绘=压亮+白 scrim，
国潮敦煌/釉彩=压暗 0.3~0.5，玻璃拟态=预模糊卡片区域或浅底渐变（不压暗），
新中式=浅底不变，黑板风=深底不变），PPTX 里每页 = 1 张全幅底图 + 原生
文本框/形状。HTML px → PPT pt 换算 1px=0.75pt。
重建要点（eastAsia 字体、半透明填充 XML、组合旋转、虚线枚举位置）全部在
`references/editable-pptx-notes.md`，动手前必读；手绘风可编辑版的字体内嵌
与手绘感退化风险见 `handdrawn-style.md` 末节；国潮风的纹样取舍（复杂纹样
全部并进背景图，PPT 层只留印章/金框/色块/竖排题签）见 `guochao-style.md`
末节。

### L3 动画版

前提：L2 可编辑版已完成（动画挂在原生形状上；L1 位图版没有独立形状，做不了有意义的动画）。

**首选（跨平台）**：纯 Python XML 注入，不需要 PowerPoint：

```bash
python scripts/add_animations.py --src <L2.pptx> --dst <动画版.pptx> [选项]
```

常用选项：`--effect fade` · `--no-wide-wipe` · `--stagger 0.12` · `--first-duration 0.5`
· `--trigger auto|click` · `--keep-pictures`。

脚本直接向每页 slide XML 写入 PowerPoint 规范的 `<p:timing>` 树；效果/触发/时长
参数与 COM 版完全对齐。**已用 PowerPoint 回读验证**：17 页共 610 个动画，首项
fade + AfterPrevious 0.5s，次项 WithPrevious 0.12s 延迟，全部被 PowerPoint 识别。

**Windows 备用（COM）**：需本机装有 PowerPoint，效果类型支持更多：

```powershell
powershell -File scripts/add_animations.ps1 -Src <L2.pptx> -Dst <动画版.pptx> -Log check.txt
```

什么场景下回退到 COM：① 想用 Python 脚本暂未支持的动画类型（如 RandomBars/
Spiral/自定义路径）；② 需要按形状 Name/位置做精细条件触发。

**回读校验（两版本通用）**：

```bash
python -c "from pptx import Presentation; p=Presentation('动画版.pptx'); \
print([s.shapes.title.text if s.shapes.title else s.slide_id for s in p.slides]); \
print('total effects per slide via COM (Win only): open in PowerPoint, Alt+F11...')"
```

Windows 上更直接：用 `export_qa.ps1` 渲染后人工确认；或在 PowerPoint 动画窗格
里数每页效果条数。

## 动画制作环节

编排原则（什么动/什么效果/顺序/节奏/触发）、注入实现（XML 树结构与预设 ID 表 /
COM 枚举）、校验方法，全部在 [workflows/animation.md](workflows/animation.md)，
做 L3 前必读。

### L4 MP4 视频版

前提：L3 动画版已完成（动画级联信息以可见性/层级编码到形状 z-order，
L4 按此还原）。完整方法论、踩坑与平台限制都在
`references/video-export.md`，动手前必读——里面有一个公式坑
（`xfade offset = k*(D−F)`，不是 `k*D−F`）会让视频无声被截断到几秒钟。

两阶段执行：

```powershell
# Phase A（Windows PowerPoint COM）—— 把每页按元素逐级显形导成 PNG
powershell -File scripts/stage_export_frames.ps1 `
  -Src <L3.pptx> -OutDir <frames-dir> -InfoPath <info.txt>
```

```bash
# Phase B（跨平台 ffmpeg）—— 把帧级联 + 页间过渡拼成 MP4
python scripts/frames_to_video.py \
  --frames-dir <frames-dir> --info <info.txt> \
  --clips-dir <clips-dir> --out <final.mp4>
```

QA：抽多帧比对（同一页不同时间必须不同 → 证明级联在播；跨页内容必须
对得上 L3 原稿）+ `ffprobe` 校时长/分辨率/编码。

关键限制：Phase A 依赖 PowerPoint COM（Windows-only）。macOS/Linux 需要
改走“HTML 源页 + headless 浏览器录制 CSS 动画”方案，本版未提供。

## QA（两级都要做）

- HTML 版：`chrome --headless=new --disable-gpu --hide-scrollbars
  --window-size=1366,800 --screenshot=<绝对路径> file://<绝对路径>`。
- PPTX 版（首选，Windows）：本机 PowerPoint COM 渲染逐页目检 =
  `powershell -File scripts/export_qa.ps1 -Src deck.pptx -OutDir qa_dir`。
  COM 渲染即最终放映效果，能暴露字体回退、旋转错位、出框等 python-pptx
  层面看不见的问题。
- PPTX 版（跨平台备用）：用 LibreOffice 无头转换再 PDF→PNG：
  ```bash
  soffice --headless --convert-to pdf deck.pptx --outdir qa_dir/    # 全平台
  pdftoppm -r 110 -png qa_dir/deck.pdf qa_dir/page                  # Linux/macOS 常用
  ```
  文字回退/排版位移与 PowerPoint 行为不完全一致（字体替换规则不同），但足以
  发现版式崩坏；最终视觉以 PowerPoint 为准。
- COM/PowerShell 脚本输出可能被宿主吞掉——一律把结果写日志文件再 Read。

## 已验证的踩坑清单

python-pptx/XML/字体/旋转/Chrome headless/ffmpeg xfade/COM 沙箱等已复现的坑与
解法，速查见 [references/pitfalls.md](references/pitfalls.md)——遇到报错或渲染
异常先查它。
