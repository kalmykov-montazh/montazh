# 13.11.2026: настоящее лицо среди находок haar — не монета, не печать, не буква со слайда:
# много кожи (YCrCb) в рамке и разумный размер. Возвращает (x, y, w, h) или None.
import cv2, numpy as np
def najti(img_bgr, hx):
    g = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    fs = cv2.CascadeClassifier(hx).detectMultiScale(g, 1.1, 6, minSize=(90, 90))
    best = None
    for (x, y, w, h) in fs:
        r = cv2.cvtColor(img_bgr[y:y + h, x:x + w], cv2.COLOR_BGR2YCrCb)
        skin = ((r[..., 1] > 133) & (r[..., 1] < 178) & (r[..., 2] > 80) & (r[..., 2] < 130)).mean()
        if skin < 0.35: continue
        sc = skin * (w ** 0.5)
        if best is None or sc > best[0]: best = (sc, (x, y, w, h))
    return best[1] if best else None
