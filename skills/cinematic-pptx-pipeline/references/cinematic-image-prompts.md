# 电影感剧照生成（ImageGen）规范

## 统一 Prompt 模板

每张剧照用同一句式，只换场景描述，保证整套画面风格一致：

```
Cinematic film still, {场景描述}, 16:9, volumetric light,
shallow depth of field, 35mm film grain, no text, no watermark
```

场景描述用具体意象（主体 + 环境 + 光线），例：
- `a tiny green sprout breaking through dark soil, morning backlit mist, extreme close-up`（封面）
- `an old bare winter tree and the same tree in full spring bloom, split composition`
- `an open classic book on a wooden desk by soft window light`
- `children running through a vast green meadow at golden hour, silhouettes`

## 硬规则

1. **画面不带文字**——所有文字由版式层（HTML/PPT 文本框）负责，否则双语乱字无法修。
2. 生成尺寸 1536×1024（3:2），背景合成时中心裁成 16:9 无损余量足够。
3. 多张图**并行调用** ImageGen，省时（按张计费，先列清单再一起发）。
4. 文件名用短语义名（cover_sprout / winter_tree / open_book…），不要用日期串。

## 场景规划法（一图多用）

一次规划 8~12 张，覆盖整套课件的复用矩阵，避免逐页现想：

| 需求页型 | 选图策略 |
|---|---|
| 封面/结尾 | 情绪最强的一张（微距破土 / 落日原野） |
| 文字密集页 | 深色底 + 剧照 0.12~0.18 透明度当纹理 |
| 对比页 | 一张图内的分屏构图（让 prompt 画 split composition） |
| 强压暗页 | 同一张图不同 dim 值复用，全套画面更统一 |

10 张左右即可支撑 17 页——同一剧照在不同页用不同压暗/渐变方向，视觉上
是"同一部电影的 different takes"，风格反而更统一。
