import json, os, re, subprocess, sys, difflib
import numpy as np
import _pywhispercpp as pw
import layout

S = json.load(open('shorts.json'))
ONLY = sys.argv[1:]  # ids
END = (658.30, 659.30)   # «Всё, пошёл работать»
CTAS = [r'Полное видео —\Nна моём YouTube\NСсылка в описании',
        r'Чем закончилось —\Nв полном видео\NСсылка в описании',
        r'Это кусок большого видео\NЦеликом — по ссылке\Nв описании']
FONT = 'Inter Black'
# раскладка 1080x1920
TOPB = 300            # верхняя полоса (надпись / призыв)
SL_Y = TOPB           # слайд 1250x740 -> 1080x639
CAM_Y = SL_Y + 639 + 6  # камера 632x386 -> 1080x660
SUB_BOTTOM = 1440

def run(c): subprocess.run(c, check=True)
def norm(w): return re.sub(r'[^\w]', '', w.lower()).replace('ё', 'е')
def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'

cp = pw.whisper_context_default_params(); cp.dtw_token_timestamps = True; cp.flash_attn = False
cp.dtw_aheads_preset = pw.whisper_alignment_heads_preset.WHISPER_AHEADS_SMALL
ctx = pw.whisper_init_from_file_with_params('model.bin', cp)

def dtw_words(pcm):
    fp = pw.whisper_full_default_params(pw.WHISPER_SAMPLING_GREEDY)
    fp.language = 'ru'; fp.print_progress = False; fp.print_realtime = False; fp.n_threads = 2
    fp.token_timestamps = True
    pw.whisper_full(ctx, fp, pcm, len(pcm))
    words = []
    for s in range(pw.whisper_full_n_segments(ctx)):
        for t in range(pw.whisper_full_n_tokens(ctx, s)):
            d = pw.whisper_full_get_token_data(ctx, s, t)
            txt = pw.whisper_full_get_token_text(ctx, s, t)
            if txt.startswith('[_') or txt.startswith('<|'): continue
            tt = max(0, d.t_dtw / 100)
            if txt.startswith(' ') or not words: words.append([tt, txt.strip()])
            else: words[-1][1] += txt
    return [w for w in words if norm(w[1])]

def align(wav16, text, dur):
    pcm = np.fromfile(wav16, np.int16).astype(np.float32) / 32768
    # куски по 20 с по тишине, чтобы DTW не плыл
    words = []
    n = len(pcm); step = 16000 * 20; pos = 0
    while pos < n:
        end = min(n, pos + step)
        if end < n:   # ищем тихое место в последних 3 с
            win = pcm[end - 48000:end]
            e = np.convolve(np.abs(win), np.ones(1600) / 1600, 'same')
            end = end - 48000 + int(np.argmin(e))
        chunk = np.concatenate([pcm[pos:end], np.zeros(6400, np.float32)])
        for t, w in dtw_words(chunk): words.append([t + pos / 16000, w])
        pos = end
    target = text.split()
    src = [norm(w[1]) for w in words]; dst = [norm(w) for w in target]
    st = [None] * len(target)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, src, dst, autojunk=False).get_opcodes():
        if tag == 'equal':
            for k in range(j2 - j1): st[j1 + k] = words[i1 + k][0]
        elif tag == 'replace' and i2 > i1:
            for k in range(j2 - j1): st[j1 + k] = words[i1 + min(k * (i2 - i1) // (j2 - j1), i2 - i1 - 1)][0]
    for j in range(len(st)):
        if st[j] is None:
            prv = next((st[k] for k in range(j - 1, -1, -1) if st[k] is not None), 0)
            nxt = next((st[k] for k in range(j + 1, len(st)) if st[k] is not None), dur)
            st[j] = (prv + nxt) / 2
    for j in range(1, len(st)): st[j] = max(st[j], st[j - 1] + 0.05)
    out = []
    for j, w in enumerate(target):
        e = st[j + 1] if j + 1 < len(st) else min(dur, st[j] + 0.6)
        out.append([st[j], max(e, st[j] + 0.05), w])
    return out, words

def clean(w): return re.sub(r'[.,!?;:—–"«»]', '', w).replace('-', '-')

def color_of(w, sh):
    n = norm(w)
    if any(n.startswith(norm(p)) for p in sh['red']): return '&H003C3CFF&'   # красный (BGR)
    if any(n.startswith(norm(p)) for p in sh['green']): return '&H0050E650&'
    return None

def make_ass(sh, words, total, cta, SB=1440):
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kar,{FONT},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,3,0,1,7,3,2,150,150,{1920 - SB},1
Style: TitleY,{FONT},84,&H000C0C0C,&H000C0C0C,&H0000D6FF,&H0000D6FF,0,0,0,0,100,100,0,0,3,20,0,8,40,40,0,1
Style: TitleW,{FONT},84,&H000C0C0C,&H000C0C0C,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,3,20,0,8,40,40,0,1
Style: Cta,{FONT},70,&H00FFFFFF,&H00FFFFFF,&H00000000,&HC8000000,0,0,0,0,100,100,0,0,3,24,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    TITLE_SEC = 3.5
    # надпись обложки — первые 3,5 с, в верхней полосе
    for i, ln in enumerate(sh['title']):
        stn = 'TitleW' if ln == sh['hl'] else 'TitleY'
        ev.append(f'Dialogue: 3,{ts(0)},{ts(TITLE_SEC)},{stn},,0,0,0,,' + r'{\an8\pos(540,' + str(48 + i * 122) + r')\fad(0,250)}' + ln)
    # призыв — последние 5 с
    ev.append(f'Dialogue: 4,{ts(total - 5.0)},{ts(total + 1)},Cta,,0,0,0,,' + r'{\an5\pos(540,150)\fscx60\fscy60\t(0,160,\fscx100\fscy100)}' + cta)
    # субтитры по словам: группы до 3 слов / 17 знаков, фраза рвётся на знаках препинания
    groups, cg = [], []
    for k, (s, e, w) in enumerate(words):
        if cg and k == len(words) - 3: groups.append(cg); cg = []
        if cg and (len(' '.join(clean(x[2]) for x in cg + [(s, e, w)])) > 17 or len(cg) >= 3):
            groups.append(cg); cg = []
        cg.append((s, e, w))
        if re.search(r'[.?!,:]$', w): groups.append(cg); cg = []
    if cg: groups.append(cg)
    for gi, g in enumerate(groups):
        nxt = groups[gi + 1][0][0] if gi + 1 < len(groups) else total
        gend = min(nxt, g[-1][1] + 0.6) if gi + 1 < len(groups) else total
        gl = len(' '.join(clean(x[2]) for x in g))
        fz = min(100, int(1200 / gl)) if gl > 12 else 100
        for j, (s, e, w) in enumerate(g):
            we = g[j + 1][0] if j + 1 < len(g) else gend
            parts = []
            for jj, x in enumerate(g):
                tx = clean(x[2]).upper()
                col = color_of(x[2], sh)
                big = 130 if col else 100
                if jj == j:
                    c = col or '&H0000E1FF&'; z = fz * (big + 12) // 100
                else:
                    c = col or '&H00FFFFFF&'; z = fz * big // 100
                parts.append(r'{\c' + c + r'\fscx%d\fscy%d}' % (z, z) + tx)
            pop = r'{\fscx92\fscy92\t(0,90,\fscx100\fscy100)}' if j == 0 and fz == 100 else ''
            st = max(s, TITLE_SEC + 0.05) if s < TITLE_SEC else s
            if we <= TITLE_SEC: continue
            ev.append(f'Dialogue: 0,{ts(st)},{ts(we)},Kar,,0,0,0,,{pop}' + ' '.join(parts))
    return hdr + '\n'.join(ev) + '\n'

for n, sh in enumerate(S):
    if ONLY and sh['id'] not in ONLY: continue
    d = f"w/{sh['id']}"; os.makedirs(d, exist_ok=True)
    a, b = sh['seg']
    total = (b - a) + (END[1] - END[0])
    # звук: кусок + «Всё, пошёл работать», стыки с затуханием 10 мс
    af = (f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.01}:d=0.01[x];"
          f"[0:a]atrim={END[0]}:{END[1]},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={END[1]-END[0]-0.03}:d=0.03[y];[x][y]concat=n=2:v=0:a=1[a]")
    run(['ffmpeg', '-v', 'error', '-y', '-i', 'src.mp4', '-filter_complex', af, '-map', '[a]', '-ar', '16000', '-ac', '1', '-f', 's16le', f'{d}/a16.raw'])
    if os.path.exists(f'{d}/words.json'): words=json.load(open(f'{d}/words.json'))['words']
    else:
      words, raw = align(f'{d}/a16.raw', sh['text'] + ' Всё, пошёл работать', total)
      json.dump({'words': words, 'asr': raw}, open(f'{d}/words.json', 'w'), ensure_ascii=False)
    cta = CTAS[n % 3]
    SLF, OH = layout.slide(sh['id']); CAMY = SL_Y + OH + 6
    open(f'{d}/subs.ass', 'w').write(make_ass(sh, words, total, cta, min(1440, CAMY + 540)))
    # видео
    af2 = (f"[0:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.01}:d=0.01[x];"
           f"[1:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={END[1]-END[0]-0.03}:d=0.03[y];[x][y]concat=n=2:v=0:a=1[a]")
    CAMF = os.environ.get('CAMDIR', '') and f"{os.environ['CAMDIR']}/{sh['id']}.mp4"
    camsrc = "[2:v]setpts=PTS-STARTPTS,scale=1080:660:flags=lanczos,unsharp=5:5:0.5:5:5:0[cm];" if CAMF else "[c]crop=632:386:1287:693,scale=1080:660:flags=lanczos,unsharp=5:5:0.5:5:5:0[cm];"
    vf = (f"[0:v]setpts=PTS-STARTPTS,split=2[v1][s0];[1:v]setpts=PTS-STARTPTS[v2];[v1][v2]concat=n=2:v=1:a=0[c];" + ("[c]nullsink;" if CAMF else "") +
          f"[s0]trim=0:{b-a-1.0:.3f},{SLF},tpad=stop_mode=clone:stop_duration={END[1]-END[0]+1.2:.2f}[sl];"
          + camsrc +
          f"color=c=0x0E1A2A:s=1080x1920:r=60:d={total:.3f}[bg];"
          f"[bg][sl]overlay=0:{SL_Y}:shortest=1[t1];[t1][cm]overlay=0:{CAMY}:shortest=1,subtitles={d}/subs.ass,format=yuv420p[v];" + af2)
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a}', '-to', f'{b}', '-i', 'src.mp4', '-ss', f'{END[0]}', '-to', f'{END[1]}', '-i', 'src.mp4'] + (['-i', CAMF] if CAMF else []) + [
         '-filter_complex', vf, '-map', '[v]', '-map', '[a]', '-threads', '2',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-profile:v', 'high', '-maxrate', '25M', '-bufsize', '50M',
         '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', f'{d}/видео.mp4'])
    print('OK', sh['id'], round(total, 1), flush=True)
print('ALLDONE')
