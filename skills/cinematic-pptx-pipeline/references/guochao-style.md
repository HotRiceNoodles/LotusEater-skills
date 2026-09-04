# 国潮风格模块规范

"传统元素 + 现代潮流"的视觉语言：传统纹样与器物做主视觉，用高饱和撞色、
粗描边、烫金质感、现代版式重新包装。三个具体美术方向，按需选一个做整套，
最多混搭 2 个同语系方向。默认推荐「敦煌重彩」——辨识度最高、生成最稳。

---

## 风格 A：国潮插画 · 敦煌重彩（默认推荐）

壁画矿物色 + 潮流插画的粗描边与撞色。

- **色板**：石青 #1B5E8C / 土红 #C0392B / 藤黄 #E8A317 / 金 #D9A441 /
  墨黑 #1F1B18 / 宣纸米 #F2E8D5（高饱和撞色是国潮灵魂，别降饱和）
- **质感**：壁画斑驳（剥落、龟裂纹理叠加）、矿物颗粒、烫金描边（金色
  1~2px 外描边 + 轻微外发光）
- **字体**（HTML font stack）：标题 `"华文中宋", "STZhongsong", "宋体", serif`；
  正文 `"微软雅黑", "PingFang SC", sans-serif`；数字/英文可用 `"Impact"` 类
  无衬线拉宽字距做潮牌感
- **ImageGen prompt 模板**：
  ```
  Guochao Chinese-trend illustration of {场景}, Dunhuang mural mineral
  palette (azurite blue, cinnabar red, gamboge yellow), bold black
  outlines, ornate cloud and flame patterns, gold accents, aged fresco
  texture, flat vector style, no text, no watermark
  ```
- **版式法则**：繁复边框（回纹/卷草纹）围一圈留白；标题竖排或大字居中压
  纹样；重点用**朱红印章**或金框；元素对称构图（国潮讲究"正"）。
- **PPT 落点**：底图中等压暗（0.3~0.5）+ 暗角；文字金/米白压深底；
  复杂纹样并进背景图，PPT 里只留印章、金框、色块等可编辑元素。

## 风格 B：国潮平面 · 新中式海报

海报排版语言：宋体大字 + 几何色块 + 极简纹样点缀，比 A 更克制、更像
"现代设计"，适合信息密集页。

- **色板**：朱红 #C1272D / 藏青 #1C2B49 / 金 #C9A063 / 月白 #F5F1E8 /
  竹青 #4A7C59
- **质感**：近乎扁平，只在标题用极细金色描边；大面积纯色块 + 网格排版
- **字体**：宋体标题（字距拉开 0.1em）+ 黑体正文；可做竖排题签（右上角
  竖排小标签 = 最典型的国潮排版符号）
- **ImageGen prompt 模板**：
  ```
  New Chinese style (guochao) flat poster illustration of {场景}, minimal
  geometric shapes, vermilion and navy palette, subtle traditional pattern
  accents, clean vector, generous negative space, no text, no watermark
  ```
- **版式法则**：网格严格对齐；**留白 ≥ 40%**；纹样只做边角点缀（1~2 处），
  绝不铺满；色块承担分区，不用线框。
- **PPT 落点**：浅底（月白）为主 + 深字（藏青/朱红），与 A 的深底路线相反；
  这是信息密集型课件最舒服的国潮方案。

## 风格 C：国潮潮玩 · 釉彩陶瓷

3D 釉面潮玩质感（陶瓷/景泰蓝/琉璃），圆润造型 + 镜面高光，年轻活泼。

- **色板**：霁蓝 #2A4C8F / 胭脂红 #D8455B / 青绿釉 #6FA8A0 / 釉白 #F7F3EA /
  描金 #E4B95B（景泰蓝配色：蓝为底、红黄为花、金为线）
- **质感**：釉面高光（大面积柔和反光 + 边缘亮线）、器物圆润倒角、釉色
  流动感；景泰蓝方向加掐丝金线
- **字体**：圆润黑体 `"幼圆", "YouYuan", "微软雅黑"`（与釉面造型呼应）
- **ImageGen prompt 模板**：
  ```
  Guochao art-toy render of {场景}, glazed ceramic material, cloisonne
  enamel colors (cobalt blue, rouge red, turquoise), gold wire inlay,
  glossy surface, rounded cute forms, studio lighting, 3D render,
  no text, no watermark
  ```
- **版式法则**：主视觉 = 一个大主体（器物/瑞兽）居中；文字少而大，配
  圆形色块底；页面四角放云纹/铜钱纹小装饰。
- **PPT 落点**：底图压暗 0.5+（3D 渲染本身亮度高）；文字用釉白/描金；
  适合封面、章节页、结尾页这类"大画面少文字"的位置。

---

## 通用 SVG 构件库（HTML 版式层，三方向共用逻辑、换配色即用）

| 构件 | 实现要点 |
|---|---|
| ① 回纹/云纹边框 | SVG `<pattern>` 平铺单元纹样，四边各一条；转角处放单独角花（不要直接平铺到角落，会错位） |
| ② 朱红印章 | 正方形圆角 + 朱红填充 + 白色反白字（2~4 字）+ 轻微旋转 2°；或做椭圆闲章 |
| ③ 烫金标题 | 文字金色渐变（linearGradient #F2D9A0→#C9A063）+ 1.5px 深色描边 + 外发光滤镜 |
| ④ 竖排题签 | `writing-mode: vertical-rl` + 窄条色底 + 字号小、字距大，放右上或左侧书脊位 |
| ⑤ 海水江崖纹脚 | 页面底部一条弧形层叠纹（同心弧线 + 山形三角），SVG path 复用即可 |
| ⑥ 铜钱/万字纹底 | 低透明度（0.05~0.08）平铺整页当纸纹，避免干扰文字 |
| ⑦ 卷草分隔线 | 中心对称的卷草纹 + 两端渐隐，替代普通直线做章节分隔 |

## 与另两个模块的关键差异

| 维度 | 电影质感 | 手绘/涂鸦 | 国潮 |
|---|---|---|---|
| 底图 | 压暗 + 黑 scrim | 压亮 + 白 scrim | A/C 压暗 0.3~0.5，B 浅底深字 |
| 文字 | 米白/金 | 深墨色 | 金 / 米白 / 朱红 / 藏青 |
| 字体 | 黑体+楷体 | 楷体/手写（需内嵌） | **宋体+黑体（系统自带，无需内嵌）** |
| 形状语言 | 锐利直角 + 金线 | 抖动手绘线 | 对称繁复边框 + 印章 + 竖排 |
| 强调 | 金色点缀 | 荧光笔/红圈 | 朱红印章 + 烫金 + 撞色块 |
| 留白 | 满版 | 大留白 | A/C 满版繁复，B 留白 ≥40% |

## 国潮风 PPT 三级交付注意事项

- **字体是最省心的一档**：宋体/黑体 Windows、macOS（宋体-简 / PingFang）、
  常见 Linux 字体包都有，可编辑版不会因字体回退毁掉风格。正文仍建议
  latin + eastAsia 双设（见 `editable-pptx-notes.md`）。
- **纹样处理（关键取舍）**：回纹/卷草/海水江崖这类复杂纹样在 PPTX 里
  **全部并进背景图**；PPT 层只保留印章、金框、色块、竖排题签这四类
  可用原生形状/文本框还原的元素。否则可编辑版会变成几十个碎片形状。
- **L2 可编辑版**：烫金渐变在 PPTX 里退化为纯金色填充（可接受）；外发光
  用同色描边模拟。
- **L3 动画版**：方案不变。国潮繁复底图 + 简洁前景时，动画节奏可稍慢
  （`--stagger 0.15`）显得更"仪式感"；如需"印章盖下"效果，Windows 端可
  回退 COM 脚本用 Zoom 类效果（Python 版 `add_animations.py --effect zoom`
  也能覆盖基础需求）。
