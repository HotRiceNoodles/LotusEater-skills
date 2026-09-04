# -*- coding: utf-8 -*-
"""背景预合成库：把 AI 剧照加工成可直接当 PPT/HTML 幻灯片底图的图。

用途：可编辑 PPTX 的底图策略——把压暗、scrim 渐变、暗角全部"烤"进背景图，
文字压在任意位置都可读，PPTX 里只需一张全幅图片 + 原生文本框。

作为库导入使用（参照本目录说明或项目内脚本）：

    from bg_compose import Compositor
    c = Compositor(src_dir, out_dir, W=1280, H=720)
    im = c.still("cover.png")          # 中心裁 16:9 -> 1280x720
    c.dim(im, (4,20,10), 0.22)         # 全图压暗（RGB + alpha 0~1）
    c.vgrad(im, 380, 720, 0.0, 0.78)   # 竖直 scrim [y0,y1) alpha a0->a1
    c.hgrad(im, 0, 760, 0.82, 0.0)     # 水平 scrim
    c.vignette(im, 0.35)               # 暗角
    c.save(im, "p00.png")

    # 左右分屏（两剧照各占一半）：
    left = c.half("winter.png", (10,20,32), 0.35, (0,0,640,720))
    right = c.half("spring.png", (4,20,10), 0.12, (640,0,1280,720))

    # 深色底 + 低透明度剧照（文字密集页）：
    im = c.solid_bg(10, 16, 12, "grass.png", 0.14)

依赖: Pillow
"""
import os

from PIL import Image


class Compositor:
    def __init__(self, src_dir, out_dir, W=1280, H=720):
        self.src_dir = src_dir
        self.out_dir = out_dir
        self.W, self.H = W, H
        os.makedirs(out_dir, exist_ok=True)
        self._cache = {}

    def still(self, name):
        """剧照中心裁成目标宽高比，再缩放到 W x H（带缓存）"""
        if name not in self._cache:
            im = Image.open(os.path.join(self.src_dir, name)).convert("RGBA")
            w, h = im.size
            th = int(w * self.H / self.W)
            if th <= h:
                top = (h - th) // 2
                im = im.crop((0, top, w, top + th))
            else:
                tw = int(h * self.W / self.H)
                left = (w - tw) // 2
                im = im.crop((left, 0, left + tw, h))
            self._cache[name] = im.resize((self.W, self.H), Image.LANCZOS)
        return self._cache[name].copy()

    @staticmethod
    def dim(im, color, alpha):
        """全图叠纯色（color 为 RGB 元组，alpha 0~1）"""
        ov = Image.new("RGBA", im.size, color + (int(alpha * 255),))
        im.alpha_composite(ov)

    def _grad(self, im, mask_1d, color):
        mask = Image.new("L", mask_1d.size, 0)
        mask.putdata(mask_1d.getdata())
        mask = mask.resize(im.size)
        ov = Image.new("RGBA", im.size, color + (255,))
        im.paste(ov, (0, 0), mask)

    def vgrad(self, im, y0, y1, a0, a1, color=(0, 0, 0)):
        """竖直渐变 scrim：[y0,y1) 内 alpha 从 a0 线性到 a1，区间外为 0"""
        W, H = im.size
        mask = Image.new("L", (1, H), 0)
        px = []
        for y in range(H):
            if y < y0 or y >= y1:
                a = 0
            else:
                t = (y - y0) / max(1, (y1 - y0 - 1))
                a = a0 + (a1 - a0) * t
            px.append(int(max(0.0, min(1.0, a)) * 255))
        mask.putdata(px)
        self._grad(im, mask, color)

    def hgrad(self, im, x0, x1, a0, a1, color=(0, 0, 0)):
        """水平渐变 scrim：[x0,x1) 内 alpha 从 a0 线性到 a1，区间外为 0"""
        W, H = im.size
        mask = Image.new("L", (W, 1), 0)
        px = []
        for x in range(W):
            if x < x0 or x >= x1:
                a = 0
            else:
                t = (x - x0) / max(1, (x1 - x0 - 1))
                a = a0 + (a1 - a0) * t
            px.append(int(max(0.0, min(1.0, a)) * 255))
        mask.putdata(px)
        self._grad(im, mask, color)

    def vignette(self, im, strength=0.35):
        """四角暗角（strength 0~1）"""
        W, H = im.size
        g = Image.radial_gradient("L").resize((int(W * 1.45), int(H * 1.45)))
        left = (g.width - W) // 2
        top = (g.height - H) // 2
        mask = g.crop((left, top, left + W, top + H))
        mask = mask.point(lambda v: int(v / 255 * strength * 255))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        im.paste(ov, (0, 0), mask)

    def half(self, name, dimc, dima, box):
        """从已裁好的剧照中按 1280x720 坐标 box=(x,y,w,h) 取区域并压暗（分屏用）"""
        im = self.still(name)
        x, y, w, h = box
        sw, sh = im.size
        sx, sy = int(x / self.W * sw), int(y / self.H * sh)
        ex, ey = int((x + w) / self.W * sw), int((y + h) / self.H * sh)
        c = im.crop((sx, sy, ex, ey)).resize((w, h), Image.LANCZOS)
        self.dim(c, dimc, dima)
        return c

    def solid_bg(self, r, g, b, still_name=None, still_alpha=0.0):
        """纯色深底（可叠加低透明度剧照当纹理）——适合文字密集页"""
        W, H = self.W, self.H
        im = Image.new("RGBA", (W, H), (r, g, b, 255))
        if still_name and still_alpha > 0:
            f = self.still(still_name)
            f.putalpha(int(still_alpha * 255))
            im.alpha_composite(f)
        return im

    def save(self, im, name):
        im.convert("RGB").save(os.path.join(self.out_dir, name), "PNG")
        print("bg", name)
