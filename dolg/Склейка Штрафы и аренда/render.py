#!/usr/bin/env python3
"""Склейка «Штрафы + 17 ловушек»: часть видео [T0, T1) выходного времени. python render.py edl.json ovdir out.mp4 T0 T1
Сверху на готовые лонги: главы со вжухом, наезды на суммах, тихий QR, перелёт на стыках, скрыт счётчик «N / 23»
и полоска прогресса (зритель не видит, где конец), конечная заставка."""
import numpy as np, cv2, subprocess, json, sys, os, math
from PIL import Image
W, H, FPS = 1920, 1080, 30
D = json.load(open(sys.argv[1])); OV = sys.argv[2]; OUT = sys.argv[3]; T0 = float(sys.argv[4]); T1 = min(float(sys.argv[5]), D['total'])
EDL, OFF, BODY = D['edl'], D['off'], D['body']
H_ = os.path.dirname(os.path.abspath(__file__))
def rgba(p):
    im = np.asarray(Image.open(p).convert('RGBA')).astype(np.float32); return im[..., :3][..., ::-1].copy(), im[..., 3:] / 255
def over(fr, img, x, y, alpha=1.0):
    c, a = img; h, w = a.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    cs = c[y0 - y:y1 - y, x0 - x:x1 - x]; as_ = a[y0 - y:y1 - y, x0 - x:x1 - x] * alpha
    reg = fr[y0:y1, x0:x1].astype(np.float32); fr[y0:y1, x0:x1] = (cs * as_ + reg * (1 - as_)).astype(np.uint8)
def zoom(f, z, cx, cy):
    if z <= 1.0005: return f
    w, h = W / z, H / z; x0 = min(max(cx - w / 2, 0), W - w); y0 = min(max(cy - h / 2, 0), H - h)
    return cv2.warpAffine(f, np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]]), (W, H), flags=cv2.INTER_LINEAR)
eo = lambda x: 1 - (1 - max(0, min(1, x))) ** 3
CH = [rgba(f'{OV}/ch{i}.png') for i in range(len(D['ch']))]
QR = rgba(f'{H_}/qr.png'); END = cv2.imread(f'{OV}/end.png')
def is_slide(src, f):
    if src == 'S':
        r = f[925:960, 160:340].astype(np.float32); m = r.mean((0, 1))   # BGR
        return abs(m[2] - 10) < 10 and abs(m[1] - 24) < 10 and abs(m[0] - 50) < 12 and r.std((0, 1)).max() < 9
    st = f[2:6, 100:1800].astype(np.float32); return (st.max(2) - st.min(2)).mean() > 120
def hide(src, f):
    """прячем «6 / 23» (Штрафы) и полоску прогресса (Ловушки) — копией фона чуть выше"""
    if src == 'S': f[962:1016, 160:345] = f[908:962, 160:345]
    else: f[1052:1074, 160:1286] = f[1030:1052, 160:1286]
class Reader:
    def __init__(s, src, t, dur):
        s.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{t:.4f}', '-i', f'{src}.mp4', '-t', f'{dur + 0.5:.3f}', '-vf', 'fps=30',
                                '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, bufsize=W * H * 6); s.f = None
    def next(s):
        b = s.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3: s.f = np.frombuffer(b, np.uint8).reshape(H, W, 3).copy()
        return s.f
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
k0 = int(round(T0 * FPS)); k1 = int(round(T1 * FPS)); seg = -1; rd = None; prev = None
for k in range(k0, k1):
    T = k / FPS
    if T >= BODY:   # конечная заставка
        d = T - BODY; e = eo(d / 0.6); o = END if e >= 1 else (END.astype(np.float32) * e + prev.astype(np.float32) * (1 - e)).astype(np.uint8) if prev is not None else END
        enc.stdin.write(np.ascontiguousarray(o).tobytes()); continue
    i = max(j for j in range(len(OFF)) if OFF[j] <= T + 1e-6); src, s, e = EDL[i]
    if i != seg:
        seg = i; ts = s + T - OFF[i]; rd = Reader(src, ts, e - ts)
    f = rd.next()
    sl = is_slide(src, f)
    if sl: hide(src, f)
    o = f
    # QR: тихо въезжает справа на 9 с, только когда на экране слайд
    for q in D['qr']:
        dt = T - q
        if 0 <= dt < 9 and sl:
            a = min(1, dt / 0.35, (9 - dt) / 0.35); a = a * a * (3 - 2 * a)
            over(o, QR, int(1920 - (1920 - 1390) * a), 150)
    # наезд на сумме
    z = 1.0
    for p in D['punch']:
        dd = T - p
        if 0 <= dd < 0.12: z = 1 + 0.07 * eo(dd / 0.12)
        elif 0.12 <= dd < 0.55: z = 1.07
        elif 0.55 <= dd < 0.8: z = 1 + 0.07 * (1 - eo((dd - 0.55) / 0.25))
    # перелёт на стыке кусков
    ds = T - OFF[i]
    if 0 <= ds < 0.25 and i > 0: z = max(z, 1 + 0.10 * (1 - eo(ds / 0.25)))
    if z > 1.0005: o = zoom(o, z, 960, 520)
    # главы
    for j, (t, *_ ) in enumerate(D['ch']):
        dd = T - t
        if 0 <= dd < 4.0:
            w_ = CH[j][1].shape[1]; a = eo(dd / 0.3) if dd < 0.3 else (1 - eo((dd - 3.65) / 0.35) if dd > 3.65 else 1)
            over(o, CH[j], int(-w_ + (w_ + 106) * a), 22)
    prev = o; enc.stdin.write(np.ascontiguousarray(o).tobytes())
enc.stdin.close(); enc.wait(); print('DONE', k1 - k0, flush=True)
