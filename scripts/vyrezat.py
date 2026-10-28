#!/usr/bin/env python3
"""Вырезать куски из готового ролика по фразам (28.10.2026, задание «проверка перед Готовые»).
python3 vyrezat.py in.mp4 plan.json cuts.json out.mp4
cuts.json: {"cut": [{"from": "я делал видео", "to": "совсем свежее"}], "end_after": "но добрые", "start_at": "фраза"}
Время слов — из plan.json распознавания этого же файла (raspoznat.yml)."""
import json, re, subprocess, sys
IN, PLAN, CUTS, OUT = sys.argv[1:5]
words = [w for p in json.load(open(PLAN)) for w in p['words'] if w['w'].strip()]
nw = lambda x: re.sub(r'[^\wё]', '', x.lower()).replace('ё', 'е')
lw = [nw(w['w']) for w in words]
def find(ph, after=0.0, last=False):
    ps = [nw(x) for x in ph.split() if nw(x)]
    for i in range(len(lw)):
        if words[i]['s'] + 0.01 < after: continue
        if all(i + k < len(lw) and lw[i + k].startswith(ps[k][:max(3, len(ps[k]) - 2)]) for k in range(len(ps))):
            return i, i + len(ps) - 1
    raise SystemExit(f'нет фразы: {ph}')
c = json.load(open(CUTS))
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', IN], capture_output=True, text=True).stdout)
start = 0.0
if c.get('start_at'): i, _ = find(c['start_at']); start = max(0, words[i]['s'] - 0.05)
end = dur
if c.get('end_after'): _, j = find(c['end_after'], start); end = min(dur, words[j]['e'] + 0.3)
holes = []
for x in c.get('cut', []):
    i, _ = find(x['from'], start); _, j = find(x['to'], words[i]['s'])
    holes.append((words[i]['s'] - 0.04, words[j]['e'] + 0.04))
keep, t = [], start
for a, b in sorted(holes):
    if a > t: keep.append((t, a))
    t = max(t, b)
if end > t: keep.append((t, end))
print('оставляю', [(round(a, 2), round(b, 2)) for a, b in keep], 'было', round(dur, 1), 'стало', round(sum(b - a for a, b in keep), 1))
fc = ''.join(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{k}];[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={max(0, b - a - 0.03):.3f}:d=0.03[a{k}];" for k, (a, b) in enumerate(keep))
fc += ''.join(f'[v{k}][a{k}]' for k in range(len(keep))) + f'concat=n={len(keep)}:v=1:a=1[v][a]'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', IN, '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16',
                '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT], check=True)
