#!/usr/bin/env python3
"""Основа шортса из сырых лонга «Медицина в Испании» (31.10.2026): полоса 300, слайд 1080x604, камера 1080x1010 с размытым фоном;
где в лонге камера крупно — лицо на всю высоту. python sbase.py ID raw.mp4 cam.mp4 rvm.onnx out_dir"""
import numpy as np, cv2, subprocess, json, sys, os, onnxruntime as ort
ID, RAW, CAM, RVM, OUT = sys.argv[1:6]
HERE = os.path.dirname(os.path.abspath(__file__))
B = json.load(open(f'{HERE}/body.json')); P = json.load(open(f'{HERE}/plan.json'))
S = {i: (a, b) for i, n, a, b in json.load(open(f'{HERE}/shorts.json'))}
T0, T1 = S[ID]; FPS = 30; SP = 1.2; W, H = 1920, 1080
def raw_of(tb):
    o = 0
    for s, e in B:
        if tb < o + (e - s): return s + tb - o
        o += e - s
    return B[-1][1] - 1 / FPS
def mode(tb):
    for a, b, t in P['F']:
        if a <= tb < b: return 'F'
    return 'A'
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
so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count()
sess = ort.InferenceSession(RVM, so, providers=['CPUExecutionProvider']); REC = [np.zeros([1, 1, 1, 1], np.float32)] * 4
def matte(img):
    global REC
    x = (img[..., ::-1].astype(np.float32) / 255).transpose(2, 0, 1)[None]
    _, pha, *REC = sess.run(None, {'src': x, 'r1i': REC[0], 'r2i': REC[1], 'r3i': REC[2], 'r4i': REC[3], 'downsample_ratio': np.array([0.5], np.float32)})
    return np.clip(cv2.GaussianBlur(pha[0, 0], (3, 3), 0), 0, 1)
MIC = np.zeros((H, W), np.float32); MIC[700:, 780:970] = 1; MIC[1010:, :] = 1; KMIC = cv2.GaussianBlur(MIC, (0, 0), 3)
def comp_full(f, a_small):
    a = np.maximum(cv2.resize(a_small, (W, H)), KMIC)
    sm = cv2.resize(f, (480, 270), interpolation=cv2.INTER_AREA).astype(np.float32)
    ws = cv2.resize(1 - a, (480, 270), interpolation=cv2.INTER_AREA)[..., None]
    bg = cv2.GaussianBlur(sm * ws, (0, 0), 7) / (cv2.GaussianBlur(ws, (0, 0), 7)[..., None] + 1e-3)
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_CUBIC); a3 = a[..., None]
    return np.clip(f.astype(np.float32) * a3 + bg * (1 - a3), 0, 255).astype(np.uint8)
os.makedirs(OUT, exist_ok=True)
N = int(round((T1 - T0) / SP * FPS))
# звук: куски сырого по телу, голосовая цепочка, ускорение 1.2 (громкость выровняет движок сцен)
r0, r1 = raw_of(T0), raw_of(T1 - 0.001)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{r0 - 1:.3f}', '-to', f'{r1 + 1:.3f}', '-i', RAW, '-vn', '-ac', '2', '-ar', '48000', '-f', 's16le', f'{OUT}/r.raw'], check=True)
x = np.fromfile(f'{OUT}/r.raw', np.int16).reshape(-1, 2).astype(np.float32) / 32768; SR = 48000; base0 = r0 - 1
o = 0; parts = []; F6 = int(0.006 * SR); ramp = np.linspace(0, 1, F6)[:, None]
for s, e in B:
    L = e - s; a = max(s, s + (T0 - o)); b = min(e, s + (T1 - o))
    if b > a:
        p = x[int(round((a - base0) * SR)):int(round((b - base0) * SR))].copy()
        if len(p) > 2 * F6: p[:F6] *= ramp; p[-F6:] *= ramp[::-1]
        parts.append(p)
    o += L
y = np.concatenate(parts); (np.clip(y, -1, 1) * 32767).astype(np.int16).tofile(f'{OUT}/c.raw')
CH = 'highpass=f=70,equalizer=f=3000:width_type=o:width=1.5:g=2.5,acompressor=threshold=-24dB:ratio=3:attack=10:release=150:makeup=2,atempo=1.2'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', '48000', '-ac', '2', '-i', f'{OUT}/c.raw', '-af', CH, '-ar', '48000', f'{OUT}/a.wav'], check=True)
VW, VH = 1080, 1920; BG = np.array([0x2A, 0x1A, 0x0E], np.uint8)
rs = int(round(raw_of(T0) * FPS))
raw = Reader(RAW, max(0, rs - 2)); cam = Reader(CAM, max(0, rs - 4))
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{VW}x{VH}', '-r', '30', '-i', '-', '-i', f'{OUT}/a.wav',
                        '-map', '0:v', '-map', '1:a', '-t', f'{N / 30:.3f}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                        f'{OUT}/base.mp4'], stdin=subprocess.PIPE)
modes = []; last = None; prev = None
for k in range(N):
    tb = T0 + k / FPS * SP; r = int(round(raw_of(tb) * FPS)); m = mode(tb)
    f = cam.get(r - 1); s = raw.get(r)
    if m != prev: REC = [np.zeros([1, 1, 1, 1], np.float32)] * 4; last = None
    if k % 2 == 0 or last is None: last = matte(cv2.resize(f, (960, 540), interpolation=cv2.INTER_AREA))
    c = comp_full(f, last); o_ = np.empty((VH, VW, 3), np.uint8); o_[:] = BG
    if m == 'F':
        o_[300:1920] = cv2.resize(c[0:1080, 570:1290], (1080, 1620), interpolation=cv2.INTER_LANCZOS4); modes.append(0)
    else:
        o_[300:904] = cv2.resize(s[78:693, 150:1250], (1080, 604), interpolation=cv2.INTER_AREA)
        o_[910:1920] = cv2.resize(c[250:1010, 523:1336], (1080, 1010), interpolation=cv2.INTER_LANCZOS4); modes.append(1)
    prev = m; enc.stdin.write(o_.tobytes())
enc.stdin.close(); enc.wait()
json.dump(modes, open(f'{OUT}/modes.json', 'w'))
# кадр для обложки: камера под полосой, слайд ниже
ks = [k for k, v in enumerate(modes) if v == 1 and k > 90] or [N // 2]
k = ks[min(len(ks) - 1, 60)]
fr = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{k / 30:.3f}', '-i', f'{OUT}/base.mp4', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
fr = np.frombuffer(fr, np.uint8).reshape(VH, VW, 3); cv = np.zeros_like(fr); cv[:] = (14, 26, 42)
cv[300:996] = fr[910:1606]; cv[1002:1606] = fr[300:904]
cv2.imwrite(f'{OUT}/cvframe.png', cv[..., ::-1])
print('DONE', ID, N)
