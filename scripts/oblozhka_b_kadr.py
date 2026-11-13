# 13.11.2026: из кадров-кандидатов (pick_frame: глаза открыты, рот закрыт) выбрать тот, где у лица меньше всего
# старых надписей (жёлтые/красные/зелёные субтитры и плашки вшиты в готовый ролик).
#   python3 scripts/oblozhka_b_kadr.py v.mp4 кандидаты.txt out.png
import sys, os, subprocess, numpy as np, cv2
v, cf, out = sys.argv[1:4]
ts = [l.strip() for l in open(cf) if l.strip()] if os.path.exists(cf) else []
hx = os.environ.get("HAAR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "haar.xml")
cc = cv2.CascadeClassifier(hx); best = None
for t in ts:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", v, "-frames:v", "1", "/tmp/c.png"], check=True)
    im = cv2.imread("/tmp/c.png"); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    fs = cc.detectMultiScale(g, 1.1, 5, minSize=(60, 60))
    if not len(fs): continue
    x, y, w, h = max(fs, key=lambda r: r[2] * r[3])
    cw = int(w / 0.40); y0 = max(0, y - int(h * 0.55)); y1 = min(im.shape[0], y + int(h * 1.35))
    x0 = max(0, x + w // 2 - cw // 2); x1 = min(im.shape[1], x + w // 2 + cw // 2)
    r = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    hue, sat, val = r[..., 0], r[..., 1], r[..., 2]
    loud = ((sat > 170) & (val > 170) & ((hue < 8) | ((hue > 18) & (hue < 35)) | ((hue > 45) & (hue < 80)))).mean()
    print(f"кадр {t}: надписей {loud:.4f}, лицо {w}")
    sc = loud - w / 1e5
    if best is None or sc < best[0]: best = (sc, t)
t = best[1] if best else (ts[0] if ts else "2")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", v, "-frames:v", "1", out], check=True)
print("кадр обложки:", t)
