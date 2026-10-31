#!/usr/bin/env python3
"""Надписи на живом кадре, стили по образцам 21.10: python3 cover_text2.py кадр.png СТИЛЬ out.jpg СТРОКА1 СТРОКА2 [СТРОКА3]
torn — чёрная рваная полоса, строки белая + красная
goldpill — золото, среднее короткое слово в тёмной плашке (верх над головой, низ на груди)
ladder — лесенка: белая, крупная жёлтая, белая на красной плашке"""
import sys, random, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import cover_safe as CS
FD = _os.environ.get('FONTS', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'fonts')) + '/'   # шрифты нового стиля (21.10.2026)
SRC, ST, OUT = sys.argv[1:4]; L = [x.upper() for x in sys.argv[4:]]
# верх не выше 300: сетка Instagram режет 1920 до 3:4 (видно 240–1680), Евгений 22.10.2026
W, H = 1080, 1920; FO = FD + 'oswald-700.ttf'; FM = FD + 'montserrat-900.ttf'
src = Image.open(SRC).convert('RGB').resize((W, H))
def fit(t, f, maxw, s):
    while ImageFont.truetype(f, s).getlength(t) > maxw: s -= 4
    return ImageFont.truetype(f, s)
def shadow(mask, off=10, blur=10, a=200):
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(mask.filter(ImageFilter.GaussianBlur(blur)).point(lambda x: x * a // 255)); img.alpha_composite(sh, (0, off))
def text_layer(t, f, x, y, fill, stroke=0, rot=0):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((x, y), t, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    if rot: lay = lay.rotate(rot, center=(W / 2, y + f.size / 2), resample=Image.BICUBIC)
    shadow(lay.split()[3]); img.alpha_composite(lay)
def centered(t, f, y): bb = f.getbbox(t); return (W - (bb[2] - bb[0])) / 2 - bb[0], y - bb[1], bb[3] - bb[1]

def hgt(t, f): bb = f.getbbox(t); return bb[3] - bb[1]
def mw(y, m): return CS.maxw_at(y, 0, m)   # строки у значка ролика Instagram — уже

# Раскладка по лицу (31.10.2026, скрин сетки Instagram): верх над головой, нижний блок строго под подбородком,
# не помещается — всё над головой (при нужде картинка сдвигается вниз). Низ не ниже 1450.
if ST == 'torn':
    def bnd(s):
        f1 = fit(L[0], FO, 960, max(40, int(190 * s))); f2 = fit(L[1], FO, 960, max(40, int(240 * s)))
        return f1, f2, hgt(L[0], f1), hgt(L[1], f2)
    def pad(s): return max(0.55, s)
    def bot_need(s): _, _, h1, h2 = bnd(s); return h1 + int(30 * pad(s)) + h2 + int(130 * pad(s)) + 46 + 40   # полоса с зубцами и наклоном
    top_need = (lambda s: hgt(L[2], fit(L[2], FM, CS.ICON_W, max(30, int(90 * s)))) + 20) if len(L) > 2 else (lambda s: 0)
elif ST == 'goldpill':
    def pill_h(s): fp = ImageFont.truetype(FM, max(30, int(64 * s))); bb = fp.getbbox(L[1]); return bb[3] - bb[1] + 40
    top_need = lambda s: hgt(L[0], fit(L[0], FO, CS.ICON_W, max(40, int(230 * s))))
    bot_need = lambda s: pill_h(s) + 30 + hgt(L[2], fit(L[2], FO, 940, max(40, int(250 * s))))
elif ST == 'ladder':
    top_need = lambda s: hgt(L[0], fit(L[0], FM, CS.ICON_W, max(30, int(100 * s)))) + 50
    def bot_need(s):
        f2 = fit(L[1], FM, 980, max(40, int(220 * s))); f3 = fit(L[2], FM, 820, max(30, int(110 * s)))
        return 25 + hgt(L[1], f2) + 50 + hgt(L[2], f3) + 46 + 60
src, Z, PL = CS.prepare(src, top_need, bot_need)
st, sb, yt, yb = PL['s_top'], PL['s_bot'], PL['y_top'], PL['y_bot']
img = src
img = ImageEnhance.Color(ImageEnhance.Contrast(img).enhance(1.1)).enhance(1.08)
v = Image.new('L', (W, H), 0); ImageDraw.Draw(v).ellipse([-250, 250, W + 250, H - 350], fill=255)
img = Image.composite(img, Image.new('RGB', (W, H)), v.filter(ImageFilter.GaussianBlur(220)).point(lambda x: 90 + x * 165 // 255)).convert('RGBA')

if ST == 'torn':
    f1, f2, h1, h2 = bnd(sb)
    k = pad(sb); y0 = yb + int(60 * k) + 28 + 20
    top, bot = y0 - int(60 * k), y0 + h1 + int(30 * k) + h2 + int(70 * k)
    random.seed(7); band = Image.new('L', (W, H), 0); d = ImageDraw.Draw(band)
    pts = [(0, top)] + [(x, top + random.randint(-28, 18)) for x in range(0, W + 30, 30)] + [(W, top), (W, bot)] + [(x, bot + random.randint(-18, 28)) for x in range(W, -30, -30)] + [(0, bot)]
    d.polygon(pts, fill=255)
    band = band.rotate(-3, center=(W / 2, (top + bot) / 2), resample=Image.BICUBIC)
    shadow(band, 14, 18, 180)
    blk = Image.new('RGBA', (W, H), (12, 12, 14, 255)); blk.putalpha(band); img.alpha_composite(blk)
    x, y, h = centered(L[0], f1, y0); text_layer(L[0], f1, x, y, (255, 255, 255), rot=-3)
    x, y, h = centered(L[1], f2, y0 + h1 + int(30 * k)); text_layer(L[1], f2, x, y, (235, 30, 35), rot=-3)
    if len(L) > 2:
        f3 = fit(L[2], FM, mw(yt, 900), max(30, int(90 * st))); x, y, h = centered(L[2], f3, yt); text_layer(L[2], f3, x, y, (255, 255, 255), stroke=6)

elif ST == 'goldpill':
    txt = Image.new('L', (W, H), 0); dt = ImageDraw.Draw(txt)
    f1 = fit(L[0], FO, mw(yt, 940), max(40, int(230 * st))); x, y, h1 = centered(L[0], f1, yt); dt.text((x, y), L[0], font=f1, fill=255)
    fp = ImageFont.truetype(FM, max(30, int(64 * sb))); bb = fp.getbbox(L[1]); pw, ph = bb[2] - bb[0] + 70, bb[3] - bb[1] + 40
    py = yb
    f3 = fit(L[2], FO, mw(py + ph + 30, 940), max(40, int(250 * sb))); y3 = py + ph + 30
    x, y, _ = centered(L[2], f3, y3); dt.text((x, y), L[2], font=f3, fill=255)
    pill = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dp = ImageDraw.Draw(pill)
    dp.rounded_rectangle([(W - pw) / 2, py, (W + pw) / 2, py + ph], ph // 2, fill=(20, 14, 10, 235), outline=(230, 180, 80, 255), width=4)
    dp.line([(W - pw) / 2 - 160, py + ph / 2, (W - pw) / 2 - 20, py + ph / 2], fill=(230, 180, 80, 255), width=4)
    dp.line([(W + pw) / 2 + 20, py + ph / 2, (W + pw) / 2 + 160, py + ph / 2], fill=(230, 180, 80, 255), width=4)
    shadow(pill.split()[3]); img.alpha_composite(pill)
    yy = np.arange(H)[:, None]; t = np.sin(yy / 30.0) * .5 + .5; g = np.zeros((H, W, 3), np.uint8)
    for ch, (lo, hi) in enumerate(((165, 255), (115, 240), (40, 165))): g[:, :, ch] = (lo + (hi - lo) * t).astype(np.uint8).repeat(W, 1)
    gold = Image.fromarray(g).convert('RGBA')
    pm = Image.new('L', (W, H), 0); ImageDraw.Draw(pm).text(((W - (bb[2] - bb[0])) / 2 - bb[0], py + 20 - bb[1]), L[1], font=fp, fill=255)
    glow = Image.new('RGBA', (W, H), (255, 160, 40, 0)); glow.putalpha(txt.filter(ImageFilter.GaussianBlur(24)).point(lambda x: x * 190 // 255))
    shadow(txt, 10, 8, 230); img.alpha_composite(glow)
    gt = gold.copy(); gt.putalpha(txt); img.alpha_composite(gt)
    gp = gold.copy(); gp.putalpha(pm); img.alpha_composite(gp)

elif ST == 'ladder':
    f1 = fit(L[0], FM, mw(yt, 860), max(30, int(100 * st))); x, y, h1 = centered(L[0], f1, yt + 25); text_layer(L[0], f1, x, y, (255, 255, 255), stroke=8, rot=3)
    y2 = yb + 25
    f2 = fit(L[1], FM, mw(y2, 980), max(40, int(220 * sb))); x, y, h2 = centered(L[1], f2, y2); text_layer(L[1], f2, x, y, (255, 214, 0), stroke=10, rot=3)
    f3 = fit(L[2], FM, 820, max(30, int(110 * sb))); bb = f3.getbbox(L[2]); w3, h3 = bb[2] - bb[0], bb[3] - bb[1]
    y3 = y2 + h2 + 50
    pl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dp = ImageDraw.Draw(pl)
    dp.rounded_rectangle([(W - w3) / 2 - 36, y3 - 22, (W + w3) / 2 + 36, y3 + h3 + 24], 14, fill=(215, 25, 35, 255))
    dp.text(((W - w3) / 2 - bb[0], y3 - bb[1]), L[2], font=f3, fill=(255, 255, 255))
    pl = pl.rotate(3, center=(W / 2, y3 + h3 / 2), resample=Image.BICUBIC)
    shadow(pl.split()[3]); img.alpha_composite(pl)
CS.report(Z, PL, OUT)
img.convert('RGB').save(OUT, quality=94)
