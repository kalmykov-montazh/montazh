# Проба HyperFrames 07.11.2026: ролик «ПУТЬ Давайте знакомиться».
# Читает words.json (тайминги слов готовой основы) и собирает hf/znakomstvo/index.html:
# основа во весь кадр + анимации GSAP (заставка, маршрут по годам, «меню» услуг, живые субтитры,
# рывки камеры на ключевых словах, концовка-чат) + тихие звуки-вжики.
import json, sys, html, re, os

D = os.path.dirname(os.path.abspath(__file__)) + "/znakomstvo"
W = json.load(open(sys.argv[1] if len(sys.argv) > 1 else D + "/words.json"))
FACE = json.load(open(D + "/face.json")) if os.path.exists(D + "/face.json") else {}
TOP = FACE.get("top", 190)       # верхняя зона плашек (над головой), px
SUB_Y = FACE.get("sub", 1470)    # центр субтитров (под подбородком), px
DUR = W[-1]["e"] + 0.35

def norm(s): return re.sub(r"[^\w-]", "", s.lower().replace("ё", "е"))
def at(phrase, after=0.0):
    """время начала фразы (первое совпадение после after)"""
    p = [norm(x) for x in phrase.split()]
    for i in range(len(W) - len(p) + 1):
        if W[i]["s"] < after: continue
        if all(norm(W[i + k]["w"]).startswith(p[k]) for k in range(len(p))):
            return W[i]["s"]
    raise SystemExit("не нашёл: " + phrase)
def end_of(phrase, after=0.0):
    p = phrase.split(); t = at(phrase, after)
    i = next(i for i, w in enumerate(W) if w["s"] == t)
    return W[i + len(p) - 1]["e"]

T = {}
T["name"] = at("Меня зовут")
T["val"] = at("Валенсии")
T["sud"] = at("Так сложилась")
T["y14"] = at("2014"); T["lug"] = at("Луганска"); T["kh"] = at("Харькове")
T["y22"] = at("2022"); T["y25"] = at("2025"); T["third"] = at("третий")
T["och"] = at("очереди"); T["doc"] = at("документы", T["och"] - 0.1); T["yaz"] = at("язык"); T["sam"] = at("прошёл сам")
T["q"] = at("С чем ко мне")
MENU = [
    ("Жильё", "снять или сдать квартиру", at("Жильё")),
    ("Управление", "квартиру ведут за вас", at("Хотите сдавать")),
    ("Ипотека", "специалист по ипотеке", at("ипотека")),
    ("Мебель и кухни", "мастер, на заказ", at("мебель")),
    ("Недвижимость ОАЭ", "партнёр напрямую", at("Недвижимость в Эмиратах")),
    ("Юристы и налоги", "ВНЖ · арайго · переводы", at("Документы и налоги")),
    ("Сита", "запись, когда не поймать", at("ситу")),
    ("Машина", "учёт · растаможка · ITV · права", at("машина")),
    ("Путешествия", "отели не по цене витрины", at("путешествия")),
]
T["cta"] = at("По всему остальному")
T["vopros"] = at("вопрос", T["cta"])
T["pom"] = at("Не помогу сам")
PUNCH = [at("3 раза"), T["y14"], T["y22"], T["third"], T["vopros"]]

# ---------- субтитры: фразы по 2–4 слова, без разрыва на паузах ----------
groups, cur = [], []
for w in W:
    if cur and (w["w"][:1].isupper() and len(cur) >= 2 or len(cur) >= 4 or w["s"] - cur[-1]["e"] > 0.35 or len("".join(x["w"] for x in cur)) > 18):
        groups.append(cur); cur = []
    cur.append(w)
    if re.search(r"[.?!:,]$", w["w"]) and len(cur) >= 2: groups.append(cur); cur = []
if cur: groups.append(cur)
ACC = {norm(x) for x in "10 3 2014 2022 2025 третий сам жилье ипотека мебель эмиратах юристов ситу машина путешествия вопрос нуля".split()}

H, J, SND = [], [], []
def tl(s): J.append(s)
def snd(kind, t, vol=0.35): SND.append((kind, round(t, 3), vol))

# 0. обложка на первом кадре (TikTok берёт кадр 0)
H.append('<img id="cover" class="full" src="img/обложка.jpg">')
tl('tl.set("#cover",{opacity:1},0).set("#cover",{opacity:0},0.12);')

# основа
H.append(f'<div id="cam" class="full"><video id="v" class="full" src="osnova.mp4" data-start="0" data-duration="{DUR:.3f}" data-has-audio="true"></video></div>')
for t in PUNCH:
    tl(f'tl.fromTo("#cam",{{scale:1.13}},{{scale:1,duration:0.7,ease:"power3.out",immediateRender:false}},{t-0.03:.3f});')
    snd("whoosh", t - 0.12, 0.25)
# лёгкое «дыхание» камеры, без качания влево-вправо
tl(f'tl.to("#v",{{scale:1.06,duration:{DUR/2:.2f},ease:"sine.inOut",yoyo:true,repeat:1}},0);')

# 1. заставка: «Давайте знакомиться» + три фишки
H.append(f'''<div id="title" class="zone" style="top:{TOP}px">
 <div class="stamp"><span>ДАВАЙТЕ</span> <span>ЗНАКОМИТЬСЯ</span></div>
 <div class="chips"><b id="c1">10 лет в банке</b><b id="c2">свой бизнес</b><b id="c3" class="red">3 раза с нуля</b></div></div>''')
tl('tl.from("#title .stamp span",{y:-120,opacity:0,rotation:-6,stagger:0.12,duration:0.45,ease:"back.out(2)"},0.12);')
for cid, w in (("c1", "банке"), ("c2", "бизнес"), ("c3", "нуля")):
    t = at(w); tl(f'tl.from("#{cid}",{{scale:0,opacity:0,duration:0.35,ease:"back.out(3)"}},{t-0.1:.3f});'); snd("pop", t - 0.1, 0.3)
tl(f'tl.to("#title",{{y:-60,opacity:0,duration:0.3}},{T["name"]-0.05:.3f});')

# 2. именная плашка + пин Валенсии
H.append(f'''<div id="name" class="lower"><div class="bar"></div><div><div class="nm">Евгений Калмыков</div><div class="nl"><i class="pin"></i>Валенсия · с июля 2025</div></div></div>''')
tl(f'tl.from("#name",{{x:-700,duration:0.5,ease:"power4.out"}},{T["name"]:.3f}).from("#name .bar",{{scaleY:0,duration:0.3}},{T["name"]+0.15:.3f});')
tl(f'tl.to("#name",{{x:-700,duration:0.35,ease:"power2.in"}},{T["sud"]-0.3:.3f});'); snd("whoosh", T["name"] - 0.1, 0.25)
H.append(f'<div id="ph1" class="photo" style="top:{TOP+20}px;right:60px"><img src="img/city2_5.jpg"><span>Валенсия</span></div>')
tl(f'tl.from("#ph1",{{scale:0.2,rotation:12,opacity:0,duration:0.45,ease:"back.out(2)"}},{T["val"]-0.05:.3f}).to("#ph1",{{scale:0.3,opacity:0,duration:0.3}},{T["sud"]-0.2:.3f});')

H.append(f'<div id="ph2" class="photo" style="top:{TOP+430}px;left:40px;transform:rotate(-5deg)"><img src="img/kharkiv_1.jpg"><span>Харьков</span></div>')
tl(f'tl.from("#ph2",{{scale:0.2,rotation:-15,opacity:0,duration:0.45,ease:"back.out(2)"}},{T["kh"]-0.05:.3f}).to("#ph2",{{scale:0.3,opacity:0,duration:0.3}},{T["y22"]-0.2:.3f});')
# 3. маршрут: Луганск → Харьков → Валенсия, линия рисуется, годы щёлкают
H.append(f'''<div id="route" class="zone" style="top:{TOP}px"><div class="rt-h">ТРИ РАЗА С НУЛЯ</div>
<svg viewBox="0 0 960 300" width="960" height="300"><path id="rp" d="M80 210 C 250 60, 330 60, 470 150 S 760 260, 880 110" fill="none" stroke="#ffd23f" stroke-width="14" stroke-linecap="round" stroke-dasharray="8 22"/></svg>
<div class="pt" id="p1" style="left:40px;top:235px"><i></i><u>2014</u><s>Луганск</s></div>
<div class="pt" id="p2" style="left:420px;top:175px"><i></i><u class="r">2022</u><s>Харьков</s></div>
<div class="pt" id="p3" style="left:820px;top:135px"><i></i><u>2025</u><s>Валенсия</s></div>
<div id="nth" class="nth">3-й<br>раз</div></div>''')
tl(f'tl.from("#route",{{opacity:0,y:-40,duration:0.35}},{T["y14"]-0.25:.3f});')
tl(f'tl.fromTo("#rp",{{strokeDashoffset:0,clipPath:"inset(0 100% 0 0)"}},{{clipPath:"inset(0 55% 0 0)",duration:{T["kh"]-T["y14"]:.2f},ease:"none"}},{T["y14"]:.3f});')
tl(f'tl.to("#rp",{{clipPath:"inset(0 0% 0 0)",duration:{T["y25"]-T["y22"]+0.6:.2f},ease:"none"}},{T["y22"]:.3f});')
for pid, t in (("p1", T["y14"]), ("p2", T["y22"]), ("p3", T["y25"])):
    tl(f'tl.from("#{pid}",{{scale:0,opacity:0,duration:0.4,ease:"back.out(3)"}},{t-0.08:.3f});'); snd("click", t - 0.05, 0.4)
tl(f'')
tl(f'tl.fromTo("#flash",{{opacity:0.55}},{{opacity:0,duration:0.5,immediateRender:false}},{T["y22"]:.3f});')
tl(f'tl.from("#nth",{{scale:3,opacity:0,rotation:-20,duration:0.45,ease:"expo.out"}},{T["third"]-0.05:.3f});'); snd("boom", T["third"] - 0.05, 0.3)
tl(f'tl.to("#route",{{opacity:0,y:-40,duration:0.3}},{T["och"]-0.25:.3f});')
H.append('<div id="flash" class="full" style="background:#e63946;opacity:0"></div>')

# 4. очереди · документы · язык — галочки
H.append(f'''<div id="sam" class="zone" style="top:{TOP+30}px"><div class="ck" id="k1"><i></i>очереди</div><div class="ck" id="k2"><i></i>документы</div><div class="ck" id="k3"><i></i>чужой язык</div></div>''')
for kid, t in (("k1", T["och"]), ("k2", T["doc"]), ("k3", T["yaz"])):
    tl(f'tl.from("#{kid}",{{x:-80,opacity:0,duration:0.3,ease:"power3.out"}},{t-0.08:.3f}).to("#{kid} i",{{scale:1,duration:0.25,ease:"back.out(3)"}},{T["sam"]:.3f});')
    snd("click", t - 0.05, 0.3)
tl(f'tl.to("#sam",{{opacity:0,y:-40,duration:0.3}},{T["q"]-0.15:.3f});')

# 5. «С чем можно обратиться» + меню услуг, карточка за карточкой
H.append(f'''<div id="menu" class="zone" style="top:{TOP-20}px"><div class="mh">С ЧЕМ МОЖНО ОБРАТИТЬСЯ</div><div class="dots">{"".join(f'<i id="d{i}"></i>' for i in range(len(MENU)))}</div><div class="cards">''' +
         "".join(f'<div class="card" id="m{i}"><em>{i+1:02d}</em><div><b>{html.escape(a)}</b><small>{html.escape(b)}</small></div></div>' for i, (a, b, _) in enumerate(MENU)) +
         '</div></div>')
tl(f'tl.from("#menu .mh",{{scaleX:0,transformOrigin:"left center",duration:0.4,ease:"power4.out"}},{T["q"]-0.05:.3f}).from("#menu .dots",{{opacity:0,duration:0.3}},{T["q"]+0.3:.3f});')
snd("whoosh", T["q"] - 0.1, 0.25)
for i, (_, _, t) in enumerate(MENU):
    tl(f'tl.fromTo("#m{i}",{{x:900,opacity:0}},{{x:0,opacity:1,duration:0.45,ease:"power4.out",immediateRender:false}},{t-0.12:.3f}).to("#d{i}",{{backgroundColor:"#ffd23f",scale:1.4,duration:0.2}},{t-0.1:.3f});')
    if i + 1 < len(MENU):
        tl(f'tl.to("#m{i}",{{x:-900,opacity:0,duration:0.35,ease:"power2.in"}},{MENU[i+1][2]-0.3:.3f});')
    snd("whoosh", t - 0.15, 0.2)
tl(f'tl.to("#menu",{{opacity:0,y:-40,duration:0.3}},{T["cta"]-0.2:.3f});')

# 6. концовка: чат «Напишите в личку» + «Какой у вас вопрос?»
H.append(f'''<div id="chat" class="zone" style="top:{TOP}px"><div class="bub">Напишите в личку<span class="ty"><i></i><i></i><i></i></span></div><div class="ask">Какой у вас вопрос?</div><div class="help">не помогу сам — подскажу, к кому</div></div>''')
tl(f'tl.from("#chat .bub",{{y:80,scale:0.6,opacity:0,duration:0.45,ease:"back.out(2)"}},{T["cta"]+0.6:.3f});')
tl(f'tl.to("#chat .ty i",{{y:-12,duration:0.25,stagger:0.1,yoyo:true,repeat:9}},{T["cta"]+1.0:.3f});')
tl(f'tl.from("#chat .ask",{{scale:2.5,opacity:0,duration:0.4,ease:"expo.out"}},{T["vopros"]-0.15:.3f});'); snd("ding", T["vopros"] - 0.1, 0.25)
tl(f'tl.from("#chat .help",{{opacity:0,y:30,duration:0.35}},{T["pom"]:.3f});')

# 7. живые субтитры: слово подсвечивается, ключевые — в цветной плашке
SH = []
for gi, g in enumerate(groups):
    gs, ge = g[0]["s"], (groups[gi + 1][0]["s"] if gi + 1 < len(groups) else DUR)
    ge = min(ge - 0.04, g[-1]["e"] + 0.6)
    spans = []
    for wi, w in enumerate(g):
        cls = "acc" if norm(w["w"]) in ACC else ""
        spans.append(f'<span id="w{gi}_{wi}" class="{cls}">{html.escape(w["w"])}</span>')
    SH.append(f'<div class="sg" id="g{gi}">{" ".join(spans)}</div>')
    tl(f'tl.set("#g{gi}",{{opacity:1}},{gs-0.02:.3f}).from("#g{gi}",{{y:30,scale:0.85,duration:0.18,ease:"back.out(2)"}},{gs-0.02:.3f}).set("#g{gi}",{{opacity:0}},{ge:.3f});')
    for wi, w in enumerate(g):
        tl(f'tl.set("#w{gi}_{wi}",{{attr:{{class:"{("acc on" if norm(w["w"]) in ACC else "on")}"}}}},{w["s"]:.3f});')
H.append(f'<div id="subs" style="top:{SUB_Y}px">' + "".join(SH) + "</div>")

# звуки
os.makedirs(D + "/snd", exist_ok=True)
for i, (k, t, v) in enumerate(SND):
    H.append(f'<audio id="s{i}" src="snd/{k}.wav" data-start="{max(0,t):.3f}" data-duration="1.0" data-volume="{v}"></audio>')

CSS = open(os.path.dirname(os.path.abspath(__file__)) + "/znakomstvo.css").read()
page = f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div id="root" data-composition-id="root" data-width="1080" data-height="1920" data-fps="30" data-start="0" data-duration="{DUR:.3f}">
{chr(10).join(H)}
</div>
<script src="gsap.min.js"></script>
<script>
const tl = gsap.timeline({{paused:true}});
{chr(10).join(J)}
tl.set({{}},{{}},{DUR:.3f});
window.__timelines = window.__timelines || {{}}; window.__timelines["root"] = tl;
</script></body></html>'''
open(D + "/index.html", "w").write(page)
print("ok", round(DUR, 2), "с;", len(groups), "фраз субтитров;", len(SND), "звуков; T:", {k: round(v, 1) for k, v in T.items()})
