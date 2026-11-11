import re, shutil, os
src = open('/tmp/claude-0/var/index.html', encoding='utf-8').read()

# 1. Тёплая средиземноморская палитра
src = src.replace('''  --bg:#f4f3f0; --surface:#ffffff; --fg:#1c2530; --muted:#66707a; --line:#e2e0db;
  --ink:#1f3347; --accent:#d9691a; --accent-ink:#ffffff;''', '''  --bg:#f6efe3; --surface:#fffaf3; --fg:#22313a; --muted:#6d6a63; --line:#eadcc6;
  --ink:#0f4c6e; --sea:#0f5a80; --accent:#c4552f; --accent-ink:#ffffff; --sun:#f2b544;''')
src = src.replace('''  --bg:#12171d; --surface:#1a2129; --fg:#eef1f4; --muted:#9aa4ae; --line:#2a333d;
  --ink:#0d1a26; --accent:#f08a3e; --accent-ink:#1c2530; color-scheme:dark}}''', '''  --bg:#14191d; --surface:#1d2429; --fg:#f1ede6; --muted:#a8a296; --line:#2f3840;
  --ink:#0d1a26; --sea:#6cb7dd; --accent:#e27350; --accent-ink:#ffffff; --sun:#f2b544; color-scheme:dark}}''')
src = src.replace('''  --bg:#12171d; --surface:#1a2129; --fg:#eef1f4; --muted:#9aa4ae; --line:#2a333d;
  --ink:#0d1a26; --accent:#f08a3e; --accent-ink:#1c2530; color-scheme:dark}''', '''  --bg:#14191d; --surface:#1d2429; --fg:#f1ede6; --muted:#a8a296; --line:#2f3840;
  --ink:#0d1a26; --sea:#6cb7dd; --accent:#e27350; --accent-ink:#ffffff; --sun:#f2b544; color-scheme:dark}''')

extra_css = '''
/* ===== Новое 11.11: цвета, чек-лист, обо мне, вопросы, значки услуг ===== */
h1,h2{color:var(--sea)}
.consult h2{color:var(--fg)}
.checklist{display:flex;gap:18px;align-items:center;padding:20px 22px;border-radius:18px;
  background:linear-gradient(120deg,#0f5a80,#1683a8);color:#fff;box-shadow:0 10px 30px rgba(15,90,128,.25)}
.checklist .doc{flex:none;width:64px;height:76px;border-radius:10px;background:#fff;display:grid;place-items:center;
  box-shadow:0 6px 14px rgba(0,0,0,.18);transform:rotate(-6deg)}
.checklist .doc svg{width:36px;height:36px;fill:#0f5a80}
.checklist .tx{flex:1;min-width:0}
.checklist .free{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  background:var(--sun);color:#3a2a00;border-radius:999px;padding:3px 10px;margin-bottom:6px}
.checklist h2{color:#fff;margin:0 0 4px;font-size:21px}
.checklist p{margin:0;opacity:.92;font-size:15px}
.checklist .get{flex:none;display:inline-flex;align-items:center;gap:8px;background:var(--sun);color:#2b1f00;font-weight:700;
  font-size:16px;text-decoration:none;border-radius:12px;padding:14px 20px;box-shadow:0 4px 0 #c98f1c}
.checklist .get:hover{filter:brightness(1.05)}
.checklist .get svg{width:18px;height:18px;fill:currentColor}
.about{display:grid;grid-template-columns:auto 1fr;gap:20px;align-items:center;padding:22px;border-radius:18px;background:var(--surface);border:1px solid var(--line)}
.about img{width:92px;height:92px;border-radius:50%;object-fit:cover}
.about h2{margin:0 0 6px}
.about p{margin:0;color:var(--fg);line-height:1.55}
.faq{display:flex;flex-direction:column;gap:8px}
.faq details{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.faq summary{cursor:pointer;font-weight:700;list-style:none;display:flex;justify-content:space-between;gap:12px}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";color:var(--accent);font-size:20px;line-height:1}
.faq details[open] summary::after{content:"–"}
.faq details p{margin:10px 0 0;color:var(--muted)}
.card .ci{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:color-mix(in srgb,var(--t) 14%,var(--surface));color:var(--t);margin-bottom:2px}
.card .ci svg{width:19px;height:19px;fill:currentColor}
.reveal{opacity:0;transform:translateY(14px);transition:opacity .5s ease,transform .5s ease}
.reveal.on{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none;transition:none}}
/* вариант Б: деловая шапка без картинки */
.hero-b{display:flex;gap:22px;align-items:center;padding:24px;border-radius:20px;background:var(--surface);border:1px solid var(--line)}
.hero-b img{width:120px;height:120px;border-radius:50%;object-fit:cover;flex:none}
.hero-b .t{flex:1;min-width:0}
.hero-b h1{margin:0}
.hero-b p{margin:6px 0 14px;color:var(--muted)}
.hero-b .btns{display:flex;flex-wrap:wrap;gap:10px}
.hero-b .btns a{display:inline-flex;align-items:center;gap:8px;font-weight:700;text-decoration:none;border-radius:12px;padding:11px 16px;font-size:15px}
.hero-b .b1{background:var(--accent);color:#fff}
.hero-b .b2{background:var(--sun);color:#2b1f00}
/* вариант В: узкая полоска моря */
.v-c .cover{aspect-ratio:1600/230}
.v-c .cover img{object-position:center 66%}
.v-c .profile{margin-top:-58px}
@media (max-width:600px){
  .checklist{flex-direction:column;align-items:flex-start;padding:18px;gap:12px}
  .checklist .doc{display:none}
  .checklist .get{align-self:stretch;justify-content:center}
  .about{grid-template-columns:1fr;text-align:left}
  .about img{display:none}
  .hero-b{flex-direction:column;align-items:flex-start;padding:18px}
  .hero-b img{width:88px;height:88px}
  .hero-b .btns a{flex:1 1 100%;justify-content:center}
  .v-c .cover{aspect-ratio:1600/330}
  .v-c .profile{margin-top:-30px}
  .checklist h2{font-size:18px}
  .checklist p{font-size:14px}
}
footer{'''
src = src.replace('\nfooter{', extra_css, 1)

# 2. Блок чек-листа сразу под соцсетями
checklist = '''  <nav class="socials" aria-label="Соцсети" id="socials"></nav>

  <section class="checklist reveal" aria-labelledby="h-check">
    <div class="doc"><svg viewBox="0 0 24 24"><path d="M9 11.2 7.6 9.8 6.2 11.2 9 14l6-6-1.4-1.4L9 11.2ZM6 2h9l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm0 14v2h12v-2H6Z"/></svg></div>
    <div class="tx">
      <span class="free">Бесплатно</span>
      <h2 id="h-check">Чек-лист: 10 пунктов проверить до подписи договора аренды</h2>
      <p>Что проверить у хозяина, в договоре и с залогом, чтобы потом не было проблем</p>
    </div>
    <a class="get" id="checkgo" target="_blank" rel="noopener">Получить чек-лист</a>
  </section>'''
src = src.replace('  <nav class="socials" aria-label="Соцсети" id="socials"></nav>', checklist, 1)

# 3. Обо мне + вопросы перед «Скоро»
about = '''  <section class="about reveal" aria-labelledby="h-about">
    <img src="photo.jpeg" alt="">
    <div>
      <h2 id="h-about">Коротко обо мне</h2>
      <p>Живу в Валенсии с июля 2025 года. Сам прошёл переезд, поиск жилья и документы, работаю с арендой. На сообщения отвечаю сам, без менеджеров. Чего не знаю — подскажу, к кому обратиться</p>
    </div>
  </section>

  <section class="head" aria-labelledby="h-faq"><h2 id="h-faq">Частые вопросы</h2></section>
  <div class="faq reveal">
    <details><summary>Вы юрист?</summary><p>Нет. Я разбираю договор и помогаю решить ситуацию без суда. Если дело всё же идёт в суд — даю контакты проверенных юристов</p></details>
    <details><summary>Работаете только в Валенсии?</summary><p>Консультации — онлайн, по всей Испании. Присылаете договор в WhatsApp, я отвечаю письменно</p></details>
    <details><summary>Договор на испанском — разберёте?</summary><p>Да. Почти все договоры здесь на испанском — объясню по-русски, что в нём написано и на что смотреть</p></details>
    <details><summary>Как быстро отвечаете?</summary><p>Обычно в тот же день. Если срочно — так и напишите</p></details>
    <details><summary>Сколько стоит?</summary><p>Разбор договора письменно — 50 €. Сопровождение до решения — от 100 €. Чек-лист — бесплатно</p></details>
  </div>

  <section class="head" aria-labelledby="h-soon">'''
src = src.replace('  <section class="head" aria-labelledby="h-soon">', about, 1)

# 4. Значки у карточек услуг
icons_js = '''const GI={
  doc:'<svg viewBox="0 0 24 24"><path d="M6 2h9l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm8 1.5V8h4.5L14 3.5ZM7 12v2h10v-2H7Zm0 4v2h7v-2H7Z"/></svg>',
  money:'<svg viewBox="0 0 24 24"><path d="M3 6h18v12H3V6Zm9 3a3 3 0 1 0 0 6 3 3 0 0 0 0-6ZM5 8v2a2 2 0 0 0 2-2H5Zm12 0a2 2 0 0 0 2 2V8h-2ZM5 14v2h2a2 2 0 0 0-2-2Zm14 0a2 2 0 0 0-2 2h2v-2Z"/></svg>',
  home:'<svg viewBox="0 0 24 24"><path d="M12 3 2 11.5h3V21h5.5v-6h3v6H19v-9.5h3L12 3Z"/></svg>',
  house:'<svg viewBox="0 0 24 24"><path d="M22 7.5 16.5 2l-2 2 1.3 1.3-7.6 7.6L6.9 11.6l-2 2 1.4 1.4L2 19.3 4.7 22 9 17.7l1.4 1.4 2-2-1.3-1.3 7.6-7.6 1.3 1.3 2-2Z"/></svg>',
  more:'<svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm1 15h-2v-2h2v2Zm2.1-7.7-.9.9c-.7.7-1.2 1.3-1.2 2.8h-2v-.5c0-1.1.5-2.1 1.2-2.8l1.2-1.3c.4-.4.6-.9.6-1.4a2 2 0 0 0-4 0H8a4 4 0 0 1 8 0c0 .9-.4 1.7-.9 2.3Z"/></svg>'
};
const grid='''
src = src.replace('const grid=', icons_js, 1)
src = src.replace('el.innerHTML=`<i class="tag">', 'el.innerHTML=`<span class="ci">${GI[g]}</span><i class="tag">', 1)

# 5. Кнопка чек-листа и плавное появление
src = src.replace('\nconst sk=', '''
const ck=document.getElementById("checkgo");
ck.href="https://wa.me/34624916605?text="+encodeURIComponent("Здравствуйте! Пришлите, пожалуйста, бесплатный чек-лист по договору аренды");
ck.insertAdjacentHTML("afterbegin",ICON.wa);
document.querySelectorAll(".consult,.grid,.soon,.partners").forEach(e=>e.classList.add("reveal"));
try{const io=new IntersectionObserver(es=>es.forEach(x=>{if(x.isIntersecting){x.target.classList.add("on");io.unobserve(x.target)}}),{threshold:.08});
document.querySelectorAll(".reveal").forEach(e=>io.observe(e));}catch(e){document.querySelectorAll(".reveal").forEach(x=>x.classList.add("on"))}
const sk=''', 1)

header_a = re.search(r'  <div>\n    <div class="cover">.*?\n  </div>\n', src, re.S).group(0)
header_b = '''  <section class="hero-b">
    <img src="photo.jpeg" alt="Евгений Калмыков">
    <div class="t">
      <h1>Евгений Калмыков</h1>
      <p>Валенсия. Помогаю с арендой, договорами и переездом в Испанию</p>
      <div class="btns"><a class="b1" href="#h-consult">Разобрать мой договор</a><a class="b2" href="#h-check">Бесплатный чек-лист</a></div>
    </div>
  </section>
'''
os.makedirs('/tmp/claude-0/var/out', exist_ok=True)
for name, html in (('a', src), ('b', src.replace(header_a, header_b)), ('c', src.replace('<body>', '<body class="v-c">'))):
    open(f'/tmp/claude-0/var/out/{name}.html', 'w', encoding='utf-8').write(html)
for f in ('cover.jpg', 'photo.jpeg'):
    shutil.copy(f'/tmp/claude-0/var/{f}', f'/tmp/claude-0/var/out/{f}')
print('ok')
