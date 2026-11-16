# 16.11.2026 (Евгений 21:55, «начинай править… их много»): рилс 9:16 во весь экран из ГОТОВЫХ слайдов 4:5,
# когда spec.json с фото нет (карусели из шпаргалок, старые фото-карусели).
#   python3 scripts/karusel/rils_916_iz_slajdov.py <папка карусели>   → <папка>/reel/01.jpg … 1080×1920
# Почему: Facebook режет рилс «видео не полностью заполняет экран», если слайд 4:5 стоит по центру с размытыми полосами.
# Как:
#  - слайд-«шпаргалка» (ровный тёмный фон, текст): фон продолжается вверх и вниз тем же цветом построчно — шва нет,
#    это просто высокий слайд; жёлтая полоска — у верхнего края кадра; текст оказывается в безопасной зоне;
#    в папке reel/ кладётся метка _bez_plashki (сайт на слайде уже есть — slajdshou.py свой не рисует);
#  - фото-слайд: слайд ставится к верху кадра, снизу — плавное продолжение его тёмной подложки в почти чёрный. Старые надписи «Листайте →» и «1/7»
#    стираются (cv2.inpaint), если на первом слайде есть жёлтое «Листайте».
import os, sys, glob, json
import numpy as np
from PIL import Image, ImageFilter

W, H = 1080, 1920


def is_flat(im):
    a = np.asarray(im.resize((270, 338))).astype(int)
    bg = np.median(a[300:330, 150:260].reshape(-1, 3), 0)
    return (np.abs(a - bg).max(-1) < 14).mean() > 0.3


def flat_916(im):
    a = np.asarray(im).copy()
    yel = lambda r: a[r, :, 0].mean() > 150 and a[r, :, 2].mean() < 120
    hb = 0
    while hb < 40 and yel(hb): hb += 1                  # толщина жёлтой полоски сверху
    top_bar = a[0:hb].copy() if hb else None
    if hb: a[0:hb] = a[hb + 2:hb + 3]
    y0 = 200
    out = np.zeros((H, W, 3), np.uint8)
    out[:y0] = a[hb + 2:hb + 3]                         # фон вверх — строка под полоской
    out[y0:y0 + a.shape[0]] = a
    out[y0 + a.shape[0]:] = a[-1:]                      # фон вниз — последняя строка
    if top_bar is not None: out[0:hb] = top_bar
    return Image.fromarray(out)


def stare_metki(im):
    import cv2
    a = np.asarray(im).copy()
    m = np.zeros(a.shape[:2], np.uint8)
    for (y1, y2, x1, x2) in ((30, 125, 0, 330), (30, 125, 880, 1080)):
        reg = a[y1:y2, x1:x2].astype(int)
        lum = reg.mean(-1); yel = (reg[..., 0] > 170) & (reg[..., 1] > 140) & (reg[..., 2] < 120)
        mk = (lum > 170) | yel
        m[y1:y2, x1:x2] = cv2.dilate(mk.astype(np.uint8) * 255, np.ones((7, 7), np.uint8))
    return Image.fromarray(cv2.inpaint(a, m, 7, cv2.INPAINT_TELEA))


def photo_916(im):
    # фото-слайд ставится к верху кадра (текст слайда оказывается на 880–1270, в безопасной зоне),
    # снизу — продолжение его тёмной подложки, плавно в почти чёрный: шва и «полос» нет
    a = np.asarray(im); sh = a.shape[0]
    out = Image.new("RGB", (W, H)); out.paste(im, (0, 0))
    last = a[-6:].astype(float).mean(0)
    k = np.ones(81) / 81                                # сглаживаем по ширине — без вертикальных полосок
    last = np.stack([np.convolve(np.pad(last[:, c], 40, mode='edge'), k, 'valid') for c in range(3)], 1)
    n = H - sh
    g = np.linspace(0, 1, n)[:, None, None] ** 0.7
    bot = last[None] * (1 - g) + np.array([12, 12, 14])[None, None] * g
    out.paste(Image.fromarray(bot.astype(np.uint8)), (0, sh))
    return out


def main(folder):
    fs = sorted(glob.glob(os.path.join(folder, "[0-9][0-9].jpg")))
    if not fs: sys.exit("нет слайдов")
    ims = [Image.open(f).convert("RGB").resize((1080, 1350)) for f in fs]
    flat = all(is_flat(i) for i in ims)               # шпаргалка — только если ВСЕ слайды с ровным фоном
    rd = os.path.join(folder, "reel"); os.makedirs(rd, exist_ok=True)
    stare = False
    if not flat:
        a = np.asarray(ims[0])[30:125, 0:330].astype(int)
        stare = ((a[..., 0] > 170) & (a[..., 1] > 140) & (a[..., 2] < 120)).sum() > 150
    for i, im in enumerate(ims, 1):
        if flat: o = flat_916(im)
        else: o = photo_916(stare_metki(im) if stare else im)
        o.save(os.path.join(rd, f"{i:02d}.jpg"), quality=92)
    mk = os.path.join(rd, "_bez_plashki")
    if flat: open(mk, "w").write("сайт уже на слайдах")
    elif os.path.exists(mk): os.remove(mk)
    print(f"reel/: {len(ims)} слайдов, {'шпаргалка (фон продлён)' if flat else 'фото' + (' + стёрты «Листайте» и номера' if stare else '')}")


if __name__ == "__main__":
    main(sys.argv[1])
