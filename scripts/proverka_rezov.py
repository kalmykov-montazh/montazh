# Резы монтажа по СЫРОМУ звуку (16.11.2026, правило «99,9 %»): каждый рез plan.json проверяем по громкости сырого
# в момент реза. Если в сыром в эту долю секунды идёт голос — рез прошёл по слову: срезан конец/начало слова
# или остался обрубок соседнего (выброшенного) слова.
# Используется из proverka_stykov.py: rezy(plan, raw_audio, sr) → список резов со временем на шкале основы.
import numpy as np

SPEED = 1.2

def db_frames(a, sr, ms=5):
    fr = int(sr * ms / 1000); n = len(a) // fr
    r = np.sqrt((a[:n * fr].reshape(n, fr) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(r + 1e-9), ms / 1000

def rezy(plan, a, sr, speed=SPEED, t_from=None, t_to=None):
    """plan — список кусков {a, b, keep, words}; a — сырой звук. Возвращает резы между оставленными кусками:
    {os: время на шкале основы, end_db/after_db (конец куска), start_db/before_db (начало следующего), bad, why}"""
    db, st = db_frames(a, sr, 5)
    peak = float(np.percentile(db, 95))
    def mx(t0, t1):
        i0 = max(0, int(t0 / st)); i1 = max(i0 + 1, int(t1 / st))
        return float(db[i0:i1].max() - peak) if i0 < len(db) else -99.0
    kept = [p for p in plan if p.get('keep')]
    out = []; pos = 0.0
    for k, p in enumerate(kept):
        pos += (p['b'] - p['a']) / speed
        if k + 1 >= len(kept): break
        q = kept[k + 1]
        if abs(q['a'] - p['b']) < 0.005:   # куски вплотную — реза нет
            continue
        e_end = mx(p['b'] - 0.025, p['b']); e_after = mx(p['b'], p['b'] + 0.025)
        e_before = mx(q['a'] - 0.025, q['a']); e_start = mx(q['a'], q['a'] + 0.025)
        why = []
        if e_end > -18 and e_after > -22: why.append(f'конец куска режет голос ({e_end:.0f} дБ, дальше {e_after:.0f})')
        if e_start > -18 and e_before > -22: why.append(f'начало куска с середины звука ({e_before:.0f} → {e_start:.0f} дБ)')
        lw = (p.get('words') or [{}])[-1].get('w', ''); fw = (q.get('words') or [{}])[0].get('w', '')
        out.append({'os': round(pos, 3), 'raw_b': round(p['b'], 3), 'raw_a': round(q['a'], 3), 'last': lw, 'first': fw,
                    'end_db': round(e_end, 1), 'after_db': round(e_after, 1), 'before_db': round(e_before, 1), 'start_db': round(e_start, 1),
                    'bad': bool(why), 'why': '; '.join(why)})
    return out
