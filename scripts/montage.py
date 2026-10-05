#!/usr/bin/env python3
"""Автомонтаж сырого вертикального ролика Евгения.
python3 montage.py raw.mp4 outdir
Делает: words.json, cut-план, два видео (2 строки / по словам), обложку, субтитры .srt
"""
import json, os, re, subprocess, sys

RAW, OUT = sys.argv[1], sys.argv[2]
MODEL = os.environ.get('WMODEL', '/home/claude/edit/model.bin')
SPEED = 1.2
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
FONT = 'Inter Black'
PROMPT = 'Испания, Валенсия, ВНЖ, NIE, недвижимость. Всё, пошёл работать.'
FIX = {'толноценно': 'полноценно', 'магазинец': 'магазине', 'магазинде': 'магазине'}
JUNK = re.compile(r'подпиш|продолжение следует|субтитр|редактор|спасибо за просмотр|^\W*(э+|м+|а+)\W*$', re.I)


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str), check=True, capture_output=True, text=True, **kw)


wav = f'{OUT}/a.wav'
sh(['ffmpeg', '-v', 'error', '-y', '-i', RAW, '-ar', '16000', '-ac', '1', wav])
dur = float(sh(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav]).stdout)

# цвет: телефон снимает HDR (HLG) — переводим в обычный цвет без бледности
trc = sh(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=color_transfer', '-of', 'csv=p=0', RAW]).stdout.strip().strip(',').split(',')[0].strip()
TM = ('zscale=t=linear:npl=250,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=2,'   # 04.10.2026 (сверено со скрином оригинала из галереи): было npl=80/desat=0 — жёлто-оранжевая бледная картинка
      'zscale=t=bt709:m=bt709:r=tv,format=yuv420p,eq=contrast=1.06:saturation=1.15,') if trc in ('arib-std-b67', 'smpte2084') else ''
COVER = os.environ.get('COVER', '')          # «СТРОКА1|СТРОКА2|СТРОКА3»
COVER_HL = os.environ.get('COVER_HL', '')    # слово жёлтым
TITLE_SEC = float(os.environ.get('TITLE_SEC', '3.5'))   # надпись обложки в начале: 3,5 с (03.10.2026: 2,6 с не успевал прочитать)
GRADE = os.environ.get('GRADE', '')   # без добавленной сочности — цвет как в оригинале
TM = TM + GRADE

# 1. паузы по звуку
log = subprocess.run(['ffmpeg', '-i', wav, '-af', 'silencedetect=noise=-30dB:d=0.22', '-f', 'null', '-'],
                     capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
sil = list(zip(starts, ends + [dur] * (len(starts) - len(ends))))
chunks, cur = [], 0.0
for a, b in sil:
    if a - cur > 0.12:
        chunks.append([cur, a])
    cur = b
if dur - cur > 0.12:
    chunks.append([cur, dur])
PADL, PADR = 0.06, 0.10
chunks = [[max(0, a - PADL), min(dur, b + PADR)] for a, b in chunks]

# 2. распознаём каждый кусок отдельно
from pywhispercpp.model import Model
m = Model(MODEL, n_threads=os.cpu_count(), print_progress=False, print_realtime=False,
          redirect_whispercpp_logs_to=None)
CACHE = f'{OUT}/asr_cache.json'
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
prev = ''
plan = []
for i, (a, b) in enumerate(chunks):
    cw = f'{OUT}/c.wav'
    sh(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', wav, '-af', 'apad=pad_dur=0.4', cw])
    key = f'{a:.3f}-{b:.3f}'
    if key not in cache:
        segs = m.transcribe(cw, language='ru', token_timestamps=True, max_len=1, split_on_word=True,
                            initial_prompt=(PROMPT + ' ' + prev)[-200:])
        cache[key] = [(s.t0 / 100, s.t1 / 100, s.text.strip()) for s in segs if s.text.strip()]
        json.dump(cache, open(CACHE, 'w'), ensure_ascii=False)
    ws = cache[key]
    text = ' '.join(w for _, _, w in ws)
    if not ws or JUNK.search(text) or (b - a < 0.35 and len(text) < 4) or len(ws) / (b - a) > 6.5:
        plan.append({'a': a, 'b': b, 'text': text, 'keep': False, 'why': 'шум/э'})
        continue
    # растягиваем слова на реальную длину речи внутри куска
    t0, t1 = ws[0][0], ws[-1][1]
    s0, s1 = PADL, (b - a) - PADR
    k = (s1 - s0) / max(0.01, t1 - t0)
    if os.environ.get('ALIGNED'):   # время слов уже точное (align.py, DTW) — не растягиваем
        t0, s0, k = 0.0, 0.0, 1.0
    words = []
    for x0, x1, w in ws:
        w = FIX.get(w.strip('.,?!').lower(), None) and w.replace(w.strip('.,?!'), FIX[w.strip('.,?!').lower()]) or w
        words.append({'w': w, 's': a + s0 + (x0 - t0) * k, 'e': a + s0 + (x1 - t0) * k})
    plan.append({'a': a, 'b': b, 'text': text, 'keep': True, 'words': words})
    prev = text

# 2б. обрезать конец куска после N-го слова (неудачный дубль внутри куска): TRIM='{"ключ куска": N}' (04.10.2026)
for k_, n_ in json.loads(os.environ.get('TRIM', '{}')).items():
    for p in plan:
        if p['keep'] and f"{p['a']:.3f}-{p['b']:.3f}" == k_ and 0 < n_ < len(p['words']):
            p['b'] = p['words'][n_]['s'] - 0.04
            p['words'] = p['words'][:n_]
            p['text'] = ' '.join(w['w'] for w in p['words'])

# 3. оговорки: кусок, который начинается так же, как следующий, = неудачный дубль
def norm(t):
    return re.sub(r'[^\w ]', '', t.lower()).split()
kept = [p for p in plan if p['keep']]
for i in range(len(kept) - 1):
    x, y = norm(kept[i]['text']), norm(kept[i + 1]['text'])
    n = min(3, len(x), len(y))
    if n >= 2 and x[:n] == y[:n]:
        kept[i]['keep'] = False; kept[i]['why'] = 'повтор/оговорка'
kept = [p for p in plan if p['keep']]

# 3б. ПРОБА 05.10.2026 (только если в папке работы есть proba.json): голос с первого кадра и обрыв сразу после «работать»
PROBA = json.load(open(f'{OUT}/proba.json')) if os.path.exists(f'{OUT}/proba.json') else None
if PROBA and kept:
    f0 = kept[0]
    if f0['words']: f0['a'] = max(f0['a'], f0['words'][0]['s'] - 0.03)
    l0 = kept[-1]
    if l0['words']: l0['b'] = min(l0['b'], l0['words'][-1]['e'] + 0.12)
    print('proba', json.dumps({k: v for k, v in PROBA.items()}, ensure_ascii=False))

# 4. таймлайн результата
t = 0.0
for p in kept:
    p['o'] = t
    for w in p['words']:
        w['os'] = (t + w['s'] - p['a']) / SPEED
        w['oe'] = (t + w['e'] - p['a']) / SPEED
    t += p['b'] - p['a']
total = t / SPEED
json.dump(plan, open(f'{OUT}/plan.json', 'w'), ensure_ascii=False, indent=1)
if os.environ.get('ASR_ONLY'):   # облако, этап 1: только распознать и разложить на куски, без рендера (04.10.2026)
    with open(f'{OUT}/текст.txt', 'w') as f_:
        for p in plan:
            f_.write(f"{p['a']:.3f}-{p['b']:.3f}\t{'+' if p['keep'] else '-'}\t{p['text']}\n")
    sys.exit(0)
words = [w for p in kept for w in p['words']]
words = [w for w in words if w['w'].strip() not in ('-', '—', '–')]   # тире в субтитрах не показываем


# 4б. где лицо: глаза, центр, подбородок (медиана по кадрам)
import cv2, statistics as st_
HAAR = os.environ.get('HAAR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'haar.xml'))
cc = cv2.CascadeClassifier(HAAR)
fx = []
allf = []   # все находки по кадрам (04.10.2026)
for tt in [x / 10 for x in range(10, int(dur * 10) - 10, 25)]:
    sh(['ffmpeg', '-v', 'error', '-y', '-ss', f'{tt:.2f}', '-i', RAW, '-frames:v', '1', '-vf',
        f'{TM}scale={W//2}:{H//2}:force_original_aspect_ratio=increase,crop={W//2}:{H//2}', f'{OUT}/fr.png'])
    g = cv2.cvtColor(cv2.imread(f'{OUT}/fr.png'), cv2.COLOR_BGR2GRAY)
    f = cc.detectMultiScale(g, 1.1, 5, minSize=(30, 30))   # 04.10.2026: шортсы в полный рост
    allf.append([((x + w / 2) / (W / 2), (y + 0.42 * h) / (H / 2), (y + h) / (H / 2), h / (H / 2)) for x, y, w, h in f])
for fr in allf:
    if fr: fx.append(max(fr, key=lambda d: d[3]))   # самое крупное, как было; при ошибке — подсказка FACE
if os.environ.get('FACE'):   # ручная подсказка «CX,EYE» (доли кадра), если детектор всё же ошибся
    _cx, _ey = map(float, os.environ['FACE'].split(','))
    fx = [d for fr in allf for d in fr if abs(d[0] - _cx) < 0.08 and abs(d[1] - _ey) < 0.05] or [(_cx, _ey, _ey + 0.06, 0.08)]
if fx:
    CX = st_.median(a[0] for a in fx); EYE = st_.median(a[1] for a in fx); CHIN = st_.median(a[2] for a in fx) + 0.02
else:
    CX, EYE, CHIN = 0.5, 0.40, 0.55
HN = st_.median(a[3] for a in fx) if fx else 0.25   # высота лица в долях кадра
EYE_T = 0.40                                  # куда ставим глаза
ZB = min(float(os.environ.get('ZMAX', '1.15')), max(1.0, (1 - 0.45) / max(0.05, 1 - EYE)))   # базовая крупность (больше 1.15 — мыло)
LEVELS = [ZB, ZB * 1.06, ZB * 1.12]
def ycrop(z): return min(max(EYE * z - EYE_T, 0), z - 1)
chin_out = max(CHIN * z - ycrop(z) for z in LEVELS)
SUB_MV = int(max(int(H * 0.25), H * (1 - chin_out - 0.03) - 110))   # низ субтитров не ниже 75% высоты: ниже надписи TikTok
HEAD_PX = (max(0.0, EYE - 0.72 * HN) * ZB - ycrop(ZB)) * H   # макушка С ВОЛОСАМИ в первом кадре, px (04.10.2026: было 0.54 — надпись садилась на волосы)
CTA_Y = int(os.environ.get('CTA_Y', '250'))   # центр плашки-призыва: высоко над головой, лоб и очки не закрывать
json.dump({'CX': float(CX), 'EYE': float(EYE), 'HN': float(HN), 'n': len(fx)}, open(f'{OUT}/face.json', 'w'))   # для cover.py, если там лицо не найдётся
if os.environ.get('FACE_ONLY'): sys.exit(0)
print('face', dict(CX=round(CX, 3), EYE=round(EYE, 3), CHIN=round(CHIN, 3), ZB=round(ZB, 2), SUB_MV=SUB_MV, CTA_Y=CTA_Y, n=len(fx)))

# 5. зумы: смена крупности на каждой склейке после конца предложения + плавный наезд на хуке
cuts = []
z = 1.0
segs_z = []
for i, p in enumerate(kept):
    st = p['o'] / SPEED
    if i == 0:
        segs_z.append((st, 'hook'))
    elif re.search(r'[.?!]$', kept[i - 1]['text'].strip()):
        z = 1.14 if z == 1.0 else 1.0
        segs_z.append((st, z))
zexpr = '1.0'
for st, zz in reversed(segs_z):
    if zz == 'hook':
        continue
    zexpr = f'if(gte(t,{st:.3f}),{zz},{zexpr})'
hook_end = segs_z[1][0] if len(segs_z) > 1 else 3
zexpr = f'if(lt(t,{hook_end:.3f}),1+0.10*t/{hook_end:.3f},{zexpr})'

# 6. субтитры
def ts(x):
    x = max(0, x); h = int(x // 3600); mi = int(x % 3600 // 60); s = x % 60
    return f'{h}:{mi:02d}:{s:05.2f}'

def clean(w):
    w = w.replace('.', '').replace(',', '').replace('…', '')
    return w

HDR = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{FONT},74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,6,2,2,90,90,{SUB_MV},1
Style: Kar,{FONT},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,3,0,1,7,3,2,150,150,{SUB_MV},1
Style: Credit,{FONT},30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,3,6,0,1,0,0,0,1
Style: Num,{FONT},150,&H0000E1FF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,10,5,8,40,40,250,1
Style: TitleY,{FONT},92,&H000C0C0C,&H000C0C0C,&H0000D6FF,&H0000D6FF,0,0,0,0,100,100,0,0,3,20,0,8,50,50,110,1
Style: TitleW,{FONT},92,&H000C0C0C,&H000C0C0C,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,3,20,0,8,50,50,110,1
Style: Cta,{FONT},82,&H00FFFFFF,&H00FFFFFF,&H00000000,&HC8000000,0,0,0,0,100,100,0,0,3,26,0,5,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# фразы: режем по знакам препинания и по длине
phr, curp = [], []
for w in words:
    curp.append(w)
    txt = ' '.join(clean(x['w']) for x in curp)
    if re.search(r'[.?!,]$', w['w']) or len(txt) > 30 or len(curp) >= 6:
        phr.append(curp); curp = []
if curp: phr.append(curp)

def two_lines(ws):
    s = [clean(x['w']) for x in ws]
    if len(' '.join(s)) <= 18 or len(s) < 2:
        return ' '.join(s)
    best = min(range(1, len(s)), key=lambda i: abs(len(' '.join(s[:i])) - len(' '.join(s[i:]))))
    return ' '.join(s[:best]) + r'\N' + ' '.join(s[best:])

# ПРОБА 05.10.2026: слова по смыслу красным/зелёным всё время, пока на экране (не больше 6 за ролик)
COLW = {}
if PROBA:
    def _hit(w, stems): return any(clean(w['w']).lower().strip('?!«»"').startswith(s) for s in stems)
    for w in words:
        if len(COLW) >= 6: break
        if w['os'] < (TITLE_SEC if COVER else 0): continue
        if _hit(w, PROBA.get('red', [])): COLW[id(w)] = r'&H00303BFF&'
        elif _hit(w, PROBA.get('green', [])): COLW[id(w)] = r'&H0050D82E&'
    print('colored', [clean(w['w']) for w in words if id(w) in COLW])
evA, evB = [], []
for i, ws in enumerate(phr):
    st = ws[0]['os']; en = phr[i + 1][0]['os'] if i + 1 < len(phr) else ws[-1]['oe'] + 0.3
    en = min(en, ws[-1]['oe'] + 0.6)
    evA.append(f'Dialogue: 0,{ts(st)},{ts(en)},Sub,,0,0,0,,{{\\fad(60,0)}}{two_lines(ws).upper()}')
    # по словам: короткие группы по 3 слова, активное слово жёлтое и чуть крупнее
    groups, cg = [], []
    for x in ws:
        if cg and (len(' '.join(clean(y['w']) for y in cg + [x])) > 17 or len(cg) >= 3):
            groups.append(cg); cg = []
        cg.append(x)
    if cg: groups.append(cg)
    for gi, g in enumerate(groups):
        gend = groups[gi + 1][0]['os'] if gi + 1 < len(groups) else en
        for j, w in enumerate(g):
            ws_ = w['os']; we_ = g[j + 1]['os'] if j + 1 < len(g) else gend
            parts = []
            for jj, x in enumerate(g):
                tx = clean(x['w']).upper()
                cc_ = COLW.get(id(x))
                if jj == j:
                    parts.append(r'{\c' + (cc_ or r'&H0000E1FF&') + r'\fscx112\fscy112}' + tx + r'{\c&H00FFFFFF&\fscx100\fscy100}')
                elif cc_:
                    parts.append(r'{\c' + cc_ + '}' + tx + r'{\c&H00FFFFFF&}')
                else:
                    parts.append(tx)
            gl = len(' '.join(clean(x['w']) for x in g))
            fit = r'{\fscx%d\fscy%d}' % ((min(100, int(1200 / gl)),) * 2) if gl > 12 else ''
            pop = r'{\fscx92\fscy92\t(0,90,\fscx100\fscy100)}' if j == 0 and not fit else ''
            line = ' '.join(parts)
            if fit:
                fz = min(100, int(1200 / gl))
                line = line.replace(r'\fscx112\fscy112', r'\fscx%d\fscy%d' % (fz * 112 // 100, fz * 112 // 100)).replace(r'\fscx100\fscy100', r'\fscx%d\fscy%d' % (fz, fz))
            evB.append(f'Dialogue: 0,{ts(ws_)},{ts(we_)},Kar,,0,0,0,,{fit}{pop}' + line)


# 5б. зум волнами: плавно приблизил за N секунд, плавно вернул за M (как ключи в CapCut)
WAVES = [(5, 1.09), (3, 1.0), (8, 1.12), (4, 1.0), (6, 1.08), (3, 1.0), (7, 1.11), (4, 1.0)]   # кадрирование как в утверждённом стиле (Евгений 03.10.2026: «верни кадрирование»); чёткость держит CRF 16
keys = [(0.0, ZB)]   # (время, крупность)
k = 0
while keys[-1][0] < total:
    d, m_ = WAVES[k % len(WAVES)]
    keys.append((keys[-1][0] + d, ZB * m_)); k += 1

# ПРОБА 05.10.2026: резкий наезд +8% за 0,15 с на 3–5 ключевых словах, держится до конца фразы (~1 с), потом плавно назад
PUNCH = []
if PROBA:
    pend = {id(w): ws[-1]['oe'] for ws in phr for w in ws}
    for w in words:
        if len(PUNCH) >= 5: break
        if w['os'] < (TITLE_SEC + 0.3 if COVER else 0.5) or w['os'] > total - 3: continue
        if not _hit(w, PROBA.get('punch', [])): continue
        if PUNCH and w['os'] - PUNCH[-1][0] < 5: continue
        PUNCH.append((w['os'], min(max(w['os'] + 0.8, pend[id(w)]), w['os'] + 1.4)))
    print('punch', [(round(a, 1), round(b, 1)) for a, b in PUNCH])
def punch_at(t):
    for a, b in PUNCH:
        if a <= t <= b: return 1 + 0.08 * min(1, (t - a) / 0.15)
        if b < t < b + 0.45: return 1 + 0.08 * (1 - ease((t - b) / 0.45))
    return 1.0

# картинка в картинке: PIP=pip.json {"from": raw_t, "to": raw_t, "segs": [{"file","ss","crop","credit"}]}
PIP = json.load(open(os.environ['PIP'])) if os.environ.get('PIP') else None
def raw2out(rt):
    for p in kept:
        if p['a'] - 0.01 <= rt <= p['b'] + 0.01:
            return (p['o'] + rt - p['a']) / SPEED
    nxt = [p for p in kept if p['a'] >= rt]
    return nxt[0]['o'] / SPEED if nxt else total
PIP_S = PIP_E = -1
PW, PH, PB, PX, PY = 588, 441, 6, (W - 600) // 2, 24
if PIP:
    PIP_S, PIP_E = raw2out(PIP['from']), raw2out(PIP['to'])
    if COVER: PIP_S = max(PIP_S, TITLE_SEC + 0.15)   # не накладывать на надпись обложки
    print('pip', round(PIP_S, 2), round(PIP_E, 2))

# всплывающие цифры
NUM = {'один': 1, 'одна': 1, 'два': 2, 'две': 2, 'три': 3, 'четыре': 4, 'пять': 5, 'шесть': 6, 'семь': 7,
       'восемь': 8, 'девять': 9, 'десять': 10, 'двадцать': 20, 'тридцать': 30, 'сто': 100, 'тысяча': 1000}
UNITS = re.compile(r'^(месяц|год|лет|раз|евро|дн|недел|час|минут|процент|тысяч|сот)', re.I)
pops = []
lw = [clean(w['w']).lower().strip('?!') for w in words]
for i, w in enumerate(lw):
    label = None
    if re.fullmatch(r'[abвб][12]', w, re.I):
        label = w.upper().replace('В', 'B').replace('Б', 'B')
    elif re.fullmatch(r'\d+([.,]\d+)?%?', w):
        unit = lw[i + 1] if i + 1 < len(lw) and UNITS.match(lw[i + 1]) else ''
        label = (w + ' ' + unit).strip()
    elif w in NUM:
        unit = ''
        if i + 1 < len(lw) and UNITS.match(lw[i + 1]): unit = lw[i + 1]
        elif i >= 2 and UNITS.match(lw[i - 2]) and lw[i - 1] in ('на', 'по', 'за'): unit = lw[i - 2]
        elif i >= 1 and UNITS.match(lw[i - 1]): unit = lw[i - 1]
        if unit: label = f'{NUM[w]} {unit}'
    elif w == 'год' and i >= 1 and lw[i - 1] in ('через', 'прошёл', 'прошел'):
        label = '1 год'
    if label:
        st = words[i]['os']
        if COVER and st < TITLE_SEC + 0.2:
            continue
        if PIP_S - 0.5 <= st <= PIP_E + 0.3:   # сверху окошко с видео
            continue
        if pops and (st - pops[-1][0] < 0.5 or (pops[-1][1] == label and st - pops[-1][0] < 3)):
            continue
        pops.append((st, label))
evN = []
for st, label in pops:
    evN.append(f'Dialogue: 1,{ts(st)},{ts(st + 1.2)},Num,,0,0,0,,'
               r'{\fscx40\fscy40\t(0,140,\fscx115\fscy115)\t(140,240,\fscx100\fscy100)\fad(0,200)}' + label.upper())

# призыв в конце: на последних словах перед «Всё, пошёл работать»
CTA = os.environ.get('CTA', 'Было так же?\\NНапишите в комментариях')
CTA_SEC = 5.0 if 'описани' in CTA.lower() else 2.6   # призыв «полное видео, ссылка в описании» — 5 с, чтобы успели прочитать (04.10.2026)
evC = [f'Dialogue: 2,{ts(max(0, total - CTA_SEC))},{ts(total)},Cta,,0,0,0,,'
       r'{\an5\pos(540,'+str(CTA_Y)+r')\fscx60\fscy60\t(0,160,\fscx100\fscy100)}' + CTA]

evT = []
nT = len(COVER.split('|')) if COVER else 0
TBLK = (nT - 1) * 132 + 115                    # высота блока надписи, px
TSC = min(1.0, max(0.7, (HEAD_PX - 30 - 110) / TBLK)) if nT else 1.0   # не влезает над головой — уменьшаем шрифт (не ниже 70%)
TTOP = int(max(110, min(HEAD_PX - 30 - TBLK * TSC, 640 - TBLK * TSC)))   # над волосами; голова высоко — можно задеть волосы; голова низко — надпись остаётся в верхней трети (низ не ниже ~640 px), с пробелом до головы (04.10.2026)
print('ttop', TTOP, 'scale', round(TSC, 2), 'head', int(HEAD_PX))
if COVER:   # как обложка: жёлтые плашки, строка с ключевым словом — на белой, текст чёрный, ровно
    for i, ln in enumerate(COVER.split('|')):
        st_name = 'TitleW' if COVER_HL and any(w.strip('?!.,') == COVER_HL for w in ln.split()) else 'TitleY'
        evT.append(f'Dialogue: 3,{ts(0)},{ts(TITLE_SEC)},{st_name},,0,0,0,,' + r'{\an8\pos(540,' + str(int(TTOP + i * 132 * TSC)) + r')\fscx' + str(int(TSC * 100)) + r'\fscy' + str(int(TSC * 100)) + r'\fad(0,250)}' + ln)
evP = []
if PIP:
    t0_ = PIP_S
    for sg in PIP['segs']:
        d_ = sg['dur']
        evP.append(f'Dialogue: 4,{ts(t0_)},{ts(min(PIP_E, t0_ + d_))},Credit,,0,0,0,,' + r'{\an1\pos(' + f'{PX + PB + 8},{PY + PH + PB - 8}' + r')}' + sg['credit'])
        t0_ += d_
        if t0_ >= PIP_E: break
    evT += evP
for name, ev in (('A', evA), ('B', evB)):
    open(f'{OUT}/subs_{name}.ass', 'w').write(HDR + '\n'.join(ev + evN + evC + evT) + '\n')

# srt на всякий случай
with open(f'{OUT}/subs.srt', 'w') as f:
    for i, ws in enumerate(phr, 1):
        st, en = ws[0]['os'], ws[-1]['oe']
        def st_(x): return f'{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(x*1000%1000):03d}'
        f.write(f"{i}\n{st_(st)} --> {st_(en)}\n{' '.join(clean(x['w']) for x in ws)}\n\n")

# ПРОБА 05.10.2026: субтитры.srt для YouTube/FB — по фразам, с пунктуацией, до 2 строк по ~42 знака
if PROBA:
    def _t(x): return f'{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(round(x*1000)%1000):03d}'
    sp, cur_ = [], []
    for w in words:
        cur_.append(w)
        tx_ = ' '.join(x['w'] for x in cur_)
        if re.search(r'[.?!…]$', w['w']) or (re.search(r'[,:;]$', w['w']) and len(tx_) > 40) or len(tx_) > 76:
            sp.append(cur_); cur_ = []
    if cur_: sp.append(cur_)
    with open(f'{OUT}/субтитры.srt', 'w') as f:
        for i, ws in enumerate(sp, 1):
            tw = [x['w'] for x in ws]; tx_ = ' '.join(tw)
            if len(tx_) > 42 and len(tw) > 1:
                b_ = min(range(1, len(tw)), key=lambda k_: abs(len(' '.join(tw[:k_])) - len(' '.join(tw[k_:]))))
                tx_ = ' '.join(tw[:b_]) + '\n' + ' '.join(tw[b_:])
            en = sp[i][0]['os'] if i < len(sp) else ws[-1]['oe']
            f.write(f"{i}\n{_t(ws[0]['os'])} --> {_t(min(en, ws[-1]['oe'] + 0.5))}\n{tx_[:1].upper() + tx_[1:]}\n\n")

# 7. сборка видео: каждый кадр отдельно — лицо по центру, плавный зум
import numpy as np, math
FPS = 30
TRANS = 0.5   # длительность плавного перехода крупности, сек
def ease(x):
    x = min(1, max(0, x)); return 0.5 - 0.5 * math.cos(math.pi * x)
def zoom_at(t):
    for (t0, z0), (t1, z1) in zip(keys, keys[1:]):
        if t <= t1:
            return z0 + (z1 - z0) * ease((t - t0) / (t1 - t0))
    return keys[-1][1]
sel = '+'.join(f'between(t,{p["a"]:.3f},{p["b"]:.3f})' for p in kept)
# проход 1: лицо на каждом 3-м кадре в маленьком размере, потом сильное сглаживание (~2 с)
SW, SH_ = W // 4, H // 4
def fq(p):   # путь в фильтре ffmpeg: запятая в имени ролика ломала граф (04.10.2026, «13 Facebook молчал, а потом…»)
    return "'" + p.replace('\\', '/').replace("'", "'\\\\''") + "'"
p1 = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', RAW, '-filter_complex',
    f"[0:v]select='{sel}',setpts=N/FRAME_RATE/TB,setpts=PTS/{SPEED},fps={FPS},"
    f"{TM}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},scale={SW}:{SH_}[v]", '-map', '[v]',
    '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE)
det = []
n = 0
while True:
    buf = p1.stdout.read(SW * SH_)
    if len(buf) < SW * SH_: break
    if n % 3 == 0:
        g = np.frombuffer(buf, np.uint8).reshape(SH_, SW)
        f = cc.detectMultiScale(g, 1.1, 5, minSize=(20, 20))
        if len(f):   # ближайшее к найденному лицу, а не самое крупное; далёкие находки — листва (04.10.2026)
            x, y, w, h = min(f, key=lambda r: abs((r[0] + r[2] / 2) * 4 - CX * W) + abs((r[1] + 0.42 * r[3]) * 4 - EYE * H))
            if abs((x + w / 2) * 4 - CX * W) < W * 0.2 and abs((y + 0.42 * h) * 4 - EYE * H) < H * 0.12:
                det.append((n, (x + w / 2) * 4, (y + 0.42 * h) * 4))
    n += 1
p1.wait()
NF = n
fxs = np.full(NF, CX * W); fys = np.full(NF, EYE * H)
if det:
    dn = np.array([d[0] for d in det]); dx = np.array([d[1] for d in det]); dy = np.array([d[2] for d in det])
    # выбрасываем выбросы (ошибки детектора)
    ok = (abs(dx - np.median(dx)) < W * 0.2) & (abs(dy - np.median(dy)) < H * 0.12)
    dn, dx, dy = dn[ok], dx[ok], dy[ok]
    fxs = np.interp(np.arange(NF), dn, dx); fys = np.interp(np.arange(NF), dn, dy)
    sig = FPS * 1.0
    kx = np.exp(-0.5 * (np.arange(-3 * int(sig), 3 * int(sig) + 1) / sig) ** 2); kx /= kx.sum()
    pad = len(kx) // 2
    fxs = np.convolve(np.pad(fxs, pad, mode='edge'), kx, mode='valid')
    fys = np.convolve(np.pad(fys, pad, mode='edge'), kx, mode='valid')

dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', RAW, '-filter_complex',
    f"[0:v]select='{sel}',setpts=N/FRAME_RATE/TB,setpts=PTS/{SPEED},fps={FPS},"
    f"{TM}scale={W}:{H}:force_original_aspect_ratio=increase:in_color_matrix=bt709,crop={W}:{H}[v]", '-map', '[v]',
    '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
aud = f"[1:a]aselect='{sel}',asetpts=N/SR/TB,atempo={SPEED},loudnorm=I=-14:TP=-1.5:LRA=11[a]"
CRF = os.environ.get('CRF', '16')   # сжатие по качеству (~15-20 Мбит/с, как Edits/CapCut), Евгений одобрил 03.10.2026; 5-8 Мбит/с размазывали кожу
VBR = os.environ.get('VBR', '8000k')   # постоянное качество; большой файл режется на куски (send_parts.py), склейщик собирает на компьютере
print('crf', CRF)
pin, pfc = [], ''
if PIP:
    D = PIP_E - PIP_S; acc = 0; parts_ = []
    for i, sg in enumerate(PIP['segs']):
        d_ = min(sg['dur'], D - acc)
        if d_ <= 0: break
        img_ = sg['file'].lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))   # фото: держим кадр dur секунд (04.10.2026)
        pin += (['-loop', '1', '-framerate', str(FPS), '-t', f'{d_ + 0.5:.3f}'] if img_ else []) + ['-i', sg['file']]
        k_ = len(parts_)
        parts_.append(f"[{2 + k_}:v]trim=start={0 if img_ else sg['ss']}:duration={d_:.3f},setpts=PTS-STARTPTS,fps={FPS},crop={sg['crop']},scale={PW}:{PH}:flags=lanczos,setsar=1,pad={PW + 2 * PB}:{PH + 2 * PB}:{PB}:{PB}:color=white,format=yuv420p[p{k_}]")
        acc += d_
    n_ = len(parts_)
    pfc = ';'.join(parts_) + ';' + ''.join(f'[p{i}]' for i in range(n_)) + f"concat=n={n_}:v=1:a=0,format=yuva420p,fade=t=in:st=0:d=0.3:alpha=1,fade=t=out:st={max(0, D - 0.3):.3f}:d=0.3:alpha=1,setpts=PTS+{PIP_S:.3f}/TB[pip];"
outs = []
for name in os.environ.get('VARIANTS', 'B').split(','):
    out = f'{OUT}/ролик_{name}.mp4'
    outs.append(subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24',
        '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', RAW] + pin + ['-filter_complex',
        (pfc + f"[0:v]scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,unsharp=5:5:0.5:5:5:0[bs];[bs][pip]overlay={PX}:{PY}:eof_action=pass,format=yuv420p,subtitles={fq(f'{OUT}/subs_{name}.ass')}[v];{aud}") if PIP else
        f"[0:v]scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,unsharp=5:5:0.5:5:5:0,subtitles={fq(f'{OUT}/subs_{name}.ass')}[v];{aud}", '-map', '[v]', '-map', '[a]',
        *(['-c:v', 'libx265', '-preset', 'medium', '-crf', CRF, '-x265-params', 'aq-mode=3:vbv-maxrate=20000:vbv-bufsize=40000:log-level=error', '-tag:v', 'hvc1'] if os.environ.get('CODEC') == 'hevc' else ['-c:v', 'libx264', '-preset', 'slow', '-crf', os.environ.get('CRF264', '17'), '-profile:v', 'high', '-maxrate', '25M', '-bufsize', '50M']),   # H.264 по умолчанию (03.10.2026): играет везде, в т.ч. в просмотре Google Диска
        '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
        '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out],
        stdin=subprocess.PIPE))
n = 0
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    ex, ey = fxs[min(n, NF - 1)], fys[min(n, NF - 1)]
    t = n / FPS
    z = zoom_at(t) * punch_at(t)
    tx =min(0, max(W - z * W, W / 2 - z * ex))
    ty = min(0, max(H - z * H, EYE_T * H - z * ey))
    M = np.float32([[z, 0, tx], [0, z, ty]])
    o = cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    if n == 0:
        cv2.imwrite(f'{OUT}/cover_base.png', o)
    b = o.tobytes()
    for pr in outs: pr.stdin.write(b)
    n += 1
for pr in outs:
    pr.stdin.close(); pr.wait()
dec.wait()

print(json.dumps({'raw': dur, 'out': round(total, 2), 'first_word': round(words[0]['os'], 2) if words else None, 'tail': round(total - words[-1]['oe'], 2) if words else None, 'chunks': len(plan), 'kept': len(kept),
                  'dropped': [(round(p['a'], 2), p['text'], p['why']) for p in plan if not p['keep']],
                  'pops': pops}, ensure_ascii=False))
print(' '.join(clean(w['w']) for w in words))
