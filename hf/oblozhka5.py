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

if S5 == "shapka":
    small = TOP if BOT else ""
    big = BOT or TOP
    top = HEAD_TOP - 25
    bl = split2(big, d, lambda s: UNB(s), 148, W - 80)
    fb = fit(d, max(bl, key=len), UNB, 148, W - 80, 64)
    fsm = fit(d, small, UNB, 70, W - 120, 44) if small else None
    hb = tsize(d, "ЁЙ", fb)[1]; hs = tsize(d, "ЁЙ", fsm)[1] if fsm else 0
    need = hb * len(bl) + 18 * (len(bl) - 1) + (hs + 24 if fsm else 0) + 40
    if top - Y0 < need:                      # голова высоко — шапка ниже не опускается, уменьшаем
        for k in (0.9, 0.8, 0.7, 0.6):
            fb = fit(d, max(bl, key=len), UNB, int(148 * k), W - 80, 52); hb = tsize(d, "ЁЙ", fb)[1]
            if fsm: fsm = UNB(max(40, int(70 * k))); hs = tsize(d, "ЁЙ", fsm)[1]
            need = hb * len(bl) + 18 * (len(bl) - 1) + (hs + 24 if fsm else 0) + 40
            if top - Y0 >= need: break
        top = max(top, Y0 + need)
    d.rectangle([0, 0, W, top], fill=HEAD)
    y = top - 40 - (hb * len(bl) + 18 * (len(bl) - 1)) - (hs + 24 if fsm else 0)
    if fsm: ctext(d, y, small, fsm, "#111"); y += hs + 24
    for ln in bl: ctext(d, y, ln, fb, "white"); y += hb + 18

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
    d = ImageDraw.Draw(im); ctext(d, y, WORD, f, "white")
    person = src.convert("RGBA"); person.putalpha(mask); im.alpha_composite(person)
    d = ImageDraw.Draw(im)
    y = CHEST[0]
    if TOP:
        fp = fit(d, TOP, lambda s: RUB(s), 96, W - 140, 48)
        tw, th, tb = tsize(d, TOP, fp)
        bx = (W - tw - 68) // 2
        d.rounded_rectangle([bx, y, bx + tw + 68, y + th + 44], radius=12, fill="#ffd400")
        d.text((bx + 34 - tb[0], y + 22 - tb[1]), TOP, font=fp, fill="black")
        y += th + 44 + 22
    if BOT and y < Y1 - 60:
        ctext(d, y, BOT.lower(), fit(d, BOT.lower(), CAV, 140, W - 80, 64), "white", 5, "#111")

elif S5 == "hormozi":
    l1 = TOP or (BOTL[0] if len(BOTL) > 1 else "")
    rest = BOTL if TOP else BOTL[1:]
    l2 = rest[0] if rest else BOT
    l3 = " ".join(rest[1:]) if len(rest) > 1 else ""
    lines = [x for x in (l1, l2, l3) if x]
    def sz(k):
        out = []
        for i, t in enumerate(lines):
            base = 124 if t != l3 or not l3 else 80
            out.append(fit(d, t, MONT, int(base * k), W - 90, 44))
        return out
    y, fonts, hs = chest_block(lines, sz)
    # 13.11.2026: на груди тесно (шрифт сжался) — первая белая строка уходит над голову крупно, на груди остальное
    if len(lines) > 1 and above_ok and fonts[0].size < 112:
        t0 = lines[0]; f0 = fit(d, t0, MONT, 124, W - 90, 52)
        h0 = tsize(d, t0, f0)[1]
        if h0 + 40 <= ABOVE[1] - ABOVE[0]:
            ctext(d, ABOVE[1] - h0 - 30, t0, f0, "white", 10)
            lines = lines[1:]; l1 = ""
            y, fonts, hs = chest_block(lines, lambda k: [fit(d, t, MONT, int((124 if t != l3 or not l3 else 84) * k), W - 90, 44) for t in lines])
    for t, f, h in zip(lines, fonts, hs):
        if t == l2:
            w, _, b = tsize(d, t, f); x = (W - w) // 2
            d.rounded_rectangle([x - 22, y - 14, x + w + 22, y + h + 16], radius=10, fill="#2ee66b")
            d.text((x - b[0], y - b[1]), t, font=f, fill="black")
        else:
            ctext(d, y, t, f, "white", 10)
        y += h + 30

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
    if small:
        fs_ = fit(d, small, lambda s: RUB(s, 800), 96, W - 80, 48)
        if above_ok: ctext(d, ABOVE[1] - tsize(d, small, fs_)[1] - 30, small, fs_, "white")
    rl = split2(red, d, RUSSO, 190, W - 50)
    f = fit(d, max(rl, key=len), RUSSO, 190, W - 50, 70)
    hh = tsize(d, "ЁЙ", f)[1]
    y = CHEST[0] + (0 if above_ok or not small else tsize(d, small, fs_)[1] + 30)
    while y + hh * len(rl) + 16 * (len(rl) - 1) > Y1 and f.size > 70:   # 13.11.2026: не вылезать ниже полосы
        f = RUSSO(f.size - 6); hh = tsize(d, "ЁЙ", f)[1]
    f1 = fit(d, red, RUSSO, 190, W - 50, 60)                              # одной строкой крупнее? — берём одну
    if len(rl) > 1 and f1.size > f.size: rl, f = [red], f1; hh = tsize(d, "ЁЙ", f)[1]
    if not above_ok and small: ctext(d, CHEST[0], small, fs_, "white")
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    yy = y
    for ln in rl: ctext(sd, yy + 10, ln, f, (0, 0, 0, 200)); yy += hh + 16
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14))); d = ImageDraw.Draw(im)
    for ln in rl: ctext(d, y, ln, f, "#ff1f1f"); y += hh + 16

im.convert("RGB").save(OUT)
print("oblozhka5: готово", OUT)
