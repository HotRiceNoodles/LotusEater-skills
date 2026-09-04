# 玻璃拟态（Glassmorphism）风格模块规范

毛玻璃语言：**三层景深**（背景彩色光斑 → 磨砂玻璃卡片 → 前景文字）+ 半透明
+ 细亮边 + 柔和长投影。三个具体美术方向，按需选一个做整套。默认推荐
「极光玻璃」——辨识度最高、生成最稳。

---

## 毛玻璃四要素（所有方向的共同底座）

```
background: rgba(255,255,255,0.14)        /* 半透明填充：浅底 0.14~0.22，深底 0.06~0.12 */
backdrop-filter: blur(24px) saturate(160%) /* 磨砂核心：背景模糊 + 提饱和 */
border: 1px solid rgba(255,255,255,0.35)   /* 细亮边：玻璃的"厚度" */
box-shadow: 0 8px 32px rgba(0,0,0,0.28),   /* 长投影：把卡片"抬"起来 */
            inset 0 1px 0 rgba(255,255,255,0.5)  /* 顶部内高光：玻璃反光 */
border-radius: 24px                        /* 大圆角：现代感 */
```

用法纪律：**一张卡片只承载一个信息组**；卡片之间留白 ≥ 卡片内边距；
文字必须放卡片内或压 scrim，绝不能直接压在彩色光斑上（对比度会失控）。

## 风格 A：极光玻璃 · Aurora Glass（默认推荐）

冷调彩色极光背景 + 冷白玻璃卡，梦幻、通透。

- **色板**：极光青 #4FD1C5 / 极光紫 #8B5CF6 / 极光粉 #F472B6 / 深靛底
  #131A2B / 玻璃白 rgba(255,255,255,0.16) / 文字 #F8FAFC
- **质感**：背景由 3~5 个大号彩色光斑（radial-gradient + blur 80~120px）
  叠成；卡片冷白磨砂；全页叠 3% 噪点防色带
- **字体**（HTML font stack）：标题 `"Inter", "PingFang SC", "微软雅黑", sans-serif`
  加粗；正文 `"PingFang SC", "微软雅黑", "Source Han Sans", sans-serif`。
  **统一无衬线**——玻璃拟态配衬线字体风格会打架
- **ImageGen prompt 模板**（背景光斑用，主体另出）：
  ```
  Abstract aurora gradient background, soft bokeh light blobs in teal,
  violet and pink, deep indigo base, dreamy glassmorphism wallpaper,
  smooth color transitions, high resolution, no text, no watermark
  ```
- **版式法则**：光斑只做背景，不抢卡片；卡片 2~4 张纵向排布；标题放顶部
  大玻璃条内；数字/关键词用胶囊玻璃标签凸显。
- **PPT 落点**：底图直接用生成的极光背景（**不需要压暗**，它本身够深），
  文字米白；卡片 = 半透明白填充形状 + 细描边。

## 风格 B：暗夜霓虹 · Neon Glass

深色底 + 霓虹描边光晕，科技感、赛博感，适合成果展示/数据页。

- **色板**：近黑底 #0A0E17 / 霓虹青 #22D3EE / 霓虹紫 #A855F7 / 霓虹绿
  #4ADE80 / 警示橙 #FB923C / 文字 #E5E7EB
- **质感**：卡片半透明更低（0.06~0.10，几乎只剩边框和光晕）；关键元素加
  外发光（box-shadow 双层：近距实色 + 远距大范围）；背景叠细网格线
  （1px, rgba(255,255,255,0.04)）
- **字体**：同上无衬线；数字可用等宽字体（`"JetBrains Mono", "Consolas"`）
  做数据科技感
- **ImageGen prompt 模板**：
  ```
  Dark night city bokeh background with neon cyan and purple glow,
  deep black base, cinematic depth of field, subtle grid lines,
  high contrast, no text, no watermark
  ```
- **版式法则**：高对比，霓虹色只用于 1~2 个焦点元素；信息用等宽数字排；
  边框粗细分层（焦点 2px 亮边 / 常规 1px 弱边）。
- **PPT 落点**：底图压暗到 0.5 以上（霓虹背景本身亮度不均）；文字浅灰白；
  发光效果在 PPT 里用"同色描边 + 柔化边缘矩形"模拟。

## 风格 C：晨雾轻拟态 · Soft Frost

浅色马卡龙渐变 + 白色磨砂卡 + 柔和长投影，清爽、轻柔，**最适合信息密集
的课件页**（长时间观看不疲劳）。

- **色板**：雾底 #EEF2FF → #FDF2F8 渐变 / 雾蓝 #A5B4FC / 雾粉 #FBCFE8 /
  雾绿 #BBF7D0 / 墨字 #1F2937 / 强调 #6366F1
- **质感**：背景是大范围柔和渐变（不是光斑）；卡片白色磨砂（0.55~0.7 不
  透明度，比暗色方向的卡片实一些）；投影更长更柔（0 12px 40px rgba(31,41,55,0.10)）
- **字体**：同无衬线；正文可用 `"思源黑体 / 苹方"` 常规字重
- **ImageGen prompt 模板**：
  ```
  Soft pastel gradient background, misty light blue and pink and mint,
  airy and clean, soft focus, minimal, high resolution,
  no text, no watermark
  ```
- **版式法则**：卡片白底深字（**整套唯一一条"深色文字"方向**）；留白充足；
  用色块/图标分类，不用强对比。
- **PPT 落点**：底图**不压暗**（本就是浅底）；文字深灰；卡片用白色半透明
  形状即可，视觉还原度最高的一档。

---

## 通用构件库（HTML 版式层，三方向共用逻辑、换配色即用）

| 构件 | 实现要点 |
|---|---|
| ① 磨砂卡 | 四要素见上；卡片内边距 ≥ 28px；圆角 20~28px |
| ② 光斑 | `radial-gradient` 圆 + `filter: blur(100px)`，3~5 个错位摆放，opacity 0.5~0.8 |
| ③ 细分隔线 | `1px rgba(255,255,255,0.18)`（浅底方向用 `rgba(31,41,55,0.10)`） |
| ④ 玻璃胶囊标签 | 小号圆角胶囊 + 半透明填充 + 8~12px 字，做分类/关键词 |
| ⑤ 浮动玻璃条 | 顶部或底部横贯的半透明条（承载标题/页码），带 1px 亮上边 |
| ⑥ 噪点层 | 全页 PNG 噪点 opacity 0.03，消除大面积渐变的色带 |
| ⑦ 图标底盘 | 圆形磨砂底 + 居中线性图标（stroke 1.5px，不用填充图标） |

## 与其他模块的关键差异

| 维度 | 电影质感 | 手绘/涂鸦 | 国潮 | 玻璃拟态 |
|---|---|---|---|---|
| 底图 | 压暗+黑 scrim | 压亮+白 scrim | 压暗金红 / 浅底 | A/B 深色原样（B 再压暗），C 浅底不压暗 |
| 文字 | 米白/金 | 深墨 | 金/朱红/藏青 | A/B 浅白，C 深灰 |
| 字体 | 黑体+楷体 | 楷体/手写（需内嵌） | 宋体+黑体 | **统一无衬线（苹方/微软雅黑，系统自带）** |
| 形状语言 | 锐利直角+金线 | 抖动手绘线 | 繁复边框+印章 | 大圆角半透明卡+细亮边+长投影 |
| 留白 | 满版 | 大留白 | 繁复/部分留白 | 卡片间留白，单卡内容密度高 |

## 玻璃拟态 PPT 三级交付注意事项（**本模块工程难度最高，务必先读**）

- **最大坑：PPT 不支持 `backdrop-filter`**。可编辑版里玻璃卡"背后的模糊"
  无法用原生形状实现。解决办法：**把模糊烤进背景图**——用 PIL 生成"卡片
  区域已局部模糊/提亮"的背景图（模糊区域用 `ImageFilter.GaussianBlur` 遮罩
  合成），PPT 层只放半透明白填充 + 细描边的矩形。视觉上等价于真毛玻璃。
- **半透明形状**：`shape.fill.fore_color.rgb` 后在 `a:solidFill` 里插
  `<a:alpha val="16000"/>`（=16%）；描边用 `shape.line.color.rgb` + 宽度 1pt。
  具体写法见 `references/editable-pptx-notes.md`。
- **截图 QA 注意**：Chrome headless 下 `backdrop-filter` 偶尔不渲染（表现为
  卡片下没有模糊、纯半透明）。出现这种情况：① 加 `--force-device-scale-factor=1`
  重试；② 仍无效则用 PIL 预模糊背景图 + 半透明卡片替代方案（与 PPT 落点
  方案一致，一次解决两端）。
- **字体风险低**：无衬线系统字体（苹方/微软雅黑/思源黑体）跨平台都有，
  可编辑版不会因字体回退毁风格。
- **L3 动画版**：玻璃卡本身就很适合淡入/缩放浮现，节奏可稍快
  （`--stagger 0.08`）；如需"卡片依次浮起"，Windows 端可回退 COM 脚本用
  Ascend/Float 类效果。
