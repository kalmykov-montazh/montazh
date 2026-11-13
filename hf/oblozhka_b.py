# 13.11.2026 (Евгений, 20:38): обложка «Б» для шортсов из лонгов и старого монтажа.
# Тёмный фон, сверху заголовок (белая + жёлтая строка), справа лицо из кадра ролика, слева карточка-картинка
# по теме (наклон, белая рамка, тень), внизу жёлтая плашка. Весь текст в полосе 300–1500 (сетка 3:4).
#   python3 hf/oblozhka_b.py <кадр.png> <картинка.jpg|-> <out.png> "<l1>" "<l2>" "<плашка>"
# Кадр выбирает scripts/pick_frame.py (глаза открыты, рот закрыт); лицо ищется здесь же, кроп вокруг лица,
# поэтому надписи и слайды старого монтажа в обложку не попадают.
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

W, H = 1080, 1920
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = os.path.join(ROOT, "fonts")
FR, PIC, OUT, L1, L2, PL = sys.argv[1:7]
YEL = "#ffd400"
UNB = lambda s: ImageFont.truetype(os.path.join(FD, "unbounded-800.ttf"), s)
MON = lambda s: ImageFont.truetype(os.path.join(FD, "montserrat-900.ttf"), s)


def fit(d, t, mk, start, maxw, mn=40):
    s = start
    while s > mn and d.textbbox((0, 0), t, font=mk(s))[2] > maxw: s -= 3
    return mk(s)


def ctext(d, y, t, f, fill):
    b = d.textbbox((0, 0), t, font=f)
    d.text(((W - (b[2] - b[0])) // 2 - b[0], y - b[1]), t, font=f, fill=fill)
    return b[3] - b[1]


# фон: тёмно-синий с мягким светом справа
bg = Image.new("RGB", (W, H), "#0d1220")
glow = Image.new("L", (W, H), 0); ImageDraw.Draw(glow).ellipse((380, 520, 1300, 1500), fill=110)
bg.paste(Image.new("RGB", (W, H), "#24324f"), (0, 0), glow.filter(ImageFilter.GaussianBlur(160)))

# лицо
src = Image.open(FR).convert("RGB")
if src.size != (W, H):
    s = max(W / src.width, H / src.height)
    src = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
    src = src.crop(((src.width - W) // 2, (src.height - H) // 2, (src.width - W) // 2 + W, (src.height - H) // 2 + H))
hx = os.environ.get("HAAR") or os.path.join(ROOT, "scripts", "haar.xml")
g = cv2.cvtColor(np.array(src), cv2.COLOR_RGB2GRAY)
fs = cv2.CascadeClassifier(hx).detectMultiScale(g, 1.1, 5, minSize=(60, 60))
if len(fs):
    fx, fy, fw, fh = max(fs, key=lambda r: r[2] * r[3])
else:
    fx, fy, fw, fh = 340, 600, 400, 400
    print("oblozhka_b: лицо не найдено — кроп по центру")
# кроп: голова и плечи, лицо ~38% ширины кропа
cw = int(fw / 0.40); chh = int(cw * 1.18)
cx = fx + fw // 2; top = fy - int(fh * 0.55)
box = (cx - cw // 2, top, cx + cw // 2, top + chh)
pad = Image.new("RGB", (W * 3, H * 3), "#0d1220"); pad.paste(src, (W, H))
face = pad.crop((box[0] + W, box[1] + H, box[2] + W, box[3] + H))
face = ImageEnhance.Contrast(face).enhance(1.06)
FW = 720; face = face.resize((FW, int(FW * chh / cw)), Image.LANCZOS)
FY0 = 560; fh_ = min(face.height, 1390 - FY0)
face = face.crop((0, 0, FW, fh_))
m = Image.new("L", face.size, 255); md = ImageDraw.Draw(m)
for i in range(140): md.line((i, 0, i, face.height), fill=int(255 * i / 140))           # мягкий левый край
for i in range(70): md.line((0, i, FW, i), fill=min(255, int(255 * i / 70)))             # и верх
bg.paste(face, (W - FW, FY0), m)

d = ImageDraw.Draw(bg)
# заголовок
y = 330
f1 = fit(d, L1, UNB, 96, W - 80, 50); y += ctext(d, y, L1, f1, "white") + 24
f2 = fit(d, L2, UNB, 96, W - 80, 50); ctext(d, y, L2, f2, YEL)

# карточка-картинка
if PIC != "-" and os.path.exists(PIC):
    try:
        p = ImageOps.exif_transpose(Image.open(PIC)).convert("RGB")
        p = ImageOps.fit(p, (400, 400), Image.LANCZOS)
        card = Image.new("RGB", (424, 424), "white"); card.paste(p, (12, 12))
        cm = Image.new("L", card.size, 0); ImageDraw.Draw(cm).rounded_rectangle((0, 0, 423, 423), radius=30, fill=255)
        card.putalpha(cm)
        card = card.rotate(7, expand=True, resample=Image.BICUBIC)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sm = Image.new("L", card.size, 0); sm.paste(card.split()[3], (0, 0))
        sh.paste((0, 0, 0, 170), (40, 790), sm.filter(ImageFilter.GaussianBlur(18)))
        bgr = bg.convert("RGBA"); bgr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6))); bgr.alpha_composite(card, (20, 760))
        bg = bgr.convert("RGB"); d = ImageDraw.Draw(bg)
    except Exception as e:
        print("oblozhka_b: картинка не встала:", e)

# жёлтая плашка
fp = fit(d, PL, MON, 86, W - 120, 46)
b = d.textbbox((0, 0), PL, font=fp); tw, th = b[2] - b[0], b[3] - b[1]
y0 = 1392; x0 = (W - tw) // 2 - 30
d.rounded_rectangle((x0, y0, x0 + tw + 60, y0 + th + 44), radius=14, fill=YEL)
d.text((x0 + 30 - b[0], y0 + 22 - b[1]), PL, font=fp, fill="black")
bg.save(OUT)
print("oblozhka_b: готово", OUT)
