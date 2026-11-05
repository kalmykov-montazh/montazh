#!/usr/bin/env python3
"""Склейка «Штрафы + 17 ловушек» (05.11.2026). Подготовка: точные стыки по тишине, звук, субтитры, плашки, QR.
Вход: S.mp4, L.mp4, S.words.json, L.words.json рядом. Выход в out/: edl.json, mix.wav, subs.srt, ov/*.png, joins.txt"""
import json, subprocess, os, sys, re, numpy as np, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter
H_ = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(f'{H_}/plan.json'))
os.makedirs('out/ov', exist_ok=True)
SR = 48000; FPS = 30

def pcm(src):
    f = f'{src}.raw'
    if not os.path.exists(f):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{src}.mp4', '-vn', '-ac', '2', '-ar', str(SR), '-f', 's16le', f], check=True)
    return np.memmap(f, np.int16, 'r').reshape(-1, 2)
A = {s: pcm(s) for s in 'SL'}

def quiet(src, a, b):
    """самая тихая точка (окно 40 мс) в [a-0.12, b+0.12]"""
    x = A[src]; i0 = int(max(0, a - 0.12) * SR); i1 = int((b + 0.12) * SR)
    m = np.abs(x[i0:i1].astype(np.float32)).mean(1)
    w = int(0.04 * SR); c = np.convolve(m, np.ones(w) / w, 'same')
    j = int(np.argmin(c[w:-w])) + w
    return (i0 + j) / SR, float(c[j])

def pt(src, v):
    if isinstance(v, list): t, e = quiet(src, *v); return round(t, 3), e
    return float(v), 0.0

edl = []; joins = []
for src, s, e in P['seg']:
    s2, es = pt(src, s); e2, ee = pt(src, e)
    edl.append([src, s2, e2]); joins.append((s2, es, e2, ee))
off = []; o = 0
for src, s, e in edl: off.append(o); o += e - s
BODY = o; END = P['end']['dur']; TOTAL = BODY + END
def out_t(src, t):
    for (sr, s, e), of in zip(edl, off):
        if sr == src and s <= t < e: return of + t - s
    return None

# --- режим кадра для QR: проверка, что 9 с подряд на экране слайд ---
def frame(src, t):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', f'{src}.mp4', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return np.frombuffer(r, np.uint8).reshape(1080, 1920, 3) if len(r) == 1920 * 1080 * 3 else None
def is_slide(src, f):
    if f is None: return False
    if src == 'S':
        r = f[925:960, 160:340].astype(np.float32); m = r.mean((0, 1))
        return abs(m[0] - 15) < 14 and abs(m[1] - 28) < 14 and abs(m[2] - 49) < 16 and r.std() < 10
    st = f[2:6, 100:1800].astype(np.float32); sat = (st.max(2) - st.min(2)).mean()
    return sat > 120
def src_at(T):
    for (sr, s, e), of in zip(edl, off):
        if of <= T < of + e - s: return sr, s + T - of
    return None, None
QR = []
for mn in P['qr_min']:
    T = mn * 60
    while T < BODY - 20:
        ok = True
        for d in (0, 3, 6, 9.5):
            sr, st = src_at(T + d)
            if sr is None or not is_slide(sr, frame(sr, st)): ok = False; break
        if ok: QR.append(round(T, 2)); break
        T += 4
print('QR', QR, flush=True)

# --- главы-плашки ---
CH = [[round(out_t(s, t), 2), k, txt] for s, t, k, txt in P['ch']]
def font(sz):
    p = subprocess.run(['fc-match', '-f', '%{file}', 'Inter:style=Black'], capture_output=True, text=True).stdout
    return ImageFont.truetype(p or 'DejaVuSans-Bold.ttf', sz)
F44, F36, F30, F70 = font(44), font(36), font(30), font(70)
for i, (_, k, txt) in enumerate(CH):
    tmp = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    w1 = tmp.textlength(k + '  ', font=F44); w2 = tmp.textlength(txt, font=F44)
    W_ = int(48 + w1 + w2 + 40); im = Image.new('RGBA', (W_, 84), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W_ - 1, 83], 16, fill=(10, 12, 18, 235)); d.rectangle([0, 0, 10, 83], fill=(255, 205, 40, 255))
    d.text((34, 16), k, font=F44, fill=(255, 205, 40, 255)); d.text((34 + w1, 16), txt, font=F44, fill=(255, 255, 255, 255))
    im.save(f'out/ov/ch{i}.png')

# --- конечная заставка (фон — размытый последний кадр) ---
lst = edl[-1]; f = frame(lst[0], lst[2] - 0.2)
bg = Image.fromarray(f).filter(ImageFilter.GaussianBlur(24)).point(lambda v: int(v * 0.35))
d = ImageDraw.Draw(bg)
d.text((110, 380), P['end']['k'], font=F36, fill=(255, 205, 40))
y = 440
words = P['end']['t'].split(); line = ''
for w in words:
    if d.textlength(line + ' ' + w, font=F70) > 760: d.text((110, y), line.strip(), font=F70, fill=(255, 255, 255)); y += 86; line = ''
    line += ' ' + w
d.text((110, y), line.strip(), font=F70, fill=(255, 255, 255)); d.rectangle([110, y + 108, 230, y + 114], fill=(255, 205, 40))
bg.save('out/ov/end.png')

# --- звук: громкость по источнику к −14 LUFS, стыки с короткой склейкой, вжух на главах и QR ---
def lufs(src):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', f'{src}.mp4', '-vn', '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])
G = {s: 10 ** ((-14 - lufs(s)) / 20) for s in 'SL'}
print('gain', G, flush=True)
fd = int(0.012 * SR); parts = []
for src, s, e in edl:
    x = A[src][int(s * SR):int(e * SR)].astype(np.float32) / 32768 * G[src]
    r = np.linspace(0, 1, fd)[:, None]; x[:fd] *= r; x[-fd:] *= r[::-1]; parts.append(x)
parts.append(np.zeros((int(END * SR), 2), np.float32))
y = np.concatenate(parts)
rng = np.random.default_rng(1)
def bandsweep(n, f0, f1):
    out = np.zeros(n); hop = 512; win = np.hanning(1024); noise = rng.standard_normal(n + 1024); fr = np.fft.rfftfreq(1024, 1 / SR)
    for i in range(0, n, hop):
        S = np.fft.rfft(noise[i:i + 1024] * win); fc = f0 * (f1 / f0) ** (i / n); S *= np.exp(-((np.log(fr + 1) - np.log(fc)) ** 2) / 0.35)
        yy = np.fft.irfft(S); j = min(1024, n - i); out[i:i + j] += yy[:j]
    return out / np.abs(out).max()
def whoosh(v=0.2):
    n = int(0.45 * SR); t = np.linspace(0, 1, n); return v * bandsweep(n, 400, 4000) * np.sin(np.pi * t) ** 2 * np.exp(-t)
def add(t, s):
    p = int(t * SR); e = min(len(y), p + len(s)); y[p:e] += s[:e - p, None]
for t, *_ in CH: add(max(0, t - 0.15), whoosh(0.2))
for t in QR: add(max(0, t - 0.1), whoosh(0.13)); add(t + 9 - 0.35, whoosh(0.1))
add(BODY - 0.1, whoosh(0.15))
pk = np.abs(y).max(); y = y / max(1, pk / 0.89)
with wave.open('out/mix.wav', 'wb') as o_:
    o_.setnchannels(2); o_.setsampwidth(2); o_.setframerate(SR); o_.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())

# --- наезды на суммах: слова с цифрами рядом с «евро», не чаще раза в 30 с ---
WD = {s: json.load(open(f'{s}.words.json')) for s in 'SL'}
PUNCH = []; last = -99
for (src, s, e), of in zip(edl, off):
    ws = WD[src]
    for i, (a, b, w) in enumerate(ws):
        if not (s + 1.5 <= a < e - 1.5): continue
        nxt = ws[i + 1][2] if i + 1 < len(ws) else ''
        if re.search(r'\d', w) and re.match(r'евро|%|процент', nxt.lower()):
            T = of + a - s
            if T - last >= 30 and all(abs(T - q) > 12 for q in QR) and all(abs(T - c) > 6 for c, *_ in CH):
                PUNCH.append(round(T, 2)); last = T

# --- субтитры .srt из распознанной речи готовых роликов ---
def ts(t): h = int(t // 3600); m = int(t % 3600 // 60); s_ = t % 60; return f'{h:02d}:{m:02d}:{int(s_):02d},{int(s_ % 1 * 1000):03d}'
cues = []; cur = []
for (src, s, e), of in zip(edl, off):
    for a, b, w in WD[src]:
        if s <= a and b <= e + 0.05:
            A_, B_ = of + a - s, of + min(b, e) - s
            if cur and (A_ - cur[-1][1] > 0.8 or len(' '.join(x[2] for x in cur + [(0, 0, w)])) > 84 or B_ - cur[0][0] > 5.5):
                cues.append(cur); cur = []
            cur.append((A_, B_, w))
    if cur: cues.append(cur); cur = []
with open('out/subs.srt', 'w', encoding='utf-8') as o_:
    for i, c in enumerate(cues, 1):
        txt = ' '.join(x[2] for x in c)
        if len(txt) > 42:
            sp = [m.start() for m in re.finditer(' ', txt)]; k = min(sp, key=lambda p: abs(p - len(txt) / 2)); txt = txt[:k] + '\n' + txt[k + 1:]
        o_.write(f'{i}\n{ts(c[0][0])} --> {ts(c[-1][1] + 0.15)}\n{txt}\n\n')

json.dump({'edl': edl, 'off': off, 'body': BODY, 'total': TOTAL, 'qr': QR, 'ch': CH, 'punch': PUNCH}, open('out/edl.json', 'w'), ensure_ascii=False)
with open('out/joins.txt', 'w') as o_:
    for i, (s, es, e, ee) in enumerate(joins): o_.write(f'{i} {edl[i][0]} {s:.3f} (тишина {es:.0f}) → {e:.3f} (тишина {ee:.0f}) вых {off[i]:.2f}\n')
print(open('out/joins.txt').read(), 'BODY', round(BODY, 1), 'PUNCH', PUNCH, 'CH', CH, flush=True)
