#!/usr/bin/env python3
"""Разбор готового горизонтального лонга для нарезки шортсов (22.10.2026).
python razbor.py long.mp4 model.bin outdir
-> outdir/asr.json  [[start,end,"слово"],...] по всему ролику (время готового лонга)
-> outdir/text.txt  строки «мм:сс текст» по фразам
-> outdir/silence.txt  тишины (-38 dB, 0.12 с)
-> outdir/sheet_NN.jpg  кадры каждые 5 с сеткой с подписями времени
"""
import json, os, subprocess, sys
import numpy as np
import _pywhispercpp as pw
SRC, MODEL, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
def run(c): subprocess.run(c, check=True)
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', SRC], capture_output=True, text=True).stdout)
# кадры
fd = f'{OUT}/fr'; os.makedirs(fd, exist_ok=True)
run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-vf', "fps=1/5,scale=384:216,drawtext=text='%{eif\\:t*5/60\\:d}\\:%{eif\\:mod(t*5\\,60)\\:d\\:2}':x=6:y=6:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.7", f'{fd}/%04d.jpg'])
n = len(os.listdir(fd))
for k in range(0, n, 48):
    run(['ffmpeg', '-v', 'error', '-y', '-start_number', str(k + 1), '-i', f'{fd}/%04d.jpg', '-frames:v', '1', '-vf', 'tile=6x8', f'{OUT}/sheet_{k // 48:02d}.jpg'])
# тишины
r = subprocess.run(['ffmpeg', '-v', 'info', '-i', SRC, '-af', 'silencedetect=n=-38dB:d=0.12', '-f', 'null', '-'], capture_output=True, text=True).stderr
open(f'{OUT}/silence.txt', 'w').write('\n'.join(l for l in r.splitlines() if 'silence_' in l))
# речь
run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-ar', '16000', '-ac', '1', '-f', 's16le', f'{OUT}/a16.raw'])
pcm = np.fromfile(f'{OUT}/a16.raw', np.int16).astype(np.float32) / 32768
cp = pw.whisper_context_default_params(); cp.flash_attn = False
ctx = pw.whisper_init_from_file_with_params(MODEL, cp)
words = []; lines = []
step = 16000 * 60; pos = 0
while pos < len(pcm):
    end = min(len(pcm), pos + step)
    if end < len(pcm):
        win = pcm[end - 64000:end]; e = np.convolve(np.abs(win), np.ones(1600) / 1600, 'same'); end = end - 64000 + int(np.argmin(e))
    ch = np.concatenate([pcm[pos:end], np.zeros(8000, np.float32)])
    fp = pw.whisper_full_default_params(pw.WHISPER_SAMPLING_GREEDY)
    fp.language = 'ru'; fp.print_progress = False; fp.print_realtime = False; fp.n_threads = os.cpu_count(); fp.token_timestamps = True
    fp.initial_prompt = 'Аренда квартиры в Испании. Залог, агентство, договор, Idealista, empadronamiento, ловушки.'
    pw.whisper_full(ctx, fp, ch, len(ch))
    for s in range(pw.whisper_full_n_segments(ctx)):
        t0 = pw.whisper_full_get_segment_t0(ctx, s) / 100 + pos / 16000
        txt = pw.whisper_full_get_segment_text(ctx, s).strip()
        lines.append(f'{int(t0 // 60):02d}:{t0 % 60:05.2f} {txt}')
        for t in range(pw.whisper_full_n_tokens(ctx, s)):
            d = pw.whisper_full_get_token_data(ctx, s, t); tx = pw.whisper_full_get_token_text(ctx, s, t)
            if tx.startswith('[_') or tx.startswith('<|'): continue
            a = d.t0 / 100 + pos / 16000; b = d.t1 / 100 + pos / 16000
            if tx.startswith(' ') or not words: words.append([a, b, tx.strip()])
            else: words[-1][1] = b; words[-1][2] += tx
    pos = end
    print('asr', round(pos / 16000), '/', round(dur), flush=True)
json.dump(words, open(f'{OUT}/asr.json', 'w'), ensure_ascii=False)
open(f'{OUT}/text.txt', 'w').write('\n'.join(lines))
os.remove(f'{OUT}/a16.raw')
print('DONE', dur, len(words))
