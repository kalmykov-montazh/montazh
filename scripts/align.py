#!/usr/bin/env python3
"""Точное время слов: python3 align.py raw.mp4 outdir [fix.json]
Для каждого куска из asr_cache.json распознаёт кусок заново с DTW (точные метки токенов),
переносит время на исправленный текст (fix.json: ключ куска -> текст; 'субтитр' = выбросить)."""
import json, os, re, subprocess, sys, difflib
import _pywhispercpp as pw
RAW, OUT = sys.argv[1], sys.argv[2]
FIX = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
MODEL = os.environ.get('WMODEL', 'ggml-small-q8_0.bin')
cache = json.load(open(f'{OUT}/asr_cache.json'))
# ключ из текст.txt может чуть отличаться от ключа в asr_cache (первый кусок «0.030-…» / «0.000-…», 06.10.2026) — сопоставляем с допуском
def _ab(k): return tuple(map(float, k.split('-')))
for k_ in [k for k in FIX if k not in cache]:
    a_, b_ = _ab(k_)
    near = [c for c in cache if abs(_ab(c)[0] - a_) < 0.3 and abs(_ab(c)[1] - b_) < 0.3]
    if len(near) == 1: FIX[near[0]] = FIX.pop(k_); print(f'ключ {k_} → {near[0]}')
    else: print(f'НЕ НАЙДЕН КЛЮЧ {k_}')
wav = f'{OUT}/a.wav'
if not os.path.exists(wav):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', RAW, '-ar', '16000', '-ac', '1', wav], check=True)
cp = pw.whisper_context_default_params(); cp.dtw_token_timestamps = True; cp.flash_attn = False; cp.dtw_aheads_preset = pw.whisper_alignment_heads_preset.WHISPER_AHEADS_SMALL
ctx = pw.whisper_init_from_file_with_params(MODEL, cp)
import numpy as np, wave
def norm(w): return re.sub(r'[^\w]', '', w.lower()).replace('ё', 'е')
for key in list(cache):
    a, b = map(float, key.split('-'))
    if FIX.get(key) == 'субтитр':
        cache[key] = [[0, 0.1, 'субтитр']]; continue
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', wav, '-af', 'apad=pad_dur=0.4', '-f', 's16le', f'{OUT}/c.raw'], check=True)
    pcm = np.fromfile(f'{OUT}/c.raw', np.int16).astype(np.float32) / 32768
    fp = pw.whisper_full_default_params(pw.WHISPER_SAMPLING_GREEDY)
    fp.language = 'ru'; fp.print_progress = False; fp.print_realtime = False; fp.n_threads = os.cpu_count()
    fp.token_timestamps = True
    pw.whisper_full(ctx, fp, pcm, len(pcm))
    words = []   # [start, text]
    for s in range(pw.whisper_full_n_segments(ctx)):
        for t in range(pw.whisper_full_n_tokens(ctx, s)):
            d = pw.whisper_full_get_token_data(ctx, s, t)
            try: txt = pw.whisper_full_get_token_text(ctx, s, t)
            except UnicodeDecodeError: continue   # токен с половиной русской буквы (04.10.2026, шортс 06) — пропустить
            if txt.startswith('[_') or txt.startswith('<|'): continue
            tt = max(0, d.t_dtw / 100)
            if txt.startswith(' ') or not words:
                words.append([tt, txt.strip()])
            else:
                words[-1][1] += txt
    words = [w for w in words if norm(w[1])]
    dur = b - a
    target = (FIX.get(key) or ' '.join(x[2] for x in cache[key])).split()
    if not words:
        continue
    # переносим время на слова нужного текста
    src = [norm(w[1]) for w in words]; dst = [norm(w) for w in target]
    st = [None] * len(target)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, src, dst, autojunk=False).get_opcodes():
        if tag == 'equal':
            for k in range(j2 - j1): st[j1 + k] = words[i1 + k][0]
        elif tag == 'replace' and i2 > i1:
            for k in range(j2 - j1): st[j1 + k] = words[i1 + min(k * (i2 - i1) // (j2 - j1), i2 - i1 - 1)][0]
    # пропуски — по соседям
    end_t = min(dur, max(w[0] for w in words) + 0.5)
    for j in range(len(st)):
        if st[j] is None:
            prv = next((st[k] for k in range(j - 1, -1, -1) if st[k] is not None), words[0][0])
            nxt = next((st[k] for k in range(j + 1, len(st)) if st[k] is not None), end_t)
            st[j] = (prv + nxt) / 2
    for j in range(1, len(st)): st[j] = max(st[j], st[j - 1] + 0.05)
    out = []
    for j, w in enumerate(target):
        e = st[j + 1] if j + 1 < len(st) else min(dur, st[j] + 0.6)
        out.append([round(st[j], 3), round(max(e, st[j] + 0.05), 3), w])
    cache[key] = out
    print(key, ' '.join(f'{x[0]:.2f}:{x[2]}' for x in out)[:160])
json.dump(cache, open(f'{OUT}/asr_cache.json', 'w'), ensure_ascii=False)
