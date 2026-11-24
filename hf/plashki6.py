# 23.11.2026 (Евгений, 22:00–22:08): ОДИН ФОРМАТ ОБЛОЖКИ НА ВСЕ РОЛИКИ — «яркие плашки как у Гриши».
# Заменяет 5 стилей oblozhka5 и текст стиля «Б». Образец и все пробы: Брокер/Обложки — пробы 23.11 яркие плашки/ (версия 6).
#
#   python3 hf/plashki6.py <cover_bg.png> <out.png> <novyj.json> [ключ]          — кадр ролика целиком (основной путь)
#   import plashki6; plashki6.title([...]) / plashki6.place(...)                   — для обложки «Б» (oblozhka_b.py)
#
# Как выглядит (ЖЁСТКО, всё это Евгений сам забраковал в других вариантах):
# - 2–3 плашки стопкой: синяя (cover.top), жёлтая — главное, самая крупная (cover.bot, 1-я часть), красная (остальное bot)
# - ВСЕ под ОДНИМ наклоном, поднимаются слева направо (3,5°), вплотную, заходят одна на другую; без просветов и чёрточек
# - скругление, перелив цвета сверху вниз, мягкая тень, БЕЗ чёрной обводки; синяя торчит влево, у красной левый край мазком
# - Montserrat 900 курсивом, сужен 0,70 (вытянут вверх); белые буквы с объёмной тенью вниз-вправо; на жёлтой — чёрные
# - жёлтый росчерк по низу красной плашки справа
# РАСКЛАДКА ПО МЕСТУ (Евгений 22:08): надпись не закрывает лицо и главное. Над головой мало места — кадр опускается
# (сверху продлевается стена), не хватает — строки делятся: часть над головой, часть на груди; иначе всё на груди.
# Крупные буквы важнее: сначала разносим строки, и только потом уменьшаем шрифт.
import os, sys, json, re, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 1080, 1920
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = os.path.join(ROOT, "fonts")
TOPY = 270          # сетка профиля 3:4 видна с 240 — верх блока не выше 270 (проба 23.11: синяя строка срезалась)
BOTY = 1420         # низ текста — выше счётчика просмотров в сетке
ANGLE = 3.5

BLUE = ((60, 120, 255), (18, 60, 200), (10, 30, 110))     # верх, низ плашки, тень букв
YEL = ((255, 236, 40), (255, 200, 0), (255, 255, 255, 110))
RED = ((245, 50, 50), (200, 15, 20), (110, 0, 0))
WHT, BLK = (255, 255, 255), (12, 12, 12)
ROLE = {"blue": (WHT, BLUE), "yellow": (BLK, YEL), "red": (WHT, RED)}


def mont(s):
    f = ImageFont.truetype(os.path.join(FD, "montserrat-900.ttf"), s)
    try: f.set_variation_by_axes([900])
    except Exception: pass
    return f


def grad(w, h, top, bot):
    g = Image.new("RGB", (w, h)); d = ImageDraw.Draw(g)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return g


def italic(im, k=0.22):
    w, h = im.size; e = int(k * h)
    return im.transform((w + e, h), Image.AFFINE, (1, k, -e, 0, 1, 0), Image.BICUBIC)


def text_img(text, size, fill, shadow, depth=9):
    f = mont(size)
    l, t, r, b = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=f)
    im = Image.new("RGBA", (r - l + depth + 20, b - t + depth + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(depth, 0, -1):
        d.text((10 - l + i, 10 - t + i), text, font=f, fill=shadow)
    d.text((10 - l, 10 - t), text, font=f, fill=fill)
    im = im.resize((max(1, int(im.width * 0.70)), im.height), Image.LANCZOS)
    return italic(im)


def plate(text, role, width, maxsize, padx=30, pady=16, radius=20, brush=False, seed=1):
    fill, (top, bot, shadow) = ROLE[role]
    size = maxsize
    while True:
        ti = text_img(text, size, fill, shadow)
        if ti.width <= width - padx * 2 or size < 40: break
        size -= 3
    pw, ph = width, ti.height + pady * 2
    m = 60
    mask = Image.new("L", (pw + m * 2, ph + m * 2), 0); d = ImageDraw.Draw(mask)
    d.rounded_rectangle([m, m, m + pw, m + ph], radius, fill=255)
    if brush:   # левый край мазком: щетинки разной длины
        rnd = random.Random(seed)
        for i in range(9):
            y0 = m + ph * i / 9; y1 = m + ph * (i + 1) / 9 + 2; ln = rnd.uniform(10, 55)
            d.rectangle([m + radius - ln, y0, m + radius + 5, y1], fill=255)
            if rnd.random() < 0.35: d.rectangle([m, y0, m + rnd.uniform(0, 14), y1], fill=0)
        mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    im = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    shl = Image.new("RGBA", mask.size, (0, 0, 0, 255)); shl.putalpha(mask.filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.6)))
    im.alpha_composite(shl, (6, 12))
    body = Image.new("RGBA", mask.size)
    body.paste(grad(mask.width, ph, top, bot), (0, m))
    body.paste(grad(mask.width, m, top, top), (0, 0)); body.paste(grad(mask.width, m, bot, bot), (0, m + ph))
    body.putalpha(mask); im.alpha_composite(body)
    im.alpha_composite(ti, (m + (pw - ti.width) // 2, m + (ph - ti.height) // 2))
    return im, m, size


def swoosh(w=640, h=90, color=(255, 214, 0)):
    S = 3; im = Image.new("L", (w * S, h * S), 0); d = ImageDraw.Draw(im)
    for i in range(101):
        x = i / 100 * w; y = h * 0.75 - h * 0.45 * (x / w) ** 1.6
        th = 6 + 22 * (1 - abs(2 * x / w - 1)) ** 0.7
        d.ellipse([(x - th / 2) * S, (y - th / 2) * S, (x + th / 2) * S, (y + th / 2) * S], fill=255)
    out = Image.new("RGBA", (w, h), color + (0,)); out.putalpha(im.resize((w, h), Image.LANCZOS))
    return out


# ширина, сдвиг вбок, максимальный шрифт по ролям (масштаб k уменьшает шрифт)
SPEC = {"blue": (1010, -25, 230), "yellow": (970, 20, 330), "red": (1030, -10, 180)}


def title(lines, k=1.0, overlap=24):
    """lines: [(текст, роль)] → RGBA блок под общим наклоном. Росчерк — под красной, если она последняя."""
    ps = []
    for i, (t, role) in enumerate(lines):
        w, dx, mx = SPEC[role]
        if role == "yellow" and len(lines) == 1: mx = 300
        p, m, _ = plate(t, role, w, int(mx * k), brush=(role == "red"), seed=i + 3)
        ps.append((p, m, dx))
    bw = max(p.width + abs(dx) * 2 for p, m, dx in ps) + 40
    bh = sum(p.height - 2 * m for p, m, dx in ps) - overlap * (len(ps) - 1) + 260
    block = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    y = 20; last = None
    for p, m, dx in ps:
        x = (bw - p.width) // 2 + dx
        block.alpha_composite(p, (x, y)); last = (x, y, p, m)
        y += p.height - 2 * m - overlap
    if lines[-1][1] == "red":
        x, y0, p, m = last; sw = swoosh()
        block.alpha_composite(sw, (x + p.width - m - sw.width - 30, y0 + p.height - m - 62))
    block = block.rotate(ANGLE, resample=Image.BICUBIC, expand=True)
    return block.crop(block.getbbox())


def lines_from_cover(cov):
    def up(s): return re.sub(r"\s+", " ", (s or "").strip()).upper()
    top = up(cov.get("top")); bot = [up(x) for x in (cov.get("bot") or "").split("|") if x.strip()]
    if not bot and cov.get("text"): bot = [up(cov["text"])]
    if not top and not bot: bot = ["СМОТРИТЕ ДО КОНЦА"]
    out = []
    if top: out.append((top, "blue"))
    if bot:
        out.append((bot[0], "yellow"))
        if len(bot) > 1: out.append((" ".join(bot[1:]), "red"))
    if len(out) == 1:   # одна строка — жёлтая; две без синей — жёлтая + красная
        out = [(out[0][0], "yellow")]
    return out


def face_box(img):
    import cv2
    hx = os.environ.get("HAAR") or os.path.join(ROOT, "scripts", "haar.xml")
    if not os.path.exists(hx): hx = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    g = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    fs = cv2.CascadeClassifier(hx).detectMultiScale(g, 1.1, 5, minSize=(120, 120))
    if len(fs):
        fx, fy, fw, fh = max(fs, key=lambda r: r[2] * r[3])
        return int(fy - 0.22 * fh), int(fy + 0.95 * fh), (fx, fy, fw, fh)
    return None


def erase_subs(src, y0):
    """24.11.2026: старый монтаж — вшитые субтитры (белые/жёлтые/зелёные буквы с тёмной обводкой) ниже y0 закрашиваем."""
    import cv2
    arr = cv2.cvtColor(np.array(src), cv2.COLOR_RGB2BGR)
    y0 = max(0, min(H - 10, int(y0)))
    hsv = cv2.cvtColor(arr[y0:], cv2.COLOR_BGR2HSV)
    h_, s_, v_ = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    txt = (((s_ < 45) & (v_ > 225)) | ((h_ > 15) & (h_ < 38) & (s_ > 140) & (v_ > 170)) | ((h_ > 45) & (h_ < 85) & (s_ > 140) & (v_ > 150))).astype(np.uint8)
    dark = (v_ < 70).astype(np.uint8)
    near = cv2.dilate(dark, np.ones((7, 7), np.uint8))
    letters = cv2.dilate(txt & near, np.ones((7, 7), np.uint8))
    letters = cv2.morphologyEx(letters, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(letters)
    keep = np.zeros_like(letters)
    for i in range(1, n):                       # строка субтитров: широкая и невысокая
        x, y, w, h, a = st[i]
        if w > 60 and h < 200 and w > 1.5 * h: keep[lab == i] = 1
    # 24.11: жёлтые субтитры без тёмной обводки — ярко-жёлтая строка, отдельно от зелени
    yel = ((h_ > 20) & (h_ < 36) & (s_ > 190) & (v_ > 200)).astype(np.uint8)
    yl = cv2.morphologyEx(cv2.dilate(yel, np.ones((5, 5), np.uint8)), cv2.MORPH_CLOSE, np.ones((9, 25), np.uint8))
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(yl)
    for i in range(1, n2):
        x, y, w, h, a_ = st2[i]
        if w > 80 and 25 < h < 180 and w > 2 * h and yel[y:y + h, x:x + w].mean() > 0.12: keep[lab2 == i] = 1
    mask = cv2.dilate(keep, np.ones((11, 11), np.uint8)) * 255
    if mask.mean() < 0.3: return src
    full = np.zeros(arr.shape[:2], np.uint8); full[y0:] = mask
    arr = cv2.inpaint(arr, full, 11, cv2.INPAINT_TELEA)
    print(f"plashki6: стёрты старые субтитры ({(full > 0).mean() * 100:.2f}% кадра)")
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))


def extend_down(src, shift):
    """Кадр опускается на shift, сверху продлевается стена (размытая верхняя полоса кадра)."""
    if shift <= 0: return src
    base = src.crop((0, 0, W, 60)).resize((W, shift + 60)).filter(ImageFilter.GaussianBlur(20))
    out = Image.new("RGB", (W, H)); out.paste(base, (0, 0))
    msk = Image.new("L", (W, H - shift), 255); dm = ImageDraw.Draw(msk)
    for y in range(60): dm.line([(0, y), (W, y)], fill=int(255 * y / 60))
    out.paste(src.crop((0, 0, W, H - shift)), (0, shift), msk)
    return out


def place(lines, head_top, chin, max_shift=480, top_y=TOPY, bot_y=BOTY):
    """План раскладки: [(блок, y)], сдвиг кадра. Лицо и рот не закрываем и не выталкиваем за сетку 3:4 (низ 1680)."""
    CHIN_MAX = 1640
    for k in (1.0, 0.9, 0.82, 0.75):
        b = title(lines, k)
        free = head_top - 15 - top_y
        if b.height <= free:
            return [(b, head_top - 15 - b.height)], 0, f"всё над головой (k {k})"
        need = b.height - free
        if need <= max_shift and chin + need <= CHIN_MAX:
            return [(b, top_y)], need, f"кадр ниже на {need}, всё над головой (k {k})"
    for k in (1.0, 0.9, 0.8):   # разносим строки: часть над головой, часть на груди
        for cut in range(len(lines) - 1, 0, -1):
            a, c = title(lines[:cut], k), title(lines[cut:], k)
            free = head_top - 15 - top_y
            sh = max(0, a.height - free)
            if sh <= max_shift and chin + sh + 20 + c.height <= bot_y:
                return [(a, top_y if sh else head_top - 15 - a.height), (c, chin + sh + 20)], sh, f"{cut} стр. над головой, {len(lines) - cut} на груди (k {k})"
    for k in (0.7, 0.65, 0.6):  # лицо очень крупное: шрифт меньше, рот в сетке остаётся
        b = title(lines, k); need = max(0, b.height - (head_top - 15 - top_y))
        if chin + need <= CHIN_MAX + 40:
            return [(b, top_y)], need, f"кадр ниже на {need} (крупное лицо), k {k}"
    b = title(lines, 0.6); need = max(0, b.height - (head_top - 15 - top_y))
    return [(b, top_y)], min(need, max(0, CHIN_MAX + 60 - chin)), "крайний случай, k 0.6"


def render(bg_path, out_path, spec_path, key=""):
    spec = json.load(open(spec_path)) if os.path.exists(spec_path) else {}
    cov = spec.get("cover") or {}
    lines = lines_from_cover(cov)
    src = Image.open(bg_path).convert("RGB")
    if src.size != (W, H):
        s = max(W / src.width, H / src.height)
        src = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
        l, t = (src.width - W) // 2, (src.height - H) // 2
        src = src.crop((l, t, l + W, t + H))
    src = ImageEnhance.Color(ImageEnhance.Contrast(src).enhance(1.06)).enhance(1.15)
    win = int(spec.get("top_px") or 0)
    fb = face_box(src)
    if spec.get("face"):                             # 24.11.2026: голова задана вручную [верх кепки/волос, подбородок]
        fb = (int(spec["face"][0]), int(spec["face"][1]), (0, 0, 999, 999))
    if spec.get("erase_subs"):
        src = erase_subs(src, spec.get("erase_from") or ((fb[1] if fb else 700) + 20))
    if win and (not fb or fb[2][2] < 330):          # две камеры: лицо окошком сверху — текст под окошком
        blocks = [(title(lines), win + 40)]; shift = 0; how = f"окошко до {win}, текст ниже"
    else:
        head_top, chin = (fb[0], fb[1]) if fb else (560, 1170)
        head_top = max(head_top, 120)
        blocks, shift, how = place(lines, head_top, chin)
    im = extend_down(src, shift).convert("RGBA")
    for b, y in blocks:
        im.alpha_composite(b, ((W - b.width) // 2, int(y)))
    im.convert("RGB").save(out_path)
    print(f"plashki6: {' / '.join(t for t, _ in lines)} — {how}")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
