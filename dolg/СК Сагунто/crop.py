#!/usr/bin/env python3
"""СК Сагунто (17.11.2026): вертикальный сырой 4K HDR → широкоформат 1920×1080 УВЕЛИЧЕНИЕМ, без полей по бокам.
Решение Евгения: окно на всю ширину кадра, по высоте — по лицам, чтобы головы не срезало сверху и снизу.
python crop.py K   (рядом K.src.mp4) → K.mov (1080p30, pcm 48k), K.crop.json, K.sheet.jpg (лист кадров результата)
Лица: YuNet (если скачалась модель) + haar фронт и профиль. Окно: верх головы ~на 14 % высоты окна.
Штатив (окно почти не гуляет) — одно положение на весь ролик; с рук — плавное, без рывков."""
import cv2, json, numpy as np, os, subprocess, sys
K = sys.argv[1]; SRC = f'{K}.src.mp4'
H_ = os.path.dirname(os.path.abspath(__file__))
pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,color_transfer:stream_side_data=rotation:format=duration',
                                '-of', 'json', SRC], capture_output=True, text=True).stdout)
st = pr['streams'][0]; dur = float(pr['format']['duration']); trc = st.get('color_transfer', '')
rot = 0
for sd in st.get('side_data_list', []) or []:
    if 'rotation' in sd: rot = int(sd['rotation'])
w0, h0 = st['width'], st['height']
if abs(rot) in (90, 270): w0, h0 = h0, w0
HDR = trc in ('arib-std-b67', 'smpte2084')
TM = ('zscale=t=linear:npl=250,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=2,'
      'zscale=t=bt709:m=bt709:r=tv,format=yuv420p,eq=contrast=1.06:saturation=1.15') if HDR else 'format=yuv420p'
print(f'{K}: {w0}x{h0} rot {rot} trc {trc} dur {dur:.1f}', flush=True)
VERT = h0 > w0

# --- 1. лица раз в 0,5 с на уменьшенном кадре
SW = 540; SH = int(round(h0 * SW / w0 / 2) * 2)
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-vf', f'fps=4,scale={SW}:{SH}:flags=bilinear,format=bgr24', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
yn = None
mp = f'{H_}/yunet.onnx'
if os.path.exists(mp):
    try: yn = cv2.FaceDetectorYN.create(mp, '', (SW, SH), 0.6, 0.3, 50)
    except Exception as e: print('yunet нет:', e)
def cas(*names):
    for nm in names:
        for d in (getattr(getattr(cv2, 'data', None), 'haarcascades', ''), f'{H_}/../../scripts/'):
            c = cv2.CascadeClassifier(os.path.join(d, nm))
            if not c.empty(): return c
    return None
hf = cas('haarcascade_frontalface_default.xml', 'haar.xml'); hp = cas('haarcascade_profileface.xml'); hu = cas('haarcascade_upperbody.xml')
WH = SW * 9 / 16   # высота окна в масштабе выборки (окно на всю ширину)
S = []   # [t, top_головы, низ_подбородка, n]
i = 0
while True:
    b = p.stdout.read(SW * SH * 3)
    if len(b) < SW * SH * 3: break
    f = np.frombuffer(b, np.uint8).reshape(SH, SW, 3); t = i / 4; i += 1
    boxes = []
    if yn is not None:
        _, fs = yn.detect(f)
        if fs is not None: boxes += [(x, y, w, h) for x, y, w, h, *r in fs if w >= 16 and r[-1] > 0.6]
    if not boxes:
        g = cv2.equalizeHist(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
        for c in (hf, hp):
            if c is not None: boxes += [tuple(x) for x in c.detectMultiScale(g, 1.1, 6, minSize=(22, 22))]
        if hp is not None:
            boxes += [(SW - x - w, y, w, h) for x, y, w, h in hp.detectMultiScale(cv2.flip(g, 1), 1.1, 6, minSize=(22, 22))]
    if not boxes and hu is not None:   # спиной или в профиль — по верху плеч и головы (голова ~ верхние 35 % рамки)
        g = cv2.equalizeHist(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
        ub = [tuple(x) for x in hu.detectMultiScale(g, 1.08, 4, minSize=(60, 60))]
        boxes += [(x + w * 0.3, y + h * 0.08, w * 0.4, h * 0.35) for x, y, w, h in ub]
    # отсеять мелочь (лица на фото, отражения): берём лица не меньше 45 % самого крупного
    if boxes:
        mx = max(w for x, y, w, h in boxes); boxes = [bx for bx in boxes if bx[2] >= 0.45 * mx]
        top = min(y - 0.45 * h for x, y, w, h in boxes); bot = max(y + 1.15 * h for x, y, w, h in boxes)
        S.append([t, top, bot, len(boxes)])
    else: S.append([t, np.nan, np.nan, 0])
p.wait()
S = np.array(S, float); n = len(S)
ok = ~np.isnan(S[:, 1])
print(f'кадров {n}, с лицами {ok.sum()} ({ok.mean() * 100:.0f} %)', flush=True)

# --- 2. желаемый верх окна
def want(top, bot):
    y = top - 0.14 * WH                       # над макушкой воздух
    if bot - y > 0.92 * WH: y = (top + bot) / 2 - WH / 2   # лица на разной высоте — по центру между ними
    return y
Y = np.full(n, np.nan)
for j in range(n):
    if ok[j]: Y[j] = want(S[j, 1], S[j, 2])
lo, hi = 0.0, SH - WH
centre = (SH - WH) * 0.42                     # без лиц (дом, комнаты) — чуть выше середины
FPSs = 4
def gauss(Y, sg):
    k = int(3 * sg) + 1; g = np.exp(-0.5 * (np.arange(-k, k + 1) / sg) ** 2); g /= g.sum()
    return np.convolve(np.pad(Y, k, mode='edge'), g, 'valid')
if ok.sum() < max(3, 0.08 * n):
    Y[:] = centre; mode = 'без лиц — центр'
else:
    med = np.median(Y[ok]); spread = np.percentile(np.abs(Y[ok] - med), 80)
    if spread < 0.06 * WH and ok.mean() > 0.8:
        Y[:] = med; mode = f'штатив — одно положение ({spread:.1f})'
    else:
        # с рук: держим последнее положение до 2 с без лиц, потом плавно к центру
        Z = np.empty(n); last = None; gap = 0
        for j in range(n):
            if ok[j]: last = Y[j]; gap = 0; Z[j] = Y[j]
            else:
                gap += 1; base = centre if last is None else last
                w_ = min(1, max(0, (gap - 2 * FPSs) / (2 * FPSs)))
                Z[j] = base * (1 - w_) + centre * w_
        pad = np.pad(Z, 1, mode='edge'); Z = np.array([np.median(pad[j:j + 3]) for j in range(n)])
        Y = gauss(Z, 1.5)                                    # ~0,4 с, без запаздывания (симметрично)
        # жёсткое правило: голова целиком в кадре, где лицо видно
        for _ in range(3):
            for j in range(n):
                if ok[j]:
                    top, bot = S[j, 1], S[j, 2]
                    upper = top - 0.03 * WH                   # верх окна не ниже макушки
                    lower = bot - 0.97 * WH                   # низ окна не выше подбородка
                    Y[j] = min(Y[j], upper) if lower > upper else min(max(Y[j], lower), upper)
            Y = gauss(Y, 0.8)
        for j in range(n):
            if ok[j]: Y[j] = min(Y[j], S[j, 1] - 0.02 * WH)
        mode = f'с рук — следит за головами ({spread:.1f})'
Y = np.clip(Y, lo, hi)
print(K, mode, flush=True)

# --- 2б. «двойная камера» телефона: улица на весь кадр + окошко с лицом справа вверху (x 697–1018, y 60–632 из 1080×1920)
PIP = None
if VERT and ok.sum() > 0.3 * n:
    bx0, bx1, by0, by1 = 697 / 1080 * SW, 1018 / 1080 * SW, 60 / 1920 * SH, 632 / 1920 * SH
    cs = [(S[j, 1] + S[j, 2]) / 2 for j in range(n) if ok[j]]
    inside = np.mean([by0 <= c <= by1 for c in cs])
    if inside > 0.7 and np.median([S[j, 2] - S[j, 1] for j in range(n) if ok[j]]) < (by1 - by0):
        PIP = True
if PIP:
    k = w0 / 1080
    bw, bh, bx, by = [int(round(v * k / 2) * 2) for v in (321, 572, 697, 60)]
    band = int(round(w0 * 9 / 16 / 2) * 2); y_b = int(round((632 + 24) * k / 2) * 2)
    y_b = min(y_b, h0 - band)
    fc = (f"[0:v]{TM},split[a][b];[a]crop={w0}:{band}:0:{y_b},scale=1920:1080:flags=lanczos[bg];"
          f"[b]crop={bw}:{bh}:{bx}:{by},scale=460:820:flags=lanczos,pad=468:828:4:4:white[p];[bg][p]overlay=W-w-70:(H-h)/2,fps=30[v]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-filter_complex', fc, '-map', '[v]', '-map', '0:a', '-c:v', 'libx264', '-preset', 'veryfast',
                    '-crf', '17', '-g', '30', '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2', f'{K}.mov'], check=True)
    mode = 'двойная камера — улица + окошко с лицом справа'
    ys = []; CH = band
    print(K, mode, flush=True)
else:
    # --- 3. рендер: окно на всю ширину, crop по времени через sendcmd, HDR→обычный цвет уже после обрезки
    CW = w0 - w0 % 2; CH = int(round(CW * 9 / 16 / 2) * 2); sc = h0 / SH
    ys = [int(round(y * sc / 2) * 2) for y in Y]; ys = [min(max(0, y), h0 - CH) for y in ys]
    with open(f'{K}.cmd', 'w') as o:
        for j in range(n):
            o.write(f'{j / FPSs:.2f} crop@c y {ys[j]};\n')
    y0 = ys[0]
    vf = f'sendcmd=f={K}.cmd,crop@c={CW}:{CH}:0:{y0},{TM},scale=1920:1080:flags=lanczos,fps=30'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-vf', vf, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-g', '30',
                    '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2', f'{K}.mov'], check=True)
json.dump({'k': K, 'mode': mode, 'dur': dur, 'faces': float(ok.mean()), 'win_h_src': CH, 'y': ys}, open(f'{K}.crop.json', 'w'))
# лист кадров результата раз в 6 с — проверить головы глазами
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{K}.mov', '-vf', 'fps=1/3,scale=384:216,drawtext=text=%{pts\\:hms}:x=6:y=6:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=6x8:padding=3',
                '-frames:v', '1', '-q:v', '4', f'{K}.sheet.jpg'], check=True)
nn = int(dur // 144)
for q in range(1, nn + 1):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(q * 144), '-i', f'{K}.mov', '-vf', 'fps=1/3,scale=384:216,drawtext=text=%{pts\\:hms}:x=6:y=6:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=6x8:padding=3',
                    '-frames:v', '1', '-q:v', '4', f'{K}.sheet{q}.jpg'], check=True)
print('DONE', K, mode, flush=True)
