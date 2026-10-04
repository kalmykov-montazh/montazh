# python3 cover.py frame.png "СТРОКА1|СТРОКА2|СТРОКА3" "СЛОВО_ЖЁЛТЫМ" out.jpg [стиль 1|2|3]
# frame.png — кадр 1080x1920 (из pick_frame.py). Лицо ставится по центру, надпись — над головой.
import sys, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src, text, hl, out = sys.argv[1:5]
style = sys.argv[5] if len(sys.argv) > 5 else '1'
D = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
YEL, BLK, WHT = (255, 214, 0), (12, 12, 12), (255, 255, 255)
F = '/usr/share/fonts/opentype/inter/Inter-Black.otf'

im = Image.open(src).convert('RGB').resize((W, H))
# лицо: крупнее и по центру, глаза примерно на 52% высоты
g = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
fc = cv2.CascadeClassifier(f'{D}/haar.xml')
f = fc.detectMultiScale(g, 1.1, 5, minSize=(60, 60))   # 04.10.2026: в шортсах в полный рост лицо мелкое, 150 его не находил
if not len(f):   # мелкое лицо в кепке и очках — искать мягче
    f = fc.detectMultiScale(g, 1.05, 3, minSize=(40, 40))
FACE = os.environ.get('FACE_JSON')   # запасной вариант: лицо, найденное montage.py по всему ролику
if not len(f) and FACE and os.path.exists(FACE):
    import json
    fj = json.load(open(FACE)); h_ = fj['HN'] * H
    f = [(int(fj['CX'] * W - h_ / 2), int(fj['EYE'] * H - 0.42 * h_), int(h_), int(h_))]
    print('cover: лицо из face.json')
if len(f):
    x, y, w, h = max(f, key=lambda r: r[2] * r[3]); cx, ey = x + w / 2, y + 0.42 * h
    y0_, h0_ = y, h
else:
    cx, ey = W / 2, H * 0.55
lines = [l.strip() for l in text.split('|') if l.strip()]
# надпись — прямо над макушкой, и всё вместе в средней части кадра: в сетке профиля (TikTok, Instagram)
# обложка обрезается сверху и снизу примерно до 3:4, видно только y ~ 250..1670 (с 03.10.2026)
SAFE_T = 270
need = len(lines) * 116 * 1.32 + 40          # высота блока надписи при полном размере шрифта
hh = (0.42 + 0.14) * (h if len(f) else 400)  # от глаз до макушки
z = 1.0   # обложка БЕЗ увеличения: обычный кадр, лицо не крупное (Евгений 03.10.2026; 1.25 давало голову на всю картинку в сетке профиля)
ey_t = max(0.52 * H, min(0.6 * H, SAFE_T + need + z * hh))
tx = min(0, max(W - z * W, W / 2 - z * cx)); ty = min(0, max(H - z * H, ey_t - z * ey))
if z != 1.0 or tx or ty:   # при 1.0 кадр не пересчитываем — без лишнего размытия
    im = im.transform((W, H), Image.AFFINE, (1 / z, 0, -tx / z, 0, 1 / z, -ty / z), Image.BICUBIC)
head_top = int(z * (y - 0.14 * h) + ty) if len(f) else int(H * 0.38)


def fit(d, ln, maxw, size):
    while size > 50:
        fo = ImageFont.truetype(F, size)
        if d.textlength(ln, font=fo) <= maxw: return fo, size
        size -= 4
    return ImageFont.truetype(F, size), size


def words_line(d, x, y, ln, fo, base, hlc, stroke=0, sc=None):
    for wd in ln.split(' '):
        col = hlc if wd.strip('?!.,') == hl else base
        d.text((x, y), wd, font=fo, fill=col, stroke_width=stroke, stroke_fill=sc)
        x += d.textlength(wd + ' ', font=fo)


if style == '3':
    # карточка: фото в белой рамке на размытом фоне, надпись сверху
    bg = im.filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.45))
    d = ImageDraw.Draw(bg); y = 90
    for ln in lines:
        fo, s_ = fit(d, ln, 960, 118)
        words_line(d, (W - d.textlength(ln, font=fo)) / 2, y, ln, fo, WHT, YEL)
        y += int(s_ * 1.1)
    top = y + 40; avail = H - top - 60
    k = avail / H; cw, ch = int(W * k), avail
    if cw > W - 80: cw = W - 80
    card = im.resize((int(W * k), int(H * k))).crop(((int(W * k) - cw) // 2, int(H * k) - ch, (int(W * k) + cw) // 2, int(H * k)))
    mask = Image.new('L', (cw, ch), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw, ch), 46, fill=255)
    frm = Image.new('RGB', (cw + 28, ch + 28), WHT)
    fm = Image.new('L', frm.size, 0); ImageDraw.Draw(fm).rounded_rectangle((0, 0, cw + 28, ch + 28), 58, fill=255)
    bg.paste(frm, ((W - cw - 28) // 2, top - 14), fm); bg.paste(card, ((W - cw) // 2, top), mask)
    im = bg
else:
    d = ImageDraw.Draw(im)
    # мягкое затемнение сверху
    grad = Image.new('L', (1, H))
    for yy in range(H): grad.putpixel((0, yy), int(140 * max(0, 1 - yy / 900)))
    d = ImageDraw.Draw(im)   # затемнение сверху убрано (03.10.2026): давало грязный оттенок фону, надпись и так на плашках
    maxh = max(300, head_top - 20 - SAFE_T)
    size = min(116, int(maxh / (len(lines) * 1.32)))
    y = max(SAFE_T, head_top - 20 - int(len(lines) * size * 1.32))   # низ надписи — над макушкой
    # над головой мало места (снято в полный рост, голова высоко) — надпись на груди, под шеей (Евгений 04.10.2026)
    chest = os.environ.get('COVER_POS') == 'chest' or (os.environ.get('COVER_POS') != 'top' and head_top - 20 - SAFE_T < len(lines) * 90 * 1.32)
    if chest and len(f):
        chin = int(z * (y0_ + 1.05 * h0_) + ty)   # низ подбородка
        size = min(116, int((1670 - chin - 60) / (len(lines) * 1.32)))
        y = chin + 60
        print('cover: надпись на груди', chin)
    for i, ln in enumerate(lines):
        fo, s = fit(d, ln, 900, size)
        tw = d.textlength(ln, font=fo); pad = 26
        if style == '1':      # чёрная плашка, жёлтое слово
            box = ((W - tw) / 2 - pad, y - 8, (W + tw) / 2 + pad, y + s * 1.18)
            d.rounded_rectangle(box, 22, fill=BLK)
            words_line(d, (W - tw) / 2, y, ln, fo, WHT, YEL)
        else:                 # жёлтые наклейки, чёрный текст, лёгкий наклон
            lay = Image.new('RGBA', (int(tw + pad * 2 + 20), int(s * 1.4)), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            fill = WHT if any(wd.strip('?!.,') == hl for wd in ln.split()) else YEL
            ld.rounded_rectangle((10, 4, tw + pad * 2 + 10, s * 1.25), 18, fill=fill)
            ld.text((pad + 10, 0), ln, font=fo, fill=BLK)
            pass   # ровно, без наклона
            im.paste(lay, (int((W - lay.width) / 2), int(y - 10)), lay); d = ImageDraw.Draw(im)
        y += int(s * 1.32)
    if style == '1':          # жёлтая рамка по краю
        d.rounded_rectangle((18, 18, W - 18, H - 18), 48, outline=YEL, width=16)
im.convert("RGB").save(out, quality=96, subsampling=0)
