#!/usr/bin/env python3
"""Шортс нового стиля из горизонтального лонга (22.10.2026, «17 ловушек аренды»).
python render.py long.mp4 model.bin job.json workdir
Раскладка 1080x1920: размытый фон, по центру окно 1080x920 (y=420):
  крупный план лонга — кадр 1080x800 вокруг лица без плашки лонга;
  слайд + камера в углу — окно камеры, увеличенное в 2,14 раза (слайд не показываем, смысл несут наши плашки).
Сверху (150–410) надпись и плашки, снизу (1380–1540) субтитры «микс». Конец — 1,2 с стоп-кадра под белую карточку призыва.
-> workdir/base.mp4 (без наложений, 30 к/с), words_out.json, spec.json, modes.json, cover_t.txt
"""
import json, os, re, subprocess, sys, difflib
import numpy as np

LONG, MODEL, JOB, W = sys.argv[1:5]
os.makedirs(W, exist_ok=True)
job = json.load(open(JOB))
segs = job['segs']
TAIL = 1.2
WIN_Y = 420
CLOSE = 'crop=940:800:520:40,scale=1080:920:flags=lanczos'
CAMW = 'crop=504:429:1292:648,scale=1080:920:flags=lanczos,unsharp=5:5:0.6:5:5:0'


def run(c): subprocess.run(c, check=True)
def norm(w): return re.sub(r'[^\wё]', '', w.lower()).replace('ё', 'е')


# ---------- звук кусков (16 кГц для выравнивания) ----------
ins = []
for a, b in segs: ins += ['-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', LONG]
n = len(segs)
af = ''.join(f'[{i}:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b - a - 0.012:.3f}:d=0.012[a{i}];' for i, (a, b) in enumerate(segs))
af += ''.join(f'[a{i}]' for i in range(n)) + f'concat=n={n}:v=0:a=1[ac]'
run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', af + ';[ac]aresample=16000[o]', '-map', '[o]', '-ac', '1', '-f', 's16le', f'{W}/a16.raw'])
total_sp = sum(b - a for a, b in segs)

# ---------- точное время слов (DTW, как в шортсах из лонга 10.10.2026) ----------
import _pywhispercpp as pw
cp = pw.whisper_context_default_params(); cp.dtw_token_timestamps = True; cp.flash_attn = False
cp.dtw_aheads_preset = pw.whisper_alignment_heads_preset.WHISPER_AHEADS_SMALL
ctx = pw.whisper_init_from_file_with_params(MODEL, cp)


def dtw_words(pcm):
    fp = pw.whisper_full_default_params(pw.WHISPER_SAMPLING_GREEDY)
    fp.language = 'ru'; fp.print_progress = False; fp.print_realtime = False; fp.n_threads = os.cpu_count(); fp.token_timestamps = True
    pw.whisper_full(ctx, fp, pcm, len(pcm))
    out = []
    for s in range(pw.whisper_full_n_segments(ctx)):
        for t in range(pw.whisper_full_n_tokens(ctx, s)):
            d = pw.whisper_full_get_token_data(ctx, s, t); tx = pw.whisper_full_get_token_text(ctx, s, t)
            if tx.startswith('[_') or tx.startswith('<|'): continue
            tt = max(0, d.t_dtw / 100)
            if tx.startswith(' ') or not out: out.append([tt, tx.strip()])
            else: out[-1][1] += tx
    return [w for w in out if norm(w[1])]


pcm = np.fromfile(f'{W}/a16.raw', np.int16).astype(np.float32) / 32768
heard = []; pos = 0; step = 16000 * 20
while pos < len(pcm):
    end = min(len(pcm), pos + step)
    if end < len(pcm):
        win = pcm[end - 48000:end]; e = np.convolve(np.abs(win), np.ones(1600) / 1600, 'same'); end = end - 48000 + int(np.argmin(e))
    ch = np.concatenate([pcm[pos:end], np.zeros(6400, np.float32)])
    for t, w in dtw_words(ch): heard.append([t + pos / 16000, w])
    pos = end
target = [w for w in job['text'].split() if norm(w)]
src = [norm(w[1]) for w in heard]; dst = [norm(w) for w in target]
st = [None] * len(target)
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, src, dst, autojunk=False).get_opcodes():
    if tag == 'equal':
        for k in range(j2 - j1): st[j1 + k] = heard[i1 + k][0]
    elif tag == 'replace' and i2 > i1:
        for k in range(j2 - j1): st[j1 + k] = heard[i1 + min(k * (i2 - i1) // (j2 - j1), i2 - i1 - 1)][0]
for j in range(len(st)):
    if st[j] is None:
        prv = next((st[k] for k in range(j - 1, -1, -1) if st[k] is not None), 0)
        nxt = next((st[k] for k in range(j + 1, len(st)) if st[k] is not None), total_sp)
        st[j] = (prv + nxt) / 2
for j in range(1, len(st)): st[j] = max(st[j], st[j - 1] + 0.05)
words = []
for j, w in enumerate(target):
    e = st[j + 1] if j + 1 < len(st) else min(total_sp, st[j] + 0.6)
    words.append({'w': w, 's': round(st[j], 3), 'e': round(max(e, st[j] + 0.05), 3)})
json.dump(words, open(f'{W}/words_out.json', 'w'), ensure_ascii=False)
match = sum(1 for x in st if x is not None)
eq = sum(j2 - j1 for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, src, dst, autojunk=False).get_opcodes() if tag == 'equal')
print(f'words {len(words)} совпало с распознанным {eq}/{len(dst)}', flush=True)
if re.search(r'пош[её]л,? работать', ' '.join(x['w'] for x in words), re.I): sys.exit('в тексте «Всё, пошёл работать»')

# ---------- где крупный план, где слайд с окном камеры ----------
# у слайда на x=1287 резкая граница окна камеры: слева фон слайда, справа комната
modes = []; tl = 0.0
for a, b in segs:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', LONG, '-vf', 'fps=5,crop=24:360:1275:690,format=gray',
                          '-f', 'rawvideo', '-'], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 360, 24).astype(float)
    d = np.abs(fr[:, :, 4:10].mean(2) - fr[:, :, 14:20].mean(2)).mean(1)   # граница около x=1287
    flat = (np.abs(np.diff(fr[:, :, :10], axis=2)).mean((1, 2)) + np.abs(np.diff(fr[:, :, 14:], axis=2)).mean((1, 2))) / 2
    sl = (d > 18) & (d > 3 * flat)
    k = 5; sm = np.array([np.median(sl[max(0, i - k // 2):i + k // 2 + 1]) for i in range(len(sl))]) > 0.5
    for i, v in enumerate(sm): modes.append((round(tl + i / 5, 2), int(v), round(float(d[i]), 1)))
    tl += b - a
json.dump(modes, open(f'{W}/modes.json', 'w'))
iv = []   # интервалы слайда во времени ролика
cur = None
for t, v, _ in modes:
    if v and cur is None: cur = t
    if not v and cur is not None: iv.append([cur, t]); cur = None
if cur is not None: iv.append([cur, total_sp + TAIL])
iv = [x for x in iv if x[1] - x[0] >= 0.6]
print('слайд с окном камеры:', iv, flush=True)
expr = '+'.join(f'between(t,{x0:.2f},{x1:.2f})' for x0, x1 in iv) or '0'

# ---------- картинка ----------
vf = ''.join(f'[{i}:v]setpts=PTS-STARTPTS,fps=30[v{i}];' for i in range(n))
vf += ''.join(f'[v{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=0,tpad=stop_mode=clone:stop_duration={TAIL},split=2[va][vb];'
vf += f'[va]{CLOSE}[cw];[vb]{CAMW}[sw];[cw][sw]overlay=0:0:enable=\'{expr}\',split=2[w1][w2];'
vf += '[w2]crop=518:920:281:0,scale=1080:1920,boxblur=28:3,eq=brightness=-0.10:saturation=0.85[bg];'
vf += '[w1]drawbox=x=0:y=0:w=iw:h=ih:color=white@0.9:t=5[wb];'
vf += f'[bg][wb]overlay=0:{WIN_Y},format=yuv420p[vo];'
vf += af.replace('[ac]', '[ac0]') + f';[ac0]apad=pad_dur={TAIL}[ao]'
run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', vf, '-map', '[vo]', '-map', '[ao]', '-r', '30',
     '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
     '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', f'{W}/base.mp4'])

# кадр для обложки — середина самого длинного крупного плана (лицо чётче)
close = []; prev = 0.0
for x0, x1 in iv + [[total_sp, total_sp]]:
    if x0 - prev > 0: close.append([prev, x0])
    prev = x1
close = [c for c in close if c[1] - c[0] > 1.5]
best = max(close, key=lambda c: c[1] - c[0]) if close else [0, total_sp]
open(f'{W}/cover_iv.txt', 'w').write(f'{best[0]:.2f} {min(best[1], best[0] + 12):.2f}')
spec = job['spec']
json.dump(spec, open(f'{W}/spec.json', 'w'), ensure_ascii=False)
print('base ok', round(total_sp + TAIL, 1), 'с; кадр обложки ищу в', best, flush=True)
