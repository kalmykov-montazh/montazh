# Серый вариант: компоновка в окна, подбор (без дохода, сдать), юр. страницы, контакт
import re
OUT = '/tmp/claude-0/var/out'
p = f'{OUT}/seryj.html'
s = open(p, encoding='utf-8').read()
assert 'id="dlg-match"' not in s, 'уже применено'

def cut(s, start_marker, end_marker='</section>'):
    i = s.index(start_marker); j = s.index(end_marker, i) + len(end_marker)
    return s[:i], s[i:j], s[j:]

# ---------- 1. Подбор: без дохода + оплата вперёд, вариант «Сдать» ----------
s = s.replace('<button type="button" data-v="Продать">Продать</button></div></div>',
              '<button type="button" data-v="Продать">Продать</button><button type="button" data-v="Сдать">Сдать свою</button></div></div>', 1)
s = s.replace('''    <p class="mnote" id="m_no" hidden>Без подтверждённого дохода хозяева в Испании почти не сдают — требуют контракт или выписки. Когда доход появится — напишите, помогу подобрать</p>''',
'''    <div id="m_pre" hidden>
      <p class="mnote" id="m_no">Сейчас почти на все квартиры в аренду требуют подтверждённый доход. Без дохода варианты бывают, но редко — обычно с оплатой вперёд за полгода или за год</p>
      <div class="q" data-q="pre"><b>Готовы оплатить вперёд?</b><div class="chips">
        <button type="button" data-v="да, за полгода">Да, за полгода</button><button type="button" data-v="да, за год">Да, за год</button><button type="button" data-v="нет">Нет</button></div></div>
    </div>''', 1)
rent_out = '''    <div class="branch" data-for="Сдать" hidden>
      <div class="q"><b>Площадь, м²</b><input type="number" inputmode="numeric" id="m_m2" placeholder="например, 80"></div>
      <div class="q"><b>Желаемая цена в месяц, €</b><input type="number" inputmode="numeric" step="50" id="m_rent" placeholder="например, 1200"></div>
      <div class="q" data-q="from"><b>Когда свободна?</b><div class="chips">
        <button type="button" data-v="уже свободна">Уже свободна</button><button type="button" data-v="в этом месяце">В этом месяце</button><button type="button" data-v="позже">Позже</button></div></div>
    </div>

    <div class="q area" hidden>'''
s = s.replace('    <div class="q area" hidden>', rent_out, 1)
# JS подбора
s = s.replace("var noinc=g==='Снять'&&val(M,'src')==='нет дохода';no.hidden=!noinc;go.hidden=!g||noinc;",
              "var noinc=g==='Снять'&&val(M,'src')==='нет дохода';document.getElementById('m_pre').hidden=!noinc;go.hidden=!g;area.querySelector('b').textContent=g==='Сдать'||g==='Продать'?'Адрес или район':'Район или город';", 1)
s = s.replace("L.push('Бюджет: '+(val(M,'rb')||'—'));",
              "if(noinc)L.push('Оплата вперёд: '+(val(M,'pre')||'—'));L.push('Бюджет: '+(val(M,'rb')||'—'));", 1)
s = s.replace("L.push('Район: '+(a||'—'));",
              "if(g==='Сдать'){var m2=document.getElementById('m_m2').value,rt=document.getElementById('m_rent').value;L.push('Хочу сдать свою квартиру.');L.push('Площадь: '+(m2?m2+' м²':'—'));L.push('Цена: '+(rt?rt+' € в месяц':'—'));L.push('Свободна: '+(val(M,'from')||'—'))}L.push((g==='Сдать'||g==='Продать'?'Адрес/район: ':'Район: ')+(a||'—'));", 1)
assert "m_pre').hidden" in s and "Хочу сдать" in s

# ---------- 2. Перенос в окна ----------
a, match, b = cut(s, '  <section class="match reveal"'); s = a + b
a, calc, b = cut(s, '  <section class="calc reveal"'); s = a + b
i = s.index('  <section class="head" aria-labelledby="h-dist">'); j = s.index('  </div>\n', s.index('<div class="dgrid">')) + len('  </div>\n')
dist = s[i:j]; s = s[:i] + s[j:]
match = match.replace('<section class="match reveal"', '<section class="match"')
calc = calc.replace('<section class="calc reveal"', '<section class="calc"')
dist = dist.replace('<section class="head" aria-labelledby="h-dist">', '<section class="distw" aria-labelledby="h-dist">').replace('</p></section>\n  <div class="dgrid">', '</p>\n  <div class="dgrid">') + '  </section>\n'
def dlg(id_, inner):
    return f'''  <dialog class="sheet" id="{id_}"><button type="button" class="x" aria-label="Закрыть">✕</button>
{inner}  </dialog>
'''
dialogs = dlg('dlg-match', match + '\n') + dlg('dlg-calc', calc + '\n') + dlg('dlg-dist', dist)

tiles = '''  <nav class="tiles" aria-label="Чем помочь">
    <button type="button" data-open="dlg-match"><i>🔑</i><b>Подобрать квартиру</b><span>Снять, купить, продать или сдать</span></button>
    <a href="#h-consult"><i>📄</i><b>Разобрать договор</b><span>Письменно, от 50 €</span></a>
    <button type="button" data-open="dlg-calc"><i>🧮</i><b>Калькулятор покупки</b><span>Налоги и расходы сверху</span></button>
    <button type="button" data-open="dlg-dist"><i>📍</i><b>Районы Валенсии</b><span>Цены аренды, плюсы и минусы</span></button>
  </nav>
'''
s = s.replace('  <section class="checklist reveal"', tiles + '\n  <section class="checklist reveal"', 1)
s = s.replace('  <a class="stickywa"', dialogs + '\n  <a class="stickywa"', 1)

# ---------- 3. Услуги: 6 + «Все услуги» ----------
s = s.replace('  <div class="grid" id="grid"></div>', '  <div class="grid" id="grid"></div>\n  <button type="button" class="allsvc" id="allsvc">Все услуги (14)</button>', 1)

# ---------- 4. Нижняя полоска на телефоне ----------
s = s.replace('  <a class="stickywa"', '''  <div class="mbar"><a id="mbar_wa" target="_blank" rel="noopener">WhatsApp</a><button type="button" data-open="dlg-match">Подобрать квартиру</button></div>
  <a class="stickywa"''', 1)

# ---------- 5. Подвал: контакт + юр. страницы ----------
vcf = 'BEGIN:VCARD\nVERSION:3.0\nN:Kalmykov;Evgenii;;;\nFN:Евгений Калмыков\nORG:Kalmykov Realty\nTITLE:Недвижимость и переезд в Испанию\nTEL;TYPE=CELL:+34624916605\nURL:https://kalmykov-realty.netlify.app\nADR;TYPE=WORK:;;;Valencia;;;España\nEND:VCARD\n'
open(f'{OUT}/kalmykov.vcf', 'w', encoding='utf-8').write(vcf)
s = s.replace('  <footer>Kalmykov Realty · Валенсия, Испания</footer>',
'''  <a class="savec" href="kalmykov.vcf" download="Евгений Калмыков.vcf">👤 Сохранить мой контакт в телефон</a>
  <footer><span>Kalmykov Realty · Валенсия, Испания</span><span class="legal"><a href="aviso-legal.html">Aviso legal</a> · <a href="privacidad.html">Privacidad</a> · <a href="cookies.html">Cookies</a></span></footer>''', 1)

# ---------- 6. Ролики: youtube-nocookie ----------
s = s.replace("https://www.youtube.com/embed/'", "https://www.youtube-nocookie.com/embed/'", 1)

css = '''
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0 6px}
.tiles>*{display:flex;flex-direction:column;align-items:flex-start;gap:3px;text-align:left;background:#fff;border:0;border-radius:18px;padding:16px;font:inherit;color:#16233a;text-decoration:none;cursor:pointer;box-shadow:0 2px 10px rgba(22,41,74,.08);transition:transform .15s,box-shadow .15s}
.tiles>*:hover{transform:translateY(-3px);box-shadow:0 10px 24px rgba(22,41,74,.14)}
.tiles i{font-style:normal;font-size:26px;line-height:1;margin-bottom:6px}
.tiles b{font-size:16px;color:#16294a}.tiles span{font-size:13px;color:#5f6b7a}
.tiles>*:first-child{background:#ff6b4a}.tiles>*:first-child b,.tiles>*:first-child span{color:#fff}
@media (max-width:700px){.tiles{grid-template-columns:1fr 1fr;gap:8px}.tiles>*{padding:13px}.tiles b{font-size:14.5px}.tiles span{font-size:12px}.tiles i{font-size:22px}}
dialog.sheet{border:0;padding:0;border-radius:22px;width:min(760px,94vw);max-height:90vh;background:#fff;box-shadow:0 30px 80px rgba(0,0,0,.35)}
dialog.sheet::backdrop{background:rgba(10,20,40,.55)}
dialog.sheet>section{margin:0;box-shadow:none;border-radius:0}
dialog.sheet .x{position:sticky;top:10px;float:right;margin:10px 10px 0 0;z-index:2;width:38px;height:38px;border-radius:50%;border:0;background:#eef1f5;font-size:17px;cursor:pointer;color:#16233a}
.distw{padding:24px 26px}.distw .dgrid{margin-bottom:0}.distw h2{margin:0 0 4px;color:#16294a}
@media (max-width:700px){dialog.sheet{width:100vw;max-width:100vw;max-height:92vh;margin:auto 0 0;border-radius:22px 22px 0 0}dialog.sheet[open]{animation:up .25s ease-out}.distw{padding:20px}}
@keyframes up{from{transform:translateY(40px);opacity:.4}to{transform:none;opacity:1}}
.grid:not(.all) .card:nth-child(n+7){display:none}
.allsvc{display:block;margin:12px auto 28px;background:#fff;border:1.5px solid #16294a;color:#16294a;font:inherit;font-weight:700;border-radius:12px;padding:12px 22px;cursor:pointer}
.grid.all+.allsvc{display:none}
.vgrid{display:flex!important;overflow-x:auto;scroll-snap-type:x mandatory;gap:12px;padding-bottom:6px}
.vgrid .yt{flex:0 0 46%;scroll-snap-align:start}
@media (max-width:700px){.vgrid .yt{flex-basis:82%}}
.soon{display:flex!important;overflow-x:auto;gap:10px;scroll-snap-type:x mandatory}
.soon div{flex:0 0 260px;scroll-snap-align:start;padding:12px 14px!important}
.mbar{display:none}
@media (max-width:600px){.stickywa{display:none!important}.mbar{display:flex;position:fixed;left:10px;right:10px;bottom:calc(10px + env(safe-area-inset-bottom,0px));z-index:20;gap:8px}
 .mbar>*{flex:1;display:flex;align-items:center;justify-content:center;gap:6px;border:0;border-radius:14px;padding:14px 8px;font:inherit;font-weight:700;font-size:15px;text-decoration:none;box-shadow:0 8px 20px rgba(0,0,0,.18)}
 .mbar a{background:#1fa855;color:#fff}.mbar a svg{width:18px;height:18px;fill:currentColor}.mbar button{background:#16294a;color:#fff}
 body{padding-bottom:80px}}
.savec{display:flex;justify-content:center;margin:24px auto 0;max-width:340px;background:#fff;border-radius:14px;padding:13px;font-weight:700;color:#16294a;text-decoration:none;box-shadow:0 2px 10px rgba(22,41,74,.08)}
footer .legal a{color:#5f6b7a}
'''
s = s.replace('</style>\n</head>', css + '</style>\n</head>', 1)

js = r'''<script>
(function(){
function op(id){var d=document.getElementById(id);if(d&&d.showModal){d.showModal();d.scrollTop=0}}
document.querySelectorAll('[data-open]').forEach(function(b){b.addEventListener('click',function(){op(b.dataset.open)})});
document.querySelectorAll('dialog.sheet').forEach(function(d){
 d.querySelector('.x').addEventListener('click',function(){d.close()});
 d.addEventListener('click',function(e){if(e.target===d)d.close()})});
var g=document.getElementById('grid'),a=document.getElementById('allsvc');
if(a)a.addEventListener('click',function(){g.classList.add('all')});
var fl=document.getElementById('filters');if(fl)fl.addEventListener('click',function(e){if(e.target.closest('button'))g.classList.add('all')});
var mw=document.getElementById('mbar_wa');if(mw){mw.href="https://wa.me/34624916605?text="+encodeURIComponent("Здравствуйте! Пишу с сайта.\nМоя ситуация: ");
 mw.insertAdjacentHTML('afterbegin','<svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .1-1.7-.1a15 15 0 0 1-6.4-5.6c-.5-.7-1-1.6-1-2.6 0-1 .5-1.5.7-1.7.2-.2.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 1.9c.1.2.1.4 0 .5l-.4.6-.3.4c-.1.1-.2.3-.1.5.5.9 1.2 1.8 2 2.4.9.8 1.7 1 1.9 1.1.2.1.4.1.5-.1l.8-.9c.2-.2.4-.2.6-.1l1.8.9c.2.1.4.2.5.3.1.2.1.8-.2 1.4Z"/></svg>')}
})();
</script>
'''
s = s.replace('</body>', js + '</body>', 1)
open(p, 'w', encoding='utf-8').write(s)

# ---------- 7. Юридические страницы ----------
base_css = '''*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:#16233a;font:16px/1.65 Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.w{max-width:760px;margin:0 auto;padding:20px 16px 60px}a{color:#2f6fd6}.back{display:inline-block;margin-bottom:14px;font-weight:700;text-decoration:none}
.card{background:#fff;border-radius:20px;padding:24px;box-shadow:0 2px 10px rgba(22,41,74,.07);margin-bottom:16px}
h1{font-size:26px;color:#16294a;margin:0 0 12px}h2{font-size:18px;color:#16294a;margin:18px 0 6px}.ru{background:#f5f7fa;border-radius:14px;padding:14px 16px;font-size:15px}
.ru b{display:block;margin-bottom:4px}'''
def legal(fname, title, es_html, ru_html):
    html = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Kalmykov Realty</title><meta name="robots" content="noindex">
<link rel="icon" href="favicon.svg" type="image/svg+xml"><style>{base_css}</style></head>
<body><div class="w"><a class="back" href="index.html">← Volver / Назад</a>
<div class="card"><h1>{title}</h1>{es_html}
<div class="ru"><b>По-русски коротко</b>{ru_html}</div></div></div></body></html>'''
    open(f'{OUT}/{fname}', 'w', encoding='utf-8').write(html)

titular = '<p><b>Titular:</b> Evgenii Kalmykov (Kalmykov Realty)<br><b>Domicilio:</b> Valencia, España<br><b>Contacto:</b> WhatsApp +34 624 916 605<br><b>NIF/NIE:</b> se indicará tras el alta como autónomo</p>'
legal('aviso-legal.html', 'Aviso legal',
 f'''<p>En cumplimiento de la Ley 34/2002, de servicios de la sociedad de la información y de comercio electrónico (LSSI-CE), se informa de los datos del titular de este sitio web:</p>{titular}
<h2>Objeto</h2><p>Este sitio ofrece información sobre la vida en España, servicios de asesoramiento sobre contratos de alquiler y compraventa, y contactos de profesionales colaboradores. El titular no es abogado: no presta servicios de representación legal.</p>
<h2>Responsabilidad</h2><p>La información y los cálculos de este sitio son orientativos. Los importes exactos se determinan en cada operación. El titular no se responsabiliza de los servicios prestados por terceros enlazados desde este sitio.</p>
<h2>Propiedad intelectual</h2><p>Los textos, imágenes y vídeos de este sitio pertenecen a su titular, salvo que se indique lo contrario.</p>''',
 '<p>Юридическое уведомление по испанскому закону о сайтах (LSSI): кто владелец сайта и как связаться. Сайт даёт информацию о жизни в Испании, разбор договоров аренды и покупки, контакты партнёров. Я не юрист и не представляю интересы в суде. Расчёты на сайте примерные, точные суммы — при сделке. За услуги партнёров по ссылкам отвечают сами партнёры. NIF/NIE появится после оформления автонома</p>')
legal('privacidad.html', 'Política de privacidad',
 f'''{titular}<h2>Qué datos tratamos</h2><p>Este sitio no tiene formularios que guarden datos. Al pulsar un botón de WhatsApp o Telegram, usted envía voluntariamente un mensaje que se trata en esas aplicaciones, conforme a sus propias políticas.</p>
<h2>Finalidad y base legal</h2><p>Responder a su consulta, con base en su consentimiento al escribirnos (art. 6.1.a RGPD).</p>
<h2>Conservación</h2><p>Los mensajes se conservan mientras sea necesario para atender su consulta.</p>
<h2>Sus derechos</h2><p>Puede solicitar acceso, rectificación o supresión de sus datos escribiendo al contacto indicado, y reclamar ante la Agencia Española de Protección de Datos (aepd.es).</p>''',
 '<p>Политика конфиденциальности (RGPD). Сайт сам ничего не сохраняет: кнопки открывают WhatsApp или Telegram, вы пишете сами. Ваши сообщения используются только чтобы ответить. Можно попросить удалить переписку, жалобы — в испанское агентство защиты данных (AEPD)</p>')
legal('cookies.html', 'Política de cookies',
 '''<p>Este sitio no utiliza cookies propias ni de análisis.</p>
<h2>Vídeos de YouTube</h2><p>Los vídeos se cargan en modo de privacidad mejorada (youtube-nocookie.com) y solo cuando usted pulsa «reproducir». A partir de ese momento, YouTube (Google) puede usar sus propias cookies según su política: policies.google.com.</p>''',
 '<p>Сайт не ставит своих файлов cookie и не ведёт статистику. Видео YouTube загружаются только по нажатию, в режиме повышенной приватности; после запуска ролика YouTube может использовать свои cookie</p>')
print('ok')
