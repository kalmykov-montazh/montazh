# Правка готового ролика без пересборки (16.11.2026, проверка стыков): обрезать конец по тишине, заглушить
# обрубок слова в начале, вырезать повтор из середины. Видео перекодируется один раз (crf 17), звук aac 192k.
# Запуск: python3 pravka_finala.py вход.mp4 выход.mp4 '<json-список операций>'
#   ["end", t]       — закончить ролик в t (подгонка к самой тихой точке ±0,1 с) + затухание 50 мс
#   ["fade", 0]      — только мягкое затухание последних 80 мс
#   ["mute", a, b]   — заглушить звук a..b (b подгоняется к тишине), с подъёмом 20 мс
#   ["cut", a, b]    — вырезать кусок a..b (обе границы — к тишине), стык с затуханием 15 мс
import sys, json, subprocess
import numpy as np

SR = 16000
src, dst, ops = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])

def dur(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
                                capture_output=True, text=True).stdout.strip())

raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
D = dur(src)

def quiet(t, lo=-0.08, hi=0.10):
    fr = int(0.01 * SR); best, bt = None, t
    x = t + lo
    while x <= t + hi:
        i = int(x * SR)
        if 0 <= i and i + fr <= len(a):
            e = float(np.sqrt((a[i:i + fr] ** 2).mean() + 1e-12)) * (1 + abs(x - t))
            if best is None or e < best: best, bt = e, x + 0.005
        x += 0.005
    return round(bt, 3)

af, vf_parts, segs = [], [], None
end = D
for op in ops:
    k = op[0]
    if k == 'end':
        end = quiet(op[1]); print('конец', op[1], '→', end)
    elif k == 'mute':
        b = quiet(op[2], -0.03, 0.08); print('заглушить', op[1], '–', b)
        af.append(f"volume=enable='between(t,{op[1]},{b})':volume=0")
        af.append(f"afade=t=in:st={b}:d=0.02")
    elif k == 'cut':
        a0, b0 = quiet(op[1]), quiet(op[2]); print('вырезать', a0, '–', b0)
        segs = [(0, a0), (b0, None)]
af.append(f"afade=t=out:st={max(0, end - 0.06):.3f}:d=0.06")
enc = ['-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart']
if segs:
    (s0, e0), (s1, _) = segs
    fc = (f"[0:v]trim=0:{e0},setpts=PTS-STARTPTS[v0];[0:v]trim={s1}:{end},setpts=PTS-STARTPTS[v1];"
          f"[0:a]atrim=0:{e0},asetpts=PTS-STARTPTS,afade=t=out:st={e0 - 0.015:.3f}:d=0.015[a0];"
          f"[0:a]atrim={s1}:{end},asetpts=PTS-STARTPTS,afade=t=in:d=0.015[a1];"
          f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][ac];[ac]afade=t=out:st={max(0, end - (s1 - e0) - 0.06):.3f}:d=0.06[a]")
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', src, '-filter_complex', fc, '-map', '[v]', '-map', '[a]', *enc, dst]
else:
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', src, '-t', f'{end:.3f}', '-af', ','.join(af), *enc, dst]
subprocess.run(cmd, check=True)
print('было', round(D, 2), 'стало', round(dur(dst), 2))
