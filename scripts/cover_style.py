#!/usr/bin/env python3
"""Обложка на живом кадре: python3 cover_style.py кадр.png "ВЕРХ|..." "НИЗ|..." СТИЛЬ out.jpg
Стили: gold, yellow, redblue, whiteyellow, neon, chrome, sunset"""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import cover_safe as CS
FD = _os.environ.get('FONTS', _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'fonts')) + '/'   # шрифты нового стиля (21.10.2026)
SRC, TOP, BOT, ST, OUT = sys.argv[1:6]
W, H = 1080, 1920
FO = FD + 'oswald-700.ttf'; FM = FD + 'montserrat-900.ttf'
P = {
 'gold':        dict(tint=(255, 140, 40), ta=.10, fill=[(255, 238, 165), (160, 110, 40)], stroke=None, glow=(255, 165, 50), font=FO, top=None),
 'yellow':      dict(tint=(0, 0, 0), ta=.0, fill=[(255, 214, 0), (255, 214, 0)], stroke=(0, 0, 0), glow=None, font=FM, top='plate_black'),
 'redblue':     dict(tint=(30, 80, 200), ta=.16, fill=[(255, 60, 60), (200, 20, 30)], stroke=(255, 255, 255), glow=(40, 90, 255), font=FM, top='plate_blue'),
 'whiteyellow': dict(tint=(0, 0, 0), ta=.0, fill=[(255, 255, 255), (255, 255, 255)], stroke=(0, 0, 0), glow=None, font=FO, top=None, last=(255, 214, 0)),
 'neon':        dict(tint=(120, 0, 160), ta=.18, fill=[(140, 255, 255), (60, 220, 255)], stroke=None, glow=(255, 40, 200), font=FO, top=None, last=(255, 120, 230)),
 'chrome':      dict(tint=(60, 70, 90), ta=.15, fill=[(255, 255, 255), (120, 130, 150)], stroke=None, glow=(150, 190, 255), font=FO, top=None),
 'sunset':      dict(tint=(255, 90, 30), ta=.20, fill=[(255, 255, 255), (255, 235, 210)], stroke=(120, 30, 0), glow=(255, 110, 20), font=FM, top=None),
}[ST]
src = Image.open(SRC).convert('RGB').resize((W, H))
def fit(t, f, maxw, s):
    while ImageFont.truetype(f, s).getlength(t) > maxw: s -= 4
    return ImageFont.truetype(f, s)

def grad_fill(mask, c1, c2, y0, y1):
    yy = np.linspace(0, 1, H)[:, None]; t = np.clip((yy * H - y0) / max(1, y1 - y0), 0, 1)
    arr = np.zeros((H, W, 3), np.uint8)
    for ch in range(3): arr[:, :, ch] = (c1[ch] + (c2[ch] - c1[ch]) * t).astype(np.uint8).repeat(W, 1)
    if ST in ('gold', 'chrome'):   # металлический блеск полосами
        s = (np.sin(np.arange(H) / 30.0) * 0.5 + 0.5)[:, None]
        for ch in range(3): arr[:, :, ch] = (c2[ch] + (c1[ch] - c2[ch]) * s).astype(np.uint8).repeat(W, 1)
    im = Image.fromarray(arr).convert('RGBA'); im.putalpha(mask); return im

def lines_of(lines, y, size):
    """Шрифты строк с учётом ширины (значок Instagram справа вверху) — список (строка, шрифт, bbox)."""
    items = []
    for ln in lines:
        f = fit(ln, P['font'], 930, size); bb = f.getbbox(ln); h = bb[3] - bb[1]
        mw = CS.maxw_at(y, h, 930)
        if mw < 930: f = fit(ln, P['font'], mw, f.size); bb = f.getbbox(ln); h = bb[3] - bb[1]
        items.append((ln, f, bb)); y += h + 26
    return items

def need(lines, size, y0):
    if not lines: return lambda s: 0
    return lambda s: sum(b[3] - b[1] for _, _, b in lines_of(lines, y0, max(40, int(size * s)))) + 26 * (len(lines) - 1)

def block(lines, y, size, top_style=None, last_hl=False):
    items = lines_of(lines, y, size)
    for k, (ln, f, bb) in enumerate(items):
        w, h = bb[2] - bb[0], bb[3] - bb[1]; x = (W - w) / 2 - bb[0]
        if top_style:
            pc = (0, 0, 0, 235) if top_style == 'plate_black' else (25, 70, 200, 240)
            pl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(pl).rounded_rectangle([(W - w) / 2 - 34, y - 20, (W + w) / 2 + 34, y + h + 22], 16, fill=pc)
            img.alpha_composite(pl.rotate(-2, center=(W / 2, y + h / 2), resample=Image.BICUBIC))
            ImageDraw.Draw(img).text((x, y - bb[1]), ln, font=f, fill=(255, 255, 255))
        else:
            m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).text((x, y - bb[1]), ln, font=f, fill=255)
            last = P.get('last') and k == len(items) - 1 and last_hl
            if P['glow']:
                g = Image.new('RGBA', (W, H), P['glow'] + (0,)); g.putalpha(m.filter(ImageFilter.GaussianBlur(26)).point(lambda a: a * 220 // 255)); img.alpha_composite(g)
            if P['stroke']:
                sm = Image.new('L', (W, H), 0); ImageDraw.Draw(sm).text((x, y - bb[1]), ln, font=f, fill=255, stroke_width=max(8, f.size // 16), stroke_fill=255)
                sl = Image.new('RGBA', (W, H), P['stroke'] + (255,)); sl.putalpha(sm)
                sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(sm.filter(ImageFilter.GaussianBlur(10)).point(lambda a: a * 150 // 255))
                img.alpha_composite(sh, (0, 10)); img.alpha_composite(sl)
            else:
                sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(7)).point(lambda a: a * 220 // 255)); img.alpha_composite(sh, (0, 10))
            c1, c2 = (P['last'], P['last']) if last else P['fill']
            img.alpha_composite(grad_fill(m, c1, c2, y, y + h))
        y += h + 26

# Раскладка по лицу (31.10.2026, скрин сетки Instagram): верх над головой, низ строго под подбородком,
# не помещается — всё над головой; низ не ниже 1450, верхние строки не залезают под значок ролика.
def make_img(src):
    global img
    img = ImageEnhance.Color(ImageEnhance.Contrast(src).enhance(1.12)).enhance(1.08)
    if P['ta']: img = Image.blend(img, Image.new('RGB', (W, H), P['tint']), P['ta'])
    v = Image.new('L', (W, H), 0); ImageDraw.Draw(v).ellipse([-250, 250, W + 250, H - 350], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(220))
    img = Image.composite(img, Image.new('RGB', (W, H)), v.point(lambda x: 70 + x * 185 // 255)).convert('RGBA')

TL = [l.upper() for l in TOP.split('|') if l]; BL = [l.upper() for l in BOT.split('|') if l]
src, Z, PL = CS.prepare(src, need(TL, 200, CS.SAFE_TOP), need(BL, 230, 900))
make_img(src)
block(TL, PL['y_top'], int(200 * PL['s_top']), top_style=P['top'])
block(BL, PL['y_bot'], int(230 * PL['s_bot']), last_hl=True)
CS.report(Z, PL, OUT)
img.convert('RGB').save(OUT, quality=94)
