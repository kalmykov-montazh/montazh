# 13.11.2026: настоящее лицо среди находок haar — не монета, не печать, не буква со слайда:
# много кожи (YCrCb) в рамке и разумный размер. Возвращает (x, y, w, h) или None.
import cv2, numpy as np
def najti(img_bgr, hx, nb=6, min_skin=0.35, fx=None):
    # fx (0..1): в кадре два человека — брать лицо, чей центр ближе к этой доле ширины (13.11.2026, интервью)
    g = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    fs = cv2.CascadeClassifier(hx).detectMultiScale(g, 1.1, nb, minSize=(90, 90))
    best = None
    mw = max([w for (_, _, w, _) in fs], default=0)
    for (x, y, w, h) in fs:
        if fx is None and w < 0.6 * mw: continue                        # мелочь рядом с крупным лицом — глаз, пятно
        r = cv2.cvtColor(img_bgr[y:y + h, x:x + w], cv2.COLOR_BGR2YCrCb)
        skin = ((r[..., 1] > 133) & (r[..., 1] < 178) & (r[..., 2] > 80) & (r[..., 2] < 130)).mean()
        if skin < min_skin: continue
        sc = skin if fx is None else -abs((x + w / 2) / img_bgr.shape[1] - fx)   # из крупных — где больше кожи; с fx — ближе к fx
        if best is None or sc > best[0]: best = (sc, (x, y, w, h))
    if not best and nb > 3:                       # холодный свет, бледное лицо — мягче
        return najti(img_bgr, hx, 3, 0.15, fx)
    return best[1] if best else None
