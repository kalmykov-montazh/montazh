# Проба фишек 07.11.2026 (разбор ролика «Claude-директор кофейного аппарата»):
# огромная надпись, окно-«рабочий стол», документ с маркером, счётчик с кольцом, белая карточка Apple.
# Ролик «НЕДВ Налог за пустую квартиру». Субтитры-караоке как в «Давайте знакомиться».
import json, html, re, os
D = os.path.dirname(os.path.abspath(__file__)) + "/pustaya"
W = json.load(open(D + "/words.json"))
TOP, SUB_Y = 230, 1470
DUR = W[-1]["e"] + 0.4
def norm(s): return re.sub(r"[^\w%-]", "", s.lower().replace("ё", "е"))
def at(ph, after=0.0):
    p = [norm(x) for x in ph.split()]
    for i in range(len(W) - len(p) + 1):
        if W[i]["s"] < after: continue
        if all(norm(W[i+k]["w"]).startswith(p[k]) for k in range(len(p))): return W[i]["s"]
    raise SystemExit("не нашёл: " + ph)
H, J, SND = [], [], []
tl = J.append
def snd(k, t, v=0.3): SND.append((k, round(t, 3), v))
def show(sel, t0, t1, frm='{y:-60,opacity:0,scale:0.9}', ease="back.out(1.8)"):
    tl(f'tl.from("{sel}",{{...{frm},duration:0.45,ease:"{ease}"}},{t0:.3f}).to("{sel}",{{opacity:0,y:-50,duration:0.3,ease:"power2.in"}},{t1-0.3:.3f});')

H.append('<img id="cover" class="full" src="img/обложка.jpg">')
tl('tl.set("#cover",{opacity:1},0).set("#cover",{opacity:0},0.12);')
H.append(f'<div id="cam" class="full"><video id="v" class="full" src="osnova.mp4" data-start="0" data-duration="{DUR:.3f}" data-has-audio="true"></video></div>')
for t in (at("пустая"), at("260"), at("2027")):
    tl(f'tl.fromTo("#cam",{{scale:1.13}},{{scale:1,duration:0.7,ease:"power3.out",immediateRender:false}},{t-0.03:.3f});'); snd("whoosh", t-0.12, 0.25)
H.append('<div id="flash" class="full" style="background:#fff;opacity:0;z-index:15"></div>')

# 1. ОГРОМНАЯ НАДПИСЬ: «ПУСТАЯ» + «а налог платите»
H.append(f'<div id="g1" class="giant" style="top:{TOP}px">ПУСТАЯ<small>А НАЛОГ ПЛАТИТЕ</small></div>')
tl(f'tl.from("#g1",{{scale:2.6,opacity:0,filter:"blur(18px)",duration:0.55,ease:"expo.out"}},{at("пустая")-0.1:.3f}).from("#g1 small",{{y:40,opacity:0,duration:0.35}},{at("налог")-0.1:.3f}).to("#g1",{{scale:0.7,opacity:0,duration:0.35}},{at("В Испании")-0.15:.3f});')
snd("boom", at("пустая")-0.1, 0.3)

# 2. ДОКУМЕНТ С МАРКЕРОМ: как считает налоговая
t0, t1 = at("Налоговая"), at("Касается")
H.append(f'<div id="d1" class="doc" style="top:{TOP+10}px"><h4>Налоговая считает так:</h4><p><span>квартира у вас есть</span></p><p class="hl" id="d1h"><span>значит, могла бы приносить деньги</span></p></div>')
show("#d1", t0-0.1, t1, '{x:-900,opacity:0,rotation:-8}', "power4.out")
tl(f'tl.fromTo("#d1h",{{"--m":0}},{{"--m":1,duration:0.6,ease:"power2.out",immediateRender:false}},{at("приносить")-0.05:.3f});'); snd("click", at("приносить"), 0.3)

# 3. ОКНО «рабочего стола»: квитанция IBI
t0, t1 = at("Считают от"), at("Обычно около")
H.append(f'<div id="w1" class="win" style="top:{TOP}px"><div class="bar"><i></i><i></i><i></i><b>Квитанция IBI · кадастровая стоимость</b></div><img src="img/receipt_1.jpg" style="height:520px"></div>')
tl(f'tl.from("#w1",{{scale:0.4,y:300,opacity:0,duration:0.5,ease:"back.out(1.6)"}},{t0-0.1:.3f}).to("#w1",{{scale:0.5,y:-200,opacity:0,duration:0.35,ease:"power2.in"}},{t1-0.35:.3f});'); snd("whoosh", t0-0.15, 0.25)

# 4. КОЛЬЦО: 1,1% → 2%
t0, tB, t1 = at("Обычно это"), at("2%"), at("Пример")
C = 2*3.14159*104
H.append(f'''<div id="m1" class="meter" style="top:{TOP+20}px"><svg width="260" height="260"><circle class="rg" cx="130" cy="130" r="104"/><circle id="m1r" class="rv" cx="130" cy="130" r="104" stroke-dasharray="{C:.1f}" stroke-dashoffset="{C:.1f}"/></svg>
<div><div class="num" id="m1n">1,1%</div><div class="lab" id="m1l">в год от кадастровой</div></div></div>''')
show("#m1", t0-0.1, t1, '{x:900,opacity:0}', "power4.out")
tl(f'tl.to("#m1r",{{strokeDashoffset:{C*(1-0.45):.1f},duration:0.8,ease:"power2.out"}},{at("1,1%",t0)-0.05:.3f});')
tl(f'tl.to("#m1r",{{strokeDashoffset:{C*(1-0.8):.1f},stroke:"#e63946",duration:0.6,ease:"power2.out"}},{tB-0.05:.3f}).set("#m1n",{{textContent:"2%"}},{tB:.3f}).set("#m1l",{{textContent:"в некоторых городах"}},{tB:.3f});')
snd("pop", tB-0.05, 0.3)

# 5. СЧЁТЧИК: 80 000 € → 880 € → 260 € в год
t0, t1 = at("Кадастровая"), at("Нерезидентам")
H.append(f'''<div id="m2" class="meter" style="top:{TOP+20}px;display:block;text-align:center"><div class="lab" id="m2l">кадастровая стоимость</div><div class="num" id="m2n">0 €</div><div class="delta" id="m2d" style="opacity:0">за закрытую квартиру</div></div>''')
show("#m2", t0-0.1, t1, '{y:-200,opacity:0}', "power4.out")
J.append(f'const cnt=(o,to,t,lab,sfx)=>{{tl.to(o,{{v:to,duration:0.9,ease:"power2.out",onUpdate:()=>{{document.querySelector("#m2n").textContent=Math.round(o.v).toLocaleString("ru-RU")+" €"+(sfx||"")}}}},t);tl.set("#m2l",{{textContent:lab}},t);}};const o2={{v:0}};')
tl(f'cnt(o2,80000,{at("80")-0.05:.3f},"кадастровая стоимость");')
tl(f'cnt(o2,880,{at("Вменённый",t0)-0.05:.3f},"вменённый доход");')
tl(f'cnt(o2,260,{at("260")-0.05:.3f},"налог в год");tl.to("#m2d",{{opacity:1,scale:1.1,duration:0.3,ease:"back.out(3)"}},{at("закрытой")-0.1:.3f});')
for w in ("80", "Вменённый", "260"): snd("click", at(w, t0)-0.05, 0.3)

# 6. ОГРОМНЫЕ 19% / 24%
for gid, w, lab, nxt in (("g2", "19%", "ГРАЖДАНЕ ЕС", "и 24%"), ("g3", "24%", "ВСЕ ОСТАЛЬНЫЕ", "Осенью")):
    t0 = at(w); t1 = at(nxt.split()[-1] if nxt != "Осенью" else "Осенью", t0)
    H.append(f'<div id="{gid}" class="giant" style="top:{TOP}px">{w}<small>НЕРЕЗИДЕНТЫ · {lab}</small></div>')
    tl(f'tl.from("#{gid}",{{scale:2.4,opacity:0,filter:"blur(16px)",duration:0.45,ease:"expo.out"}},{t0-0.1:.3f}).to("#{gid}",{{opacity:0,duration:0.25}},{t1-0.25:.3f});'); snd("pop", t0-0.1, 0.3)

# 7. ОГРОМНАЯ «2027» со вспышкой
t0, t1 = at("2027"), at("Заодно")
H.append(f'<div id="g4" class="giant" style="top:{TOP}px;color:#ffd23f">2027<small style="color:#fff">НОВЫЕ ПРАВИЛА</small></div>')
tl(f'tl.fromTo("#flash",{{opacity:0.7}},{{opacity:0,duration:0.45,immediateRender:false}},{t0-0.05:.3f}).from("#g4",{{scale:3,opacity:0,duration:0.5,ease:"expo.out"}},{t0-0.05:.3f}).to("#g4",{{y:-80,opacity:0,duration:0.3}},{t1-0.3:.3f});'); snd("boom", t0-0.05, 0.3)

# 8. БЕЛАЯ КАРТОЧКА Apple — призыв
t0 = at("Контакты")
H.append(f'<div id="ap" class="apple" style="top:{TOP+10}px"><b>Юристы<br>по налогам</b><span>контакты проверенных — у меня</span><em>Пишите в личку</em></div>')
tl(f'tl.from("#ap",{{y:120,scale:0.85,opacity:0,duration:0.55,ease:"back.out(1.6)"}},{t0-0.1:.3f}).from("#ap em",{{scale:0,duration:0.35,ease:"back.out(3)"}},{at("Пишите")-0.1:.3f});'); snd("ding", at("Пишите")-0.1, 0.25)

# субтитры-караоке
groups, cur = [], []
for w in W:
    if cur and (w["w"][:1].isupper() and len(cur) >= 2 or len(cur) >= 4 or w["s"]-cur[-1]["e"] > 0.35 or len("".join(x["w"] for x in cur)) > 18):
        groups.append(cur); cur = []
    cur.append(w)
    if re.search(r"[.?!:,]$", w["w"]) and len(cur) >= 2: groups.append(cur); cur = []
if cur: groups.append(cur)
ACC = {norm(x) for x in "пустая налог 1,1% 2% 80 880 260 19% 24% 2027 юристов личку".split()}
SH = []
for gi, g in enumerate(groups):
    gs = g[0]["s"]; ge = min((groups[gi+1][0]["s"] if gi+1 < len(groups) else DUR)-0.04, g[-1]["e"]+0.6)
    SH.append('<div class="sg" id="g%d">' % gi + " ".join(f'<span id="w{gi}_{wi}" class="{"acc" if norm(w["w"]) in ACC else ""}">{html.escape(w["w"])}</span>' for wi, w in enumerate(g)) + "</div>")
    tl(f'tl.set("#g{gi}",{{opacity:1}},{gs-0.02:.3f}).from("#g{gi}",{{y:30,scale:0.85,duration:0.18,ease:"back.out(2)"}},{gs-0.02:.3f}).set("#g{gi}",{{opacity:0}},{ge:.3f});')
    for wi, w in enumerate(g):
        tl(f'tl.set("#w{gi}_{wi}",{{attr:{{class:"{"acc on" if norm(w["w"]) in ACC else "on"}"}}}},{w["s"]:.3f});')
H.append(f'<div id="subs" style="top:{SUB_Y}px">' + "".join(SH) + "</div>")
for i, (k, t, v) in enumerate(SND):
    H.append(f'<audio id="s{i}" src="snd/{k}.wav" data-start="{max(0,t):.3f}" data-duration="1.0" data-volume="{v}"></audio>')
B = os.path.dirname(os.path.abspath(__file__))
CSS = open(B + "/znakomstvo.css").read() + open(B + "/fishki.css").read()
open(D + "/index.html", "w").write(f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div id="root" data-composition-id="root" data-width="1080" data-height="1920" data-fps="30" data-start="0" data-duration="{DUR:.3f}">
{chr(10).join(H)}
</div><script src="gsap.min.js"></script><script>
const tl = gsap.timeline({{paused:true}});
{chr(10).join(J)}
tl.set({{}},{{}},{DUR:.3f});
window.__timelines = window.__timelines || {{}}; window.__timelines["root"] = tl;
</script></body></html>''')
print("ok", round(DUR, 1), "с,", len(groups), "фраз,", len(SND), "звуков")
