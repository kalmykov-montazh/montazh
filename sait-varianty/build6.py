# Серый вариант: цифры, подбор квартиры, калькулятор, районы, ролики, отзывы (скрыт)
import os, re
OUT = '/tmp/claude-0/var/out'
p = f'{OUT}/seryj.html'
s = open(p, encoding='utf-8').read()
WA = 'https://wa.me/34624916605?text='

# ---------- 1. Цифры под шапкой ----------
stats = '''  <div class="stats">
    <div><b>11 000+</b><span>подписчиков в Facebook</span></div>
    <div><b>1 000+</b><span>роликов о жизни в Испании</span></div>
    <div><b>с 2025</b><span>живу в Валенсии</span></div>
  </div>
'''
# ---------- 2. Подбор квартиры ----------
match = '''  <section class="match reveal" aria-labelledby="h-match">
    <span class="mkick">Подбор за 1 минуту</span>
    <h2 id="h-match">Подобрать квартиру</h2>
    <p class="lead">Ответьте на несколько вопросов — ответы сами сложатся в сообщение в WhatsApp</p>
    <div class="q" data-q="goal"><b>Что нужно?</b><div class="chips">
      <button type="button" data-v="Снять">Снять</button><button type="button" data-v="Купить">Купить</button><button type="button" data-v="Продать">Продать</button></div></div>

    <div class="branch" data-for="Снять" hidden>
      <div class="q"><b>Доход семьи в месяц, €</b><input type="number" inputmode="numeric" min="0" step="100" id="m_inc" placeholder="например, 2500"></div>
      <div class="q" data-q="src"><b>Откуда доход?</b><div class="chips">
        <button type="button" data-v="контракт в Испании">Контракт в Испании</button><button type="button" data-v="автоном в Испании">Автоном в Испании</button><button type="button" data-v="Украина">Украина</button><button type="button" data-v="другая страна">Другая страна</button><button type="button" data-v="нет дохода" class="no">Нет дохода</button></div></div>
      <div class="q" data-q="rb"><b>Бюджет аренды в месяц</b><div class="chips">
        <button type="button" data-v="до 900 €">до 900 €</button><button type="button" data-v="900–1200 €">900–1200 €</button><button type="button" data-v="1200–1500 €">1200–1500 €</button><button type="button" data-v="от 1500 €">от 1500 €</button></div></div>
      <div class="q" data-q="rw"><b>Когда въезд?</b><div class="chips">
        <button type="button" data-v="в этом месяце">В этом месяце</button><button type="button" data-v="через 1–2 месяца">Через 1–2 месяца</button><button type="button" data-v="позже">Позже</button></div></div>
    </div>

    <div class="branch" data-for="Купить" hidden>
      <div class="q" data-q="bb"><b>Бюджет покупки</b><div class="chips">
        <button type="button" data-v="до 150 000 €">до 150 000 €</button><button type="button" data-v="150–250 тыс. €">150–250 тыс. €</button><button type="button" data-v="250–400 тыс. €">250–400 тыс. €</button><button type="button" data-v="от 400 000 €">от 400 000 €</button></div></div>
      <div class="q" data-q="bm"><b>Нужна ипотека?</b><div class="chips">
        <button type="button" data-v="да">Да</button><button type="button" data-v="нет, свои деньги">Нет, свои деньги</button><button type="button" data-v="не знаю">Не знаю</button></div></div>
      <div class="q" data-q="bw"><b>Когда планируете?</b><div class="chips">
        <button type="button" data-v="в ближайший месяц">В ближайший месяц</button><button type="button" data-v="за 3 месяца">За 3 месяца</button><button type="button" data-v="через полгода и позже">Через полгода и позже</button></div></div>
    </div>

    <div class="branch" data-for="Продать" hidden>
      <div class="q" data-q="st"><b>Что продаёте?</b><div class="chips">
        <button type="button" data-v="квартиру">Квартиру</button><button type="button" data-v="дом">Дом</button><button type="button" data-v="коммерческое помещение">Коммерческое</button></div></div>
      <div class="q" data-q="sw"><b>Когда хотите продать?</b><div class="chips">
        <button type="button" data-v="срочно">Срочно</button><button type="button" data-v="за 3 месяца">За 3 месяца</button><button type="button" data-v="не спешу">Не спешу</button></div></div>
    </div>

    <div class="q area" hidden><b>Район или город</b><input type="text" id="m_area" placeholder="например, Русафа или «не важно»"></div>
    <p class="mnote" id="m_no" hidden>Без подтверждённого дохода хозяева в Испании почти не сдают — требуют контракт или выписки. Когда доход появится — напишите, помогу подобрать</p>
    <a class="go mgo" id="m_go" target="_blank" rel="noopener" hidden>Отправить в WhatsApp</a>
  </section>
'''
# ---------- 3. Калькулятор ----------
calc = '''  <section class="calc reveal" aria-labelledby="h-calc">
    <span class="mkick">Калькулятор</span>
    <h2 id="h-calc">Сколько стоит купить квартиру в Валенсии</h2>
    <p class="lead">Налоги и расходы сверху цены квартиры. Расчёт примерный — точные суммы будут при сделке</p>
    <div class="cgrid">
      <div class="cin">
        <label><b>Цена квартиры, €</b><input type="number" id="c_price" value="200000" min="10000" step="5000" inputmode="numeric"></label>
        <div class="q" data-q="ctype"><b>Квартира</b><div class="chips">
          <button type="button" data-v="old" aria-pressed="true">Вторичка</button><button type="button" data-v="new">Новостройка</button></div></div>
        <div class="q" data-q="cmort"><b>Ипотека</b><div class="chips">
          <button type="button" data-v="no" aria-pressed="true">Без ипотеки</button><button type="button" data-v="yes">С ипотекой</button></div></div>
      </div>
      <div class="cout" id="c_out"></div>
    </div>
    <p class="cnote">Ставки Валенсийского сообщества с 1 июня 2026: налог на покупку вторички (ITP) — 9 %, дороже 1 млн € — 11 %; новостройка — IVA 10 % + 1,4 % (AJD). Молодым до 35 лет, многодетным и некоторым другим положены сниженные ставки. Суммы примерные и могут немного отличаться — точный расчёт будет при сделке</p>
    <a class="go" id="c_go" target="_blank" rel="noopener">Обсудить покупку в WhatsApp</a>
  </section>
'''
# ---------- 4. Районы ----------
D = [
 ('ruzafa','Русафа','Ruzafa',18.6,'Кафе, рынок, жизнь в центре','Для тех, кто хочет всё рядом и работает удалённо',
  ['Всё пешком: центр, вокзал, парк Турия','Рынок Русафы, сотни кафе и магазинов','Удобно без машины'],
  ['Вечером и в выходные шумно','Один из самых дорогих районов','В старых домах бывает без лифта'],
  'Русафа входит в район L’Eixample — цена по нему. В объявлениях по самой Русафе часто выше'),
 ('benimaclet','Бенимаклет','Benimaclet',14.6,'Студенты и спокойная жизнь','Для тех, кто считает бюджет: студенты, молодые семьи',
  ['Одни из самых доступных цен рядом с центром','Метро и трамвай, рядом университеты','Атмосфера «деревни в городе», огороды по краю'],
  ['Много старых домов без ремонта','Много студентов — бывает шумно','Мало новостроек'],''),
 ('campanar','Кампанар','Campanar',17.9,'Новые дома и парки','Для семей с детьми и тех, кто хочет тишину',
  ['Новые дома с бассейнами и паркингом','Парки и зелень','Тихо, удобно с детьми'],
  ['Дальше от моря','Новые дома — дороже','Без машины чуть менее удобно'],''),
 ('cabanyal','Кабаньяль','Cabanyal',16.5,'Жизнь у моря','Для тех, кто хочет пляж рядом',
  ['Пляж Мальварроса в шаговой доступности','Трамвай в центр','Свой рынок и рыбные ресторанчики'],
  ['Есть улицы попроще — смотреть конкретный дом','Летом много туристов','У моря сыро зимой'],
  'Кабаньяль входит в район Poblats Marítims — цена по нему'),
 ('patraix','Патраикс','Patraix',13.6,'Спокойно и доступно','Для семей и тех, кто экономит',
  ['Самая низкая цена среди районов Валенсии','Спокойно, много школ и магазинов','Метро в центр'],
  ['Мало развлечений','Далеко от моря','Много старых домов'],''),
 ('algiros','Алжирос','Algirós',14.8,'Университеты и трамвай','Для студентов и тех, кто хочет к морю подешевле',
  ['Цены ниже центра','Трамвай до моря и до центра','Рядом университеты и Бенимаклет'],
  ['Спальный район','Меньше кафе и жизни на улицах','Много студенческого жилья'],''),
]
def card(d):
    slug,ru,es,m2,tag,who,pl,mi,note = d
    return f'''      <a class="dcard" href="rayony/{slug}.html"><small>{es}</small><b>{ru}</b><span>{tag}</span><em>≈ {format(round(m2*70/10)*10, ",").replace(",", " ")} € / мес</em><i>Подробнее →</i></a>'''
districts = '''  <section class="head" aria-labelledby="h-dist"><h2 id="h-dist">Районы Валенсии</h2>
    <p class="lead">Цены аренды квартиры 70 м² — примерно, по данным Idealista за октябрь 2026</p></section>
  <div class="dgrid">
''' + '\n'.join(card(d) for d in D) + '''
  </div>
'''
# ---------- 5. Ролики ----------
V = [('C5Y5ka8njw8','Временная защита → ВНЖ на 4 года и ПМЖ'),('6a1WSjx0vUY','Медицина в Испании 2026'),
     ('n4-DJCyKB9k','17 ловушек при аренде в Испании'),('GFh4QCWANTo','15 штрафов в Испании')]
videos = '''  <section class="head" aria-labelledby="h-vid"><h2 id="h-vid">Главное в видео</h2>
    <p class="lead">Разборы на YouTube — документы, медицина, аренда</p></section>
  <div class="vgrid">
''' + '\n'.join(f'''    <button type="button" class="yt" data-id="{i}" aria-label="Смотреть: {t}"><img src="https://i.ytimg.com/vi/{i}/hqdefault.jpg" alt="" loading="lazy"><span class="play"></span><b>{t}</b></button>''' for i,t in V) + '''
  </div>
'''
# ---------- 6. Отзывы (скрыт, пока нет) ----------
reviews = '''  <section class="reviews" id="reviews" aria-labelledby="h-rev" hidden>
    <h2 id="h-rev">Отзывы</h2>
    <div class="rgrid" id="rgrid"><!-- сюда: <figure class="review"><img src="otzyvy/1.jpg" alt="Отзыв"><figcaption>Аренда, Валенсия</figcaption></figure> --></div>
  </section>
'''

css = '''
.stats{display:flex;justify-content:center;gap:10px;margin:14px 0 4px;flex-wrap:wrap}
.stats div{background:#fff;border-radius:14px;padding:10px 16px;text-align:center;box-shadow:0 1px 4px rgba(22,41,74,.07);min-width:150px}
.stats b{display:block;font-size:20px;color:#16294a}
.stats span{font-size:12.5px;color:#5f6b7a}
@media (max-width:600px){.stats{gap:6px;flex-wrap:nowrap}.stats div{min-width:0;flex:1;padding:8px 6px}.stats b{font-size:16px}.stats span{font-size:11px;line-height:1.25;display:block}}
.match,.calc{margin:28px 0;padding:24px 26px;border-radius:20px;background:#fff;box-shadow:0 2px 10px rgba(22,41,74,.07)}
.match{border-top:6px solid #ff6b4a}.calc{border-top:6px solid #16294a}
.mkick{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;color:#ff6b4a}
.calc .mkick{color:#2f6fd6}
.match h2,.calc h2{margin:6px 0 4px;font-size:23px;color:#16294a}
.match .lead,.calc .lead{margin:0 0 14px}
.q{margin:14px 0 0}.q>b{display:block;font-size:14.5px;margin-bottom:8px;color:#16233a}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chips button{border:1.5px solid #dde3ea;background:#f5f7fa;color:#16233a;border-radius:99px;padding:9px 15px;font:inherit;font-size:14.5px;font-weight:600;cursor:pointer}
.chips button[aria-pressed="true"]{background:#16294a;border-color:#16294a;color:#fff}
.chips button.no[aria-pressed="true"]{background:#9aa4b2;border-color:#9aa4b2}
.q input{width:100%;max-width:340px;border:1.5px solid #dde3ea;border-radius:12px;padding:11px 13px;font:inherit;font-size:16px;background:#f5f7fa}
.q input:focus{outline:2px solid #ff6b4a;border-color:transparent}
.mnote{margin:16px 0 0;padding:12px 14px;border-radius:12px;background:#fff4e5;color:#7a4b00;font-size:14px}
.mgo,.calc .go{margin-top:18px;display:inline-flex}
.cgrid{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}
.cin label b{display:block;font-size:14.5px;margin-bottom:8px}
.cin label input{width:100%;border:1.5px solid #dde3ea;border-radius:12px;padding:11px 13px;font:inherit;font-size:18px;font-weight:700;background:#f5f7fa}
.cout{background:#16294a;color:#fff;border-radius:16px;padding:18px 18px 14px}
.cout table{width:100%;border-collapse:collapse;font-size:14.5px}
.cout td{padding:6px 0;border-bottom:1px solid rgba(255,255,255,.12)}
.cout td:last-child{text-align:right;white-space:nowrap;font-weight:700}
.cout .tot td{border:0;padding-top:12px;font-size:17px;color:#ffd166}
.cout p{margin:10px 0 0;font-size:13px;color:#c9d3e0}
.cnote{margin:14px 0 0;font-size:12.5px;color:#64707b;line-height:1.5}
@media (max-width:700px){.cgrid{grid-template-columns:1fr}.match,.calc{padding:20px}.match h2,.calc h2{font-size:20px}.mgo,.calc .go{display:flex;justify-content:center}}
.dgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:28px}
.dcard{display:flex;flex-direction:column;gap:3px;background:#fff;border-radius:16px;padding:16px 18px;text-decoration:none;color:#16233a;box-shadow:0 2px 10px rgba(22,41,74,.07);transition:transform .15s}
.dcard:hover{transform:translateY(-3px)}
.dcard small{font-size:12px;color:#5f6b7a;letter-spacing:.3px}
.dcard b{font-size:18px;color:#16294a}
.dcard span{font-size:14px;color:#5f6b7a}
.dcard em{font-style:normal;font-weight:700;color:#ff6b4a;margin-top:6px}
.dcard i{font-style:normal;font-size:13.5px;font-weight:700;color:#2f6fd6;margin-top:2px}
@media (max-width:700px){.dgrid{grid-template-columns:1fr 1fr;gap:8px}.dcard{padding:13px}.dcard b{font-size:16px}.dcard span{font-size:12.5px}}
.vgrid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:28px}
.yt{position:relative;border:0;padding:0;border-radius:16px;overflow:hidden;background:#000;cursor:pointer;aspect-ratio:16/9;font:inherit;text-align:left}
.yt img{width:100%;height:100%;object-fit:cover;display:block;opacity:.85}
.yt b{position:absolute;left:0;right:0;bottom:0;padding:26px 14px 12px;color:#fff;font-size:15px;background:linear-gradient(transparent,rgba(0,0,0,.8))}
.yt .play{position:absolute;left:50%;top:45%;width:64px;height:44px;margin:-22px 0 0 -32px;border-radius:12px;background:#f00}
.yt .play::after{content:"";position:absolute;left:26px;top:13px;border-left:16px solid #fff;border-top:9px solid transparent;border-bottom:9px solid transparent}
.yt iframe{width:100%;height:100%;border:0;display:block}
@media (max-width:700px){.vgrid{grid-template-columns:1fr}}
.reviews{margin:28px 0}.rgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.review{margin:0;background:#fff;border-radius:16px;padding:10px;box-shadow:0 2px 10px rgba(22,41,74,.07)}
.review img{width:100%;border-radius:10px;display:block}.review figcaption{font-size:13px;color:#5f6b7a;padding:6px 4px 0}
@media (max-width:700px){.rgrid{grid-template-columns:1fr}}
'''

js = r'''<script>
(function(){
var WA="https://wa.me/34624916605?text=";
function chips(root,cb){root.querySelectorAll('.q[data-q] .chips').forEach(function(g){g.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;g.querySelectorAll('button').forEach(function(x){x.setAttribute('aria-pressed',x===b)});cb&&cb()})})}
function val(root,q){var b=root.querySelector('.q[data-q="'+q+'"] button[aria-pressed="true"]');return b?b.dataset.v:''}
/* подбор */
var M=document.querySelector('.match');
if(M){var go=document.getElementById('m_go'),no=document.getElementById('m_no'),area=M.querySelector('.area');
 function upd(){var g=val(M,'goal');M.querySelectorAll('.branch').forEach(function(b){b.hidden=b.dataset.for!==g});area.hidden=!g;
  var noinc=g==='Снять'&&val(M,'src')==='нет дохода';no.hidden=!noinc;go.hidden=!g||noinc;
  var a=document.getElementById('m_area').value.trim(),L=['Здравствуйте! Пишу с сайта. Подбор.'];
  if(g==='Снять'){var inc=document.getElementById('m_inc').value;L.push('Хочу снять квартиру.');L.push('Доход семьи: '+(inc?inc+' € в месяц':'—')+(val(M,'src')?', '+val(M,'src'):''));L.push('Бюджет: '+(val(M,'rb')||'—'));L.push('Въезд: '+(val(M,'rw')||'—'))}
  if(g==='Купить'){L.push('Хочу купить.');L.push('Бюджет: '+(val(M,'bb')||'—'));L.push('Ипотека: '+(val(M,'bm')||'—'));L.push('Когда: '+(val(M,'bw')||'—'))}
  if(g==='Продать'){L.push('Хочу продать '+(val(M,'st')||'недвижимость')+'.');L.push('Когда: '+(val(M,'sw')||'—'))}
  L.push('Район: '+(a||'—'));go.href=WA+encodeURIComponent(L.join('\n'))}
 chips(M,upd);M.addEventListener('input',upd);upd()}
/* калькулятор */
var C=document.querySelector('.calc');
if(C){var out=document.getElementById('c_out'),pr=document.getElementById('c_price'),cg=document.getElementById('c_go');
 function f(n){return Math.round(n).toLocaleString('ru-RU').replace(/ /g,' ')+' €'}
 function calc(){var p=+pr.value||0,isNew=val(C,'ctype')==='new',mort=val(C,'cmort')==='yes',rows=[],lo=0,hi=0;
  if(isNew){rows.push(['IVA 10 %',p*.10,p*.10]);rows.push(['AJD 1,4 %',p*.014,p*.014])}
  else{var r=p>1e6?.11:.09;rows.push(['Налог ITP '+(r*100)+' %',p*r,p*r])}
  rows.push(['Нотариус',600,1000]);rows.push(['Регистрация',400,700]);rows.push(['Гестория (оформление)',300,500]);
  if(mort)rows.push(['Оценка для банка',300,500]);
  rows.forEach(function(x){lo+=x[1];hi+=x[2]});
  var h='<table>'+rows.map(function(x){return '<tr><td>'+x[0]+'</td><td>'+(x[1]===x[2]?f(x[1]):f(x[1])+' – '+f(x[2]))+'</td></tr>'}).join('')+
   '<tr class="tot"><td>Расходы сверху</td><td>'+f(lo)+' – '+f(hi)+'</td></tr></table>';
  if(mort)h+='<p>С ипотекой банк обычно даёт до 80 % цены (нерезидентам — меньше). Свои деньги примерно: '+f(p*.2+lo)+' – '+f(p*.2+hi)+'</p>';
  else h+='<p>Всего с квартирой примерно: '+f(p+lo)+' – '+f(p+hi)+'</p>';
  out.innerHTML=h;
  cg.href=WA+encodeURIComponent('Здравствуйте! Пишу с сайта. Покупка.\nЦена около '+f(p)+', '+(isNew?'новостройка':'вторичка')+', '+(mort?'нужна ипотека':'без ипотеки')+'.\nМой вопрос: ')}
 chips(C,calc);pr.addEventListener('input',calc);calc()}
/* ролики: грузим плеер только по нажатию */
document.querySelectorAll('.yt').forEach(function(b){b.addEventListener('click',function(){b.innerHTML='<iframe src="https://www.youtube.com/embed/'+b.dataset.id+'?autoplay=1&rel=0" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen title="YouTube"></iframe>'},{once:true})});
/* отзывы: показываем блок, только когда есть хоть один */
var R=document.getElementById('reviews');if(R&&R.querySelector('.review'))R.hidden=false;
})();
</script>
'''

if 'class="stats"' not in s:
    s = s.replace('  <nav class="socials"', stats + '\n  <nav class="socials"', 1)
    s = s.replace('  <section class="consult"', match + '\n  <section class="consult"', 1)
    s = s.replace('  <section class="about reveal"', calc + '\n' + districts + '\n' + videos + '\n  <section class="about reveal"', 1)
    s = s.replace('  <section class="head" aria-labelledby="h-faq">', reviews + '\n  <section class="head" aria-labelledby="h-faq">', 1)
    s = s.replace('</style>\n</head>', css + '</style>\n</head>', 1)
    s = s.replace('</body>', js + '</body>', 1)
    open(p, 'w', encoding='utf-8').write(s)

# ---------- страницы районов ----------
os.makedirs(f'{OUT}/rayony', exist_ok=True)
page_css = '''*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:#16233a;font:16px/1.6 Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.w{max-width:760px;margin:0 auto;padding:20px 16px 90px}a{color:#2f6fd6}
.back{display:inline-block;margin-bottom:14px;font-weight:700;text-decoration:none}
.card{background:#fff;border-radius:20px;padding:24px;box-shadow:0 2px 10px rgba(22,41,74,.07);margin-bottom:16px}
h1{font-size:28px;line-height:1.25;color:#16294a;margin:0 0 6px}h2{font-size:20px;color:#16294a;margin:0 0 10px}
.sub{color:#5f6b7a;margin:0}.price{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.price div{background:#16294a;color:#fff;border-radius:14px;padding:12px 16px}.price b{display:block;font-size:22px;color:#ffd166}.price span{font-size:13px;color:#c9d3e0}
ul{margin:0;padding-left:20px}li{margin:4px 0}.pm{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.plus h2{color:#1f9a5a}.minus h2{color:#d9461a}.note{font-size:13px;color:#64707b}
.go{display:flex;justify-content:center;align-items:center;gap:8px;background:#ff6b4a;color:#fff;font-weight:700;text-decoration:none;border-radius:14px;padding:15px;font-size:16px;box-shadow:0 5px 0 #c94a2f}
.more{display:flex;flex-wrap:wrap;gap:8px}.more a{background:#fff;border-radius:99px;padding:8px 14px;text-decoration:none;font-weight:600;box-shadow:0 1px 4px rgba(22,41,74,.07)}
@media (max-width:600px){h1{font-size:23px}.pm{grid-template-columns:1fr}.card{padding:18px}}'''
for d in D:
    slug,ru,es,m2,tag,who,pl,mi,note = d
    rent = round(m2*70/10)*10
    wa = WA + __import__('urllib.parse').parse.quote(f'Здравствуйте! Пишу с сайта, страница района {ru}.\nИнтересует: аренда / покупка.\nДоход семьи и откуда: \nКогда въезд: ')
    others = ''.join(f'<a href="{o[0]}.html">{o[1]}</a>' for o in D if o[0]!=slug)
    note_html = f'<p class="note">{note}</p>' if note else ''
    html = f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{ru} ({es}), Валенсия: цены аренды, для кого район, плюсы и минусы — 2026</title>
<meta name="description" content="Район {ru} ({es}) в Валенсии: сколько стоит аренда квартиры в 2026 году, кому подходит, плюсы и минусы. Евгений Калмыков, Валенсия">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<style>{page_css}</style></head>
<body><div class="w">
<a class="back" href="../index.html">← Евгений Калмыков · все услуги</a>
<div class="card"><h1>{ru} ({es}) — {tag.lower()}</h1><p class="sub">{who}</p>
<div class="price"><div><b>≈ {str(m2).replace('.',',')} €/м²</b><span>аренда в месяц, Idealista, октябрь 2026</span></div><div><b>≈ {rent:,} €</b><span>квартира 70 м² в месяц</span></div></div>
{note_html}</div>
<div class="pm"><div class="card plus"><h2>Плюсы</h2><ul>{''.join(f'<li>{x}</li>' for x in pl)}</ul></div>
<div class="card minus"><h2>Минусы</h2><ul>{''.join(f'<li>{x}</li>' for x in mi)}</ul></div></div>
<div class="card"><h2>Хотите снять или купить в районе {ru}?</h2><p>Напишите доход семьи, откуда он и когда планируете въезд — подскажу, что реально найти за ваш бюджет</p>
<a class="go" href="{wa}" target="_blank" rel="noopener">Написать в WhatsApp</a>
<p class="note">Цены примерные, по средней цене за м² на Idealista. Конкретная квартира может стоить больше или меньше</p></div>
<h2>Другие районы</h2><div class="more">{others}</div>
</div></body></html>'''.replace(f'{rent:,}', f'{rent:,}'.replace(',', ' '))
    open(f'{OUT}/rayony/{slug}.html','w',encoding='utf-8').write(html)
print('ok')

# кнопки в подборе и калькуляторе — как оранжевая кнопка консультации
btn = '.mgo,.calc .go{align-items:center;justify-content:center;gap:8px;background:#ff6b4a;color:#fff!important;text-decoration:none!important;font-weight:700;font-size:16px;border-radius:14px;padding:14px 22px;box-shadow:0 5px 0 #c94a2f}\n.mgo:hover,.calc .go:hover{transform:translateY(-1px)}\n'
p = '/tmp/claude-0/var/out/seryj.html'
s = open(p, encoding='utf-8').read()
if '.mgo,.calc .go{align-items' not in s:
    s = s.replace('</style>\n</head>', btn + '</style>\n</head>', 1)
    open(p, 'w', encoding='utf-8').write(s)
print('btn ok')
