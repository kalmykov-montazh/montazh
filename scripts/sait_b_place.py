#!/usr/bin/env python3
# 14.11.2026 (решение Евгения: окошко сайта «Б» + значок KG в КАЖДЫЙ ролик, место — индивидуально под ролик).
# Выбирает для готового ролика секунду, высоту и место окошка так, чтобы оно не легло на лицо, голову, плашки и слайды.
#   python3 scripts/sait_b_place.py video.mp4  ->  печатает JSON {"t":..,"top":..,"h":..,"lay":..,"kg_left":0/1,"kg_s":..}
# Как выбирает:
#   - кадры раз в 0,5 с (270×480), лица — haar (scripts/haar.xml); голова = верх лица минус треть его высоты
#   - «слайдовый» ролик (нарезка из лонга: лицо в нижней половине, сверху слайд) — компактное окошко внизу слайда,
#     в 4 секунды, когда слайд не меняется (уже прочитан)
#   - обычный ролик — над головой; места меньше 170 px — внизу под субтитрами (1690 px)
#   - секунда — 4 с подряд, где в полосе окошка меньше всего движения и надписей (плашки, картинки), ближе к 45% ролика;
#     не раньше 6-й секунды (хук) и не позже чем за 6 с до конца (белая карточка-призыв)
#   - значок KG — правый верхний угол; если там в первые секунды голова или много текста — левый
import sys, os, json, subprocess, numpy as np, cv2

v = sys.argv[1]
D = os.path.dirname(os.path.abspath(__file__))
SW, SH, ST = 270, 480, 0.5
K = 1920 / SH
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v],
                           capture_output=True, text=True).stdout.strip())
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", v, "-vf", f"fps={1/ST},scale={SW}:{SH}", "-f", "rawvideo",
                      "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
fc = cv2.CascadeClassifier(f"{D}/haar.xml")
fr, faces = [], []
while True:
    b = p.stdout.read(SW * SH)
    if len(b) < SW * SH: break
    g = np.frombuffer(b, np.uint8).reshape(SH, SW)
    fr.append(g.astype(np.int16))
    f = fc.detectMultiScale(g, 1.1, 5, minSize=(30, 30))
    faces.append([(x, y, w, h) for x, y, w, h in f])
n = len(fr)
tops, cys, multi = [], [], 0
for f in faces:
    if not f: continue
    big = sorted(f, key=lambda r: -r[2] * r[3])
    if len(big) >= 2 and big[1][2] * big[1][3] > 0.35 * big[0][2] * big[0][3]: multi += 1
    tops.append(min(y - h * 0.38 for x, y, w, h in big[:2]) * K)
    cys.append((big[0][1] + big[0][3] / 2) * K)
headtop = float(np.percentile(tops, 15)) if tops else 700.0   # самая высокая голова за ролик (с запасом)
cy = float(np.median(cys)) if cys else 900.0
slide = cy > 1150                                             # лицо в нижней половине — сверху слайд
two = multi > 0.3 * max(1, len(tops))

if slide:
    faceband_top = float(np.percentile(tops, 10)) if tops else 1100
    h = 230; top = int(max(560, faceband_top - h - 40)); lay = "слайд"
else:
    avail = headtop - 40 - 120
    if avail >= 170: h = int(min(320, avail)); top = 120; lay = "верх"
    else: h = 200; top = 1690; lay = "низ"
# движение и надписи в полосе окошка
y0, y1 = int(top / K), int(min(SH - 1, (top + h) / K))
act = np.zeros(n)
for i in range(1, n):
    reg = fr[i][y0:y1]; prv = fr[i - 1][y0:y1]
    act[i] = np.abs(reg - prv).mean() + 0.15 * np.abs(np.diff(reg, axis=1)).mean()
W = int(4.0 / ST)
best = None
for i in range(int(6 / ST), max(int(6 / ST) + 1, int((dur - 6) / ST) - W)):
    s = act[i:i + W + 1].max() + act[i:i + W + 1].mean()
    s += 0.6 * abs(i * ST / dur - 0.45)
    if best is None or s < best[0]: best = (s, i * ST)
t = best[1] if best else max(1.0, dur * 0.4)
# значок: правый угол занят головой/текстом — левый
rt = np.mean([np.abs(np.diff(fr[i][int(150 / K):int(234 / K), -int(110 / K):], axis=1)).mean() for i in range(min(n, 20))])
lt = np.mean([np.abs(np.diff(fr[i][int(150 / K):int(234 / K), :int(110 / K)], axis=1)).mean() for i in range(min(n, 20))])
kg_left = 1 if rt > lt * 1.6 and rt > 6 else 0
print(json.dumps({"t": round(t, 2), "top": top, "h": h, "lay": lay, "two": two, "headtop": int(headtop),
                  "kg_left": kg_left, "kg_s": 70 if slide else 84, "dur": round(dur, 2)}, ensure_ascii=False))
