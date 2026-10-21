import numpy as np, cv2, subprocess, onnxruntime as ort
SRC = '/home/claude/s/src.mp4'
A, B, E0, E1 = 429.98, 453.06, 658.30, 659.30
Wc, Hc = 632, 386
cmd = ['ffmpeg', '-v', 'error', '-ss', str(A), '-to', str(B), '-i', SRC, '-ss', str(E0), '-to', str(E1), '-i', SRC,
       '-filter_complex', f'[0:v]setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0,crop={Wc}:{Hc}:1287:693',
       '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
sess = ort.InferenceSession('rvm.onnx', providers=['CPUExecutionProvider'])
rec = [np.zeros([1, 1, 1, 1], np.float32)] * 4
dr = np.array([0.6], np.float32)
shelf = cv2.resize(cv2.imread('shelf.png'), (Wc, Hc), interpolation=cv2.INTER_AREA).astype(np.float32)
outs = {k: subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{Wc}x{Hc}', '-r', '60', '-i', '-',
                             '-c:v', 'libx264', '-preset', 'fast', '-crf', '12', '-pix_fmt', 'yuv420p', f'cam_{k}.mp4'], stdin=subprocess.PIPE)
        for k in ('blur', 'shelf', 'corner')}
# маска «левого угла» и велосипеда для варианта corner
xx = np.arange(Wc)[None, :].astype(np.float32); yy = np.arange(Hc)[:, None].astype(np.float32)
left = np.clip((250 - xx) / 120, 0, 1) * np.ones((Hc, 1), np.float32)
rightlow = np.clip((xx - 430) / 60, 0, 1) * np.clip((yy - 150) / 40, 0, 1)
cmask = np.maximum(left, rightlow)[..., None]
keep = np.zeros((Hc, Wc), np.float32)
keep[248:, 262:338] = 1; keep[354:, :] = 1
keep = cv2.GaussianBlur(keep, (0, 0), 2)[..., None]
n = 0
while True:
    buf = p.stdout.read(Wc * Hc * 3)
    if len(buf) < Wc * Hc * 3: break
    fr = np.frombuffer(buf, np.uint8).reshape(Hc, Wc, 3)
    x = (fr[..., ::-1].astype(np.float32) / 255).transpose(2, 0, 1)[None]
    fgr, pha, *rec = sess.run(None, {'src': x, 'r1i': rec[0], 'r2i': rec[1], 'r3i': rec[2], 'r4i': rec[3], 'downsample_ratio': dr})
    a = pha[0, 0][..., None]
    a = cv2.GaussianBlur(a, (3, 3), 0)[..., None] if a.ndim == 3 else a
    a = np.clip(a, 0, 1)
    a = np.maximum(a, keep)
    f = fr.astype(np.float32)
    # 1. размытый свой фон (как портретный режим)
    wgt = 1 - a
    bgb = cv2.GaussianBlur(f * wgt, (0, 0), 9) / (cv2.GaussianBlur(wgt, (0, 0), 9)[..., None] + 1e-3)
    o1 = f * a + bgb * (1 - a)
    # 2. полка
    o2 = f * a + shelf * (1 - a)
    # 3. свой фон: левый угол и велосипед размыты и затемнены
    dark = cv2.GaussianBlur(f * wgt, (0, 0), 7) / (cv2.GaussianBlur(wgt, (0, 0), 7)[..., None] + 1e-3) * 0.45
    bg3 = f * (1 - cmask) + dark * cmask
    o3 = f * a + bg3 * (1 - a)
    for k, o in (('blur', o1), ('shelf', o2), ('corner', o3)):
        outs[k].stdin.write(np.clip(o, 0, 255).astype(np.uint8).tobytes())
    if n == 300: cv2.imwrite('test.jpg', np.vstack([np.hstack([fr, o1.astype(np.uint8)]), np.hstack([o2.astype(np.uint8), o3.astype(np.uint8)])]))
    n += 1
for o in outs.values(): o.stdin.close(); o.wait()
print('frames', n)
