# 13.11.2026 (Евгений, скрин сетки Instagram: «сильно мелко», выбран вариант «Б: крупно»): слайды карусели 1080×1350.
#   python3 scripts/karusel/slajdy.py spec.json out_dir            ← карусель 4:5 (01.jpg …)
#   python3 scripts/karusel/slajdy.py spec.json out_dir --reel     ← 16.11.2026: слайды для рилса 1080×1920 (во весь экран)
# spec.json:
# {"plashka": "АРЕНДА · ВАЛЕНСИЯ",
#  "slides": [
#    {"photo": "kuhnya.jpg", "big": "60 м²", "title": "свежий ремонт", "price": "1 250 € / месяц"},   ← первый (обложка)
#    {"photo": "spalnya.jpg", "title": "Спальня", "sub": "двуспальная кровать, шкаф"},              ← остальные
#    {"photo": "x.jpg", "title": "1 250 € в месяц", "sub": "WhatsApp +34 …  · код EM083", "last": true}]}
# Правила крупного текста (Б): на первом огромное «big» (метры/цифра) 150, под ним title 84, цена на жёлтой плашке 80;
# на остальных title 92, sub 54. Текст в нижней части на тёмном градиенте, не ниже 1270 (в сетке 3:4 обрезает ~70 сверху
# и снизу, слева внизу счётчик просмотров — последний ряд держим выше 1180). Плашка сверху жёлтая 52.
# Номер «1/7» и «Листайте» больше не пишем: значок карусели в сетке уже показывает, что слайдов несколько.
#
# 16.11.2026 (Евгений 21:34, Facebook у рилса «Зима в Валенсии» написал «качество контента: видео с неполным
# заполнением экрана» и занизил показ): рилсы больше НЕ собираем из слайда 4:5 с размытыми полосами.
# --reel рисует те же слайды сразу 1080×1920: фото на весь кадр, текст в безопасной зоне Reels —
# не выше 260 (шапка), не ниже 1480 (подпись, имя, музыка), справа 170 свободно (кнопки лайк/коммент).
import os, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageOps

YEL = (255, 214, 0)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FD = os.path.join(ROOT, "fonts")

# размеры: карусель 4:5 и рилс 9:16
FMT = {
    "45":  dict(W=1080, H=1350, x=50, right=50, plashka_y=90, first_top=820, other_top=950, bottom=None),
    "916": dict(W=1080, H=1920, x=60, right=170, plashka_y=260, first_top=None, other_top=None, bottom=1480),
}


def F(size): return ImageFont.truetype(os.path.join(FD, "montserrat-800.ttf"), size)


def fit(d, t, size, maxw, minsz=40):
    while size > minsz and d.textbbox((0, 0), t, font=F(size))[2] > maxw: size -= 3
    return F(size)


def wrap2(d, t, size, maxw, minsz):
    """16.11: на узком рилсе длинную строку не ужимать до мелочи — перенос на 2 строки."""
    f = F(size)
    if d.textbbox((0, 0), t, font=f)[2] <= maxw or " " not in t: return [t], fit(d, t, size, maxw, minsz)
    w = t.split(); best = None
    ok = lambda k: w[k][:1].isalpha() and w[k] not in ("м²", "м2") and w[k - 1] not in ("—", "·", "-")
    cand = [k for k in range(1, len(w)) if ok(k)] or list(range(1, len(w)))   # числа и «€» не разрываем
    for k in cand:
        a, b = " ".join(w[:k]), " ".join(w[k:])
        m = max(d.textbbox((0, 0), a, font=f)[2], d.textbbox((0, 0), b, font=f)[2])
        if best is None or m < best[0]: best = (m, [a, b])
    lines = best[1]
    s = size
    while s > minsz and max(d.textbbox((0, 0), l, font=F(s))[2] for l in lines) > maxw: s -= 3
    return lines, F(s)


def bg(path, W, H):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    return ImageOps.fit(im, (W, H), Image.LANCZOS)


def shade(im, top, W, H, bottom=None):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for y in range(max(0, top), H):
        a = min(240, int(240 * (y - top) / 220))
        od.line((0, y, W, y), fill=(14, 14, 16, a))
    im = im.convert("RGBA"); im.alpha_composite(ov); return im


def plashka(d, txt, y0, maxw):
    f = fit(d, txt, 52, maxw - 56, 34); b = d.textbbox((0, 0), txt, font=f)
    d.rounded_rectangle((40, y0, 40 + b[2] + 56, y0 + 86), radius=12, fill=YEL)
    d.text((68, y0 + 43), txt, font=f, fill="black", anchor="lm")


def layout_first(d, s, c, W):
    """Список элементов первого слайда: (тип, текст/строки, шрифт, высота)."""
    mw = W - c["x"] - c["right"]; el = [("bar", None, None, 40)]
    lb, fb = wrap2(d, s.get("big", ""), 150, mw, 90) if c["bottom"] else ([s.get("big", "")], fit(d, s.get("big", ""), 150, mw, 90))
    el.append(("txt", lb, fb, len(lb) * (fb.size + 14) + 6, "white"))
    if s.get("title"):
        lt, ft = wrap2(d, s["title"], 84, mw, 50) if c["bottom"] else ([s["title"]], fit(d, s["title"], 84, mw, 50))
        el.append(("txt", lt, ft, len(lt) * (ft.size + 12) + 18, "white"))
    if s.get("price"):
        fp = fit(d, s["price"], 80, mw - 60, 50); el.append(("price", s["price"], fp, fp.size + 34))
    return el


def layout_other(d, s, c, W):
    mw = W - c["x"] - c["right"]; el = [("bar", None, None, 36)]
    t = s.get("title", "")
    lt, ft = wrap2(d, t, 92, mw, 50) if c["bottom"] else ([t], fit(d, t, 92, mw, 50))
    el.append(("txt", lt, ft, len(lt) * (ft.size + 12) + 12, YEL if s.get("last") else "white"))
    if s.get("sub"):
        ls, fs = wrap2(d, s["sub"], 54, mw, 34) if c["bottom"] else ([s["sub"]], fit(d, s["sub"], 54, mw, 34))
        el.append(("txt", ls, fs, len(ls) * (fs.size + 10), (235, 235, 235)))
    return el


def draw(d, el, x, y, first):
    for e in el:
        if e[0] == "bar":
            d.rectangle((x, y, x + (130 if first else 110), y + (14 if first else 12)), fill=YEL)
        elif e[0] == "txt":
            yy = y
            for line in e[1]:
                d.text((x, yy), line, font=e[2], fill=e[4]); yy += e[2].size + (14 if first else 12)
        elif e[0] == "price":
            fp = e[2]; bw = d.textbbox((0, 0), e[1], font=fp)[2]
            d.rounded_rectangle((x - 10, y, x + bw + 34, y + fp.size + 34), radius=12, fill=YEL)
            d.text((x + 12, y + 17 + fp.size // 2), e[1], font=fp, fill="black", anchor="lm")
        y += e[3]
    return y


def render(spec, out, fmt="45"):
    c = FMT[fmt]; W, H = c["W"], c["H"]
    sp = json.load(open(spec, encoding="utf-8")); base = os.path.dirname(os.path.abspath(spec))
    os.makedirs(out, exist_ok=True)
    for i, s in enumerate(sp["slides"], 1):
        im = bg(os.path.join(base, s["photo"]), W, H)
        probe = ImageDraw.Draw(im)
        el = layout_first(probe, s, c, W) if i == 1 else layout_other(probe, s, c, W)
        hgt = sum(e[3] for e in el)
        if c["bottom"]:                                   # рилс: блок текста заканчивается на 1480
            top = c["bottom"] - hgt
        else:
            top = c["first_top"] if i == 1 else c["other_top"]
        im = shade(im, top - (200 if i == 1 else 190), W, H); d = ImageDraw.Draw(im)
        if i == 1 and sp.get("plashka"): plashka(d, sp["plashka"], c["plashka_y"], W - 40 - c["right"])
        draw(d, el, c["x"], top, i == 1)
        im.convert("RGB").save(os.path.join(out, f"{i:02d}.jpg"), quality=92)
        print("слайд", i, fmt)


def main(spec, out):
    render(spec, out, "916" if "--reel" in sys.argv else "45")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
