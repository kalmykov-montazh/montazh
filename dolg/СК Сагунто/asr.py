#!/usr/bin/env python3
"""Подборка: распознавание готового лонга по словам. python asr.py KEY  (рядом a.wav) → KEY.words.json, KEY.txt"""
import json, os, re, subprocess, sys
from pywhispercpp.model import Model
K = sys.argv[1]
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', 'a.wav'], capture_output=True, text=True).stdout)
log = subprocess.run(['ffmpeg', '-i', 'a.wav', '-af', 'silencedetect=noise=-40dB:d=0.35', '-f', 'null', '-'], capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
ch = []; cur = 0.0
for a, b in zip(st, en + [dur] * (len(st) - len(en))):
    if a - cur > 0.15: ch.append([cur, a])
    cur = b
if dur - cur > 0.15: ch.append([cur, dur])
# слить мелкие куски до ~20 с, длинные порезать по 28 с
g = []
for a, b in ch:
    if g and b - g[-1][0] < 20 and a - g[-1][1] < 1.5: g[-1][1] = b
    else: g.append([a, b])
ch = []
for a, b in g:
    while b - a > 28: ch.append([a, a + 25]); a += 25
    ch.append([a, b])
m = Model(os.environ['WMODEL'], n_threads=4, print_progress=False, print_realtime=False, redirect_whispercpp_logs_to=None)
P = 'Испания, Валенсия, Сагунто, Airbnb, Booking, аренда по комнатам, долгосрок, краткосрок, автономо, ВНЖ, управление недвижимостью, собственник, жильцы, коммуналка, ремонт.'
W = []; prev = ''; lines = []
for i, (a, b) in enumerate(ch):
    A = max(0, a - 0.05); B = min(dur, b + 0.1)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{A:.3f}', '-to', f'{B:.3f}', '-i', 'a.wav', '-af', 'apad=pad_dur=0.4', 'c.wav'], check=True)
    segs = m.transcribe('c.wav', language='ru', token_timestamps=True, max_len=1, split_on_word=True, initial_prompt=(P + ' ' + prev)[-200:])
    ws = [[round(A + s.t0 / 100, 2), round(A + s.t1 / 100, 2), s.text.strip()] for s in segs if s.text.strip()]
    W += ws; prev = ' '.join(w for *_, w in ws)
    lines.append(f'[{int(a // 60)}:{a % 60:05.2f}] {prev}')
    if i % 20 == 0: print(i, len(ch), flush=True)
json.dump(W, open(f'{K}.words.json', 'w'), ensure_ascii=False)
open(f'{K}.txt', 'w').write('\n'.join(lines))
print('DONE', len(W), flush=True)
