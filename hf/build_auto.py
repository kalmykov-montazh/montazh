# Пакетный перемонтаж в формат HyperFrames (решение Евгения 08.11.2026, 20:35).
# Эталон — «ПРОБА v2 — Налог за пустую квартиру» (hf/build_pustaya2.py). Переводчик из настроек старого монтажа
# novyj/<ключ>.json в композицию: title → штамп + красная фишка; card/big/full → тёмная карточка (одно число —
# счётчиком, процент — кольцом); stamp → новостная плашка; cta → белая карточка-призыв; cover → обложка стиля В
# слоем на первом кадре (текст 270–1640 px). Размытие в движении, тёплый цвет (lut в задаче), субтитры «микс» — subs.json.
# Плашки только над головой: высота считается по face.json (как в montage.py) и всё лишнее ужимается.
# Запуск: python hf/build_auto.py <папка проекта> <novyj.json> <osnova_words.json> <face.json> [vstavki.json]
import json, html, re, os, sys, shutil
from PIL import ImageFont

B = os.path.dirname(os.path.abspath(__file__))
P, SPEC, WORDS, FACE = sys.argv[1:5]
VST = json.load(open(sys.argv[5])) if len(sys.argv) > 5 and os.path.exists(sys.argv[5]) else {}
spec = json.load(open(SPEC))
W0 = json.load(open(WORDS))
os.makedirs(P, exist_ok=True)
for d in ("fonts", "snd"):
    if not os.path.exists(f"{P}/{d}"): shutil.copytree(f"{B}/pustaya2/{d}", f"{P}/{d}")
shutil.copy(f"{B}/pustaya2/gsap.min.js", P)
LOG = []
def log(*a): LOG.append(" ".join(str(x) for x in a))

def norm(s): return re.sub(r"[^\wё%]", "", s.lower().replace("ё", "е"))

# «Всё, пошёл работать» нигде не используем (21.10.2026) — если осталось в конце, ролик кончается до этих слов
W = list(W0)
lw = [norm(w["w"]) for w in W]
for i in range(len(W) - 1):
    if lw[i].startswith("пош") and lw[i + 1].startswith("работ") and W[i]["s"] > W[-1]["e"] - 6:
        j = i - 1 if i > 0 and lw[i - 1] in ("всё", "все") else i
        W = W[:j]; log("отрезано «пошёл работать» с", round(W0[j]["s"], 2)); break
json.dump(W, open(f"{P}/words.json", "w"), ensure_ascii=False)
DUR = round(W[-1]["e"] + 0.45, 3)

def find(phrase, after=0.0):
    ph = [norm(x) for x in str(phrase).split()]
    ph = [x for x in ph if x]
    # 10.11.2026: слово из правки (fix) может быть склеено из нескольких («Так что не спрашивайте») — ищем по частям
    lw, ls = [], []
    for w in W:
        for x in str(w["w"]).split():
            lw.append(norm(x)); ls.append(w["s"])
    for i in range(len(lw)):
        if ls[i] + 0.01 < after: continue
        if all(i + k < len(lw) and lw[i + k].startswith(ph[k][:max(3, len(ph[k]) - 2)]) for k in range(len(ph))):
            return ls[i]
    return None
def T(v, after=0.0):
    return find(v, after) if isinstance(v, str) else float(v)

# ---------- где голова: плашки строго выше макушки (как HEAD_MIN в montage.py, волна +6%) ----------
f = json.load(open(FACE)) if os.path.exists(FACE) else {"EYE": 0.5, "HN": 0.27}
EYE, HN = f["EYE"], f["HN"]
CHIN = EYE + 0.6 * HN
ANC = min(CHIN + 0.04, 0.95)
HEAD = min(((EYE - 0.72 * HN) * z - ANC * (z - 1)) * 1920 for z in (1.0, 1.06))
TOP = 200 if HEAD < 560 else 230
AVAIL = max(170, int(HEAD - 28 - TOP))          # сколько пикселей по высоте есть над головой
# видео с двух камер (лицо в маленьком окошке сверху): плашки ниже окошка — top_px задаётся в novyj/<ключ>.json
# top_after (фраза или секунды): окошко с лицом только с этого места — до него плашки как обычно
TOP_B, AVAIL_B = TOP, AVAIL
TOP_AFTER = ((T(spec["top_after"]) if T(spec["top_after"]) is not None else 1e9) if spec.get("top_after") is not None else 0.0) if spec.get("top_px") else None
TOP_UNTIL = (T(spec["top_until"]) or 1e9) if spec.get("top_px") and spec.get("top_until") is not None else 1e9
def set_top(t):
    global TOP, AVAIL
    if TOP_AFTER is not None and TOP_AFTER - 0.05 <= t < TOP_UNTIL - 0.05: TOP = int(spec["top_px"]); AVAIL = int(spec.get("avail_px", 420))
    else: TOP, AVAIL = TOP_B, AVAIL_B
set_top(0.0)
log(f"голова {HEAD:.0f} px, верх плашек {TOP}, место {AVAIL} px")

H, J, SND = [], [], []
tl = J.append
def snd(k, t, v=0.3): SND.append((k, round(max(0, t), 3), v))
BUSY = []   # (t0, t1) когда верх кадра занят — картинки-предметы туда не ставим
def esc(s): return html.escape(str(s))
def sanitize(s): return re.sub(r"с\s+нуля", "всё сначала", str(s), flags=re.I)

# ---------- обложка стиля В (маркер) слоем на кадре 0 ----------
FM = ImageFont.truetype(f"{B}/pustaya2/fonts/montserrat-900.ttf", 100)
def fit(text, width, start, minsz):
    s = start
    while s > minsz and FM.font_variant(size=s).getlength(text) > width: s -= 2
    return s
cov = spec.get("cover") or {}
ct = sanitize(cov.get("top", "")).upper().strip()
cb = [x.strip() for x in sanitize(cov.get("bot", "")).upper().split("|") if x.strip()]
lines = [x for x in [ct] if x]
bj = " ".join(cb)
if bj and FM.font_variant(size=70).getlength(bj) <= 920: lines.append(bj)
else: lines += cb
lines = lines[:3]
sizes = [fit(x, 920, 92, 54) for x in lines]
sz = min(sizes) if sizes else 86
cl = []
y = int(cov.get("y", 290))   # 10.11.2026: съёмка в полный рост на улице — голова ниже, текст можно выше (cover.y в novyj)
for k, x in enumerate(lines):
    cls = "b" if k % 2 == 0 else "y"
    cl.append(f'<div class="cvl {cls}" style="top:{y}px;font-size:{sz}px"><span>{esc(x)}</span></div>'); y += int(sz * 1.28)
sticker = ""
tc = (spec.get("title") or {}).get("cards") or []
def _stems(t): return {norm(x)[:5] for x in t.split() if len(norm(x)) >= 4}
if tc and len(tc[0]) <= 24 and not (_stems(tc[0]) & _stems(" ".join(lines))):
    st = sanitize(tc[0])
    stl = max(30, min(42, int(560 / max(6, len(st)))))
    stop = max(y + 20, 520)
    sticker = f'<div class="cst" style="top:{stop}px;font-size:{stl}px">{esc(st)}</div>'
bgimg = '<img class="full" src="cover_bg.png"><div class="full cg"></div>' if os.path.exists(f"{P}/cover_bg.png") else ""
H.append(f'<div id="cover" class="full cov">{bgimg}{"".join(cl)}{sticker}</div>')
tl('tl.set("#cover",{opacity:1},0).set("#cover",{opacity:0},0.12);')
log("обложка:", " / ".join(lines), "| наклейка:", tc[0] if sticker else "—", "| кегль", sz)

H.append(f'<div id="cam" class="full"><video id="v" class="full" src="osnova.mp4" data-start="0" data-duration="{DUR:.3f}" data-has-audio="true"></video></div>')

# ---------- кадры с места на весь экран вместо лица (11.11.2026, «Забастовка»: 40% лицо, 60% кадры) ----------
# novyj: "broll": [{"at": фраза, "to": фраза (где снова лицо) или "sec", "file": "kolonna.mp4", "vol": 0.18}]
# файлы — в P/br (задача кладёт из «работа/<ключ>/br»), рядом .wav с живым звуком улицы (тихо под голос)
BROLL = []
for k, b in enumerate(spec.get("broll", [])):
    t0 = T(b["at"])
    if t0 is None: log("кадры: не нашёл фразу", b["at"]); continue
    t1 = T(b["to"], t0 + 0.3) if b.get("to") else None
    if t1 is None: t1 = t0 + float(b.get("sec", 4))
    fp = f"{P}/br/{b['file']}"
    if not os.path.exists(fp): log("кадры: нет файла", b["file"]); continue
    try:
        import subprocess
        cd = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", fp], capture_output=True, text=True).stdout.strip())
    except Exception: cd = 99
    t0 = max(t0 - 0.05, 0.4); t1 = min(t1 - 0.05, t0 + cd - 0.05, DUR - 0.3)
    if t1 - t0 < 0.8: log("кадры: слишком коротко", b["file"]); continue
    bid = f"br{k}"
    H.append(f'<video id="{bid}" class="full" src="br/{b["file"]}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-has-audio="false" muted></video>')
    wav = fp[:-4] + ".wav"
    if os.path.exists(wav) and float(b.get("vol", 0.18)) > 0:
        H.append(f'<audio id="{bid}a" src="br/{os.path.basename(wav)}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-volume="{float(b.get("vol", 0.18))}"></audio>')
    BROLL.append((t0, t1)); log(f"кадры: {b['file']} {t0:.1f}–{t1:.1f} с")
if BROLL: log(f"кадры с места: {sum(b - a for a, b in BROLL):.1f} из {DUR:.1f} с ({100 * sum(b - a for a, b in BROLL) / DUR:.0f}%)")

# ---------- резкие наезды (как в эталоне): до 3 слов из punch, не чаще раза в 6 с ----------
pt, last = [], -10
for k in (spec.get("punch") or [])[:8]:
    t = find(k)
    if t is not None and t - last > 6 and t > 1.5 and len(pt) < 3: pt.append(t); last = t
for t in pt:
    tl(f'tl.fromTo("#cam",{{scale:1.12}},{{scale:1,duration:0.7,ease:"power3.out",immediateRender:false}},{t-0.03:.3f});'); snd("whoosh", t - 0.12, 0.22)

# ---------- надпись в начале: штамп + красная фишка ----------
CTA = spec.get("cta")
CTA_T = DUR - float(CTA.get("sec", 2.8)) - 0.2 if CTA else DUR
tt = spec.get("title")
def _first_group_t():
    ts = []
    for g in spec.get("groups", []):
        for it in g["items"]:
            if it["type"] != "arrow":
                t = T(it["at"])
                if t is not None: ts.append(t)
                break
    for it in spec.get("full", []):
        t = T(it["at"])
        if t is not None: ts.append(t)
    return min(ts) if ts else 1e9
FG = _first_group_t()
TITLE_END = 0
if tt:
    t1 = min(float(tt.get("sec", 3.5)), CTA_T - 0.2)
    if FG - 0.15 < t1: t1 = max(1.8, FG - 0.15)   # надпись уступает первой плашке
    TITLE_END = t1
    chips = "".join(f'<b class="{"red" if k == 0 else ""}">{esc(sanitize(x))}</b>' for k, x in enumerate(tt.get("cards", [])))
    H.append(f'<div id="ti" class="zone fit" style="top:{TOP}px"><div class="stamp"><span>{esc(sanitize(tt["stamp"]))}</span></div><div class="chips">{chips}</div></div>')
    t0 = 0.18
    tl(f'tl.from("#ti .stamp span",{{x:-700,opacity:0,duration:0.45,ease:"power4.out"}},{t0:.3f}).from("#ti .chips b",{{scale:0,stagger:0.12,duration:0.35,ease:"back.out(3)"}},{t0+0.35:.3f}).to("#ti",{{y:-60,opacity:0,duration:0.3,ease:"power2.in"}},{t1-0.3:.3f});')
    snd("boom", t0, 0.28); BUSY.append((0, t1))

# ---------- группы плашек ----------
NUM = re.compile(r"^[~≈+−-]?\s*(\d[\d\s]*(?:[.,]\d+)?)\s*(%|€|евро|км|месяц\w*|лет|год\w*|дней|дня|раз)?$", re.I)
def parse_num(s):
    m = NUM.match(s.strip().replace(" ", " "))
    if not m: return None
    v = float(m.group(1).replace(" ", "").replace(",", "."))
    return v, (m.group(2) or ""), m.group(1)

items_all = []
groups = spec.get("groups", [])
for gi, g in enumerate(groups):
    last = 0.0; built = []
    for it in g["items"]:
        if it["type"] == "arrow": continue
        t0 = T(it["at"], last)
        if t0 is None: log("не нашёл фразу:", it["at"]); continue
        last = t0; built.append((it, t0))
    if not built: continue
    te = T(g["end"], built[0][1]) if g.get("end") else None
    if te is None: te = built[-1][1] + 3.0
    items_all.append([gi, built, te])
for it in spec.get("full", []):
    t0 = T(it["at"])
    if t0 is None: log("не нашёл фразу:", it["at"]); continue
    items_all.append([100 + len(items_all), [({"type": "full", **it}, t0)], t0 + float(it.get("sec", 2.6))])
items_all.sort(key=lambda x: x[1][0][1])
# группы не висят вместе: каждая уходит до появления следующей, всё уходит до призыва
start_min = TITLE_END + 0.1 if tt else 0.3
clean = []
for k, (gi, built, te) in enumerate(items_all):
    built = [(it, max(t, start_min)) for it, t in built]
    nxt = items_all[k + 1][1][0][1] if k + 1 < len(items_all) else 1e9
    te = min(max(te, built[-1][1] + 1.8), nxt - 0.12, CTA_T - 0.1, built[-1][1] + 6.0)
    if te - built[0][1] < 0.8: log("группа слишком короткая, пропущена:", [i["text"] if "text" in i else i.get("type") for i, _ in built]); continue
    clean.append((gi, built, te))

def card_row(it, rid):
    txt = sanitize(it.get("text", "")); lab = sanitize(it.get("label", "") or "")
    parts = [x.strip() for x in txt.split("|")]
    if len(parts) > 1 and not lab: txt, lab = parts[0], " ".join(parts[1:])
    else: txt = " ".join(parts)
    red = it.get("lab", 0) == 1
    big = len(txt) <= 11
    cls = ("num" if big else "txt") + (" red" if red else "")
    return f'<div class="rw" id="{rid}"><b class="{cls}">{esc(txt)}</b>{f"<span>{esc(lab)}</span>" if lab else ""}</div>'

for n, (gi, built, te) in enumerate(clean):
    gid = f"p{n}"
    t0 = built[0][1]
    set_top(t0)
    kinds = [it["type"] for it, _ in built]
    cards = [(it, t) for it, t in built if it["type"] in ("card", "big", "full")]
    stamps = [(it, t) for it, t in built if it["type"] == "stamp"]
    BUSY.append((t0 - 0.1, te + 0.3))
    # 1) одно число — счётчик (процент — кольцом)
    one = cards[0][0] if len(cards) == 1 and not stamps else None
    pn = parse_num(one.get("text", "").split("|")[0]) if one else None
    if one and pn and pn[0] > 0:
        v, unit, raw = pn
        lab = sanitize(one.get("label") or one.get("top") or (one.get("text", "").split("|")[1] if "|" in one.get("text", "") else ""))
        dec = ("," in raw or "." in raw)
        ring = unit == "%" and v <= 100
        C = 2 * 3.14159 * 104
        sfx = {"евро": " €"}.get(unit.lower(), (" " + unit) if unit and unit != "%" else unit)
        if ring:
            H.append(f'''<div id="{gid}" class="meter fit" style="top:{TOP}px"><svg width="260" height="260"><circle class="rg" cx="130" cy="130" r="104"/><circle id="{gid}r" class="rv" cx="130" cy="130" r="104" stroke-dasharray="{C:.1f}" stroke-dashoffset="{C:.1f}"/></svg><div><div class="num" id="{gid}n">0%</div><div class="lab">{esc(lab)}</div></div></div>''')
            tl(f'tl.to("#{gid}r",{{strokeDashoffset:{C*(1-min(v,100)/100*0.9-0.05):.1f},duration:0.8,ease:"power2.out"}},{t0+0.1:.3f});')
        else:
            H.append(f'''<div id="{gid}" class="meter fit" style="top:{TOP}px;display:block;text-align:center"><div class="lab">{esc(lab)}</div><div class="num" id="{gid}n">0</div></div>''')
        nd = len(re.split(r"[.,]", raw.strip())[1]) if dec else 0
        year = (not unit) and (not dec) and 1800 <= v <= 2100
        fmt = (f'(o.v).toFixed({nd}).replace(".",",")' if dec else ('String(Math.round(o.v))' if year else 'Math.round(o.v).toLocaleString("ru-RU")'))
        tl(f'(()=>{{const o={{v:{(v - 15) if year else 0}}};tl.to(o,{{v:{v},duration:0.7,ease:"power3.out",onUpdate:()=>{{document.querySelector("#{gid}n").textContent={fmt}+"{sfx}"}}}},{t0+0.05:.3f});}})();')
        tl(f'tl.from("#{gid}",{{x:900,opacity:0,duration:0.45,ease:"power4.out"}},{t0-0.1:.3f}).to("#{gid}",{{opacity:0,y:-50,duration:0.3,ease:"power2.in"}},{te-0.3:.3f});')
        snd("whoosh", t0 - 0.15, 0.25); snd("click", t0 + 0.05, 0.25)
        continue
    # 2) только штампы — новостная плашка (красный блок + тёмная полоса)
    if not cards:
        for k, (it, t) in enumerate(stamps):
            sid = f"{gid}s{k}"
            t_end = stamps[k + 1][1] - 0.05 if k + 1 < len(stamps) else te
            txt = sanitize(it["text"])
            m = re.match(r"\s*[+−-]?\d[\d.,]*(?:\s?\d{3})*\s*(%|€|°\s?C|°)?", txt)   # число только в начале штампа
            red = m.group(0).strip() if m and len(m.group(0).strip()) <= 8 else "!"
            rest = txt[len(m.group(0)):].strip(" ,:—-+") if red != "!" else txt
            fs = 110 if len(red) <= 4 else 80
            H.append(f'<div id="{sid}" class="news fit" style="top:{TOP+20}px"><div class="nd"><b style="font-size:{fs}px">{esc(red)}</b></div>{f'<div class="nt">{esc(rest)}</div>' if (rest or red == "!") and (rest or txt) else ""}</div>')
            tl(f'tl.set("#{sid}",{{opacity:0}},0).set("#{sid}",{{opacity:1}},{t-0.1:.3f}).from("#{sid} .nd",{{x:-500,duration:0.45,ease:"power4.out"}},{t-0.1:.3f}).from("#{sid} .nt",{{scaleX:0,transformOrigin:"0% 50%",duration:0.4,ease:"power4.out"}},{t:.3f}).to("#{sid}",{{y:-60,opacity:0,duration:0.3}},{t_end-0.3:.3f});')
            snd("whoosh", t - 0.12, 0.28)
        continue
    # 3) карточка-таблица: строки появляются по словам, штампы — красной фишкой внизу
    rows = []
    for k, (it, t) in enumerate(built):
        rid = f"{gid}r{k}"
        if it["type"] == "stamp":
            rows.append(f'<div class="rw chiprow" id="{rid}"{' style="display:none"' if k >= 1 else ''}{' data-m="1"' if k == 1 else ''}><i>{esc(sanitize(it["text"]))}</i></div>')
        else:
            r_ = card_row(it, rid)
            rows.append(r_.replace('class="rw"', 'class="rw" style="display:none"' + (' data-m="1"' if k == 1 else ''), 1) if k >= 1 else r_)
    hdr = ""
    H.append(f'<div id="{gid}" class="rates fit" style="top:{TOP}px">{hdr}{"".join(rows)}</div>')
    tl(f'tl.from("#{gid}",{{x:{900 if n % 2 == 0 else -900},opacity:0,duration:0.45,ease:"power4.out"}},{t0-0.1:.3f}).to("#{gid}",{{opacity:0,y:-50,duration:0.3,ease:"power2.in"}},{te-0.3:.3f});')
    snd("whoosh", t0 - 0.15, 0.25)
    for k, (it, t) in enumerate(built):
        if k == 0: continue
        # строка занимает место только с момента появления; в таблице не больше двух строк сразу (не ужимать до мелкого)
        if k >= 2: tl(f'tl.set("#{gid}r{k-2}",{{display:"none"}},{t-0.1:.3f});')
        tl(f'tl.set("#{gid}r{k}",{{display:"flex"}},{t-0.1:.3f});')
        tl(f'tl.from("#{gid}r{k}",{{x:200,opacity:0,duration:0.35,ease:"power3.out"}},{t-0.1:.3f});'); snd("pop" if it["type"] == "stamp" else "click", t - 0.1, 0.28)
        if k >= 1 and it["type"] != "stamp":
            tl(f'tl.to("#{gid}r{k-1}",{{opacity:0.55,duration:0.2}},{t-0.1:.3f});')

# ---------- всплывающий призыв на сайт (пункт 13, 11.11.2026): окошко-уведомление со скрином блока сайта ----------
# spec["sait"] = {"img": "bbva.png", "text": "Основной текст. Ссылка в шапке профиля", "at": "фраза"}; 3,6 с, со «вжиком»,
# сверху над головой (где нет плашек), иначе внизу под субтитрами; не на лице, не поверх белой карточки в конце
KART = []
PICB = []
SAIT = spec.get("sait")
if SAIT:
    SD = 3.6
    ws = sorted({w["s"] for w in W if max(start_min, 6.0) <= w["s"] <= CTA_T - 0.3 - SD})
    ta = find(SAIT["at"]) if SAIT.get("at") else None
    if ta is None: ta = DUR * 0.4
    order = sorted(ws, key=lambda x: (0 if x >= ta - 0.2 else 1, abs(x - ta)))
    my = (spec.get("mix_y") or [int(min(1640, max(1380, CHIN * 1920 + 110)))])[0]
    lowtop = my + 78; lowh = min(1920 - 30 - lowtop, 270)
    pick = None
    for t in order:
        set_top(t)
        if not any(a < t + SD and t < b for a, b in BUSY) and AVAIL >= 230: pick = (t, "верх"); break
    if pick is None and lowh >= 190:
        for t in order:
            if not any(a < t + SD and t < b for a, b in PICB): pick = (t, "низ"); break
    if pick is None: log("окошко сайта пропущено: нет места")
    else:
        t, where = pick; t1 = t + SD
        os.makedirs(f"{P}/sait", exist_ok=True); shutil.copy(f"{B}/sait_skriny/{SAIT['img']}", f"{P}/sait/{SAIT['img']}")
        txt = sanitize(SAIT["text"]).strip().rstrip(".")
        main, pill = (txt.rsplit(". ", 1) + [""])[:2] if ". " in txt else (txt, "Ссылка в шапке профиля")
        if where == "верх":
            set_top(t); hc = min(AVAIL + 6, 330); top = TOP - 20; BUSY.append((t, t1))
        else:
            hc = lowh; top = lowtop; PICB.append((t, t1))
        fs = 46 if len(main) <= 34 else (40 if len(main) <= 50 else 34)
        H.append(f'<div id="sait" class="sait" style="top:{top}px;height:{hc}px"><img src="sait/{SAIT["img"]}" style="width:{int(hc*0.92)}px">'
                 f'<div class="st"><u>kalmykov-realty · сайт</u><b style="font-size:{fs}px">{esc(main)}</b><i>{esc(pill)}</i></div></div>')
        dy = -320 if where == "верх" else 320
        tl(f'tl.from("#sait",{{y:{dy},opacity:0,duration:0.5,ease:"back.out(1.5)"}},{t-0.08:.3f}).from("#sait i",{{scale:0,duration:0.35,ease:"back.out(3)"}},{t+0.5:.3f}).to("#sait",{{y:{dy//2},opacity:0,duration:0.32,ease:"power2.in"}},{t1-0.32:.3f});')
        snd("whoosh", t - 0.12, 0.25); snd("ding", t + 0.45, 0.2)
        log(f"окошко сайта: {SAIT['img']} в {t:.1f} с ({where}), «{main}»")

# ---------- картинки-предметы (03.11.2026): фото-карточка сбоку сверху, только когда верх свободен ----------
BAD = {"receipt_1.jpg"}   # 07.11.2026: старая французская квитанция — негодная
for k, (ph, img, opt) in enumerate(VST.get("ins", [])):
    if img in BAD: continue
    t = find(ph)
    if t is None: continue
    t = max(t, start_min); t1 = t + 2.2
    # pic_low (10.11.2026, склейки): картинка сбоку внизу над субтитрами, полного размера — верх не нужен,
    # иначе при высокой голове картинка ужимается до крошечной
    LOW = bool(spec.get("pic_low"))
    if t1 > CTA_T - 0.1 or any(a < t1 and t < b for a, b in (PICB if LOW else BUSY)): log("картинка пропущена (место занято):", img); continue
    (PICB if LOW else BUSY).append((t, t1)); KART.append(img)
    pid = f"ph{k}"; side = "left:40px" if len(KART) % 2 else "right:40px"
    st = f'<em>{esc(opt["stamp"])}</em>' if opt.get("stamp") else ""
    if LOW:
        my = (spec.get("mix_y") or [int(min(1640, max(1380, CHIN * 1920 + 110)))])[0]
        # правило 03.11: низ справа/слева по очереди, НИЖЕ субтитров, высота не больше 250 px — никогда не на лице
        top = my + 78; sc = max(0.55, min(1.0, (1920 - 24 - top) / 254))
        H.append(f'<div id="{pid}" class="photo2" style="top:{top}px;{side};transform-origin:50% 0;transform:scale({sc:.2f}) rotate({-4 if len(KART)%2 else 4}deg)"><img src="img/{os.path.basename(img)}">{st}</div>')
    else:
        H.append(f'<div id="{pid}" class="photo2 fit" style="top:{TOP}px;{side};transform:rotate({-4 if len(KART)%2 else 4}deg)"><img src="img/{os.path.basename(img)}">{st}</div>')
    tl(f'tl.from("#{pid}",{{scale:0.3,y:200,opacity:0,duration:0.45,ease:"back.out(1.7)"}},{t-0.08:.3f}).to("#{pid}",{{scale:0.6,y:{200 if LOW else -150},opacity:0,duration:0.3,ease:"power2.in"}},{t1-0.3:.3f});')
    snd("whoosh", t - 0.12, 0.22)
with open(f"{P}/kartinki.txt", "w") as fk:
    for img in KART: fk.write(("Брокер/Вставки/Предметы_ov/" + img[3:]) if img.startswith("ov/") else ("Брокер/Вставки/Предметы/" + img)); fk.write("\n")

# ---------- белая карточка-призыв ----------
if TOP_AFTER is not None and (TOP_AFTER > 0.05 or TOP_UNTIL < 1e8): AVAIL_MIX = min(AVAIL_B, int(spec.get("avail_px", 420)))
else: AVAIL_MIX = None
if CTA:
    set_top(CTA_T)
    lab, txt = sanitize(CTA.get("label") or ""), sanitize(CTA["text"])
    if lab[:1].islower():   # «Напишите «Монтаж»» + «в комментариях» — одна фраза, крупно, без кнопки
        lab, txt = (txt.rstrip(",") + (", " if txt.endswith(",") else " ") + lab), ""
    H.append(f'<div id="ap" class="apple fit" style="top:{TOP}px"><b class="{"sm" if len(lab) > 16 else ""}">{esc(lab)}</b>{f"<em>{esc(txt)}</em>" if txt else ""}</div>')
    tl(f'tl.from("#ap",{{y:120,scale:0.85,opacity:0,duration:0.55,ease:"back.out(1.6)"}},{CTA_T:.3f}){'.from("#ap em",{scale:0,duration:0.35,ease:"back.out(3)"},' + f'{CTA_T+0.45:.3f})' if txt else ''};')
    snd("ding", CTA_T + 0.4, 0.25)

# ---------- субтитры «микс» (overlay.py поверх рендера) ----------
mix = spec.get("mix_y") or [int(min(1640, max(1380, CHIN * 1920 + 110)))] * 4
json.dump({"keys": spec.get("keys", []), "mix_y": mix}, open(f"{P}/subs.json", "w"), ensure_ascii=False)

for i, (k, t, v) in enumerate(SND):
    H.append(f'<audio id="s{i}" src="snd/{k}.wav" data-start="{t:.3f}" data-duration="1.0" data-volume="{v}"></audio>')
if AVAIL_MIX: AVAIL = AVAIL_MIX
CSS = "".join(open(f"{B}/{x}").read() for x in ("znakomstvo.css", "fishki.css", "fishki2.css", "auto.css"))
open(f"{P}/index.html", "w").write(f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div id="root" data-composition-id="root" data-width="1080" data-height="1920" data-fps="30" data-motion-blur="on" data-motion-blur-shutter="200" data-start="0" data-duration="{DUR:.3f}">
{chr(10).join(H)}
</div><script src="gsap.min.js"></script><script>
/* всё, что сверху, ужимается, чтобы не залезть на голову (место {AVAIL} px) */
document.querySelectorAll(".fit").forEach(e=>{{const m=e.querySelectorAll("[data-m]");m.forEach(x=>x.style.display="flex");const h=e.offsetHeight;m.forEach(x=>x.style.display="none");const s=Math.min(1,{AVAIL}/Math.max(1,h));if(s<1){{e.style.scale=s;e.style.transformOrigin="50% 0";}}}});
const tl = gsap.timeline({{paused:true}});
{chr(10).join(J)}
tl.set({{}},{{}},{DUR:.3f});
window.__timelines = window.__timelines || {{}}; window.__timelines["root"] = tl;
</script></body></html>''')
json.dump({"dur": DUR, "head": round(HEAD), "top": TOP, "avail": AVAIL, "plates": len(clean), "kart": KART, "log": LOG}, open(f"{P}/build.json", "w"), ensure_ascii=False, indent=1)
print("ok", DUR, "с;", len(clean), "плашек;", len(KART), "картинок;", "\n".join(LOG))
