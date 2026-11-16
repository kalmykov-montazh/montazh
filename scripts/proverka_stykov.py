# Проверка стыков готового ролика (правило Евгения 16.11.2026: «99,9 %, всё чётко»).
# Звук готового ролика слушают ДВЕ программы: GigaAM v2 (Сбер) и Whisper large-v3-turbo (с уверенностью по словам).
# Ищем места, где слово срезано на стыке:
#   СТЫК-В-РЕЧИ   — стык с подрезкой громкости (afade у склеек/перезапусков) идёт по живой речи
#   ОБРЫВ         — голос обрывается в тишину быстрее 10 мс (так речь не затихает — это рез)
#   НЕ СЛОВО      — одна из программ слышит несуществующее слово («флияет», «децина»)
#   РАЗНОЧТЕНИЕ   — программы слышат разные слова в одном месте (вес выше рядом со стыком)
#   ИСХОДНИК      — в исходнике (сырое рядом в папке) слово звучит иначе, чем в готовом
#   ПОВТОР        — фраза повторяется подряд
# Запуск: python3 proverka_stykov.py ролик.mp4 [сырое.mp4] > отчёт.json
import sys, os, re, json, subprocess, difflib
import numpy as np

SR = 16000
G = os.environ.get('GIGAAM', 'models/gigaam')

def load(v):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', v, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

NUMW = re.compile(r'^(ноль|один|одна|одно|одну|два|две|двух|три|трех|четыр|пят|шест|сем|восем|девят|десят|одиннадцат|двенадцат|тринадцат|четырнадцат|пятнадцат|шестнадцат|семнадцат|восемнадцат|девятнадцат|двадцат|тридцат|сорок|пятьдесят|шестьдесят|семьдесят|восемьдесят|девяност|сто|двест|трист|четырест|пятьсот|шестьсот|семьсот|восемьсот|девятьсот|тысяч|миллион|евро|процент|первого|второго|третьего|половин)')
def norm(w): return re.sub(r'[^\w]', '', w.lower().replace('ё', 'е'))

# ---------- распознавание ----------
_gr = None
def giga(a):
    global _gr
    import sherpa_onnx
    if _gr is None:
        _gr = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{G}/encoder.int8.onnx', decoder=f'{G}/decoder.onnx',
              joiner=f'{G}/joiner.onnx', tokens=f'{G}/tokens.txt', model_type='nemo_transducer')
    out = []; pos = 0; n = len(a)
    while pos < n:
        end = min(n, pos + 6 * SR)
        if end < n:
            lo = end - int(1.5 * SR); fr = 400
            en = [np.abs(a[i:i + fr]).mean() for i in range(lo, end - fr, fr)]
            end = lo + int(np.argmin(en)) * fr + fr // 2
        s = _gr.create_stream(); s.accept_waveform(SR, a[pos:end]); _gr.decode_stream(s)
        cur = None
        for ch, t in zip(s.result.tokens, s.result.timestamps):
            t = pos / SR + t
            if ch.strip() == '':
                if cur: out.append(cur); cur = None
                continue
            if cur is None: cur = {'w': '', 's': round(t, 3), 'e': round(t, 3)}
            cur['w'] += ch; cur['e'] = round(t + 0.04, 3)
        if cur: out.append(cur)
        pos = end
    return out

_wm = None
def whisper(a):
    global _wm
    from faster_whisper import WhisperModel
    if _wm is None:
        _wm = WhisperModel(os.environ.get('WMODEL', 'deepdml/faster-whisper-large-v3-turbo-ct2'), device='cpu', compute_type='int8',
                           cpu_threads=os.cpu_count())
    segs, _ = _wm.transcribe(a, language='ru', word_timestamps=True, beam_size=5, vad_filter=False,
                             condition_on_previous_text=False, temperature=0)
    out = []
    for sg in segs:
        for w in sg.words or []:
            out.append({'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3), 'p': round(w.probability, 3)})
    return out

# ---------- стыки по звуку ----------
def env_db(a, ms=5):
    fr = int(SR * ms / 1000); n = len(a) // fr
    r = np.sqrt((a[:n * fr].reshape(n, fr) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(r + 1e-9), ms / 1000

def joints(a):
    db, st = env_db(a, 5)
    if not len(db): return [], db, st, -30
    peak = np.percentile(db, 95)
    out = []
    # 1) подрезка громкости до «цифровой» тишины на 5–60 мс посреди звука (afade на стыке кусков)
    dig = db < min(-62, peak - 45)
    i = 0; n = len(db)
    while i < n:
        if dig[i]:
            j = i
            while j < n and dig[j]: j += 1
            L = (j - i) * st
            if 0.004 <= L <= 0.07 and i > 4 and j < n - 4:
                before = db[max(0, i - 6):i].max(); after = db[j:j + 6].max()
                if before > peak - 40 or after > peak - 40:
                    out.append({'t': round((i + j) / 2 * st, 3), 'type': 'fade', 'before_db': round(float(before - peak), 1),
                                'after_db': round(float(after - peak), 1)})
            i = j
        else:
            i += 1
    # 2) обрыв: громкая речь → почти тишина за 10 мс (без цифровой тишины — жёсткий рез aselect)
    floor = np.percentile(db, 10)
    for k in range(4, n - 4):
        if db[k - 2:k].min() > peak - 14 and db[k:k + 2].max() < max(floor + 4, peak - 38):
            t = round(k * st, 3)
            if not any(abs(t - x['t']) < 0.08 for x in out):
                out.append({'t': t, 'type': 'cut-off', 'before_db': round(float(db[k - 2:k].min() - peak), 1),
                            'after_db': round(float(db[k:k + 2].max() - peak), 1)})
    out.sort(key=lambda x: x['t'])
    return out, db, st, peak

# ---------- словарь ----------
_m = None
def known(w):
    global _m
    w = norm(w)
    if not w or w.isdigit() or re.search(r'[a-z]', w) or len(w) <= 2: return True
    if _m is None:
        import pymorphy3; _m = pymorphy3.MorphAnalyzer()
    return any(p.is_known for p in _m.parse(w))

def ctx(ws, t, r=2.0): return ' '.join(w['w'] for w in ws if t - r <= (w['s'] + w['e']) / 2 <= t + r)

def at(ws, t, pad=0.12): return [w for w in ws if w['s'] - pad <= t <= w['e'] + pad]

def sim(x, y):
    x, y = norm(x), norm(y)
    if not x or not y: return 0.0
    return difflib.SequenceMatcher(None, x, y).ratio()

def main():
    V = sys.argv[1]; RAW = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
    a = load(V); D = len(a) / SR
    gw = giga(a); ww = whisper(a)
    J, db, st, peak = joints(a)
    flags = []
    def add(kind, t, why, strong):
        flags.append({'kind': kind, 't': round(t, 2), 'why': why, 'strong': bool(strong),
                      'giga': ctx(gw, t), 'whisper': ctx(ww, t)})

    # стыки по живой речи
    for j in J:
        if j['type'] == 'fade':
            loud = max(j['before_db'], j['after_db'])
            if j['before_db'] > -14:
                add('СТЫК-В-РЕЧИ', j['t'], f"перед подрезкой голос громкий: {j['before_db']} дБ от пика (после {j['after_db']})", False)
        else:
            add('ОБРЫВ', j['t'], f"голос оборвался за 10 мс ({j['before_db']} → {j['after_db']} дБ)", False)

    # несуществующие слова
    for src, ws in (('GigaAM', gw), ('Whisper', ww)):
        for w in ws:
            if not known(w['w']):
                t = (w['s'] + w['e']) / 2
                other = at(ww if src == 'GigaAM' else gw, t)
                if other and all(sim(o['w'], w['w']) > 0.85 for o in other): continue   # обе слышат одинаково — имя/термин
                near = min([abs(t - j['t']) for j in J] or [99])
                add('НЕ СЛОВО', t, f"{src} слышит «{w['w']}» — такого слова нет" + (f"; стык в {near:.2f} с" if near < 0.6 else ''), near < 0.6)

    # разночтения двух программ
    A = [norm(w['w']) for w in gw]; B = [norm(w['w']) for w in ww]
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal': continue
        ga = ' '.join(w['w'] for w in gw[i1:i2]); wb = ' '.join(w['w'] for w in ww[j1:j2])
        if sim(ga.replace(' ', ''), wb.replace(' ', '')) > 0.8: continue   # «из-за» / «изза», слитно/раздельно
        if re.search(r'\d', wb) and all(NUMW.match(norm(x)) for x in ga.split()): continue   # «десять» / «10»
        tt = [w for w in gw[i1:i2]] + [w for w in ww[j1:j2]]
        if not tt: continue
        t = sum((w['s'] + w['e']) / 2 for w in tt) / len(tt)
        near = min([abs(t - j['t']) for j in J] or [99])
        lowp = [w for w in ww[j1:j2] if w.get('p', 1) < 0.5]
        add('РАЗНОЧТЕНИЕ', t, f"GigaAM: «{ga}» / Whisper: «{wb}»" + (f"; стык в {near:.2f} с" if near < 0.6 else '') +
            (f"; Whisper не уверен в «{' '.join(w['w'] for w in lowp)}»" if lowp else ''), near < 0.6 and bool(lowp))

    # сверка с задуманным текстом (osnova_words.json — слова, которые монтаж оставил, на шкале основы)
    WJ = os.environ.get('WORDS')
    if WJ and os.path.exists(WJ):
        I = [w for w in json.load(open(WJ, encoding='utf-8')) if norm(w['w'])]
        IN = [norm(w['w']) for w in I]
        def heard(model):
            M = [norm(w['w']) for w in model]; ok = [False] * len(I); mp = [None] * len(I)
            for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, IN, M, autojunk=False).get_opcodes():
                if op == 'equal':
                    for k in range(i2 - i1): ok[i1 + k] = True; mp[i1 + k] = j1 + k
                elif op == 'replace':
                    a_ = ''.join(IN[i1:i2]); b_ = ''.join(M[j1:j2])
                    if sim(a_, b_) >= 0.8 or (re.search(r'\d', a_ + b_) and len(b_) > 0):
                        for k in range(i1, i2): ok[k] = True
                    for k in range(i1, i2):
                        for q in range(j1, j2):
                            if sim(IN[k], M[q]) >= 0.75: ok[k] = True; mp[k] = q
            return ok, mp
        okg, mg = heard(gw); okw, mw = heard(ww)
        # сдвиг шкалы основы → готовый ролик (по совпавшим словам Whisper)
        dd = [ww[mw[k]]['s'] - I[k]['s'] for k in range(len(I)) if mw[k] is not None]
        off = float(np.median(dd)) if dd else 0.0
        k = 0
        while k < len(I):
            if okg[k] or okw[k]: k += 1; continue
            k2 = k
            while k2 < len(I) and not (okg[k2] or okw[k2]): k2 += 1
            txt = ' '.join(w['w'] for w in I[k:k2]); t = I[k]['s'] + off
            if not all(NUMW.match(x) or x.isdigit() for x in IN[k:k2]):
                add('НЕ СЛЫШНО', t, f"по плану «{txt}», а обе программы слышат другое", True)
            k = k2
        # лишнее: обе программы слышат слово, которого нет в плане
        def extra(model, mp):
            used = set(x for x in mp if x is not None); return [q for q in range(len(model)) if q not in used]
        ex_w = extra(ww, mw)
        for q in ex_w:
            w = ww[q]; tm = (w['s'] + w['e']) / 2
            g = [x for x in at(gw, tm, 0.15)]
            if g and not any(sim(x['w'], y['w']) >= 0.75 for x in g for y in I if abs(y['s'] + off - tm) < 1.0):
                if any(sim(x['w'], w['w']) >= 0.6 for x in g) and not NUMW.match(norm(w['w'])) and not norm(w['w']).isdigit():
                    add('ЛИШНЕЕ', tm, f"обе программы слышат «{w['w']}», в плане его нет", True)

    # сверка с исходником
    if RAW and os.path.exists(RAW):
        r = load(RAW); rw = giga(r)
        R = [norm(w['w']) for w in rw]
        sm = difflib.SequenceMatcher(None, A, R, autojunk=False)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op != 'replace' or i2 - i1 > 3: continue
            fa = ' '.join(w['w'] for w in gw[i1:i2]); ra = ' '.join(w['w'] for w in rw[j1:j2])
            if sim(fa.replace(' ', ''), ra.replace(' ', '')) > 0.85: continue
            t = (gw[i1]['s'] + gw[i2 - 1]['e']) / 2
            # в готовом звучит часть исходного слова — признак среза
            part = any(norm(x) and norm(x) in norm(ra) and norm(x) != norm(ra) for x in fa.split())
            add('ИСХОДНИК', t, f"в готовом «{fa}», в сыром «{ra}»", part)

    # повтор фразы
    toks = A
    for n in (4, 3, 2):
        for i in range(len(toks) - 2 * n + 1):
            g = toks[i:i + n]
            if any(len(x) < 2 for x in g) or sum(len(x) for x in g) < 8: continue
            if toks[i + n:i + 2 * n] == g and gw[i + n]['s'] - gw[i]['s'] < 5:
                add('ПОВТОР', gw[i]['s'], f"«{' '.join(w['w'] for w in gw[i:i + n])}» два раза подряд", True)

    # начало и конец ролика
    if len(db):
        on = next((k for k, v in enumerate(db) if v > peak - 18), None)
        if on is not None and on * st < 0.02: add('НАЧАЛО', 0, 'голос громкий с первого кадра — первое слово срезано?', True)
        if db[-4:].max() > peak - 14: add('КОНЕЦ', D, 'голос громкий в последнем кадре — последнее слово срезано?', True)

    flags.sort(key=lambda f: f['t'])
    print(json.dumps({'file': V, 'dur': round(D, 2), 'joints': J, 'flags': flags,
                      'giga': ' '.join(w['w'] for w in gw), 'whisper': ' '.join(w['w'] for w in ww),
                      'gw': gw, 'ww': ww}, ensure_ascii=False, default=float))

if __name__ == '__main__':
    main()
