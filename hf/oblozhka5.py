# 11.11.2026 (решение Евгения 21:20): НОВЫЙ НАБОР ИЗ 5 ОБЛОЖЕК вместо стиля В и набора 08.11.
# Рисует готовую обложку 1080x1920 поверх кадра (cover_bg.png из scripts/pick_frame.py).
#
#   python3 hf/oblozhka5.py <cover_bg.png> <out.png> <novyj.json> [ключ ролика]
#
# Стиль берётся из novyj → cover.s5, иначе сам по тегу ролика:
#   shapka  — ЦВЕТНАЯ ШАПКА (основная): верх залит цветом рубрики до макушки, top — мелкая строка, bot — крупная белая
#   spina   — ТЕКСТ ЗА СПИНОЙ: огромное слово cover.word за головой (фигура поверх по маске rembg), top — жёлтая плашка, bot — от руки
#   hormozi — СТИЛЬ ХОРМОЗИ: на груди top белая / первое слово-строка bot на зелёной плашке / остаток bot мелко
#   novost  — НОВОСТНАЯ МОЛНИЯ: метка cover.label («ВАЖНО» по умолчанию), тёмная полоса: top белая, bot жёлтая
#   chb     — Ч/Б + КРАСНОЕ СЛОВО: кадр ч/б, top — белая строка над головой, bot — крупно красным на груди
# Автовыбор: тег НОВ → novost, ПУТЬ / ХРОН → chb, cover.word задан → spina, иначе shapka.
# Правила: текст никогда на лице и голове, весь текст в полосе y 300–1450 (сетка профиля 3:4), главное слово крупно.
# 13.11.2026 (Евгений, скрин сетки Instagram 18:29): «сильно мелко» — все 5 стилей КРУПНЕЕ (×1.2–1.3, минимумы выше),
# новость: метка «НОВОСТЬ · <top>», bot одной жёлтой строкой во всю ширину (230 → не меньше 110), полоса сразу под подбородком, низ не ниже 1500
# (ниже — счётчик просмотров в сетке).
import os, sys, json, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

W, H = 1080, 1920
Y0, Y1 = 300, 1500   # 13.11.2026: низ 1450 → 1500 (в сетке 3:4 видно до 1680, счётчик просмотров ниже 1560)
YN = 1500   # низ полосы новости: выше счётчика просмотров в сетке
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = os.path.join(ROOT, "fonts")

BG, OUT, SPEC = sys.argv[1], sys.argv[2], sys.argv[3]
KEY = sys.argv[4] if len(sys.argv) > 4 else os.path.splitext(os.path.basename(SPEC))[0]
spec = json.load(open(SPEC)) if os.path.exists(SPEC) else {}
cov = spec.get("cover") or {}


def up(s): return re.sub(r"\s+", " ", (s or "").replace("|", " ").strip()).upper()


TOP = up(cov.get("top"))
BOTL = [x.strip().upper() for x in (cov.get("bot") or "").split("|") if x.strip()]
BOT = " ".join(BOTL)
WORD = up(cov.get("word"))

tag = re.split(r"[ _\-]", os.path.basename(KEY).replace("Шортс ", ""))[0].upper()
S5 = (cov.get("s5") or "").lower()
if not S5:
    S5 = "novost" if tag in ("НОВ", "НОВОСТЬ") else "chb" if tag in ("ПУТЬ", "ХРОН") else "spina" if WORD else "shapka"
if S5 == "spina" and not WORD:
    S5 = "shapka"
if not TOP and not BOT:
    BOT = up(cov.get("text")) or "СМОТРИТЕ ДО КОНЦА"

RUBR = {"ЖИЗНЬ": "#ff5a1f", "НЕДВ": "#1d5fd1", "ВНЖ": "#e3191c", "БИЗ": "#13a865", "ПУТЕШ": "#13a865",
        "АВТО": "#7b3fe4", "СК": "#0fa3a3", "МОНТАЖ": "#7b3fe4", "НОВ": "#e3191c", "ПУТЬ": "#ff5a1f"}
HEAD = cov.get("color") or RUBR.get(tag, "#ff5a1f")
# 14.11.2026 (Евгений 22:55): шапка только красная или синяя, чередуем по ролику (стабильно по ключу), свой цвет — cover.color
import zlib
def _shapka_col():
    if cov.get("shapka_color"): return cov["shapka_color"]   # ручной цвет; старое cover.color (цвета рубрик) не берём
    k = os.path.splitext(os.path.basename(KEY))[0]
    try:   # по порядку роликов в novyj (имя = время записи): красный, синий, красный…
        keys = sorted(os.path.splitext(x)[0] for x in os.listdir(os.path.join(ROOT, "novyj")) if x.endswith(".json"))
        i = keys.index(k)
    except Exception:
        i = zlib.crc32(k.encode())
    return "#e3191c" if i % 2 == 0 else "#1d5fd1"
SHAPKA_COL = _shapka_col()


def font(name, size, wght=None):
    f = ImageFont.truetype(os.path.join(FD, name), size)
    if wght is not None:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f


MONT = lambda s: font("montserrat-900.ttf", s)
UNB = lambda s: font("unbounded-800.ttf", s)
OSW = lambda s: font("oswald-700.ttf", s)
RUSSO = lambda s: font("russo-one.ttf", s)
RUB = lambda s, w=900: font("rubik-var.ttf", s, w)
CAV = lambda s: font("caveat-var.ttf", s, 700)


def tsize(d, t, f):
    b = d.textbbox((0, 0), t, font=f)
    return b[2] - b[0], b[3] - b[1], b


def fit(d, t, mk, start, maxw, minsz=30):
    s = start
    while s > minsz and tsize(d, t, mk(s))[0] > maxw: s -= 3
    return mk(s)


def ctext(d, y, t, f, fill, stroke=0, sf="black"):
    w, h, b = tsize(d, t, f)
    d.text(((W - w) // 2 - b[0], y - b[1]), t, font=f, fill=fill, stroke_width=stroke, stroke_fill=sf)
    return h


def split2(t, d, mk, start, maxw):
    """Одна строка, если влезает крупно; иначе две по словам."""
    if tsize(d, t, mk(int(start * 0.72)))[0] <= maxw or " " not in t: return [t]
    f = mk(start)
    ws = t.split(); best = None
    for i in range(1, len(ws)):
        a, b = " ".join(ws[:i]), " ".join(ws[i:])
        m = max(tsize(d, a, f)[0], tsize(d, b, f)[0])
        if best is None or m < best[0]: best = (m, [a, b])
    return best[1]


# ---------- кадр и лицо ----------
src = Image.open(BG).convert("RGB")
if src.size != (W, H):
    s = max(W / src.width, H / src.height)
    src = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
    l, t = (src.width - W) // 2, (src.height - H) // 2
    src = src.crop((l, t, l + W, t + H))
src = ImageEnhance.Contrast(src).enhance(1.08)
src = ImageEnhance.Color(src).enhance(1.12)

import cv2
hx = os.environ.get("HAAR") or os.path.join(ROOT, "scripts", "haar.xml")
if not os.path.exists(hx): hx = os.path.join(ROOT, "models", "haar.xml")
if not os.path.exists(hx): hx = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
g = cv2.cvtColor(np.array(src), cv2.COLOR_RGB2GRAY)
fs = cv2.CascadeClassifier(hx).detectMultiScale(g, 1.1, 5, minSize=(120, 120))
if len(fs):
    fx, fy, fw, fh = max(fs, key=lambda r: r[2] * r[3])
    HEAD_TOP = int(fy - 0.20 * fh); CHIN = int(fy + 0.93 * fh)
else:
    fx, fw = 300, 480; HEAD_TOP, CHIN = 560, 1170
HEAD_TOP = max(HEAD_TOP, 200)
# 13.11.2026 (Евгений 20:23): ролик на две камеры — лицо маленьким окошком сверху (top_px в novyj), на весь кадр улица.
# Окошко не закрываем: весь текст опускается ниже окошка, на середину кадра.
WIN = int(spec.get("top_px") or 0)
if WIN and (not len(fs) or fw < 330):
    Y0 = WIN + 30; HEAD_TOP = Y0 + 520; CHIN = Y0 + 540
    print(f"oblozhka5: окошко с лицом сверху до {WIN} — текст ниже окошка")
else:
    WIN = 0
print(f"oblozhka5: стиль {S5}, рубрика {tag}, макушка {HEAD_TOP}, подбородок {CHIN}")

ABOVE = (Y0, HEAD_TOP - 20)                 # над головой
CHEST = (max(CHIN + 25, 900), Y1)           # грудь
above_ok = ABOVE[1] - ABOVE[0] >= 110


def chest_block(lines, sizes_fn):
    """Подбирает общий масштаб, чтобы блок строк влез в грудную зону; возвращает y начала и шрифты."""
    for k in [1.0, 0.92, 0.84, 0.76, 0.68, 0.6]:
        fonts = sizes_fn(k)
        hs = [tsize(ImageDraw.Draw(src), t, f)[1] for t, f in zip(lines, fonts)]
        tot = sum(hs) + 22 * (len(lines) - 1)
        if tot <= CHEST[1] - CHEST[0]: return CHEST[0], fonts, hs
    return CHEST[0], fonts, hs


im = src.copy().convert("RGBA")
d = ImageDraw.Draw(im)
# 15.11.2026 (Евгений 00:40): читаемость «за спиной», «Хормози», «Ч/Б» — варианты a/b (OBL_VAR), пусто — как было
VAR = (os.environ.get("OBL_VAR") or cov.get("var") or "").lower()


def soft_shadow(y, t, f, stroke=0, off=8, blur=10, alpha=180, x=None):
    global im, d
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    if x is None: ctext(sd, y + off, t, f, (0, 0, 0, alpha), stroke, (0, 0, 0, alpha))
    else:
        b = sd.textbbox((0, 0), t, font=f); sd.text((x - b[0], y + off - b[1]), t, font=f, fill=(0, 0, 0, alpha), stroke_width=stroke, stroke_fill=(0, 0, 0, alpha))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur))); d = ImageDraw.Draw(im)


def stext(y, t, f, fill, stroke=8, sf="#0b0d12"):
    """Текст с обводкой и мягкой тенью — читается на любом фоне."""
    soft_shadow(y, t, f, stroke)
    ctext(d, y, t, f, fill, stroke, sf)
    return tsize(d, t, f)[1]


def plate(y, t, f, bg, fg, px=30, py=18, r=14, alpha=255):
    """Текст на плашке по центру. Возвращает полную высоту плашки."""
    global im, d
    w, h, b = tsize(d, t, f); x = (W - w) // 2
    if alpha < 255 or bg.startswith("#0b"):
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        c = tuple(int(bg.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)
        od.rounded_rectangle([x - px, y - py, x + w + px, y + h + py], radius=r, fill=c)
        im.alpha_composite(ov); d = ImageDraw.Draw(im)
    else:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([x - px, y - py + 8, x + w + px, y + h + py + 8], radius=r, fill=(0, 0, 0, 120))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10))); d = ImageDraw.Draw(im)
        d.rounded_rectangle([x - px, y - py, x + w + px, y + h + py], radius=r, fill=bg)
    d.text((x - b[0], y - b[1]), t, font=f, fill=fg)
    return h + 2 * py


# 15.11.2026 (Евгений 01:00): утверждённые цвета — Ч/Б оранжевый, «за спиной» оранжевый, Хормози синяя плашка
KK = "#0b0d12"
ORANGE, ORANGE2, BLUE, NAVY = "#ff7a00", "#ff9a2e", "#1f4fff", "#123a8c"


def tline(y, t, f, fill="white", stroke=None, sw=0, plate=None):
    """Строка по центру: обводка + мягкая тень, либо цветная плашка с тенью. Возвращает высоту блока."""
    global im, d
    w, h, b = tsize(d, t, f); x = (W - w) // 2
    px, py = int(h * 0.32) + 14, int(h * 0.22) + 10
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    if plate:
        sd.rounded_rectangle([x - px, y - py + 10, x + w + px, y + h + py + 10], radius=16, fill=(0, 0, 0, 130))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12))); d = ImageDraw.Draw(im)
        d.rounded_rectangle([x - px, y - py, x + w + px, y + h + py], radius=16, fill=plate)
        d.text((x - b[0], y - b[1]), t, font=f, fill=fill)
        return h + 2 * py
    sd.text((x - b[0], y + 10 - b[1]), t, font=f, fill=(0, 0, 0, 170), stroke_width=sw, stroke_fill=(0, 0, 0, 170))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12))); d = ImageDraw.Draw(im)
    d.text((x - b[0], y - b[1]), t, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke or KK)
    return h

if S5 == "shapka":
    small = TOP if BOT else ""
    big = BOT or TOP
    top = HEAD_TOP - 25
    bl = split2(big, d, lambda s: UNB(s), 148, W - 80)
    fb = fit(d, max(bl, key=len), UNB, 148, W - 80, 64)
    # 14.11.2026: мелкая строка крупнее; чёрточки по бокам, если влезает не меньше 76, иначе без чёрточек по ширине кадра
    def fit_small(start):
        f = fit(d, small, UNB, start, W - 420, 76)
        if tsize(d, small, f)[0] <= W - 420: return f, True
        return fit(d, small, UNB, start, W - 80, 48), False
    fsm, DASH = fit_small(112) if small else (None, False)
    hb = tsize(d, "ЁЙ", fb)[1]; hs = tsize(d, "ЁЙ", fsm)[1] if fsm else 0
    need = hb * len(bl) + 18 * (len(bl) - 1) + (hs + 30 if fsm else 0) + 40
    if top - Y0 < need:                      # голова высоко — шапка ниже не опускается, уменьшаем
        for k in (0.9, 0.8, 0.7, 0.6):
            fb = fit(d, max(bl, key=len), UNB, int(148 * k), W - 80, 52); hb = tsize(d, "ЁЙ", fb)[1]
            if fsm: fsm, DASH = fit_small(max(76, int(112 * k))); hs = tsize(d, "ЁЙ", fsm)[1]
            need = hb * len(bl) + 18 * (len(bl) - 1) + (hs + 30 if fsm else 0) + 40
            if top - Y0 >= need: break
        top = max(top, Y0 + need)
    if WIN:                                  # полоса посередине, под окошком с лицом
        top = Y0 + need + 30
        d.rectangle([0, Y0, W, top], fill=SHAPKA_COL)
    else:
        d.rectangle([0, 0, W, top], fill=SHAPKA_COL)
    y = top - 40 - (hb * len(bl) + 18 * (len(bl) - 1)) - (hs + 30 if fsm else 0)
    # 14.11.2026 (Евгений 22:55, вариант 3): мелкая строка жёлтая с чёрточками по бокам, главная жёлтая с мягкой тенью
    def shadow_text(y, t, f, fill, blur=10, off=8, alpha=170):
        global im, d
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ctext(ImageDraw.Draw(sh), y + off, t, f, (0, 0, 0, alpha))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur))); d = ImageDraw.Draw(im)
        ctext(d, y, t, f, fill)
    if fsm:
        w_, h_, _ = tsize(d, small, fsm); cx0 = (W - w_) // 2; my = y + h_ // 2
        if DASH:
            d.rounded_rectangle([cx0 - 150, my - 4, cx0 - 40, my + 4], radius=4, fill="#ffd400")
            d.rounded_rectangle([cx0 + w_ + 40, my - 4, cx0 + w_ + 150, my + 4], radius=4, fill="#ffd400")
        shadow_text(y, small, fsm, "#ffd400", 6, 4, 140); y += hs + 30
    for ln in bl: shadow_text(y, ln, fb, "#ffd400"); y += hb + 18

elif S5 == "spina":
    try:
        from rembg import remove, new_session
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "rembg", "onnxruntime"], check=True)
        from rembg import remove, new_session
    mask = remove(src, session=new_session("u2net_human_seg"), only_mask=True).convert("L").filter(ImageFilter.GaussianBlur(1.5))
    m = np.array(mask) > 128
    rows = np.where(m[:, max(0, fx - 60):fx + fw + 60].any(axis=1))[0]
    if len(rows): HEAD_TOP = int(rows[0])
    f = fit(d, WORD, MONT, 430, W - 40, 120)
    w, h, b = tsize(d, WORD, f)
    y = max(Y0, HEAD_TOP + int(h * 0.38) - h)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    ctext(sd, y + 8, WORD, f, (0, 0, 0, 140))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(im)
    if VAR in ("old",):
        ctext(d, y, WORD, f, "white")
    else:   # 15.11.2026: слово оранжевое с чёрной обводкой и тенью
        tline(y, WORD, f, ORANGE, KK, 12)
    person = src.convert("RGBA"); person.putalpha(mask); im.alpha_composite(person)
    d = ImageDraw.Draw(im)
    y0 = max(CHEST[0] + 15, 960)
    for k in (1, .92, .84, .76, .68, .6):   # всё на груди влезает выше Y1, ни одна строка не пропадает
        f1 = fit(d, TOP, MONT, int(110 * k), W - 110, 48) if TOP else None
        f2 = fit(d, BOT, MONT, int(100 * k), W - 70, 44) if BOT else None
        h1 = int(tsize(d, TOP, f1)[1] * 1.44) + 20 if TOP else 0
        h2 = tsize(d, BOT, f2)[1] if BOT else 0
        if y0 + h1 + 34 + h2 <= Y1: break
    y = y0
    if TOP:
        y += tline(y + int(tsize(d, TOP, f1)[1] * .22) + 10, TOP, f1, "white", plate=NAVY) + 34
    if BOT:
        tline(y, BOT, f2, ORANGE2, KK, 9)

elif S5 == "hormozi":
    # 15.11.2026 (Евгений 01:00, «синяя плашка»): верх белый с обводкой, главное — белым на синей плашке,
    # хвост — оранжевый с обводкой. Грудь тесная — верх крупно над головой, низ одной строкой на синей плашке.
    l1 = TOP or (BOTL[0] if len(BOTL) > 1 else "")
    rest = BOTL if TOP else BOTL[1:]
    l2 = rest[0] if rest else BOT
    l3 = " ".join(rest[1:]) if len(rest) > 1 else ""
    yc = max(CHEST[0] + 5, 980)
    tight = Y1 - yc < 330
    if l1 and above_ok:
        f1 = fit(d, l1, MONT, 130 if tight else 112, W - 100, 56); h1 = tsize(d, l1, f1)[1]
        while h1 + 40 > ABOVE[1] - ABOVE[0] and f1.size > 56: f1 = MONT(f1.size - 6); h1 = tsize(d, l1, f1)[1]
        tline(ABOVE[1] - h1 - 40, l1, f1, "white", KK, 9); l1 = ""
    if tight and l3:
        l2, l3 = f"{l2} {l3}", ""
    parts = [x for x in (l1, l2, l3) if x]
    for k in (1, .92, .84, .76, .68, .6, .52):
        fs_ = []
        for t in parts:
            base = 160 if t == l2 else 112
            fs_.append(fit(d, t, MONT, int(base * k), W - (150 if t == l2 else 110), 44))
        hs_ = [int(tsize(d, t, f)[1] * (1.44 if t == l2 else 1)) + (20 if t == l2 else 0) for t, f in zip(parts, fs_)]
        if yc + sum(hs_) + 40 * (len(parts) - 1) <= Y1 + 30: break
    y = yc
    for t, f, hh in zip(parts, fs_, hs_):
        if t == l2: tline(y + int(tsize(d, t, f)[1] * .22) + 10, t, f, "white", plate=BLUE)
        elif t == l1: tline(y, t, f, "white", KK, 9)
        else: tline(y, t, f, ORANGE2, KK, 9)
        y += hh + 40

elif S5 == "novost":
    # 13.11.2026: крупно. Метка «НОВОСТЬ · <top>», bot — жёлтым во всю ширину, полоса сразу под подбородком
    lab = up(cov.get("label")) or "ВАЖНО"
    lines = BOTL or ([TOP] if TOP else [])
    if TOP and BOTL: lab = f"{lab} · {TOP}"
    tf = fit(d, lab, OSW, 66, W - 230, 44); w, h, b = tsize(d, lab, tf)
    lab_in_band = not above_ok
    if not lab_in_band:
        ly = Y0 + 40
        d.rectangle([40, ly, 40 + w + 104, ly + h + 36], fill="#e3191c")
        d.ellipse([64, ly + (h + 36) // 2 - 13, 90, ly + (h + 36) // 2 + 13], fill="white")
        d.text((112 - b[0], ly + 18 - b[1]), lab, font=tf, fill="white")
    one = " ".join(lines)
    f1 = fit(d, one, OSW, 230, W - 90, 60)
    if f1.size >= 150 or len(lines) == 1 and " " not in one:
        rows = [one]; f = f1
    else:
        rows = lines if len(lines) > 1 else split2(one, d, OSW, 200, W - 90)
        f = fit(d, max(rows, key=len), OSW, 200, W - 90, 60)
    def band(fnt):
        hh_ = tsize(d, "ЁЙ", fnt)[1]
        lh = (tsize(d, "ЁЙ", tf)[1] + 26) if lab_in_band else 0
        return hh_, lh, 48 + lh + hh_ * len(rows) + 22 * (len(rows) - 1)
    hh, lh, bh = band(f)
    top = max(CHIN + 10, 820)
    while top + bh > YN and f.size > 110:
        f = OSW(f.size - 6); hh, lh, bh = band(f)
    if top + bh > YN: top = max(700, YN - bh)
    bot = top + bh
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).rectangle([0, top, W, bot], fill=(10, 12, 16, 235))
    im.alpha_composite(ov); d = ImageDraw.Draw(im)
    d.rectangle([0, top, 24, bot], fill="#e3191c")
    y = top + 24
    if lab_in_band:
        _, _, bb = tsize(d, lab, tf); d.text((60 - bb[0], y - bb[1]), lab, font=tf, fill="white"); y += lh
    for t in rows:
        _, _, bb = tsize(d, t, f); d.text((56 - bb[0], y - bb[1]), t, font=f, fill="#ffd400"); y += hh + 22

elif S5 == "chb":
    gimg = ImageEnhance.Contrast(ImageOps.grayscale(src)).enhance(1.35).convert("RGBA")
    im = gimg; d = ImageDraw.Draw(im)
    red = BOT or TOP
    small = TOP if BOT else ""
    # 15.11.2026 (Евгений 01:00, «оранжевый»): верх белый с чёрной обводкой, главное — оранжевое с чёрной обводкой
    fs_ = None
    if small:
        fs_ = fit(d, small, MONT, 110, W - 140, 56)
        hs0 = tsize(d, small, fs_)[1]
        if above_ok:
            while hs0 + 60 > ABOVE[1] - ABOVE[0] and fs_.size > 56: fs_ = MONT(fs_.size - 6); hs0 = tsize(d, small, fs_)[1]
            tline(ABOVE[1] - hs0 - 50, small, fs_, "white", KK, 9)
    rl = split2(red, d, RUSSO, 190, W - 90)
    f = fit(d, max(rl, key=len), RUSSO, 190, W - 90, 70)
    hh = tsize(d, "ЁЙ", f)[1]
    y = max(CHEST[0] + 15, 1000) + (0 if above_ok or not small else tsize(d, small, fs_)[1] + 36)
    while y + hh * len(rl) + 18 * (len(rl) - 1) > Y1 and f.size > 70:
        f = RUSSO(f.size - 6); hh = tsize(d, "ЁЙ", f)[1]
    f1 = fit(d, red, RUSSO, 190, W - 90, 60)
    if len(rl) > 1 and f1.size > f.size: rl, f = [red], f1; hh = tsize(d, "ЁЙ", f)[1]
    if not above_ok and small: tline(max(CHEST[0] + 15, 1000), small, fs_, "white", KK, 9)
    for ln in rl: tline(y, ln, f, ORANGE, KK, 11); y += hh + 18

im.convert("RGB").save(OUT)
print("oblozhka5: готово", OUT)
