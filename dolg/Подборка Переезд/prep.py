#!/usr/bin/env python3
"""Подборка из готовых лонгов (15.11.2026). Подготовка: стыки по тишине, звук −14 LUFS по источнику, главы, вжух,
QR (только где правый верх кадра неподвижен 9 с), наезды на суммах, .srt, оглавление для описания.
Вход рядом: K.mov (1080p30), K.words.json; plan.json в папке скрипта. Выход в out/."""
import json, subprocess, os, re, numpy as np, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter
H_ = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(f'{H_}/plan.json'))
os.makedirs('out/ov', exist_ok=True)
SR = 48000
KEYS = sorted({s for s, *_ in P['seg']})

def pcm(src):
    f = f'{src}.raw'
    if not os.path.exists(f):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{src}.mov', '-vn', '-ac', '2', '-ar', str(SR), '-f', 's16le', f], check=True)
    return np.memmap(f, np.int16, 'r').reshape(-1, 2)
A = {s: pcm(s) for s in KEYS}

def quiet(src, a, b):
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
def out_t(src, t, after=0):
    for (sr, s, e), of in zip(edl, off):
        if sr == src and s - 0.3 <= t < e and of >= after: return of + max(0, t - s)
    return None

def frame(src, t, small=True):
    vf = ['-vf', 'scale=480:270'] if small else []
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', f'{src}.mov', '-frames:v', '1', *vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    w, h = (480, 270) if small else (1920, 1080)
    return np.frombuffer(r, np.uint8).reshape(h, w, 3).astype(np.float32) if len(r) == w * h * 3 else None
def src_at(T):
    for (sr, s, e), of in zip(edl, off):
        if of <= T < of + e - s: return sr, s + T - of
    return None, None
# QR 390x? справа сверху (x 1390–1920, y 150–560): там должно быть неподвижно 9 с (слайд, а не лицо и не улица)
QH = Image.open(f'{H_}/qr.png').size[1]
def calm(T):
    fr = []
    for d in (0, 3, 6, 9.5):
        sr, st = src_at(T + d)
        if sr is None or sr not in P.get('qr_src', KEYS): return False
        f = frame(sr, st)
        if f is None: return False
        fr.append(f[37:int((150 + QH) / 4) + 2, 347:480])
    return all(np.abs(fr[0] - x).mean() < 4 for x in fr[1:]) and max(x.std() for x in fr) > 3
QR = []
for mn in P['qr_min']:
    T = mn * 60
    while T < min(BODY - 20, mn * 60 + 300):
        if calm(T): QR.append(round(T, 2)); break
        T += 4
print('QR', QR, flush=True)

def font(sz):
    p = subprocess.run(['fc-match', '-f', '%{file}', 'Inter:style=Black'], capture_output=True, text=True).stdout
    return ImageFont.truetype(p or 'DejaVuSans-Bold.ttf', sz)
F44, F36, F70 = font(44), font(36), font(70)
CH = []
for c in P['ch']:
    src, t, k, txt = c[:4]; after = c[4] if len(c) > 4 else 0; yy = c[5] if len(c) > 5 else 22; du = c[6] if len(c) > 6 else 4.0
    CH.append([round(out_t(src, t, after), 2), k, txt, yy, du])
for i, (_, k, txt, *_r) in enumerate(CH):
    tmp = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    w1 = tmp.textlength(k + '  ', font=F44) if k else 0; w2 = tmp.textlength(txt, font=F44)
    W_ = int(48 + w1 + w2 + 40); im = Image.new('RGBA', (W_, 84), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W_ - 1, 83], 16, fill=(10, 12, 18, 235)); d.rectangle([0, 0, 10, 83], fill=(255, 205, 40, 255))
    if k: d.text((34, 16), k, font=F44, fill=(255, 205, 40, 255))
    d.text((34 + w1, 16), txt, font=F44, fill=(255, 255, 255, 255))
    im.save(f'out/ov/ch{i}.png')

# конечная заставка: размытый последний кадр + «СМОТРИТЕ ДАЛЬШЕ»
lst = edl[-1]; f = frame(lst[0], lst[2] - 0.2, small=False)
bg = Image.fromarray(f.astype(np.uint8)).filter(ImageFilter.GaussianBlur(24)).point(lambda v: int(v * 0.35))
d = ImageDraw.Draw(bg); d.text((110, 380), P['end']['k'], font=F36, fill=(255, 205, 40)); y = 440; line = ''
for w in P['end']['t'].split():
    if d.textlength(line + ' ' + w, font=F70) > 760: d.text((110, y), line.strip(), font=F70, fill=(255, 255, 255)); y += 86; line = ''
    line += ' ' + w
d.text((110, y), line.strip(), font=F70, fill=(255, 255, 255)); d.rectangle([110, y + 108, 230, y + 114], fill=(255, 205, 40))
bg.save('out/ov/end.png')

def lufs(src):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', f'{src}.mov', '-vn', '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])
G = {s: 10 ** ((-14 - lufs(s)) / 20) for s in KEYS}
print('gain', G, flush=True)
fd = int(0.015 * SR); parts = []
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

WD = {s: json.load(open(f'{s}.words.json')) for s in KEYS}
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

def ts(t): h = int(t // 3600); m = int(t % 3600 // 60); s_ = t % 60; return f'{h:02d}:{m:02d}:{int(s_):02d},{int(s_ % 1 * 1000):03d}'
fixes = P.get('fix', {})
cues = []; cur = []
for (src, s, e), of in zip(edl, off):
    for a, b, w in WD[src]:
        if s - 0.05 <= a and b <= e + 0.05:
            w = fixes.get(w, w)
            A_, B_ = of + max(a, s) - s, of + min(b, e) - s
            if cur and (A_ - cur[-1][1] > 0.8 or len(' '.join(x[2] for x in cur + [(0, 0, w)])) > 84 or B_ - cur[0][0] > 5.5):
                cues.append(cur); cur = []
            cur.append((A_, B_, w))
    if cur: cues.append(cur); cur = []
with open('out/subs.srt', 'w', encoding='utf-8') as o_:
    for i, c in enumerate(cues, 1):
        txt = ' '.join(x[2] for x in c)
        if len(txt) > 42 and ' ' in txt:
            sp = [m.start() for m in re.finditer(' ', txt)]; k = min(sp, key=lambda p: abs(p - len(txt) / 2)); txt = txt[:k] + '\n' + txt[k + 1:]
        o_.write(f'{i}\n{ts(c[0][0])} --> {ts(c[-1][1] + 0.15)}\n{txt}\n\n')

def mmss(t): t = int(t); return f'{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}' if t >= 3600 else f'{t // 60:02d}:{t % 60:02d}'
toc = []
for c in P['toc']:
    src, t, txt = c[:3]; after = c[3] if len(c) > 3 else 0
    T = 0 if src == '0' else out_t(src, t, after)
    toc.append(f'{mmss(T) if T is not None else "??"} {txt}')
open('out/toc.txt', 'w').write('\n'.join(toc))
check = sorted({round(x, 1) for x in [3, 10, 20] + [of + d for of in off[1:] for d in (-1.5, 0.5, 2)] + [c[0] + 1.5 for c in CH] + [q + 4 for q in QR] + PUNCH[:6] + [BODY + 5]})
json.dump({'edl': edl, 'off': off, 'body': BODY, 'total': TOTAL, 'qr': QR, 'ch': CH, 'punch': PUNCH, 'intro': P.get('intro'), 'check': check},
          open('out/edl.json', 'w'), ensure_ascii=False)
with open('out/joins.txt', 'w') as o_:
    for i, (s, es, e, ee) in enumerate(joins): o_.write(f'{i} {edl[i][0]} {s:.3f} (тишина {es:.0f}) → {e:.3f} (тишина {ee:.0f}) вых {off[i]:.2f}\n')
print(open('out/joins.txt').read(), 'BODY', round(BODY, 1), 'PUNCH', PUNCH, 'CH', CH, '\n' + '\n'.join(toc), flush=True)
