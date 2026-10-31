import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import cover_safe as CS
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import os as _os
FD = _os.environ.get('FONTS', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'fonts')) + '/'   # шрифты нового стиля (21.10.2026)
SRC, TOP, BOT, OUT, var = sys.argv[1:6]
W, H = 1080, 1920; F = FD + 'oswald-700.ttf'
src = Image.open(SRC).convert('RGB').resize((W, H))
def _fit(t, maxw, s):
    while ImageFont.truetype(F, s).getlength(t) > maxw and s > 20: s -= 4
    return ImageFont.truetype(F, s)
def _need(lines, size, y0):
    def f(s):
        if not lines: return 0
        y = y0; tot = 0
        for ln in lines:
            fo = _fit(ln, CS.maxw_at(y, 0, 940), max(40, int(size * s))); bb = fo.getbbox(ln); tot += bb[3] - bb[1] + 24; y += bb[3] - bb[1] + 24
        return tot - 24
    return f
TL = [l.upper() for l in TOP.split('|') if l]; BL = [l.upper() for l in BOT.split('|') if l]
# Раскладка по лицу (31.10.2026, скрин сетки Instagram): верх над головой, низ строго под подбородком, иначе всё над головой
src, Z, PL = CS.prepare(src, _need(TL, 210, CS.SAFE_TOP), _need(BL, 230, 900))
img = ImageEnhance.Contrast(src).enhance(1.12)
img = ImageEnhance.Color(img).enhance(1.1)
warm = Image.new('RGB', (W, H), (255, 140, 40)); img = Image.blend(img, warm, 0.10)
# виньетка + затемнение сверху и снизу, чтобы текст читался
v = Image.new('L', (W, H), 0); ImageDraw.Draw(v).ellipse([-250, 250, W + 250, H - 350], fill=255)
v = v.filter(ImageFilter.GaussianBlur(220))
dark = Image.new('RGB', (W, H), (0, 0, 0)); img = Image.composite(img, dark, v.point(lambda x: 70 + x * 185 // 255))
img = img.convert('RGBA')
def fit(t, maxw, s):
    while ImageFont.truetype(F, s).getlength(t) > maxw: s -= 4
    return ImageFont.truetype(F, s)
txt = Image.new('L', (W, H), 0); d = ImageDraw.Draw(txt)
def put(lines, y, size, anchor_bottom=False):
    for ln in lines:
        f = _fit(ln, CS.maxw_at(y, 0, 940), size); bb = f.getbbox(ln)
        d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], y - bb[1]), ln, font=f, fill=255); y += bb[3] - bb[1] + 24
put(TL, PL['y_top'], max(40, int(210 * PL['s_top'])))
put(BL, PL['y_bot'], max(40, int(230 * PL['s_bot'])))
CS.report(Z, PL, OUT)
yy = np.arange(H)[:, None]; t = np.sin(yy / 30.0) * 0.5 + 0.5
grad = np.zeros((H, W, 3), np.uint8)
for ch, (lo, hi) in enumerate(((160, 255), (110, 238), (40, 165))): grad[:, :, ch] = (lo + (hi - lo) * t).astype(np.uint8).repeat(W, 1)
gold = Image.fromarray(grad).convert('RGBA'); gold.putalpha(txt)
glow = Image.new('RGBA', (W, H), (255, 165, 50, 0)); glow.putalpha(txt.filter(ImageFilter.GaussianBlur(26)).point(lambda x: x * 210 // 255))
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(txt.filter(ImageFilter.GaussianBlur(7)).point(lambda x: x * 230 // 255))
img.alpha_composite(sh, (0, 10)); img.alpha_composite(glow); img.alpha_composite(gold)
img.convert('RGB').save(OUT, quality=94)
