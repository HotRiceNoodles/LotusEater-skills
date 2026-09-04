# 用 python-pptx 原生重建可编辑 PPTX —— 技术要点与踩坑

来源：电影版课件 17 页从 HTML 重建为可编辑 PPTX 的实战（本机 PowerPoint 10/PowerPoint COM 验证）。

## 总体架构

```
HTML 版式源（1280x720, absolute 定位, 单位 px）
        │  等比换算: 1px = 1pt / (1280/960) → 直接用 Pt(px * 0.75)
        ▼
python-pptx: 16:9 (Inches(13.333) x Inches(7.5))，blank = slide_layouts[6]
  1. 底图: add_picture(预合成背景, 全幅铺满)   ← 只此一张图片
  2. 文字: add_textbox + 真 run（字体/字号/颜色/字距可编辑）
  3. 图形: add_shape(面板/圆环/胶囊/线条) 原生形状
```

换算约定：HTML 用 px（1280×720），PPT 用 pt（960×540）。**1px = 0.75pt**，
封装 `def P(v): return Pt(v * 0.75)` 后所有坐标照抄 HTML 版即可。

## 文本框要点

- 字体必须同时设 latin 和 eastAsia，否则中文回退宋体：
  ```python
  run.font.name = "KaiTi"                      # latin
  rPr = run._r.get_or_add_rPr()
  ea = rPr.makeelement(qn('a:ea'), {'typeface': '楷体'})
  rPr.append(ea)
  ```
- 字距（HTML letter-spacing）→ `rPr.set('spc', str(int(px * 100)))`（单位 1/100 pt）。
- 多色一行 = 多个 run，逐个设色。
- 自动换行关掉更贴近 HTML 版：`tf.word_wrap = False`；边距清零：
  `tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0`。
- 半透明文字：run 级 `a:solidFill` 里插 `a:alpha val="60000"`。

## 形状要点

- 半透明填充：`shape.fill.fore_color.rgb = RGBColor(...)` 后，手动在该
  `a:solidFill` 元素里插入 `<a:alpha val="N"/>`（N=不透明度×100000）。
- 圆角矩形半径：`shape.adjustments[0] = radius / min(w, h)`（比例而非绝对值）。
- **组合旋转**：`shape.rotation` 是顺时针角度，绕形状自身中心旋转。若整个
  板条旋转 -8°，其上的子条纹必须各自也设 -8°，且子形状位置要按"绕板条
  中心旋转"重算——直接沿用未旋转时的坐标会出现条纹错位（实战踩过）。
- 虚线边框：`from pptx.enum.dml import MSO_LINE_DASH_STYLE`（**在 enum.dml，
  不在 enum.line**），`shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH`。
- 仅描边无填充：`shape.fill.background()`。

## 背景预合成（文字可读性的关键）

不要在 PPT 里叠半透明矩形当遮罩——把压暗/scrim 渐变/暗角用 PIL 烤进背景图
（见 `scripts/bg_compose.py`），PPTX 里就是一张普通图片。原则：

- 文字所在一侧渐变到 0.75~0.85 黑；
- 全图基础压暗 0.2~0.8 视文字密度；
- 暗角统一 0.35；
- 文字密集页改用深色底 + 剧照 0.12~0.18 低透明度当纹理。

### 玻璃拟态专用：预模糊背景（PPT 无 backdrop-filter 的替代方案）

毛玻璃"卡片背后的模糊"在 PPTX 里无法用原生形状实现。做法是把模糊烤进背景图，
PPT 层只放"半透明白填充 + 1pt 浅色描边"的矩形：

```python
from PIL import Image, ImageFilter, ImageDraw

def glass_bg(im, cards, blur=24, lift=0.10):
    """cards=[(x,y,w,h)]（1280x720 坐标）：卡片区域局部模糊 + 轻微提亮"""
    blurred = im.filter(ImageFilter.GaussianBlur(blur))
    mask = Image.new("L", im.size, 0)
    d = ImageDraw.Draw(mask)
    for (x, y, w, h) in cards:
        d.rounded_rectangle([x, y, x + w, y + h], radius=24, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(8))          # 边缘柔化，避免硬切
    im.paste(blurred, (0, 0), mask)
    ov = Image.new("RGBA", im.size, (255, 255, 255, int(lift * 255)))
    im.paste(ov, (0, 0), mask)                              # 卡片区域再提亮一点
    return im
```

PPTX 侧对应形状：`fill=FFFFFF` + `<a:alpha val="16000"/>`（浅底方向用
`val="60000"`），`line.color.rgb = FFFFFF`、宽度 1pt、line alpha 30~40%。

## QA 流程

1. `powershell -File scripts/export_qa.ps1 -Src deck.pptx -OutDir qa_dir`
   （本机 PowerPoint COM 渲染 = 最终放映效果）。
2. 目检前清空旧 PNG（防缓存错觉）。
3. 逐页看：出框 / 遮挡 / 旋转错位 / 字体回退。
4. COM 脚本的 `Write-Output` 可能被宿主吞掉——把结果 `Set-Content` 写日志
   文件再 Read，最可靠。

## 已验证的能力边界

- python-pptx 本身**不支持动画**——动画用 PowerPoint COM 注入
  （见 `scripts/add_animations.ps1`）。
- 复杂矢量装饰（月桂枝、胶片颗粒）在 PPTX 里简化或放弃，保圆环/胶囊/线条
  等可编辑形状即可；颗粒感由背景图携带。
