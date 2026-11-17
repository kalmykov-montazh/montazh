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
        # 16.11.2026: куски по ~18 с, рез — в самой тихой точке последних 4 с (окно 25 мс). Короткие куски по 6 с
        # резали слова пополам («дейс|твует») — GigaAM слышал обрубки, которых в ролике нет
        end = min(n, pos + 18 * SR)
        if end < n:
            lo = end - int(4 * SR); fr = 400
            en = [np.abs(a[i:i + fr]).mean() for i in range(lo, end - fr, fr // 2)]
            end = lo + int(np.argmin(en)) * (fr // 2) + fr // 2
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
        _wm = WhisperModel(os.environ.get('FW_MODEL', 'deepdml/faster-whisper-large-v3-turbo-ct2'), device='cpu', compute_type='int8',
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

def frag(x, y):
    # признак среза: одно слово — кусок другого (начало/конец) или отличается только первой/последней буквой
    x, y = norm(x), norm(y)
    if len(x) < 2 or len(y) < 2 or x == y or x.isdigit() or y.isdigit(): return False
    s, l = (x, y) if len(x) <= len(y) else (y, x)
    if len(l) - len(s) >= 2 and (l.startswith(s) or l.endswith(s)) and len(s) >= 2: return True
    if len(x) == len(y) and len(x) >= 4 and (x[1:] == y[1:]) : return True
    return False

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
    flags = []; CUTS = []
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
                fr_ = any(frag(w['w'], o['w']) for o in other)
                add('НЕ СЛОВО', t, f"{src} слышит «{w['w']}» — такого слова нет; другая: «{' '.join(o['w'] for o in other)}»", fr_)

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
        lowp = [w for w in ww[j1:j2] if w.get('p', 1) < 0.5]
        fr_ = any(frag(x, y) for x in ga.split() for y in wb.split())
        add('РАЗНОЧТЕНИЕ', t, f"GigaAM: «{ga}» / Whisper: «{wb}»" +
            (f"; Whisper не уверен в «{' '.join(w['w'] for w in lowp)}»" if lowp else ''), fr_)

    # сверка с задуманным текстом (osnova_words.json — слова, которые монтаж оставил, на шкале основы)
    WJ = os.environ.get('WORDS')
    if WJ and os.path.exists(WJ):
        I = []
        for w in json.load(open(WJ, encoding='utf-8')):
            parts_ = [x for x in w['w'].split() if norm(x)]
            if not parts_: continue
            L_ = sum(len(x) for x in parts_); s_ = w['s']
            for x in parts_:   # в склейках слово плана бывает фразой — делим по длине
                e_ = s_ + (w['e'] - w['s']) * len(x) / L_; I.append({'w': x, 's': s_, 'e': e_}); s_ = e_
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
                hv = ' '.join(w['w'] for w in gw if abs((w['s'] + w['e']) / 2 - t) < 0.6) + ' / ' + ' '.join(w['w'] for w in ww if abs((w['s'] + w['e']) / 2 - t) < 0.6)
                fragm = any(len(norm(h)) >= 2 and norm(h) != norm(x) and (norm(x).startswith(norm(h)) or norm(x).endswith(norm(h)) or norm(x)[1:] == norm(h)[1:])
                           for h in hv.split() for x in txt.split())
                add("НЕ СЛЫШНО", t, f"по плану «{txt}», слышно: {hv}", fragm)
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
                    add('ЛИШНЕЕ', tm, f"обе программы слышат «{w['w']}», в плане его нет", not known(w['w']))

    # ---- РЕЗЫ: по плану монтажа (plan.json + сырое) и стыки кусков склейки (skleika.json) ----
    cuts = []   # (время в готовом, описание, плохо_по_сырому)
    PJ = os.environ.get('PLAN'); SJ = os.environ.get('SKLEIKA')
    if WJ and os.path.exists(WJ):
        if PJ and os.path.exists(PJ) and RAW and os.path.exists(RAW):
            import proverka_rezov
            rw_a = load(RAW)
            for c in proverka_rezov.rezy(json.load(open(PJ, encoding='utf-8')), rw_a, SR):
                cuts.append((c['os'] + off, f"рез «{c['last']} | {c['first']}»", c))
        if SJ and os.path.exists(SJ):
            sk = json.load(open(SJ, encoding='utf-8'))
            k0 = 0
            for n_, part in enumerate(sk.get('parts', [])):
                fr = [norm(x) for x in part.get('from', '').split() if norm(x)]
                if not fr: continue
                for k in range(k0, len(IN) - len(fr) + 1):
                    if all(sim(IN[k + q], fr[q]) >= 0.75 for q in range(len(fr))):
                        if n_ > 0 and k > 0:
                            tj = (I[k - 1]['e'] + I[k]['s']) / 2 + off
                            cuts.append((tj, f"стык кусков «{I[k-1]['w']} | {I[k]['w']}»", None))
                        k0 = k + 1; break
        # каждый рез: громкость сырого в момент реза + отдельное распознавание окна ±1,6 с (без общего контекста)
        for tj, name, c in cuts:
            if c and c['bad']:
                add('РЕЗ ПО СЛОВУ', tj, f"{name}: {c['why']}", True)
            w0, w1 = max(0.0, tj - 1.6), min(D, tj + 1.6)
            seg = a[int(w0 * SR):int(w1 * SR)]
            try:
                segs, _ = _wm.transcribe(seg, language='ru', word_timestamps=True, beam_size=5, vad_filter=False,
                                         condition_on_previous_text=False, temperature=0)
                lw = [{'w': w.word.strip(), 's': w.start + w0, 'e': w.end + w0} for sg in segs for w in (sg.words or [])]
            except Exception:
                lw = []
            gl = giga(seg); gl = [{**w, 's': w['s'] + w0, 'e': w['e'] + w0} for w in gl]
            # слова плана у реза: последнее до и первое после
            before = [x for x in I if x['e'] + off <= tj + 0.05][-2:]
            after = [x for x in I if x['s'] + off >= tj - 0.05][:2]
            miss = []
            for x in before + after:
                xm = (x['s'] + x['e']) / 2 + off
                if NUMW.match(norm(x['w'])) or norm(x['w']).isdigit() or re.search(r'[a-z]', norm(x['w'])): continue
                hw = [y for y in lw if y['s'] - 0.35 <= xm <= y['e'] + 0.35]
                hg = [y for y in gl if y['s'] - 0.35 <= xm <= y['e'] + 0.35]
                th = 0.6 if len(norm(x['w'])) >= 5 else 0.75
                def good(hs):
                    if not hs: return False
                    if len(norm(x['w'])) >= 4 and norm(x['w']) in ''.join(norm(y['w']) for y in hs): return True   # «по-настоящему» = «по настоящему»
                    y = max(hs, key=lambda y: sim(y['w'], x['w']))
                    if sim(y['w'], x['w']) < th: return False
                    if frag(y['w'], x['w']): return False             # слышен кусок слова («кон» вместо «балкон»)
                    if known(x['w']) and not known(y['w']): return False   # слово исказилось («звукориацию»)
                    return True
                okw = good(hw); okg = good(hg)
                if not okw and not okg:
                    miss.append(f"«{x['w']}» (слышно: {' '.join(y['w'] for y in hw) or '—'} / {' '.join(y['w'] for y in hg) or '—'})")
            if miss:
                add('СТЫК', tj, f"{name}: у реза не слышно {', '.join(miss)}", True)
            rec = {'t': round(tj, 2), 'name': name, 'win_whisper': ' '.join(y['w'] for y in lw), 'win_giga': ' '.join(y['w'] for y in gl)}
            if c: rec.update({k_: c[k_] for k_ in ('end_db', 'after_db', 'before_db', 'start_db', 'bad')})
            CUTS.append(rec)

    WIN = []
    # ---- КАЖДОЕ СЛОВО: распознаём ролик окнами 3,2 с (шаг 1,6 с) без общего контекста — так срезанное слово
    # не «дорисовывается» по смыслу. Каждое слово (по плану, а если плана нет — по Whisper целиком) проверяем
    # в окне, где оно ближе к середине. Не услышали ни Whisper, ни GigaAM — замечание.
    if os.environ.get('WINDOWS', '1') == '1' and D < 400:
        base = [dict(x, s=x['s'] + off, e=x['e'] + off) for x in I] if (WJ and os.path.exists(WJ)) else [dict(x) for x in ww]
        near_cut = [c[0] for c in cuts] if (WJ and os.path.exists(WJ)) else []
        step, half = 1.6, 1.6
        cs = np.arange(half, max(half + 0.01, D - half + step), step)
        WIN = []
        for c0 in cs:
            w0, w1 = max(0.0, c0 - half), min(D, c0 + half); seg = a[int(w0 * SR):int(w1 * SR)]
            try:
                segs, _ = _wm.transcribe(seg, language='ru', word_timestamps=True, beam_size=5, vad_filter=False,
                                         condition_on_previous_text=False, temperature=0)
                lw = [{'w': w.word.strip(), 's': w.start + w0, 'e': w.end + w0} for sg in segs for w in (sg.words or [])]
            except Exception:
                lw = []
            gl = [{**w, 's': w['s'] + w0, 'e': w['e'] + w0} for w in giga(seg)]
            WIN.append((c0, w0, w1, lw, gl))
        for x in base:
            xn = norm(x['w'])
            if not xn or NUMW.match(xn) or xn.isdigit() or re.search(r'[a-z]', xn) or len(xn) < 3: continue
            xm = (x['s'] + x['e']) / 2
            cand = [q for q in WIN if q[1] + 0.45 <= xm <= q[2] - 0.45] or [min(WIN, key=lambda q: abs(q[0] - xm))]
            th = 0.6 if len(xn) >= 5 else 0.75
            def good(hs):
                if not hs: return False
                if len(xn) >= 4 and xn in ''.join(norm(y['w']) for y in hs): return True
                y = max(hs, key=lambda y: sim(y['w'], x['w']))
                if sim(y['w'], x['w']) < th: return False
                if frag(y['w'], x['w']): return False
                if known(x['w']) and not known(y['w']): return False
                return True
            heard_ok = False; hw = hg = []
            for c0, w0, w1, lw, gl in cand:
                hw = [y for y in lw if y['s'] - 0.35 <= xm <= y['e'] + 0.35]
                hg = [y for y in gl if y['s'] - 0.35 <= xm <= y['e'] + 0.35]
                if good(hw) or good(hg): heard_ok = True; break
            if not heard_ok:
                nc = min([abs(xm - q) for q in near_cut] or [99])
                add('СЛОВО', xm, f"«{x['w']}» в отдельном прослушивании не слышно: {' '.join(y['w'] for y in hw) or '—'} / {' '.join(y['w'] for y in hg) or '—'}"
                    + (f"; рез в {nc:.2f} с" if nc < 0.8 else ''), True)

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

    # ---- НЕУДАЧНЫЕ ДУБЛИ (17.11.2026, перезапуск 64: «Подаёте на ВНЖ в Испании… заново со слов, подаёте…» на 0–3 с;
    # Whisper целиком склеил дубль с чистой фразой, проверка сказала «чисто»). Ищем по ВСЕМУ ролику, четырьмя способами:
    # служебные слова, фальстарт (та же фраза снова через несколько секунд), лишняя речь (в отдельных окнах слышно
    # больше слов, чем в общей расшифровке) и «резиновое» слово (Whisper растянул одно слово на проглоченный кусок).
    SLUZH = re.compile(r'^(перезапис\w*|дубль|переснима\w*)$')   # всегда команда
    SLUZH2 = re.compile(r'^(заново|стоп)$')   # бывает и в речи («подаваться заново») — сильное только рядом с «со слов»/«давай»
    def stream_words():
        yield from gw
        for c0, w0, w1, lw, gl in WIN:
            yield from gl; yield from lw
    seen_sl = []
    for w in stream_words():
        n_ = norm(w['w'])
        if (SLUZH.match(n_) or SLUZH2.match(n_)) and not any(abs(w['s'] - t) < 1.0 for t in seen_sl):
            seen_sl.append(w['s'])
            near = norm(ctx(gw, w['s'], 1.5))
            strong = bool(SLUZH.match(n_)) or 'сослов' in near or 'давай' in near or 'ещераз' in near
            add('СЛУЖЕБНОЕ', w['s'], f"слышно «{w['w']}» — команда при записи? {ctx(gw, w['s'])}", strong)
    for i in range(len(gw) - 1):
        if norm(gw[i]['w']) == 'со' and norm(gw[i + 1]['w']).startswith('слов') and not any(abs(gw[i]['s'] - t) < 1.0 for t in seen_sl):
            seen_sl.append(gw[i]['s']); add('СЛУЖЕБНОЕ', gw[i]['s'], f"слышно «со слов» — дубль не вырезан: {ctx(gw, gw[i]['s'])}", True)
    # фальстарт: та же фраза из 2+ слов повторяется вскоре (не обязательно подряд)
    done_fs = []
    for n_, lim in ((4, 12), (3, 9), (2, 5)):
        for i in range(len(A) - n_):
            g = A[i:i + n_]
            if any(len(x) < 2 for x in g) or sum(len(x) for x in g) < (9 if n_ == 2 else 8): continue
            for j in range(i + n_, len(A) - n_ + 1):
                if gw[j]['s'] - gw[i]['s'] > lim: break
                if A[j:j + n_] == g and not any(abs(gw[i]['s'] - t) < 3 for t in done_fs):
                    done_fs.append(gw[i]['s'])
                    between = j - (i + n_)
                    sl = any(abs(gw[i]['s'] - t) < 4 for t in seen_sl)
                    strong = n_ >= 4 or between <= 3 or sl
                    add('ФАЛЬСТАРТ', gw[i]['s'], f"«{' '.join(w['w'] for w in gw[i:i + n_])}» звучит дважды за {gw[j]['s'] - gw[i]['s']:.1f} с (между ними {between} сл.) — неудачный дубль? {ctx(gw, gw[i]['s'], 3)}", strong)
                    break
    # лишняя речь: окно слышит заметно больше слов, чем общая расшифровка в том же месте
    for c0, w0, w1, lw, gl in WIN:
        a0, a1 = w0 + 0.4, w1 - 0.4
        nb = sum(1 for w in ww if a0 <= (w['s'] + w['e']) / 2 <= a1)
        ng = sum(1 for w in gl if a0 <= (w['s'] + w['e']) / 2 <= a1)
        nl = sum(1 for w in lw if a0 <= (w['s'] + w['e']) / 2 <= a1)
        nx = max(ng, nl)
        dig = any(re.search(r'\d', w['w']) for w in ww if a0 - 0.5 <= (w['s'] + w['e']) / 2 <= a1 + 0.5)
        need = 7 if dig else 3   # числа Whisper пишет цифрой (1221 = «тысяча двести двадцать один»)
        if nx - nb >= need and nx >= 1.5 * max(nb, 1):
            add('ЛИШНЯЯ РЕЧЬ', c0, f"в отдельном прослушивании {nx} слов, в общей расшифровке {nb}: «{' '.join(w['w'] for w in (gl if ng >= nl else lw))}» — дубль или проглоченный кусок", True)
    # «резиновое» слово: одно слово длиннее 1,3 с — под ним почти всегда проглоченная речь или пауза-дубль
    for w in ww:
        if w['e'] - w['s'] > 1.3 and len(norm(w['w'])) >= 2:
            seg = a[int(w['s'] * SR):int(w['e'] * SR)]
            if len(seg) and np.mean(np.abs(seg) > 0.02) > 0.35:
                add('РЕЗИНОВОЕ СЛОВО', w['s'], f"«{w['w']}» растянуто на {w['e'] - w['s']:.1f} с, внутри звучит речь — проверить, нет ли там дубля", True)

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
    # куски звука для ручной проверки (спектрограмма): у каждого сильного замечания ±1,5 с, плюс начало и конец ролика
    CD = os.environ.get('CLIPS')
    if CD:
        import wave
        os.makedirs(CD, exist_ok=True)
        def clip(t0, t1, name):
            x = a[int(max(0, t0) * SR):int(min(D, t1) * SR)]
            w = wave.open(f'{CD}/{name}.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
        clip(0, 1.5, 'nachalo'); clip(D - 1.5, D, 'konec')
        for f_ in flags:
            if f_['strong'] or f_['kind'] in ('КОНЕЦ', 'НАЧАЛО', 'ПОВТОР', 'РЕЗ ПО СЛОВУ', 'ФАЛЬСТАРТ', 'СЛУЖЕБНОЕ'):
                clip(f_['t'] - 1.5, f_['t'] + 1.5, f"t{f_['t']:07.2f}")
    print(json.dumps({'file': V, 'dur': round(D, 2), 'joints': J, 'cuts': CUTS, 'flags': flags,
                      'giga': ' '.join(w['w'] for w in gw), 'whisper': ' '.join(w['w'] for w in ww),
                      'gw': gw, 'ww': ww}, ensure_ascii=False, default=float))

if __name__ == '__main__':
    main()
