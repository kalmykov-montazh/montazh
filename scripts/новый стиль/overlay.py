#!/usr/bin/env python3
"""Накладывает на смонтированный ролик субтитры и плашки в выбранном стиле.
python3 overlay.py base.mp4 words_out.json spec.json STYLE out.mp4 [t_from t_to]
STYLE: card | redkey | mix | karaoke
Все элементы проходят проверку: целиком в кадре, отступы SAFE.
"""
import json, re, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE, WORDS, SPEC, STYLE, OUT = sys.argv[1:6]
T_FROM = float(sys.argv[6]) if len(sys.argv) > 6 else 0
T_TO = float(sys.argv[7]) if len(sys.argv) > 7 else 1e9
W, H, FPS = 1080, 1920, 30
SAFE_L, SAFE_R, SAFE_T, SAFE_B = 56, 56, 150, 380   # сверху шапка соцсетей, снизу подпись/кнопки
F = '/root/.fonts/'
def font(name, size): return ImageFont.truetype(F + name, size)
M9, M8, OSW, UNB, PLF = 'montserrat-900.ttf', 'montserrat-800.ttf', 'oswald-700.ttf', 'unbounded-800.ttf', 'playfair-display-800.ttf'

words = json.load(open(WORDS))
if isinstance(words, list) and words and 'keep' in words[0]:   # plan.json: слова с пунктуацией
    words = [{'w': w['w'].strip(), 's': round(w['os'], 3), 'e': round(w['oe'], 3)} for p in words if p['keep'] for w in p['words'] if w['w'].strip() not in ('-', '—', '–')]
spec = json.load(open(SPEC))
total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', BASE],
                             capture_output=True, text=True).stdout)
FIXW = spec.get('fix', {})
for w in words:
    k = w['w']
    if k in FIXW: w['w'] = FIXW[k]
KEYS = set(x.lower() for x in spec.get('keys', []))   # слова-акценты

THEME = {
    'light': dict(card=(255, 255, 255, 250), text=(18, 18, 22), dim=0.55, lab=[(70, 110, 150), (150, 30, 40)], stamp=(150, 30, 40), arrow=(150, 30, 40)),
    'dark': dict(card=(24, 24, 28, 245), text=(255, 255, 255), dim=0.55, lab=[(90, 90, 96), (225, 30, 40)], stamp=(225, 30, 40), arrow=(225, 30, 40)),
    'yellow': dict(card=(255, 255, 255, 250), text=(18, 18, 22), dim=0.55, lab=[(30, 30, 30), (240, 190, 0)], stamp=(240, 190, 0), arrow=(240, 190, 0)),
}[spec.get('theme', {'card': 'light', 'redkey': 'dark', 'mix': 'light', 'karaoke': 'yellow'}[STYLE])]


def shadow_wrap(img, rad=14, off=(0, 8), alpha=90):
    """тень под элементом"""
    pad = rad * 2 + max(abs(off[0]), abs(off[1]))
    big = Image.new('RGBA', (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new('RGBA', img.size, (0, 0, 0, 255)); sh.putalpha(a)
    big.paste(sh, (pad + off[0], pad + off[1]), sh)
    big = big.filter(ImageFilter.GaussianBlur(rad))
    big.alpha_composite(img, (pad, pad))
    return big


def wrap(text, fnt, maxw):
    out, cur = [], ''
    for wd in text.split():
        t = (cur + ' ' + wd).strip()
        if fnt.getlength(t) <= maxw or not cur: cur = t
        else: out.append(cur); cur = wd
    if cur: out.append(cur)
    return out


# ---------- плашки сверху ----------
def card_img(text, label=None, lab_i=0, size=48, maxw=300, kind='card'):
    th = THEME
    f = font(M9, size)
    lines = wrap(text, f, maxw)
    lh = int(size * 1.08)
    tw = max(f.getlength(l) for l in lines)
    lf = font(M9, 22)
    labh = 40 if label else 0
    cw = int(max(tw, lf.getlength(label or '') + 30) + 56)
    ch = int(len(lines) * lh + labh + 44)
    im = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], 26, fill=th['card'])
    y = 22
    if label:
        lw = int(lf.getlength(label.upper())) + 26
        d.rounded_rectangle([(cw - lw) // 2, y, (cw + lw) // 2, y + 32], 16, fill=th['lab'][lab_i])
        d.text((cw // 2, y + 16), label.upper(), font=lf, fill='white', anchor='mm')
        y += labh + 2
    for l in lines:
        d.text((cw // 2, y + lh // 2), l, font=f, fill=th['text'], anchor='mm'); y += lh
    return shadow_wrap(im)


def stamp_img(text, size=58):
    th = THEME
    f = font(M9, size)
    tw = int(f.getlength(text.upper()))
    cw, ch = tw + 50, size + 34
    im = Image.new('RGBA', (cw + 20, ch + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, cw + 9, ch + 9], 10, fill=th['stamp'])
    d.rounded_rectangle([18, 18, cw + 1, ch + 1], 7, outline=(255, 255, 255, 230), width=3)
    d.text(((cw + 20) // 2, (ch + 20) // 2 + 2), text.upper(), font=f, fill='white', anchor='mm')
    return shadow_wrap(im.rotate(-4, resample=Image.BICUBIC, expand=True), rad=10, off=(0, 6))


def arrow_img(r=30):
    th = THEME
    im = Image.new('RGBA', (r * 2 + 8, r * 2 + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([4, 4, r * 2 + 4, r * 2 + 4], fill=th['arrow'], outline='white', width=5)
    c = r + 4
    d.line([c - 12, c, c + 11, c], fill='white', width=6)
    d.polygon([(c + 14, c), (c + 2, c - 11), (c + 2, c + 11)], fill='white')
    return im


def big_img(text, size=150, color=None):
    """крупная цифра/слово сверху (5 лет, 40°)"""
    th = THEME
    f = font(M9, size)
    sub = None
    if '|' in text: text, sub = text.split('|', 1)
    tw = f.getlength(text)
    sf = font(M9, 40)
    cw = int(max(tw, sf.getlength(sub or '')) + 80); ch = int(size * 1.1 + (60 if sub else 0) + 40)
    im = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], 30, fill=th['card'])
    d.text((cw // 2, 20 + size * 0.55), text, font=f, fill=color or th['stamp'], anchor='mm')
    if sub: d.text((cw // 2, ch - 45), sub.upper(), font=sf, fill=th['text'], anchor='mm')
    return shadow_wrap(im)


# элементы из spec: группа = ряд плашек сверху; держится до конца группы
EL = []   # dict(img, x, y, t0, t1, dim_from)
def clampxy(img, cx, cy):
    """центр -> левый верх, строго внутри безопасной зоны"""
    x = int(cx - img.width / 2); y = int(cy - img.height / 2)
    x = max(SAFE_L - 30, min(x, W - SAFE_R + 30 - img.width))   # 30 = поля тени
    y = max(SAFE_T - 30, min(y, H - SAFE_B + 30 - img.height))
    return x, y


def wt(i):   # время слова по номеру
    return words[min(max(i, 0), len(words) - 1)]['s']


def find(phrase, after=0.0):
    """время начала фразы в тексте (первое вхождение после after)"""
    ph = [re.sub(r'[^\wё]', '', x.lower()) for x in phrase.split()]
    lw = [re.sub(r'[^\wё]', '', w['w'].lower()) for w in words]
    for i in range(len(lw)):
        if words[i]['s'] + 0.01 < after: continue
        if all(i + k < len(lw) and lw[i + k].startswith(ph[k][:max(3, len(ph[k]) - 2)]) for k in range(len(ph))):
            return words[i]['s']
    raise SystemExit(f'нет фразы: {phrase}')


def T(v, after=0.0):
    return find(v, after) if isinstance(v, str) else float(v)


TOP_Y = spec.get('top_y', 330)   # центр ряда плашек
for g in spec.get('groups', []):
    items = g['items']
    t_end = T(g['end']) if 'end' in g else None
    # готовим картинки
    built = []
    last = 0.0
    for it in items:
        t0 = T(it['at'], last); last = t0
        if it['type'] == 'card':
            im = card_img(it['text'], it.get('label'), it.get('lab', 0), it.get('size', 46), it.get('maxw', 270))
        elif it['type'] == 'arrow':
            im = arrow_img()
        elif it['type'] == 'stamp':
            im = stamp_img(it['text'])
        elif it['type'] == 'big':
            im = big_img(it['text'], it.get('size', 150))
        built.append((it, im, t0))
    for k in range(len(built)):   # стрелка появляется вместе со следующей плашкой
        if built[k][0]['type'] == 'arrow':
            nxt = [b for b in built[k + 1:] if b[0]['type'] in ('card', 'big')]
            if nxt: built[k] = (built[k][0], built[k][1], nxt[0][2])
    if t_end is None: t_end = built[-1][2] + 3.0
    # раскладка ряда: карточки и стрелки в линию, по центру кадра, при переполнении — уменьшаем
    row = [(it, im, t0) for it, im, t0 in built if it['type'] in ('card', 'arrow', 'big')]
    def gaps(r): return [(-34 if 'arrow' in (r[k][0]['type'], r[k + 1][0]['type']) else 18) for k in range(len(r) - 1)]
    tot = sum(im.width for _, im, _ in row) + sum(gaps(row))
    avail = W - SAFE_L - SAFE_R + 60
    sc = min(1.0, avail / tot) if tot else 1
    if sc < 1:
        row = [(it, im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS), t0) for it, im, t0 in row]
        tot = sum(im.width for _, im, _ in row) + sum(gaps(row))
    off = g.get('shift', 0)   # лесенка: группа левее/правее, но в кадре
    x = W / 2 - tot / 2 + off
    x = max(SAFE_L - 30, min(x, W - SAFE_R + 30 - tot))
    cards_t = []
    rowmaxh = max((im.height for _, im, _ in row), default=0)
    gl = gaps(row) + [0]
    for k_, (it, im, t0) in enumerate(row):
        gap = gl[k_]
        dy = it.get('dy', 0)
        y = TOP_Y - im.height / 2 + dy
        if it['type'] == 'arrow': y = TOP_Y - im.height / 2
        px, py = clampxy(im, x + im.width / 2, y + im.height / 2)
        EL.append(dict(img=im, x=px, y=py, t0=t0, t1=t_end, kind=it['type']))
        if it['type'] == 'card': cards_t.append((len(EL) - 1, t0))
        x += im.width + gap
    # предыдущие карточки тускнеют, когда появляется следующая
    for k in range(len(cards_t) - 1):
        EL[cards_t[k][0]]['dim'] = cards_t[k + 1][1]
    for it, im, t0 in built:
        if it['type'] == 'stamp':
            cx = W / 2 + off + it.get('dx', 0)
            px, py = clampxy(im, cx, TOP_Y + rowmaxh / 2 * sc - 14 + it.get('dy', 0))
            EL.append(dict(img=im, x=px, y=py, t0=t0, t1=t_end, kind='stamp'))

EL.sort(key=lambda e: {'card': 0, 'big': 0, 'arrow': 1, 'stamp': 2}[e['kind']])
# проверка: всё в кадре
for e in EL:
    assert e['x'] >= 0 and e['y'] >= 0 and e['x'] + e['img'].width <= W and e['y'] + e['img'].height <= H, ('вылезает', e)

# ---------- субтитры ----------
SUB_Y = spec.get('sub_y', 1330)
def phrases(maxc=22):
    out, cur = [], []
    for i, w in enumerate(words):
        ends = bool(re.search(r'[.?!:,]$', w['w']))
        if cur and ((len(' '.join(x['w'] for x in cur + [w])) > maxc and not (ends and len(' '.join(x['w'] for x in cur + [w])) <= maxc + 9)) or w['s'] - cur[-1]['e'] > 0.35):
            out.append(cur); cur = []
        cur.append(w)
        if re.search(r'[.?!:]$', w['w']) or (w['w'].endswith(',') and len(' '.join(x['w'] for x in cur)) > 12):
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out


def norm(w): return re.sub(r'[^\wё]', '', w.lower())


def iskey(w): return norm(w['w']) in KEYS or re.search(r'\d', w['w'])


SUBCACHE = {}
def sub_card(ph, cur=None):
    """белая карточка, чёрный текст (как в приложении); karaoke — текущее слово на жёлтом"""
    key = ('c', id(ph[0]), cur)
    if key in SUBCACHE: return SUBCACHE[key]
    f = font(M9, 56)
    txt = [w['w'] for w in ph]
    lines = wrap(' '.join(txt), f, 800)
    lh = 66
    tw = max(f.getlength(l) for l in lines)
    cw, ch = int(tw + 56), len(lines) * lh + 30
    im = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], 18, fill=(255, 255, 255, 248))
    y = 15; wi = 0
    for l in lines:
        x = (cw - f.getlength(l)) / 2
        for k, wd in enumerate(l.split()):
            ww = f.getlength(wd)
            col = (18, 18, 22)
            if STYLE == 'karaoke':
                if cur is not None and wi == cur:
                    d.rounded_rectangle([x - 8, y + 2, x + ww + 8, y + lh - 2], 10, fill=(255, 205, 0))
                elif cur is not None and wi > cur:
                    col = (170, 170, 175)
            d.text((x, y + lh / 2), wd, font=f, fill=col, anchor='lm')
            x += ww + f.getlength(' '); wi += 1
        y += lh
    im = shadow_wrap(im, rad=10, off=(0, 5), alpha=70)
    SUBCACHE[key] = im
    return im


def outline_text(d, xy, text, f, fill, sw=0, anchor='mm'):
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=(0, 0, 0, 255) if sw else None)


def sub_redkey(ph):
    """мелкий белый текст + одно крупное красное слово"""
    key = ('r', id(ph[0]))
    if key in SUBCACHE: return SUBCACHE[key]
    ki = None
    for i, w in enumerate(ph):
        if iskey(w): ki = i; break
    small = font(M8, 44); big = font(M9, 104)
    im = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if ki is None:
        outline_text(d, (W / 2, 150), ' '.join(w['w'] for w in ph), small, 'white', 3)
    else:
        a = ' '.join(w['w'] for w in ph[:ki]); b = ' '.join(w['w'] for w in ph[ki + 1:])
        kw = re.sub(r'[,.]$', '', ph[ki]['w'])
        while big.getlength(kw) > W - 160: big = font(M9, big.size - 6)
        if a: outline_text(d, (W / 2, 70), a, small, 'white', 3)
        outline_text(d, (W / 2, 150), kw, big, (235, 35, 45), 4)
        if b: outline_text(d, (W / 2, 232), b, small, 'white', 3)
    im = shadow_wrap(im.crop(im.getbbox() or (0, 0, 1, 1)), rad=8, off=(0, 4), alpha=110)
    SUBCACHE[key] = im
    return im


MIXSTY = [   # микс в духе «кинетики»: разные шрифты, размеры, цвета, места
    dict(fn=OSW, sz=118, col=(255, 214, 0), up=True, al='l'),
    dict(fn=M9, sz=64, col=(255, 255, 255), up=False, al='c'),
    dict(fn=UNB, sz=74, col=(255, 255, 255), up=True, al='r'),
    dict(fn=PLF, sz=86, col=(255, 214, 0), up=False, al='c'),
]
def sub_mix(ph, idx, upto):
    """слова появляются по одному; ключевые — крупнее и жёлтым"""
    key = ('m', id(ph[0]), upto)
    if key in SUBCACHE: return SUBCACHE[key]
    s = MIXSTY[idx % len(MIXSTY)]
    has_key = any(iskey(w) for w in ph)
    if has_key and s['fn'] in (M9,): s = MIXSTY[0]
    toks = [(w['w'].upper() if s['up'] else w['w'], iskey(w)) for w in ph]
    lines, cur, curw = [], [], 0
    maxw = W - SAFE_L - SAFE_R - 40
    for t, k in toks:
        f = font(s['fn'], int(s['sz'] * (1.25 if k else 1)))
        ww = f.getlength(t + ' ')
        if cur and curw + ww > maxw: lines.append(cur); cur, curw = [], 0
        cur.append((t, k, f)); curw += ww
    if cur: lines.append(cur)
    hh = sum(max(f.size for _, _, f in l) * 1.05 for l in lines)
    im = Image.new('RGBA', (W, int(hh) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y = 20; n = 0
    for l in lines:
        lw = sum(f.getlength(t + ' ') for t, _, f in l)
        x = {'l': SAFE_L + 10, 'c': (W - lw) / 2, 'r': W - SAFE_R - 10 - lw}[s['al']]
        lh = max(f.size for _, _, f in l) * 1.05
        for t, k, f in l:
            if n <= upto:
                col = (255, 214, 0) if k and s['col'] == (255, 255, 255) else ((255, 255, 255) if k else s['col'])
                d.text((x, y + lh * 0.82), t, font=f, fill=col, anchor='ls', stroke_width=max(3, f.size // 18), stroke_fill=(0, 0, 0))
            x += f.getlength(t + ' '); n += 1
        y += lh
    im = shadow_wrap(im.crop(im.getbbox() or (0, 0, 1, 1)), rad=10, off=(0, 6), alpha=120)
    SUBCACHE[key] = im
    return im


PH = phrases(26 if STYLE == 'redkey' else 22)
PHT = [(p[0]['s'], (PH[i + 1][0]['s'] if i + 1 < len(PH) and PH[i + 1][0]['s'] - p[-1]['e'] < 0.6 else p[-1]['e'] + 0.25), p) for i, p in enumerate(PH)]
MIX_Y = [1260, 1180, 1330, 1220]   # микс: высота меняется от фразы к фразе


def ease_back(x):
    x = min(1, max(0, x)); c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def paste(fr, im, x, y, alpha=1.0, scale=1.0):
    if scale != 1.0:
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        x += (im.width - nw) / 2; y += (im.height - nh) / 2
        im = im.resize((nw, nh), Image.BILINEAR)
    if alpha < 1.0:
        a = im.split()[3].point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    x, y = int(x), int(y)
    x = max(0, min(x, W - im.width)); y = max(0, min(y, H - im.height))   # страховка: никогда не за кадр
    fr.alpha_composite(im, (x, y))


def draw(fr, t):
    for e in EL:
        if not (e['t0'] <= t < e['t1'] + 0.2): continue
        a = min(1, (t - e['t0']) / 0.12)
        if t > e['t1']: a *= max(0, 1 - (t - e['t1']) / 0.2)
        if e.get('dim') and t >= e['dim']: a *= THEME['dim'] + (1 - THEME['dim']) * max(0, 1 - (t - e['dim']) / 0.2)
        sc = 0.55 + 0.45 * ease_back((t - e['t0']) / 0.28)
        if e['kind'] == 'stamp': sc = 1.6 - 0.6 * min(1, (t - e['t0']) / 0.15)
        paste(fr, e['img'], e['x'], e['y'], a, sc)
    for i, (t0, t1, ph) in enumerate(PHT):
        if not (t0 <= t < t1): continue
        cur = max([k for k, w in enumerate(ph) if w['s'] <= t] or [0])
        if STYLE in ('card', 'karaoke'):
            im = sub_card(ph, cur if STYLE == 'karaoke' else None)
            sc = 0.9 + 0.1 * ease_back((t - t0) / 0.18)
            paste(fr, im, (W - im.width) / 2, SUB_Y - im.height / 2, min(1, (t - t0) / 0.08), sc)
        elif STYLE == 'redkey':
            im = sub_redkey(ph)
            paste(fr, im, (W - im.width) / 2, SUB_Y - im.height / 2, min(1, (t - t0) / 0.08), 0.92 + 0.08 * ease_back((t - t0) / 0.2))
        elif STYLE == 'mix':
            im = sub_mix(ph, i, cur)
            y = MIX_Y[i % len(MIX_Y)] - im.height / 2
            paste(fr, im, (W - im.width) / 2, y, 1.0, 1.0)


t_to = min(T_TO, total)
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(T_FROM), '-to', str(t_to), '-i', BASE, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-ss', str(T_FROM), '-to', str(t_to), '-i', BASE, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
                        '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                        '-c:a', 'copy', '-movflags', '+faststart', '-shortest', OUT], stdin=subprocess.PIPE)
n = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    fr = Image.frombytes('RGB', (W, H), buf).convert('RGBA')
    draw(fr, T_FROM + n / FPS)
    enc.stdin.write(fr.convert('RGB').tobytes())
    n += 1
enc.stdin.close(); enc.wait(); dec.wait()
print('ok', OUT, n, 'кадров', len(EL), 'плашек', len(PH), 'фраз')
