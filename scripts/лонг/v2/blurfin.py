"""Размытый фон в готовом лонге (7 финал). Режимы кадра по времени: хук, крупная камера, слайд с окном камеры, заставка."""
import numpy as np, cv2, subprocess, onnxruntime as ort, sys, time
SRC, OUT = sys.argv[1], sys.argv[2]
FPS = 60; W, H = 1920, 1080
import json
P=json.load(open('plan.json'))
Hs = P['H'] + 74 / 60
WIN = [(x, y) for x, y, _ in P['W']]
FULL = [((x + Hs) / 1.2, (y + Hs) / 1.2) for x, y in WIN]
HOOK_END = Hs / 1.2
DUR = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', SRC], capture_output=True, text=True).stdout)
import os
END_START = float(os.environ.get('ENDS', DUR - 12.0))

def mode(t):
    if t < HOOK_END: return 'hook'
    if t >= END_START: return 'end'
    for a, b in FULL:
        if a <= t < b: return 'full'
    return 'win'

sess = ort.InferenceSession('rvm_mobilenetv3_fp32.onnx', providers=['CPUExecutionProvider'])
def zrec(): return [np.zeros([1, 1, 1, 1], np.float32)] * 4
REC = {'hook': zrec(), 'full': zrec(), 'win': zrec()}
def matte(img, m, dr):
    x = (img[..., ::-1].astype(np.float32) / 255).transpose(2, 0, 1)[None]
    r = REC[m]
    _, pha, *REC[m] = sess.run(None, {'src': x, 'r1i': r[0], 'r2i': r[1], 'r3i': r[2], 'r4i': r[3], 'downsample_ratio': np.array([dr], np.float32)})
    return np.clip(cv2.GaussianBlur(pha[0, 0], (3, 3), 0), 0, 1)

def soft(mask): return cv2.GaussianBlur(mask, (0, 0), 3)
# зоны, которые всегда резкие
kw = np.zeros((436, 632), np.float32); kw[298:, 262:338] = 1; kw[404:, :] = 1; KW = soft(kw)
from PIL import ImageFont
FNT = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf', 56)
TXT = [t for _, _, t in P['W']]
PL = []   # (t0, t1, x0, x1) плашки в готовом ролике
for (a, b), tx in zip(WIN, TXT):
    if not tx: continue
    tw = FNT.getlength(tx); PL.append(((a + Hs + 0.8) / 1.2 - 0.05, (b + Hs - 0.4) / 1.2 + 0.05, int(960 - tw / 2 - 40), int(960 + tw / 2 + 40)))
MIC = np.zeros((H, W), np.float32); MIC[720:, 830:1010] = 1; MIC[1000:, :] = 1
def keep_full(t):
    k = MIC.copy()
    for t0, t1, x0, x1 in PL:
        if t0 <= t < t1: k[845:1020, max(0, x0):min(W, x1)] = 1
    return soft(k)
KMIC = soft(MIC)
def keep_hook(fr):
    hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
    h, s_, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    white = (v > 235) & (s_ < 40)
    yel = (h >= 8) & (h <= 35) & (s_ > 140) & (v > 170)
    m = (white | yel).astype(np.uint8)
    m[:80] = 0; m[260:680] = 0          # текст только в полосе значка и подписей
    m = cv2.dilate(m, np.ones((15, 15), np.uint8)).astype(np.float32)
    return np.maximum(soft(m), KMIC)

def comp_small(f, a, sig):
    f = f.astype(np.float32); wgt = (1 - a)[..., None]
    bg = cv2.GaussianBlur(f * wgt, (0, 0), sig) / (cv2.GaussianBlur(wgt, (0, 0), sig)[..., None] + 1e-3)
    return np.clip(f * (1 - wgt) + bg * wgt, 0, 255).astype(np.uint8)

def comp_full(f, a_small, keep):
    # фон размываем на уменьшенной копии (быстро), альфа увеличивается до полного кадра
    a = np.maximum(cv2.resize(a_small, (W, H), interpolation=cv2.INTER_LINEAR), keep)
    sm = cv2.resize(f, (480, 270), interpolation=cv2.INTER_AREA).astype(np.float32)
    ws = cv2.resize(1 - a, (480, 270), interpolation=cv2.INTER_AREA)[..., None]
    bg = cv2.GaussianBlur(sm * ws, (0, 0), 7) / (cv2.GaussianBlur(ws, (0, 0), 7)[..., None] + 1e-3)
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_CUBIC)
    a3 = a[..., None]
    return np.clip(f.astype(np.float32) * a3 + bg * (1 - a3), 0, 255).astype(np.uint8)

dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', SRC,
                        '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'copy',
                        '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
n = 0; last = {}; prevm = None; t0 = time.time(); FS = W * H * 3
while True:
    buf = dec.stdout.read(FS)
    if len(buf) < FS: break
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    t = n / FPS; m = mode(t)
    if m != prevm and m in REC: REC[m] = zrec(); last.pop(m, None)   # новый кусок — сбросить память модели
    prevm = m
    if m == 'end':
        out = fr
    elif m == 'win':
        out = fr.copy(); crop = fr[643:1079, 1287:1919]
        if n % 2 == 0 or m not in last: last[m] = np.maximum(matte(crop, 'win', 0.6), KW)
        out[643:1079, 1287:1919] = comp_small(crop, last[m], 9)
    else:
        if n % 2 == 0 or m not in last:
            last[m] = matte(cv2.resize(fr, (960, 540), interpolation=cv2.INTER_AREA), m, 0.5)
        out = comp_full(fr, last[m], keep_full(t) if m == 'full' else keep_hook(fr))
    enc.stdin.write(out.tobytes())
    n += 1
    if n % 1800 == 0: print(f'{t:.0f}s {m} {time.time()-t0:.0f}s', flush=True)
    if n in (int(5 * FPS), int(8.5 * FPS), int(30 * FPS), int(150 * FPS)): cv2.imwrite(f'chk_{n}.jpg', cv2.resize(out, (960, 540)))
enc.stdin.close(); enc.wait(); print('DONE', n, flush=True)
