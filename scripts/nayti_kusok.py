#!/usr/bin/env python3
"""Где в лонге звучит кусок из шортса (28.10.2026): взаимная корреляция огибающей звука.
python3 nayti_kusok.py long.mp4 short.mp4 speed [from to]  — speed: во сколько раз шортс ускорен (1.2)."""
import subprocess, sys, numpy as np
L, S, SP = sys.argv[1], sys.argv[2], float(sys.argv[3])
a0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0; a1 = float(sys.argv[5]) if len(sys.argv) > 5 else 1e9
SR = 8000
def pcm(f, extra):
    r = subprocess.run(['ffmpeg', '-v', 'error', *extra[0], '-i', f, *extra[1], '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(r, np.int16).astype(np.float32)
lg = pcm(L, ([] if a0 == 0 else ['-ss', str(a0)], [] if a1 > 1e8 else ['-t', str(a1 - a0)]))
sh = pcm(S, ([], ['-af', f'atempo={1 / SP:.6f}']))
def env(x, hop=80):   # огибающая 10 мс
    n = len(x) // hop; e = np.abs(x[:n * hop]).reshape(n, hop).mean(1); e = np.log1p(e); return (e - e.mean()) / (e.std() + 1e-9)
el, es = env(lg), env(sh)
n = 1 << int(np.ceil(np.log2(len(el) + len(es))))
c = np.fft.irfft(np.fft.rfft(el, n) * np.conj(np.fft.rfft(es, n)), n)[:len(el) - len(es) + 1] / len(es)
k = int(np.argmax(c)); t = a0 + k * 0.01
print(f"начало {t:.2f} конец {t + len(es) * 0.01:.2f} сходство {c[k]:.2f} (второе лучшее {np.sort(c)[-30]:.2f})")
