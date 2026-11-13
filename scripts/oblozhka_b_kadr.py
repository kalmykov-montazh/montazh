# 13.11.2026: из кадров-кандидатов (pick_frame: глаза открыты, рот закрыт) выбрать тот, где у лица меньше всего
# старых надписей (жёлтые/красные/зелёные субтитры и плашки вшиты в готовый ролик).
#   python3 scripts/oblozhka_b_kadr.py v.mp4 кандидаты.txt out.png
import sys, os, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from litso import najti
v, cf, out = sys.argv[1:4]
ts = [l.strip() for l in open(cf) if l.strip()] if os.path.exists(cf) else []
hx = os.environ.get("HAAR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "haar.xml")
cc = cv2.CascadeClassifier(hx); best = None
for t in ts:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", v, "-frames:v", "1", "/tmp/c.png"], check=True)
    im = cv2.imread("/tmp/c.png"); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    fb = najti(im, hx)
    if not fb: continue
    x, y, w, h = fb
    cw = int(w / 0.40); y0 = max(0, y - int(h * 0.55)); y1 = min(im.shape[0], y + int(h * 1.35))
    x0 = max(0, x + w // 2 - cw // 2); x1 = min(im.shape[1], x + w // 2 + cw // 2)
    r = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    hue, sat, val = r[..., 0], r[..., 1], r[..., 2]
    loud = ((sat > 170) & (val > 170) & ((hue < 8) | ((hue > 18) & (hue < 35)) | ((hue > 45) & (hue < 80)))).mean()
    # белые субтитры с чёрной обводкой у подбородка: белое рядом с чёрным
    yb0 = min(im.shape[0], y + int(h * 0.75)); yb1 = min(im.shape[0], y + int(h * 1.9))
    band = cv2.cvtColor(im[yb0:yb1, x0:x1], cv2.COLOR_BGR2HSV)
    wh = ((band[..., 2] > 225) & (band[..., 1] < 45)).astype(np.uint8)
    dk = (band[..., 2] < 45).astype(np.uint8)
    sub = (cv2.dilate(wh, np.ones((5, 5), np.uint8)) & cv2.dilate(dk, np.ones((5, 5), np.uint8))).mean() if band.size else 0
    print(f"кадр {t}: цветных надписей {loud:.4f}, субтитров {sub:.4f}, лицо {w}")
    sc = loud + sub * 2 - w / 1e5
    if best is None or sc < best[0]: best = (sc, t)
t = best[1] if best else (ts[0] if ts else "2")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", v, "-frames:v", "1", out], check=True)
print("кадр обложки:", t)
