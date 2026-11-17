#!/usr/bin/env python3
# 17.11.2026: есть ли в готовом ролике окошко сайта / значок KG (замок 2).
# Ищет значок KG (hf/kg.png) в верхних углах кадров на 25/45/65 % ролика — его ставят вместе с окошком «Б»
# и build_auto.py на весь ролик. Нет значка ни в одном кадре — ролика без окошка.
#   python3 est_okoshko.py video.mp4  → печатает «да 0.83» или «нет 0.41»
import sys, subprocess, numpy as np, cv2, os
v = sys.argv[1]
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
kg = cv2.imread(f"{R}/hf/kg.png", cv2.IMREAD_UNCHANGED)
if kg is None: print("нет-шаблона 0"); sys.exit(0)
if kg.shape[2] == 4:
    a = kg[:, :, 3:4] / 255.0; kg = (kg[:, :, :3] * a).astype(np.uint8)
kgg = cv2.cvtColor(kg, cv2.COLOR_BGR2GRAY)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v],
                           capture_output=True, text=True).stdout.strip())
best = 0.0
for p in (0.25, 0.45, 0.65):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{dur * p:.2f}", "-i", v, "-frames:v", "1", "-vf", "scale=1080:1920",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    if len(raw) < 1080 * 1920: continue
    g = np.frombuffer(raw, np.uint8).reshape(1920, 1080)
    for reg in (g[60:420, 760:1080], g[60:420, 0:320]):
        for s in (60, 70, 84, 100):
            t = cv2.resize(kgg, (s, int(kgg.shape[0] * s / kgg.shape[1])))
            if t.shape[0] >= reg.shape[0] or t.shape[1] >= reg.shape[1]: continue
            r = cv2.matchTemplate(reg, t, cv2.TM_CCOEFF_NORMED)
            best = max(best, float(r.max()))
print(("да" if best >= 0.6 else "нет"), round(best, 2))
