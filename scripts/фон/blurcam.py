"""Размытый фон для окна камеры. python3 blurcam.py out.mp4 x y w h keepjson start:end [start:end ...]
keepjson: [[y0,y1,x0,x1],...] — зоны, которые всегда остаются резкими (микрофон, стол)."""
import numpy as np, cv2, subprocess, sys, json, onnxruntime as ort
out, X, Y, Wc, Hc, keepj = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
segs = [tuple(map(float, s.split(':'))) for s in sys.argv[7:]]
SRC = '/home/claude/s/src.mp4'
ins, fl = [], ''
for i, (a, b) in enumerate(segs):
    ins += ['-ss', str(a), '-to', str(b), '-i', SRC]; fl += f'[{i}:v]setpts=PTS-STARTPTS[v{i}];'
fl += ''.join(f'[v{i}]' for i in range(len(segs))) + f'concat=n={len(segs)}:v=1:a=0,crop={Wc}:{Hc}:{X}:{Y}'
p = subprocess.Popen(['ffmpeg', '-v', 'error'] + ins + ['-filter_complex', fl, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
o = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{Wc}x{Hc}', '-r', '60', '-i', '-',
                      '-c:v', 'libx264', '-preset', 'fast', '-crf', '12', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
sess = ort.InferenceSession('/home/claude/bg/rvm.onnx', providers=['CPUExecutionProvider'])
rec = [np.zeros([1, 1, 1, 1], np.float32)] * 4
dr = np.array([0.6], np.float32)
keep = np.zeros((Hc, Wc), np.float32)
for y0, y1, x0, x1 in json.loads(keepj): keep[y0:y1, x0:x1] = 1
keep = cv2.GaussianBlur(keep, (0, 0), 2)
n = 0; a = None
while True:
    buf = p.stdout.read(Wc * Hc * 3)
    if len(buf) < Wc * Hc * 3: break
    fr = np.frombuffer(buf, np.uint8).reshape(Hc, Wc, 3)
    if n % 2 == 0:
        x = (fr[..., ::-1].astype(np.float32) / 255).transpose(2, 0, 1)[None]
        _, pha, *rec = sess.run(None, {'src': x, 'r1i': rec[0], 'r2i': rec[1], 'r3i': rec[2], 'r4i': rec[3], 'downsample_ratio': dr})
        a = np.maximum(np.clip(cv2.GaussianBlur(pha[0, 0], (3, 3), 0), 0, 1), keep)[..., None]
    f = fr.astype(np.float32); wgt = 1 - a
    bgb = cv2.GaussianBlur(f * wgt, (0, 0), 9) / (cv2.GaussianBlur(wgt, (0, 0), 9)[..., None] + 1e-3)
    o.stdin.write(np.clip(f * a + bgb * wgt, 0, 255).astype(np.uint8).tobytes())
    n += 1
o.stdin.close(); o.wait(); print('frames', n, flush=True)
