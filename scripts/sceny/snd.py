import numpy as np
# ---------- звук ----------
SR = 48000
def snd(kind):
    rnd = np.random.default_rng(1)
    if kind == "whoosh":
        n = int(0.42 * SR); t = np.arange(n) / SR; x = rnd.standard_normal(n)
        env = np.sin(np.pi * t / t[-1]) ** 2
        # простой полосовой: разность сглаживаний, частота растёт
        y = np.zeros(n); a = 0; b = 0
        for i in range(n):
            al = 0.02 + 0.25 * (i / n); a += al * (x[i] - a); b += 0.01 * (a - b)
            y[i] = a - b
        return y / np.abs(y).max() * env * 0.5
    if kind == "click":
        n = int(0.06 * SR); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 90) + rnd.standard_normal(n) * np.exp(-t * 300) * 0.4) * 0.6
    if kind == "boom":
        n = int(0.9 * SR); t = np.arange(n) / SR
        f = 40 + 90 * np.exp(-t * 18); ph = 2 * np.pi * np.cumsum(f) / SR
        return (np.sin(ph) * np.exp(-t * 4.5) + rnd.standard_normal(n) * np.exp(-t * 40) * 0.5) * 0.9
    if kind == "pop":
        n = int(0.12 * SR); t = np.arange(n) / SR
        f = 500 + 900 * t / t[-1]; ph = 2 * np.pi * np.cumsum(f) / SR
        return np.sin(ph) * np.exp(-t * 30) * 0.6
    if kind == "ding":
        n = int(1.0 * SR); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 1976 * t)) * np.exp(-t * 5) * 0.4
    if kind == "alarm":
        n = int(0.5 * SR); t = np.arange(n) / SR
        f = np.where((t * 8).astype(int) % 2 == 0, 880, 660)
        return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.18 * np.exp(-t * 2)
    if kind == "cash":
        n = int(0.6 * SR); y = np.zeros(n); t = np.arange(n) / SR
        for k, st in enumerate([0, 0.07, 0.15, 0.24]):
            i0 = int(st * SR); tt = t[: n - i0]
            y[i0:] += np.sin(2 * np.pi * (2400 + k * 300) * tt) * np.exp(-tt * 25) * 0.3
        return y
    return np.zeros(1)

