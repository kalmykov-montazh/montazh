#!/usr/bin/env python3
"""Проверка готового ролика на повторы (недорезанные дубли) перед отдачей.
python3 check_dups.py ролик.mp4 [модель.bin]   (или WMODEL=...)
Режет звук по паузам, каждый кусок распознаёт ОТДЕЛЬНО (без контекста, иначе распознавание
склеивает два одинаковых куска в один), и ищет:
  1) соседние куски, которые начинаются одинаково (дубль фразы);
  2) повтор 2+ слов подряд внутри куска или на стыке кусков;
  3) кусок, где речь подозрительно медленная (возможен склеенный дубль) — его делит
     пополам по самой тихой точке и проверяет половинки.
Печатает найденное с секундами. Код выхода 1 = есть повторы, 0 = чисто."""
import os, re, sys, json, subprocess, tempfile, statistics, wave
import numpy as np

src = sys.argv[1]
MODEL = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('WMODEL', 'ggml-small-q8_0.bin')
tmp = tempfile.mkdtemp()
wav = f'{tmp}/a.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', '16000', wav], check=True)
w = wave.open(wav); SR = 16000
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float)
dur = len(x) / SR

# паузы по энергии (окно 20 мс)
H = 320
e = np.array([np.sqrt((x[i:i + H] ** 2).mean()) for i in range(0, len(x) - H, H)])
thr = max(150.0, np.percentile(e, 20) * 1.5)
quiet = e < thr
pieces, cur, i = [], None, 0
while i < len(e):
    if not quiet[i]:
        if cur is None: cur = i
        i += 1; continue
    j = i
    while j < len(e) and quiet[j]: j += 1
    if cur is not None and (j - i) * H / SR >= 0.08:   # пауза от 80 мс = граница куска
        pieces.append([cur * H / SR, i * H / SR]); cur = None
    i = j
if cur is not None: pieces.append([cur * H / SR, dur])
pieces = [[max(0, a - 0.05), min(dur, b + 0.08)] for a, b in pieces if b - a > 0.12]

from pywhispercpp.model import Model
m = Model(MODEL, n_threads=os.cpu_count(), print_progress=False, print_realtime=False,
          redirect_whispercpp_logs_to=None)

def asr(a, b, full=False):
    cw = f'{tmp}/c.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', wav,
                    '-af', 'apad=pad_dur=0.6', cw], check=True)
    ctx = 1500 if full else min(1500, max(768, int((b - a + 0.6) * 50) + 128))   # окно кодера по длине куска — в разы быстрее
    return ' '.join(s.text.strip() for s in m.transcribe(cw, language='ru', no_context=True, audio_ctx=ctx))

FILL = {'а', 'и', 'ну', 'вот', 'так', 'но', 'э', 'эм', 'это', 'то'}
def norm(t):
    return re.sub(r'[^\w ]', ' ', t.lower().replace('ё', 'е')).split()
def core(ws):
    k = 0
    while k < len(ws) - 1 and ws[k] in FILL: k += 1
    return ws[k:]
def rep_inside(ws, n=2):
    """повтор n+ слов подряд: ... a b ... a b ... (на расстоянии до 8 слов)"""
    for i in range(len(ws) - n + 1):
        g = ws[i:i + n]
        if all(t in FILL for t in g): continue
        for j in range(i + n, min(len(ws) - n + 1, i + n + 8)):
            if ws[j:j + n] == g: return ' '.join(g)
    return None

items = []
for a, b in pieces:
    t = asr(a, b)
    items.append({'a': a, 'b': b, 't': t, 'w': norm(t)})

# 3) медленные куски — делим по самой тихой точке и распознаём половинки
rates = [len(''.join(it['w'])) / (it['b'] - it['a']) for it in items if it['b'] - it['a'] > 0.6 and it['w']]
med = statistics.median(rates) if rates else 12
extra = []
for it in items:
    L = it['b'] - it['a']
    if L > 1.2 and it['w'] and len(''.join(it['w'])) / L < 0.65 * med:
        lo, hi = int((it['a'] + 0.4) * SR / H), int((it['b'] - 0.4) * SR / H)
        if hi > lo:
            c = (lo + int(np.argmin(e[lo:hi]))) * H / SR
            t1, t2 = asr(it['a'], c), asr(c, it['b'])
            extra.append((it['a'], c, it['b'], t1, t2))

found = []
for i, it in enumerate(items):
    r = rep_inside(it['w'])
    if r: r = rep_inside(norm(asr(it['a'], it['b'], full=True)))   # перепроверка полным окном (короткое окно иногда «заикается»)
    if r: found.append((it['a'], f'повтор внутри фразы: «{r}» — {it["t"]}'))
    for j in (i + 1, i + 2):
        if j >= len(items): break
        if j == i + 2 and items[i + 1]['b'] - items[i + 1]['a'] > 1.0: break
        x, y = core(it['w']), core(items[j]['w'])
        n = min(3, len(x), len(y))
        if n >= 2 and x[:n] == y[:n]:
            found.append((it['a'], f'дубль: «{it["t"]}» ({it["a"]:.1f} с) и «{items[j]["t"]}» ({items[j]["a"]:.1f} с)'))
    if i + 1 < len(items):
        r = rep_inside(it['w'][-6:] + items[i + 1]['w'][:6])
        if r: r = rep_inside(norm(asr(it['a'], it['b'], True))[-6:] + norm(asr(items[i+1]['a'], items[i+1]['b'], True))[:6])
        if r: found.append((it['b'], f'повтор на стыке: «{r}» — …{it["t"][-40:]} | {items[i+1]["t"][:40]}…'))
for a, c, b, t1, t2 in extra:
    x, y = core(norm(t1)), core(norm(t2))
    n = min(3, len(x), len(y))
    r = rep_inside(norm(t1)[-6:] + norm(t2)[:6])
    if (n >= 2 and x[:n] == y[:n]) or r:
        found.append((a, f'склеенный дубль ({a:.1f}–{b:.1f} с, граница ~{c:.1f} с): «{t1}» | «{t2}»'))

seen = set()
for t, msg in sorted(found):
    if round(t) in seen: continue
    seen.add(round(t))
    print(f'ПОВТОР {t:.1f} с: {msg}')
if not found:
    print('повторов нет')
sys.exit(1 if found else 0)
