import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import os as _os
FD = _os.environ.get('FONTS', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'fonts')) + '/'   # шрифты нового стиля (21.10.2026)
SRC, TOP, BOT, OUT, var = sys.argv[1:6]
W, H = 1080, 1920; F = FD + 'oswald-700.ttf'
src = Image.open(SRC).convert('RGB').resize((W, H))
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
    hs = []
    for ln in lines:
        f = fit(ln, 940, size); bb = f.getbbox(ln); hs.append((ln, f, bb))
    tot = sum(bb[3] - bb[1] for _, _, bb in hs) + 24 * (len(hs) - 1)
    if anchor_bottom: y -= tot
    for ln, f, bb in hs:
        d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], y - bb[1]), ln, font=f, fill=255); y += bb[3] - bb[1] + 24
put([l.upper() for l in TOP.split('|') if l], 300, 210, anchor_bottom=False)
put([l.upper() for l in BOT.split('|') if l], H - 330, 230, anchor_bottom=True)
yy = np.arange(H)[:, None]; t = np.sin(yy / 30.0) * 0.5 + 0.5
grad = np.zeros((H, W, 3), np.uint8)
for ch, (lo, hi) in enumerate(((160, 255), (110, 238), (40, 165))): grad[:, :, ch] = (lo + (hi - lo) * t).astype(np.uint8).repeat(W, 1)
gold = Image.fromarray(grad).convert('RGBA'); gold.putalpha(txt)
glow = Image.new('RGBA', (W, H), (255, 165, 50, 0)); glow.putalpha(txt.filter(ImageFilter.GaussianBlur(26)).point(lambda x: x * 210 // 255))
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(txt.filter(ImageFilter.GaussianBlur(7)).point(lambda x: x * 230 // 255))
img.alpha_composite(sh, (0, 10)); img.alpha_composite(glow); img.alpha_composite(gold)
img.convert('RGB').save(OUT, quality=94)
