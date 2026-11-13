# 13.11.2026 (Евгений, скрин сетки Instagram: «сильно мелко», выбран вариант «Б: крупно»): слайды карусели 1080×1350.
#   python3 scripts/karusel/slajdy.py spec.json out_dir
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
import os, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1350
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FD = os.path.join(ROOT, "fonts")
YEL = (255, 214, 0)


def F(size): return ImageFont.truetype(os.path.join(FD, "montserrat-800.ttf"), size)


def fit(d, t, size, maxw, minsz=40):
    while size > minsz and d.textbbox((0, 0), t, font=F(size))[2] > maxw: size -= 3
    return F(size)


def bg(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    return ImageOps.fit(im, (W, H), Image.LANCZOS)


def shade(im, top):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for y in range(top, H):
        a = min(240, int(240 * (y - top) / 220))
        od.line((0, y, W, y), fill=(14, 14, 16, a))
    im = im.convert("RGBA"); im.alpha_composite(ov); return im


def plashka(d, txt):
    f = F(52); b = d.textbbox((0, 0), txt, font=f)
    d.rounded_rectangle((40, 90, 40 + b[2] + 56, 90 + 86), radius=12, fill=YEL)
    d.text((68, 133), txt, font=f, fill="black", anchor="lm")


def main(spec, out):
    sp = json.load(open(spec)); base = os.path.dirname(os.path.abspath(spec))
    os.makedirs(out, exist_ok=True)
    for i, s in enumerate(sp["slides"], 1):
        im = bg(os.path.join(base, s["photo"]))
        x = 50
        if i == 1:
            im = shade(im, 620); d = ImageDraw.Draw(im)
            if sp.get("plashka"): plashka(d, sp["plashka"])
            y = 820
            d.rectangle((x, y, x + 130, y + 14), fill=YEL); y += 40
            fb = fit(d, s.get("big", ""), 150, W - 100, 90); d.text((x, y), s.get("big", ""), font=fb, fill="white"); y += fb.size + 20
            if s.get("title"):
                ft = fit(d, s["title"], 84, W - 100, 50); d.text((x, y), s["title"], font=ft, fill="white"); y += ft.size + 30
            if s.get("price"):
                fp = fit(d, s["price"], 80, W - 160, 50); bw = d.textbbox((0, 0), s["price"], font=fp)[2]
                d.rounded_rectangle((x - 10, y, x + bw + 34, y + fp.size + 34), radius=12, fill=YEL)
                d.text((x + 12, y + 17 + fp.size // 2), s["price"], font=fp, fill="black", anchor="lm")
        else:
            im = shade(im, 760); d = ImageDraw.Draw(im)
            y = 950
            d.rectangle((x, y, x + 110, y + 12), fill=YEL); y += 36
            ft = fit(d, s.get("title", ""), 92, W - 100, 50)
            d.text((x, y), s.get("title", ""), font=ft, fill=YEL if s.get("last") else "white"); y += ft.size + 24
            if s.get("sub"):
                fs = fit(d, s["sub"], 54, W - 100, 34); d.text((x, y), s["sub"], font=fs, fill=(235, 235, 235))
        im.convert("RGB").save(os.path.join(out, f"{i:02d}.jpg"), quality=92)
        print("слайд", i)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
