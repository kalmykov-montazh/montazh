import os
#!/usr/bin/env python3
# Стиль v2: без мультяшных эмодзи. Фон — размытый кадр самого ролика, стеклянные карточки,
# линейные иконки, документ «как настоящий», маркер, кольцо-таймер, блик.
import math, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W, H = 1080, 1920
BLK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
BLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
GOLD = (245, 196, 40);  # 29.10.2026 Евгений выбрал фон №1: тёмно-синий + жёлтый (было 240,190,90)
WH = (255, 250, 242); TERRA = (226, 110, 60); G = (60, 200, 130); R = (235, 70, 60)
INK = (40, 28, 22); PAPER = (250, 246, 236)
def F(s, p=BLK): return ImageFont.truetype(p, s)

def navy_bg():
    """фон сцен с 29.10.2026 (Евгений, вариант 1): тёмно-синий, тонкие линии, жёлтая полоса сверху, края темнее"""
    im = Image.new("RGBA", (W, H), (14, 27, 52, 255)); d = ImageDraw.Draw(im)
    for y in range(0, H, 12): d.line([(0, y), (W, y)], fill=(17, 31, 59, 255), width=3)
    v = Image.new("L", (W // 4, H // 4), 0); ImageDraw.Draw(v).ellipse([-120, 60, W // 4 + 120, H // 4 - 60], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(70)).resize((W, H))
    im = Image.composite(im, Image.new("RGBA", (W, H), (7, 14, 30, 255)), v)
    ImageDraw.Draw(im).rectangle([0, 0, W, 22], fill=(*GOLD, 255))
    return im

def bg_from(video, t):
    if os.environ.get("SCENE_BG", "navy") == "navy": return navy_bg()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", video, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    im = Image.frombytes("RGB", (W, H), raw).filter(ImageFilter.GaussianBlur(38)).convert("RGBA")
    im.alpha_composite(Image.new("RGBA", (W, H), (30, 14, 8, 170)))      # тёплое затемнение
    v = Image.new("L", (W, H), 0); ImageDraw.Draw(v).ellipse([-300, 200, W + 300, H - 200], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGBA", (W, H), (10, 5, 3, 255)); im = Image.composite(im, dark, v)
    return im

def glass(dst, box, r=36, border=GOLD, alpha=110):
    x0, y0, x1, y1 = box
    if x1 - x0 < 4 or y1 - y0 < 4: return   # 29.10.2026: на первом кадре появления карточка нулевая — падал процесс рендера
    r = min(r, (x1 - x0) // 2, (y1 - y0) // 2)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([x0 + 8, y0 + 18, x1 + 8, y1 + 18], r, fill=(0, 0, 0, 120))
    dst.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    reg = dst.crop(box).filter(ImageFilter.GaussianBlur(18))
    m = Image.new("L", reg.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], r, fill=255)
    dst.paste(reg, box[:2], m)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle(box, r, fill=(8, 18, 38, 215), outline=(*border, alpha + 80), width=3)
    dst.alpha_composite(ov)

def sweep(dst, box, u):   # блик по карточке
    if not 0 <= u <= 1: return
    x0, y0, x1, y1 = box; L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    cx = x0 - 200 + (x1 - x0 + 400) * u
    d.polygon([(cx, y0), (cx + 90, y0), (cx - 60, y1), (cx - 150, y1)], fill=(255, 255, 255, 70))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle(box, 30, fill=255)
    L.putalpha(Image.composite(L.getchannel("A"), Image.new("L", (W, H), 0), m)); dst.alpha_composite(L.filter(ImageFilter.GaussianBlur(6)))

def edge_glow(dst, col, k=1.0):
    fl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fl)
    for i in range(0, 90, 3): fd.rectangle([i, i, W - i, H - i], outline=(*col, int(170 * k * (1 - i / 90) ** 1.6)), width=4)
    dst.alpha_composite(fl)

def text(d, xy, s, size, col=WH, font=BLK, anchor="mm", sh=True):
    if sh: d.text((xy[0] + 3, xy[1] + 4), s, font=F(size, font), fill=(0, 0, 0, 140), anchor=anchor)
    d.text(xy, s, font=F(size, font), fill=col, anchor=anchor)

def kicker(d, y, s, col=GOLD):   # маленький заголовок с линиями
    f = F(40, BLD); w = f.getlength(s)
    d.text((W / 2, y), s, font=f, fill=col, anchor="mm")
    d.line([(W / 2 - w / 2 - 130, y), (W / 2 - w / 2 - 30, y)], fill=col, width=3)
    d.line([(W / 2 + w / 2 + 30, y), (W / 2 + w / 2 + 130, y)], fill=col, width=3)

# ---- линейные иконки ----
def ic_person(d, cx, cy, s, col, w=8):
    d.ellipse([cx - 0.28 * s, cy - 0.62 * s, cx + 0.28 * s, cy - 0.06 * s], outline=col, width=w)
    d.arc([cx - 0.55 * s, cy + 0.02 * s, cx + 0.55 * s, cy + 1.1 * s], 180, 360, fill=col, width=w)
def ic_key(d, cx, cy, s, col, w=8):
    d.ellipse([cx - 0.6 * s, cy - 0.25 * s, cx - 0.1 * s, cy + 0.25 * s], outline=col, width=w)
    d.line([(cx - 0.1 * s, cy), (cx + 0.6 * s, cy)], fill=col, width=w)
    for x in (0.35, 0.52): d.line([(cx + x * s, cy), (cx + x * s, cy + 0.2 * s)], fill=col, width=w)
def ic_house(d, cx, cy, s, col, w=8):
    d.line([(cx - 0.6 * s, cy), (cx, cy - 0.55 * s), (cx + 0.6 * s, cy)], fill=col, width=w, joint="curve")
    d.rectangle([cx - 0.42 * s, cy - 0.05 * s, cx + 0.42 * s, cy + 0.55 * s], outline=col, width=w)
    d.rectangle([cx - 0.1 * s, cy + 0.2 * s, cx + 0.1 * s, cy + 0.55 * s], outline=col, width=w)
def ic_clock(d, cx, cy, r, col, ang, w=8):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=w)
    for k in range(12):
        a = k * math.pi / 6; d.line([(cx + math.cos(a) * r * 0.82, cy + math.sin(a) * r * 0.82), (cx + math.cos(a) * r * 0.92, cy + math.sin(a) * r * 0.92)], fill=col, width=4)
    d.line([(cx, cy), (cx + math.sin(ang) * r * 0.75, cy - math.cos(ang) * r * 0.75)], fill=GOLD, width=w)
    d.line([(cx, cy), (cx + math.sin(ang / 12) * r * 0.5, cy - math.cos(ang / 12) * r * 0.5)], fill=col, width=w + 2)
    d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=GOLD)
def check(d, cx, cy, s, col, w=12):
    d.line([(cx - s, cy), (cx - s * 0.3, cy + s * 0.7), (cx + s, cy - s * 0.8)], fill=col, width=w, joint="curve")
def cross(d, cx, cy, s, col, w=12):
    d.line([(cx - s, cy - s), (cx + s, cy + s)], fill=col, width=w); d.line([(cx + s, cy - s), (cx - s, cy + s)], fill=col, width=w)
def badge(dst, cx, cy, r, col, kind):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.ellipse([cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18], fill=(*col, 50))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*col, 255))
    (check if kind else cross)(d, cx, cy, r * 0.45, WH, 14); dst.alpha_composite(ov)

# ---- документ ----
def nota(dst, cx, cy, sc, hl=1.0, titular="TITULAR: J. GARCÍA LÓPEZ", stamp=True, rot=-3):
    w, h = int(640 * sc), int(860 * sc)
    doc = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(doc)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 14, fill=PAPER)
    d.rectangle([0, 0, w, int(110 * sc)], fill=(232, 224, 205))
    d.text((w / 2, 40 * sc), "REGISTRO DE LA PROPIEDAD", font=F(int(30 * sc), BLD), fill=(110, 90, 70), anchor="mm")
    d.text((w / 2, 80 * sc), "NOTA SIMPLE INFORMATIVA", font=F(int(36 * sc), BLK), fill=INK, anchor="mm")
    y = 160 * sc
    for ln in ["DESCRIPCIÓN DE LA FINCA", None, None, "TITULARIDAD", "TIT", None, "CARGAS", None, None]:
        if ln == "TIT":
            if hl > 0:
                d.rectangle([40 * sc, y - 26 * sc, 40 * sc + (w - 80 * sc) * hl, y + 26 * sc], fill=(255, 214, 80))
            d.text((50 * sc, y), titular, font=F(int(30 * sc), BLK), fill=INK, anchor="lm")
        elif ln: d.text((50 * sc, y), ln, font=F(int(24 * sc), BLD), fill=(150, 120, 90), anchor="lm")
        else:
            for k in range(2): d.line([(50 * sc, y - 10 * sc + k * 22 * sc), (w - (50 + 90 * k) * sc, y - 10 * sc + k * 22 * sc)], fill=(205, 195, 175), width=max(2, int(6 * sc)))
        y += 72 * sc
    if stamp:
        sx, sy, r = w - 140 * sc, h - 130 * sc, 90 * sc
        d.ellipse([sx - r, sy - r, sx + r, sy + r], outline=(40, 70, 160, 200), width=int(7 * sc))
        d.ellipse([sx - r * 0.7, sy - r * 0.7, sx + r * 0.7, sy + r * 0.7], outline=(40, 70, 160, 160), width=int(4 * sc))
        d.text((sx, sy), "REGISTRO", font=F(int(22 * sc), BLK), fill=(40, 70, 160, 200), anchor="mm")
    doc = doc.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([cx - w / 2 + 20, cy - h / 2 + 30, cx + w / 2 + 20, cy + h / 2 + 30], fill=(0, 0, 0, 150))
    dst.alpha_composite(sh.filter(ImageFilter.GaussianBlur(28)))
    dst.alpha_composite(doc, (int(cx - doc.width / 2), int(cy - doc.height / 2)))

def sub(dst, s, hi):   # субтитры меньше: 64 px
    d = ImageDraw.Draw(dst); f = F(64); ws = s.split(); tw = f.getlength(s)
    x = W / 2 - tw / 2; y = 1430
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.rounded_rectangle([x - 30, y - 50, x + tw + 30, y + 50], 22, fill=(20, 10, 6, 200)); dst.alpha_composite(ov)
    for i, w_ in enumerate(ws):
        d.text((x, y), w_, font=f, fill=GOLD if i == hi else WH, anchor="lm"); x += f.getlength(w_ + " ")

