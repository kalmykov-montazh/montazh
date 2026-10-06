# Плашки для экспертных роликов (проба 06.10.2026): карточки цифр, закона, списка, штрафа.
# Рисует PNG с прозрачным фоном по описанию plashki/<ключ>/spec.json.
# Запуск: python scripts/plashki.py plashki/<ключ>
# spec.json: {"cards": [{"name": "a1", "rows": [[стиль, текст], ...]} | {"name": "c2", "list": {...}}]}
# Стили строк: title (белый, мелкий заголовок), big (жёлтый, крупно), bigred (красный, крупно),
#   strike (серый зачёркнутый), text (белый), small (серый мелкий), redtext (красный текст)
# Список: {"title": "...", "items": ["...", ...], "active": номер (с 0), "done": сколько уже прошли}
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

D = '/usr/share/fonts/opentype/inter/'
def F(w, s): return ImageFont.truetype(D + f'Inter-{w}.otf', s)
W = 960                     # ширина карточки, px (кадр 1080)
PAD = 44
BG = (14, 14, 18, 225)      # тёмная подложка
YEL = (255, 214, 0, 255)
RED = (255, 59, 48, 255)
GRN = (46, 216, 80, 255)
WHT = (255, 255, 255, 255)
GRY = (170, 170, 178, 255)
STY = {
    'title':   (F('ExtraBold', 44), WHT),
    'big':     (F('Black', 128), YEL),
    'bigred':  (F('Black', 118), RED),
    'mid':     (F('Black', 76), YEL),
    'strike':  (F('Black', 76), GRY),
    'text':    (F('Bold', 50), WHT),
    'redtext': (F('ExtraBold', 52), RED),
    'small':   (F('SemiBold', 40), GRY),
}
GAP = 18

def wrap(d, txt, font, maxw):
    out, cur = [], ''
    for w in txt.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= maxw or not cur: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out

PH = 240                    # высота фото в карточке, px
SRC = ''                    # папка, куда сервер скачал фото с Диска (plashki/<ключ>/src)
def photo(path):
    # фото с Диска (путь внутри «Монтаж!») — сервер скачал его в SRC под тем же именем; обрезка «по центру» под W×PH
    im = Image.open(os.path.join(SRC, os.path.basename(path))).convert('RGB')
    k = max(W / im.width, PH / im.height)
    im = im.resize((int(im.width * k + 0.5), int(im.height * k + 0.5)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - PH) // 2
    return im.crop((x, y, x + W, y + PH))

def card_rows(rows):
    tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    ph = None
    if rows and rows[0][0] == 'photo':   # фото — только первой строкой, во всю ширину карточки сверху
        ph = photo(rows[0][1]); rows = rows[1:]
    lines = []
    for st, txt in rows:
        font, col = STY[st]
        for ln in wrap(tmp, txt, font, W - 2 * PAD):
            bb = tmp.textbbox((0, 0), ln, font=font)
            lines.append((st, ln, font, col, bb))
    top = PH if ph else 0
    h = top + PAD * 2 + sum(b[3] - b[1] for *_, b in lines) + GAP * (len(lines) - 1)
    im = Image.new('RGBA', (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), 36, fill=BG)
    if ph:   # фото со скруглёнными верхними углами
        m = Image.new('L', (W, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, W - 1, PH + 40), 36, fill=255)
        m = m.crop((0, 0, W, PH)); im.paste(ph, (0, 0), m)
    y = top + PAD
    for st, ln, font, col, bb in lines:
        tw = d.textlength(ln, font=font)
        x = (W - tw) / 2
        d.text((x, y - bb[1]), ln, font=font, fill=col)
        if st == 'strike':   # красная черта поперёк
            my = y + (bb[3] - bb[1]) / 2
            d.line((x - 10, my, x + tw + 10, my), fill=RED, width=10)
        y += bb[3] - bb[1] + GAP
    return im

def card_list(spec):
    tf, itf = F('ExtraBold', 44), F('Bold', 50)
    tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    NUMW = 78
    items = [wrap(tmp, t, itf, W - 2 * PAD - NUMW - 10) for t in spec['items']]
    LH = 62
    tb = tmp.textbbox((0, 0), spec['title'], font=tf)
    h = PAD * 2 + (tb[3] - tb[1]) + 30 + sum(len(x) * LH + 22 for x in items) - 22
    im = Image.new('RGBA', (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, h - 1), 36, fill=BG)
    d.text(((W - d.textlength(spec['title'], font=tf)) / 2, PAD - tb[1]), spec['title'], font=tf, fill=YEL)
    y = PAD + (tb[3] - tb[1]) + 30
    act, done = spec.get('active', 0), spec.get('done', spec.get('active', 0))
    for i, lines in enumerate(items):
        bh = len(lines) * LH
        if i == act:   # активный пункт — жёлтая плашка, текст чёрный
            d.rounded_rectangle((PAD - 18, y - 10, W - PAD + 18, y + bh + 4), 18, fill=YEL)
            col, ncol, mark = (12, 12, 12, 255), (12, 12, 12, 255), str(i + 1)
        elif i < done:
            col, ncol, mark = WHT, GRN, '✓'
        else:
            col, ncol, mark = GRY, GRY, str(i + 1)
        nf = F('Black', 54)
        if mark == '✓':   # галочка рисуется линиями (в Inter её может не быть)
            d.line((PAD + 6, y + 30, PAD + 24, y + 48, PAD + 56, y + 8), fill=GRN, width=10, joint='curve')
        else:
            d.text((PAD, y - 4), mark, font=nf, fill=ncol)
        for k, ln in enumerate(lines):
            d.text((PAD + NUMW, y + k * LH), ln, font=itf, fill=col)
        y += bh + 22
    return im

def main(folder):
    global SRC
    SRC = os.path.join(folder, 'src')
    spec = json.load(open(os.path.join(folder, 'spec.json'), encoding='utf-8'))
    for c in spec['cards']:
        im = card_list(c['list']) if 'list' in c else card_rows(c['rows'])
        p = os.path.join(folder, c['name'] + '.png')
        im.save(p)
        print(p, im.size)

if __name__ == '__main__':
    main(sys.argv[1])
