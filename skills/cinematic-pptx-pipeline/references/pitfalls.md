# 已验证的踩坑清单（速查）

读本文的时机：写生成器代码、重建 PPTX、注入动画或导出视频遇到报错/渲染异常时，先来这查。

- python-pptx 不支持动画 → 必须 PowerPoint COM 注入（L3 脚本已封装）。
- `MSO_LINE_DASH_STYLE` 在 `pptx.enum.dml`，不在 `enum.line`。
- `shape.rotation` 顺时针、绕自身中心：父形状旋转后，子形状位置需绕父中心
  重算 + 同角度旋转，否则错位。
- 中文字体必须 latin + eastAsia 双设，否则放映回退宋体。
- 圆角矩形 `adjustments[0]` 是比例（radius/min(w,h)），不是绝对半径。
- ImageGen 生成多张图并行调用；f-string 内不能引用未定义循环变量。
- Chrome headless 截图必须绝对路径；QA 前删旧 PNG。
- 玻璃拟态专属：Chrome headless 下 `backdrop-filter` 偶发不渲染（卡片下没有
  模糊）→ `--force-device-scale-factor=1` 重试，仍不行就改用"PIL 预模糊背景
  + 半透明卡片"方案（同一个方案同时解决 PPT 无 backdrop-filter 的问题）。
- L4 视频专属：ffmpeg `xfade offset = k*(D−F)`，不是 `k*D−F`（后者会无声截断
  视频到几秒钟；3 张色图实测可复现）。链尾标签必须 `-map "[label]"`。
- L4 视频专属：PowerPoint `CreateVideo` 在沙箱/部分 Office 安装里不可用
  （最小 deck 立即 status 1→3 失败）→ 不要依赖它，走本 skill 的级联帧 +
  ffmpeg 方案。
- L4 视频专属：`.ps1` 里写中文字面量会让 `Open` 抛 0x8007007B；COM 后台运行
  会 0x800706BE → 源 pptx 复制到 ASCII 名 + 前台跑 + per-slide 实例化。
