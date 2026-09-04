# 手绘 / 涂鸦风格模块规范

三个具体美术方向（都可直接指导生图与排版），按需选一个做整套课件，最多混搭
2 个同纸本语系的方向。默认推荐 Doodle Marker（通用性最强、生成最稳）。

---

## 风格 A：马克笔涂鸦 · Doodle Marker（默认推荐）

白纸 + 粗马克笔 + 高光笔的"课堂涂鸦本"语言。

- **色板**：纸白 #FAF7F0 / 墨黑 #26241F / 马克红 #E8503A / 马克蓝 #2B6CB0 /
  马克黄 #F2B705 / 草绿 #5C9E52（强调不超过红黄两色，其余黑线白底）
- **质感**：纸面细颗粒；笔触有出锋和补笔；高光笔黄色斜杠当重点标记
- **字体**（HTML font stack）：`"楷体", "KaiTi", "华文楷体", cursive`；
  标题可用 `"幼圆", "YouYuan"` 加粗。开源加固方案：霞鹜文楷（LXGW WenKai，
  免费可商用，建议随项目内嵌 @font-face，保证任何机器放映不回退）
- **ImageGen prompt 模板**：
  ```
  Hand-drawn marker doodle illustration of {场景}, bold black outlines,
  flat marker colors, children's notebook sketch style, textured white
  paper background, visible pen strokes, no text, no watermark
  ```
- **版式法则**：元素微微旋转（-3°~3°）手贴感；框线用歪歪扭扭的手绘框
  （见构件①）；重点用高光笔斜杠或红圈；页面留白大、元素少而大。
- **PPT 落点**：底图 = 生成图压亮不加暗（与电影版相反，scrim 改用白色
  渐变保证黑字可读）；形状用"无边框 + 黑色手绘感描边"或直接图片化。

## 风格 B：蜡笔童绘 · Crayon Storybook

绘本蜡笔质感，色块厚重、边缘留白齿痕。适合低年级、故事类课文。

- **色板**：奶油纸 #FBF3E4 / 蜡笔橙 #E8833A / 湖蓝 #4A90B8 / 苔绿 #7BA05B /
  樱粉 #E8A0A8 / 炭笔 #3A3530
- **质感**：蜡笔颗粒（noise 纹理叠加）、色块边缘不齐、白纸齿痕边
- **字体**：同 A（楷体/霞鹜文楷），字号更大更圆
- **ImageGen prompt 模板**：
  ```
  Children's picture book crayon illustration of {场景}, thick waxy
  texture, soft warm palette, rough paper edges, storybook composition,
  no text, no watermark
  ```
- **版式法则**：大色块分区（不用细线框）；标题配蜡笔下划波浪线；插画占
  页面 1/2 以上，文字压在留白云朵/纸片上。

## 风格 C：粉笔黑板 · Chalkboard

深黑板 + 彩色粉笔。适合课堂导入页、板书页，与其他风格做页内对比。

- **色板**：黑板绿 #2E4B3F（或石板黑 #2B2B2B）/ 粉笔白 #F2EFE6 /
  粉笔黄 #E8D06A / 粉笔蓝 #8FB8CE / 粉笔红 #D98A80
- **质感**：黑板底纹（擦痕、粉笔灰）、粉笔线半透明断续、板擦痕迹
- **字体**：楷体 + 轻微透明度（0.92）模拟粉笔；不用描边
- **ImageGen prompt 模板**：
  ```
  Chalkboard illustration of {场景}, colored chalk drawing on dark green
  blackboard, chalk dust texture, hand-drawn lines, no text, no watermark
  ```
- **版式法则**：全页就是一块黑板（底图直接是黑板剧照）；粉笔白字为主，
  彩色粉笔只标重点；构件用虚线粉笔框 + 下角粉笔盒/板擦装饰。

---

## 通用 SVG 构件库（HTML 版式层，三风格共用逻辑、换配色即用）

| 构件 | 实现要点 |
|---|---|
| ① 手绘框 | SVG path 带随机抖动（每 30~50px 偏移 ±2px），闭合处留 1 个小缺口更自然；或双描边错位 2px |
| ② 荧光笔划线 | 半透明色块（黄/绿，opacity 0.45）+ 轻微倾斜 skewX(-2°) + mix-blend-mode: multiply |
| ③ 胶带贴角 | 旋转 45° 的半透明矩形（#E8D9A8, opacity 0.55），两端锯齿用 clip-path |
| ④ 贴纸描边 | 图形外圈白色粗描边（stroke 6~8px）+ 细阴影，产生"贴上去"效果 |
| ⑤ 涂鸦箭头 | SVG 手绘曲线箭头，线宽 3px，箭头两笔分开画（不要几何箭头） |
| ⑥ 圈重点 | 红笔椭圆圈 1.5 圈不闭合（同电影版红圈逻辑，但线要抖动） |
| ⑦ 纸纹理 | 整页叠加 noise/纤维 PNG（opacity 0.06~0.1，multiply） |

## 与电影版模块的关键差异（改流水线时对照）

| 维度 | 电影质感 | 手绘/涂鸦 |
|---|---|---|
| 底图处理 | 压暗 + scrim 黑渐变 + 暗角 | 压亮/原样 + 白色 scrim 渐变（深底黑板风除外） |
| 文字对比 | 亮字压暗底 | 深字压亮底（黑板风：亮字压深底） |
| 形状语言 | 直角/锐利 + 金线 | 抖动手绘线 + 胶带/贴纸 |
| 强调色逻辑 | 金 + 红 | 每风格自带上限 2 个强调色 |
| 构件库 | letterbox/场记板/面板 | 手绘框/荧光笔/胶带/贴纸/涂鸦箭头 |

## 手绘风 PPT 三级交付的注意事项

- L1 位图版：与电影版完全一致，无差异。
- L2 可编辑版：手绘感形状（抖动框、涂鸦箭头）在 PPTX 里退化为"虚线边框 +
  手写体"，插画类装饰建议并进背景图；字体务必确认放映机有（或内嵌），
  否则手写感全失——这是手绘风可编辑版最大的风险点。
- L3 动画版：方案不变；手绘风更适合 PPT 自带的"铅笔/画笔"类强调动画，
  COM 注入时 MsoAnimEffect 可试 CurvyLeft 系（手绘擦除），失败则退回
  Fade/Wipe 兜底（脚本参数化 fx 即可）。
