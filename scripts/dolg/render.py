#!/usr/bin/env python3
"""Шортс из горизонтального лонга (22.10.2026, «17 ловушек аренды»), старая раскладка «Штрафов»:
полоса 300 сверху, слайд, под ним окно камеры; где в лонге крупно — лицо на всю высоту под полосой.
Новое: субтитры «микс», надпись в начале, белая карточка призыва, обложка первым кадром, плашки только на цифрах.
python render.py long.mp4 model.bin job.json workdir
-> workdir/base.mp4, words_out.json, spec.json, modes.json, cover_iv.txt
"""
import json, os, re, subprocess, sys, difflib
import numpy as np

LONG, MODEL, JOB, W = sys.argv[1:5]
os.makedirs(W, exist_ok=True)
job = json.load(open(JOB))
segs = job['segs']
TAIL = 1.2


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

# ---------- время слов: из распознавания всего лонга (job.words, сверено с паузами: медиана 0,0 с) ----------
# DTW по кускам 20 с срывался (22.10: в «01» 40 слов пролетели за 2 с), поэтому только если words нет
if job.get('words'):
    words = job['words']
    print(f'words {len(words)} из распознавания лонга', flush=True)
else:
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
if re.search(r'пош[её]л,? работать', ' '.join(x['w'] for x in words), re.I): sys.exit('в тексте «Всё, пошёл работать»')

# ---------- где крупный план, где слайд с окном камеры (по каждому кадру, 30 к/с) ----------
# у слайдов лонга сверху тонкая цветная полоса (y 1–5), у крупного плана её нет
modes = []; tl = 0.0
for a, b in segs:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', LONG, '-vf', 'fps=30,crop=1600:4:100:1,format=rgb24',
                          '-f', 'rawvideo', '-'], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 4, 1600, 3).astype(float)
    sat = (fr.max(3) - fr.min(3)).mean((1, 2))   # у слайдов сверху цветная полоса (насыщенность ~200), у крупного плана ~18
    sl = (sat > 100).astype(int)
    if job.get('always_slide'): sl[:] = 1   # 28.10.2026: «Штрафы» — у слайдов нет цветной полосы, крупных планов нет
    sm = sl.copy()   # одиночные кадры-выбросы (1–2 кадра) убираем, границы остаются точными
    for i in range(2, len(sl) - 2):
        if sl[i - 2] == sl[i + 2] != sl[i] and (sl[i - 1] == sl[i - 2] or sl[i + 1] == sl[i + 2]): sm[i] = sl[i - 2]
    for i, v in enumerate(sm): modes.append((round(tl + i / 30, 3), int(v)))
    tl += b - a
json.dump(modes, open(f'{W}/modes.json', 'w'))
iv = []; cur = None
for t, v in modes:
    if v and cur is None: cur = t
    if not v and cur is not None: iv.append([cur, t]); cur = None
if cur is not None: iv.append([cur, total_sp + TAIL])
print('слайд:', iv, flush=True)
close = []; prev = 0.0
for x0, x1 in iv + [[total_sp + TAIL, total_sp + TAIL]]:
    if x0 - prev > 0.05: close.append([prev, x0])
    prev = x1
print('крупно:', close, flush=True)

# ---------- раскладка как в шортсах из «Штрафов»: полоса 300, слайд, под ним окно камеры; крупный план — лицо на всю высоту ----------
TOPB = 300; BG = '0x0E1A2A'
SLIDE = 'crop=1214:680:68:40,scale=1080:604:flags=lanczos'           # слайд без угла камеры (x < 1287)
CAM_Y = TOPB + 604 + 6
# крупный план: лицо по центру, плашка лонга (y>850) отрезана
import cv2
_hx = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'haar.xml')
fc = cv2.CascadeClassifier(_hx if os.path.exists(_hx) else cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')   # 28.10.2026: haar.xml в хранилище нет
def tl2src(t):
    acc = 0.0
    for a, b in segs:
        if t < acc + (b - a): return a + (t - acc)
        acc += b - a
    return segs[-1][1] - 0.1
xs = []
for c0, c1 in close:
    for k in range(3):
        t = c0 + (c1 - c0) * (k + 1) / 4
        img = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{tl2src(t):.3f}', '-i', LONG, '-frames:v', '1', '-vf', 'scale=960:540,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
        if len(img) < 960 * 540: continue
        g = np.frombuffer(img, np.uint8).reshape(540, 960)
        f = fc.detectMultiScale(g[:430], 1.1, 5, minSize=(50, 50))
        if len(f): x, y, w, h = max(f, key=lambda r: r[2] * r[3]); xs.append((x + w / 2) * 2)
FX = int(np.median(xs)) if xs else 990
CW = 566   # 566x850 -> 1080x1620
CX0 = max(0, min(1800 - CW, FX - CW // 2))
CLOSE = f'crop={CW}:850:{CX0}:0,scale=1080:1620:flags=lanczos'
print('лицо крупно x =', FX, 'по', len(xs), 'кадрам', flush=True)
# окно камеры на слайде: обрезаем по лицу, чтобы ты был по центру (22.10: в окне сидел правее центра)
cx, cy = [], []
for c0, c1 in iv:
    for k in range(3):
        t = c0 + (c1 - c0) * (k + 1) / 4
        if t >= total_sp: continue
        img = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{tl2src(t):.3f}', '-i', LONG, '-frames:v', '1', '-vf', 'crop=512:436:1288:644,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
        if len(img) < 512 * 436: continue
        g = np.frombuffer(img, np.uint8).reshape(436, 512)
        f = fc.detectMultiScale(g, 1.1, 5, minSize=(40, 40))
        if len(f): x, y, w, h = max(f, key=lambda r: r[2] * r[3]); cx.append(1288 + x + w / 2); cy.append(644 + y)
CWW, CWH = 400, 258   # 400x258 -> 1080x696
FCX = float(np.median(cx)) if cx else 1544; FCY = float(np.median(cy)) if cy else 720
CX = int(max(1288, min(1800 - CWW, FCX - CWW / 2))); CY = int(max(644, min(1080 - CWH, FCY - 50)))
CAM = f'crop={CWW}:{CWH}:{CX}:{CY},scale=1080:696:flags=lanczos,unsharp=5:5:0.5:5:5:0'
print('окно камеры: лицо', round(FCX), round(FCY), 'по', len(cx), 'кадрам, кадр', CX, CY, flush=True)
expr = '+'.join(f'between(t,{x0:.3f},{x1 - 0.001:.3f})' for x0, x1 in close) or '0'

vf = ''.join(f'[{i}:v]setpts=PTS-STARTPTS,fps=30[v{i}];' for i in range(n))
vf += ''.join(f'[v{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=0,tpad=stop_mode=clone:stop_duration={TAIL},split=3[va][vb][vc];'
vf += f'color=c={BG}:s=1080x1920:r=30:d={total_sp + TAIL:.3f}[bg];'
# слайд в лонге переключается на следующую ловушку чуть раньше речи: если смена слайда в последние 8 с — держим прежний слайд
sch = []; tl0 = 0.0
for a, b in segs:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', LONG, '-vf', 'fps=10,crop=1214:680:68:40,scale=96:54,format=gray',
                          '-f', 'rawvideo', '-'], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 54, 96).astype(float)
    for i in range(1, len(fr)):
        t = tl0 + i / 10
        both = any(x0 <= t - 0.1 and t < x1 for x0, x1 in iv)
        if both and np.abs(fr[i] - fr[i - 1]).mean() > 6: sch.append(round(t, 2))
    tl0 += b - a
late = [t - 0.15 for t in sch if t > total_sp - 8]
# слайд вернулся после крупного плана в последние 8 с — там может быть уже следующий слайд; держим кадр до крупного плана
for k in range(1, len(iv)):
    if iv[k][0] > total_sp - 8 and iv[k][0] < total_sp: late.append(iv[k - 1][1] - 0.15)
late.sort()
SLV = SLIDE
if late:
    tf = late[0]
    SLV = f'trim=end={tf:.3f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={total_sp + TAIL - tf + 1:.3f},{SLIDE}'
    print('смена слайда в конце на', late[0], 'с — держу прежний слайд', flush=True)
vf += f'[va]{SLV}[sl];[vb]{CAM}[cm];[vc]{CLOSE}[cl];'
vf += f'[bg][sl]overlay=0:{TOPB}:shortest=1[t1];[t1][cm]overlay=0:{CAM_Y}:shortest=1[t2];'
vf += f'[t2][cl]overlay=0:{TOPB}:shortest=1:enable=\'{expr}\',format=yuv420p[vo];'
vf += af.replace('[ac]', '[ac0]') + f';[ac0]apad=pad_dur={TAIL}[ao]'
run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', vf, '-map', '[vo]', '-map', '[ao]', '-r', '30',
     '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
     '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', f'{W}/base.mp4'])

# кадр обложки — со слайдом и тобой: окно камеры сразу под полосой, слайд ниже (надпись обложки ложится на слайд, лицо открыто).
# Берётся первый участок слайда от 3 с — там слайд этой ловушки.
sl_iv = [x for x in iv if x[1] - x[0] >= 3] or [x for x in iv if x[1] - x[0] > 1] or [[0, min(10, total_sp)]]
best = sl_iv[0]
c0, c1 = best[0] + 0.5, min(best[1] - 0.2, best[0] + 10)
cvf = (f"color=c={BG}:s=1080x1920:r=30:d={c1 - c0:.3f}[bg];[0:v]fps=30,split=2[a][b];[a]{CAM}[cm];[b]{SLIDE}[sl];"
       f"[bg][cm]overlay=0:{TOPB}:shortest=1[t1];[t1][sl]overlay=0:{TOPB + 696 + 6}:shortest=1,format=yuv420p[v]")
run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{tl2src(c0):.3f}', '-t', f'{c1 - c0:.3f}', '-i', LONG, '-filter_complex', cvf, '-map', '[v]', '-map', '0:a',
     '-c:v', 'libx264', '-crf', '16', '-c:a', 'aac', f'{W}/cv.mp4'])
open(f'{W}/cover_iv.txt', 'w').write(f'{c0:.2f} {c1:.2f}\n')

# плашки на цифрах: в пустом месте слайда (y≈720); если в этот момент крупный план — выше головы (y≈470)
spec = job['spec']
def nw(x): return re.sub(r'[^\wё]', '', x.lower())
lw = [nw(x['w']) for x in words]
def find(ph, after=0.0):
    ph = [nw(x) for x in ph.split() if nw(x)]
    for i in range(len(lw)):
        if words[i]['s'] + 0.01 < after: continue
        if all(i + k < len(lw) and lw[i + k].startswith(ph[k][:max(3, len(ph[k]) - 2)]) for k in range(len(ph))): return words[i]['s']
    return None
TOPY = spec.get('top_y', 600)
for g in spec.get('groups', []):
    t = find(g['items'][0]['at']) or 0
    incl = any(c0 <= t < c1 for c0, c1 in close)
    for it in g['items']: it['dy'] = (470 if incl else 720) - TOPY
    # плашка уходит до смены слайд/крупно (22.10: в «06» плашка из крупного плана осталась на тексте слайда)
    sw = next((c1 for c0, c1 in (close if incl else iv) if c0 <= t < c1), None)
    te = find(g['end'], t + 0.01) if isinstance(g.get('end'), str) else None
    lim = [x for x in (sw - 0.15 if sw else None, te) if x]
    if lim: g['end'] = round(min(lim), 2)
json.dump(spec, open(f'{W}/spec.json', 'w'), ensure_ascii=False)
print('base ok', round(total_sp + TAIL, 1), 'с; обложка со слайдом из', best, flush=True)
