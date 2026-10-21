#!/usr/bin/env python3
"""Надписи на живом кадре, стили по образцам 21.10: python3 cover_text2.py кадр.png СТИЛЬ out.jpg СТРОКА1 СТРОКА2 [СТРОКА3]
torn — чёрная рваная полоса, строки белая + красная
goldpill — золото, среднее короткое слово в тёмной плашке (верх над головой, низ на груди)
ladder — лесенка: белая, крупная жёлтая, белая на красной плашке"""
import sys, random, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
SRC, ST, OUT = sys.argv[1:4]; L = [x.upper() for x in sys.argv[4:]]
W, H = 1080, 1920; FO = '/root/.fonts/oswald-700.ttf'; FM = '/root/.fonts/montserrat-900.ttf'
img = Image.open(SRC).convert('RGB').resize((W, H))
img = ImageEnhance.Color(ImageEnhance.Contrast(img).enhance(1.1)).enhance(1.08)
v = Image.new('L', (W, H), 0); ImageDraw.Draw(v).ellipse([-250, 250, W + 250, H - 350], fill=255)
img = Image.composite(img, Image.new('RGB', (W, H)), v.filter(ImageFilter.GaussianBlur(220)).point(lambda x: 90 + x * 165 // 255)).convert('RGBA')
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

if ST == 'torn':
    y0 = int(H * 0.64)
    f1 = fit(L[0], FO, 960, 190); f2 = fit(L[1], FO, 960, 240)
    h1 = f1.getbbox(L[0])[3] - f1.getbbox(L[0])[1]; h2 = f2.getbbox(L[1])[3] - f2.getbbox(L[1])[1]
    top, bot = y0 - 60, y0 + h1 + 30 + h2 + 70
    random.seed(7); band = Image.new('L', (W, H), 0); d = ImageDraw.Draw(band)
    pts = [(0, top)] + [(x, top + random.randint(-28, 18)) for x in range(0, W + 30, 30)] + [(W, top), (W, bot)] + [(x, bot + random.randint(-18, 28)) for x in range(W, -30, -30)] + [(0, bot)]
    d.polygon(pts, fill=255)
    band = band.rotate(-3, center=(W / 2, (top + bot) / 2), resample=Image.BICUBIC)
    shadow(band, 14, 18, 180)
    blk = Image.new('RGBA', (W, H), (12, 12, 14, 255)); blk.putalpha(band); img.alpha_composite(blk)
    x, y, h = centered(L[0], f1, y0); text_layer(L[0], f1, x, y, (255, 255, 255), rot=-3)
    x, y, h = centered(L[1], f2, y0 + h1 + 30); text_layer(L[1], f2, x, y, (235, 30, 35), rot=-3)
    if len(L) > 2:
        f3 = fit(L[2], FM, 900, 90); x, y, h = centered(L[2], f3, 230); text_layer(L[2], f3, x, y, (255, 255, 255), stroke=6)

elif ST == 'goldpill':
    txt = Image.new('L', (W, H), 0); dt = ImageDraw.Draw(txt)
    f1 = fit(L[0], FO, 940, 230); x, y, h1 = centered(L[0], f1, 200); dt.text((x, y), L[0], font=f1, fill=255)
    f3 = fit(L[2], FO, 940, 250); h3 = f3.getbbox(L[2])[3] - f3.getbbox(L[2])[1]
    y3 = H - 340 - h3; x, y, _ = centered(L[2], f3, y3); dt.text((x, y), L[2], font=f3, fill=255)
    # плашка со средним словом — над нижней строкой
    fp = ImageFont.truetype(FM, 64); bb = fp.getbbox(L[1]); pw, ph = bb[2] - bb[0] + 70, bb[3] - bb[1] + 40
    py = y3 - ph - 30
    pill = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dp = ImageDraw.Draw(pill)
    dp.rounded_rectangle([(W - pw) / 2, py, (W + pw) / 2, py + ph], ph // 2, fill=(20, 14, 10, 235), outline=(230, 180, 80, 255), width=4)
    dp.line([(W - pw) / 2 - 160, py + ph / 2, (W - pw) / 2 - 20, py + ph / 2], fill=(230, 180, 80, 255), width=4)
    dp.line([(W + pw) / 2 + 20, py + ph / 2, (W + pw) / 2 + 160, py + ph / 2], fill=(230, 180, 80, 255), width=4)
    shadow(pill.split()[3]); img.alpha_composite(pill)
    yy = np.arange(H)[:, None]; t = np.sin(yy / 30.0) * .5 + .5; g = np.zeros((H, W, 3), np.uint8)
    for ch, (lo, hi) in enumerate(((165, 255), (115, 240), (40, 165))): g[:, :, ch] = (lo + (hi - lo) * t).astype(np.uint8).repeat(W, 1)
    gold = Image.fromarray(g).convert('RGBA')
    pm = Image.new('L', (W, H), 0); ImageDraw.Draw(pm).text(((W - (bb[2] - bb[0])) / 2 - bb[0], py + 20 - bb[1]), L[1], font=fp, fill=255)
    full = Image.composite(Image.new('L', (W, H), 255), txt, txt)
    glow = Image.new('RGBA', (W, H), (255, 160, 40, 0)); glow.putalpha(txt.filter(ImageFilter.GaussianBlur(24)).point(lambda x: x * 190 // 255))
    shadow(txt, 10, 8, 230); img.alpha_composite(glow)
    gt = gold.copy(); gt.putalpha(txt); img.alpha_composite(gt)
    gp = gold.copy(); gp.putalpha(pm); img.alpha_composite(gp)

elif ST == 'ladder':
    f1 = fit(L[0], FM, 860, 100); x, y, h1 = centered(L[0], f1, 210); text_layer(L[0], f1, x, y, (255, 255, 255), stroke=8, rot=3)
    y2 = int(H * 0.60)
    f2 = fit(L[1], FM, 980, 220); x, y, h2 = centered(L[1], f2, y2); text_layer(L[1], f2, x, y, (255, 214, 0), stroke=10, rot=3)
    f3 = fit(L[2], FM, 820, 110); bb = f3.getbbox(L[2]); w3, h3 = bb[2] - bb[0], bb[3] - bb[1]
    y3 = y2 + h2 + 50
    pl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dp = ImageDraw.Draw(pl)
    dp.rounded_rectangle([(W - w3) / 2 - 36, y3 - 22, (W + w3) / 2 + 36, y3 + h3 + 24], 14, fill=(215, 25, 35, 255))
    dp.text(((W - w3) / 2 - bb[0], y3 - bb[1]), L[2], font=f3, fill=(255, 255, 255))
    pl = pl.rotate(3, center=(W / 2, y3 + h3 / 2), resample=Image.BICUBIC)
    shadow(pl.split()[3]); img.alpha_composite(pl)
img.convert('RGB').save(OUT, quality=94)
