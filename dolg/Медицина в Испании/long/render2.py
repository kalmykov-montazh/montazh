#!/usr/bin/env python3
"""Лонг «Медицина в Испании» v2 (31.10.2026): два режима (слайд+окно / крупно), наезды, качание, переходы,
главы, вставки на весь экран, наезд на новую карточку слайда, QR, подписка. python render2.py out.mp4 T0 T1"""
import numpy as np, cv2, subprocess, json, sys, time, os, math, onnxruntime as ort
from PIL import Image
H_ = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080; FPS = 30; SP = 1.2
P = json.load(open(f'{H_}/plan2.json')); B = json.load(open(f'{H_}/body.json'))
BL = sum(e - s for s, e in B)
OUT = sys.argv[1]; T0 = float(sys.argv[2]); T1 = float(sys.argv[3]); TAIL = 3.0
RAW = os.environ.get('RAW', 'raw.mp4'); CAMF = os.environ.get('CAM', 'cam.mp4'); RVM = os.environ.get('RVM', 'rvm.onnx')
def raw_of(tb):
    o = 0
    for s, e in B:
        if tb < o + (e - s): return s + tb - o
        o += e - s
    return B[-1][1] - 1 / FPS
class Reader:
    def __init__(s, src, start):
        s.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{start / FPS:.4f}', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, bufsize=W * H * 6)
        s.i = start - 1; s.f = None
    def get(s, idx):
        while s.i < idx:
            b = s.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            s.i += 1; s.f = b
        return np.frombuffer(s.f, np.uint8).reshape(H, W, 3)
so = ort.SessionOptions(); so.intra_op_num_threads = max(1, (os.cpu_count() or 2) - 1)
sess = ort.InferenceSession(RVM, so, providers=['CPUExecutionProvider'])
def zrec(): return [np.zeros([1, 1, 1, 1], np.float32)] * 4
REC = {'A': zrec(), 'F': zrec()}
def matte(img, m, dr):
    x = (img[..., ::-1].astype(np.float32) / 255).transpose(2, 0, 1)[None]; r = REC[m]
    _, pha, *REC[m] = sess.run(None, {'src': x, 'r1i': r[0], 'r2i': r[1], 'r3i': r[2], 'r4i': r[3], 'downsample_ratio': np.array([dr], np.float32)})
    return np.clip(cv2.GaussianBlur(pha[0, 0], (3, 3), 0), 0, 1)
soft = lambda m: cv2.GaussianBlur(m, (0, 0), 3)
WY0, WY1, WX0, WX1 = 643, 1080, 1287, 1914; wh, ww = WY1 - WY0, WX1 - WX0
SX0, SY0, SX1, SY1 = 106, 78, 1814, 1039   # слайд
kw = np.zeros((wh, ww), np.float32); kw[int(wh * 0.68):, int(ww * 0.41):int(ww * 0.54)] = 1; kw[int(wh * 0.93):, :] = 1; KW = soft(kw)
MIC = np.zeros((H, W), np.float32); MIC[700:, 780:970] = 1; MIC[1010:, :] = 1; KMIC = soft(MIC)
def comp_small(f, a, sig):
    f = f.astype(np.float32); wg = (1 - a)[..., None]
    bg = cv2.GaussianBlur(f * wg, (0, 0), sig) / (cv2.GaussianBlur(wg, (0, 0), sig)[..., None] + 1e-3)
    return np.clip(f * (1 - wg) + bg * wg, 0, 255).astype(np.uint8)
def comp_full(f, a_small):
    a = np.maximum(cv2.resize(a_small, (W, H)), KMIC)
    sm = cv2.resize(f, (480, 270), interpolation=cv2.INTER_AREA).astype(np.float32)
    ws = cv2.resize(1 - a, (480, 270), interpolation=cv2.INTER_AREA)[..., None]
    bg = cv2.GaussianBlur(sm * ws, (0, 0), 7) / (cv2.GaussianBlur(ws, (0, 0), 7)[..., None] + 1e-3)
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_CUBIC); a3 = a[..., None]
    return np.clip(f.astype(np.float32) * a3 + bg * (1 - a3), 0, 255).astype(np.uint8)
def rgba(p):
    im = np.asarray(Image.open(p).convert('RGBA')).astype(np.float32); return im[..., :3][..., ::-1].copy(), im[..., 3:] / 255
def over(fr, img, x, y, alpha=1.0):
    c, a = img; h, w = a.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    cs = c[y0 - y:y1 - y, x0 - x:x1 - x]; as_ = a[y0 - y:y1 - y, x0 - x:x1 - x] * alpha
    reg = fr[y0:y1, x0:x1].astype(np.float32); fr[y0:y1, x0:x1] = (cs * as_ + reg * (1 - as_)).astype(np.uint8)
def zoom(f, z, cx, cy, ox=0.0):
    if z <= 1.0005 and abs(ox) < 0.5: return f
    w, h = W / z, H / z; x0 = min(max(cx - w / 2 + ox, 0), W - w); y0 = min(max(cy - h / 2, 0), H - h)
    M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]]); return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR)
eo = lambda x: 1 - (1 - max(0, min(1, x))) ** 3
PL = {i: rgba(f'{H_}/ov2/p{i:02d}.png') for i, (a, b, t) in enumerate(P['F']) if t}
CH = [rgba(f'{H_}/ov2/ch{i}.png') for i in range(len(P['CH']))]
INS = [cv2.imread(f'{H_}/ov2/ins{i}.png') for i in range(len(P['INS']))]
QR = rgba(f'{H_}/ov/qr.png'); SUBF = [rgba(f'{H_}/sub/{i:03d}.png') for i in range(120)]
INSD = 3.6
def mode(tb):
    for i, (a, b, t) in enumerate(P['F']):
        if a <= tb < b: return 'F', i, a, b
    a = max([b for _, b, _ in P['F'] if b <= tb] + [0]); b = min([x for x, _, _ in P['F'] if x > tb] + [1e9])
    return 'A', None, a, b
def punch(tb):
    for t in P['PUNCH']:
        d = (tb - t) / SP
        if 0 <= d < 0.12: return 1 + 0.08 * eo(d / 0.12)
        if 0.12 <= d < 0.52: return 1.08
        if 0.52 <= d < 0.77: return 1 + 0.08 * (1 - eo((d - 0.52) / 0.25))
    return 1.0
def cardz(tb):
    for c in P['CARDS']:
        d = (tb - c['t']) / SP
        if 0 <= d < 2.6:
            k = eo(d / 0.5) if d < 0.5 else (1 - eo((d - 2.0) / 0.6) if d > 2.0 else 1)
            x0, y0, x1, y1 = c['bbox']; cx = SX0 + (x0 + x1) / 2 * (SX1 - SX0) / 1181; cy = SY0 + (y0 + y1) / 2 * (SY1 - SY0) / 960
            return 1 + 0.22 * k, cx, cy
    return 1.0, None, None
def slide_layer(raw):
    f = raw.copy(); f[WY0:WY1, WX0:min(WX1, SX1)] = (15, 8, 7); return f
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
                        '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
N = int(BL / SP * FPS); k0 = int(T0 / SP * FPS); k1 = min(N, int(T1 / SP * FPS))
r0 = int(round(raw_of(k0 / FPS * SP) * FPS))
raw = Reader(RAW, max(0, r0 - 2)); cam = Reader(CAMF, max(0, r0 - 4))
last = {}; prev = None; lastfr = None; t0 = time.time(); n = 0
for k in range(k0, k1 + int(TAIL * FPS) if k1 == N else k1):
    if k >= N: enc.stdin.write(lastfr.tobytes()); continue
    tb = k / FPS * SP; rt = raw_of(tb); r = int(round(rt * FPS))
    m, i, a, b = mode(tb)
    if m != prev: REC[m] = zrec(); last.pop(m, None)
    rf = raw.get(r)
    if m == 'F':
        f = cam.get(r - 1)
        if k % 2 == 0 or 'F' not in last: last['F'] = matte(cv2.resize(f, (960, 540), interpolation=cv2.INTER_AREA), 'F', 0.5)
        o = comp_full(f, last['F'])
        bb = min(b, BL); u = (tb - a) / max(1, bb - a)
        z = (1.03 + 0.10 * u) * punch(tb); sway = math.sin((tb - a) / SP * 2 * math.pi / 9) * 28
        o = zoom(o, z, 960 + sway, 430, 0)
        tx = P['F'][i][2]
        if tx and a + 0.8 * SP <= tb < bb - 0.4 * SP:
            c_, al = PL[i]; over(o, PL[i], (W - al.shape[1]) // 2, H - 200)
    else:
        o = slide_layer(rf)
        cz, cx, cy = cardz(tb); z = max(cz, punch(tb))
        if z > 1.001:
            if cx is None: cx, cy = 660, 470
            sl = o[SY0:SY1, SX0:SX1]; sh, sw_ = sl.shape[:2]
            lx, ly = cx - SX0, cy - SY0; w_, h_ = sw_ / z, sh / z
            x0 = min(max(lx - w_ / 2, 0), sw_ - w_); y0 = min(max(ly - h_ / 2, 0), sh - h_)
            M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]]); o[SY0:SY1, SX0:SX1] = cv2.warpAffine(np.ascontiguousarray(sl), M, (sw_, sh), flags=cv2.INTER_LINEAR)
        crop = rf[WY0:WY1, WX0:WX1]
        if k % 2 == 0 or 'A' not in last: last['A'] = np.maximum(matte(crop, 'A', 0.6), KW)
        o[WY0:WY1, WX0:WX1] = comp_small(crop, last['A'], 9)
        for q in P['QR']:
            d = tb - q
            if 0 <= d < 9 * SP:
                dt = d / SP; e = min(1, dt / 0.35, (9 - dt) / 0.35); e = e * e * (3 - 2 * e)
                over(o, QR, int(1920 - (1920 - 1390) * e), 175)
    # переход между режимами: короткий перелёт с увеличением
    ds = (tb - a) / SP
    if 0 <= ds < 0.25 and a > 1: o = zoom(o, 1 + 0.10 * (1 - eo(ds / 0.25)), 960, 500)
    # вставка на весь экран
    for j, x in enumerate(P['INS']):
        d = (tb - x['t']) / SP; L = INSD / SP
        if 0 <= d < L:
            s = 1.06 - 0.06 * eo(d / 0.22); im = INS[j]
            if s > 1.001: im = zoom(im, s, 960, 540)
            al = min(1, d / 0.12, (L - d) / 0.15); o = (im.astype(np.float32) * al + o.astype(np.float32) * (1 - al)).astype(np.uint8)
    # глава
    for j, (t, txt) in enumerate(P['CH']):
        d = (tb - t) / SP
        if 0 <= d < 3.2:
            c_, al = CH[j]; w_ = al.shape[1]
            e = eo(d / 0.3) if d < 0.3 else (1 - eo((d - 2.85) / 0.35) if d > 2.85 else 1)
            over(o, CH[j], int(-w_ + (w_ + 106) * e), 14)
    for s in P['SUB']:
        j = int((tb - s) / SP * FPS)
        if 0 <= j < 120: over(o, SUBF[j], 60, H - 300)
    prev = m; lastfr = o
    enc.stdin.write(o.tobytes()); n += 1
    if n % 900 == 0: print(f'{tb:.0f} {m} {time.time() - t0:.0f}s', flush=True)
enc.stdin.close(); enc.wait(); print('DONE', n, flush=True)
