# Новый вид страницы новости (образец 23.11.2026, решение Евгения: «на одной новости сначала, посмотрю вживую»).
# Широкая страница (новость + правая колонка), лёгкий цветной фон, кнопки: Telegram — тёмно-синяя с золотом,
# услуга и WhatsApp — чёрные с золотом, буквы крупнее, двойная окантовка, значки SVG вместо эмодзи.
# Применяется к готовому HTML из novosti_build.article_html: redesign(html). Какие новости — DESIGN2_SLUGS.
import re

DESIGN2_SLUGS = {'2026-11-22-ispaniya-za-nedelyu-minimalka-pensii-svet-benzin-i-airbnb'}

_PLANE = '<path d="M5.5 11.7l11-4.3c.5-.2 1 .1.8.9l-1.9 8.8c-.1.6-.5.8-1 .5l-2.8-2.1-1.4 1.3c-.2.2-.3.3-.6.3l.2-2.9 5.2-4.7c.2-.2 0-.3-.3-.1l-6.4 4-2.8-.9c-.6-.2-.6-.6.1-.9z" fill="#fff"/>'
TG = f'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="12" fill="#2aa1da"/>{_PLANE}</svg>'
WA = ('<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="16" fill="#25d366"/><path fill="#fff" d="M16 6.5a9.4 9.4 0 0 0-8 14.3L6.8 25l4.3-1.1A9.4 9.4 0 1 0 16 6.5zm0 17.2c-1.5 0-2.9-.4-4.1-1.1l-.3-.2-2.6.7.7-2.5-.2-.3a7.8 7.8 0 1 1 6.5 3.4zm4.3-5.8c-.2-.1-1.4-.7-1.6-.8-.2-.1-.4-.1-.5.1l-.7.9c-.1.2-.3.2-.5.1a6.4 6.4 0 0 1-3.2-2.8c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.7-1.7c-.2-.5-.4-.4-.5-.4h-.5c-.2 0-.4.1-.6.3-.2.2-.8.8-.8 2s.8 2.3.9 2.5c.1.2 1.6 2.5 4 3.5 1.5.6 2.1.7 2.8.6.5-.1 1.4-.6 1.6-1.1.2-.5.2-1 .1-1.1l-.5-.4z"/></svg>')
G = '#ffd54a'
ICONS = {  # значки услуг в золотом цвете
    'avto': f'<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="{G}" d="M5 11l1.5-4.2A2 2 0 0 1 8.4 5.5h7.2a2 2 0 0 1 1.9 1.3L19 11a2 2 0 0 1 1.5 1.9V17a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1v-1H6.5v1a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1v-4.1A2 2 0 0 1 5 11zm2.1 0h9.8l-1.1-3.1a.6.6 0 0 0-.6-.4H8.8a.6.6 0 0 0-.6.4zM7 14.6a1.2 1.2 0 1 0 0-2.4 1.2 1.2 0 0 0 0 2.4zm10 0a1.2 1.2 0 1 0 0-2.4 1.2 1.2 0 0 0 0 2.4z"/></svg>',
    'bilety': f'<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="{G}" d="M21 15.5v-2l-8-5V3.8a1.5 1.5 0 0 0-3 0v4.7l-8 5v2l8-2.5v5l-2 1.5V21l3.5-1 3.5 1v-1.5L13 18v-5z"/></svg>',
    'kompensaciya': f'<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="{G}" d="M21 15.5v-2l-8-5V3.8a1.5 1.5 0 0 0-3 0v4.7l-8 5v2l8-2.5v5l-2 1.5V21l3.5-1 3.5 1v-1.5L13 18v-5z"/></svg>',
    'avtobus': f'<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="{G}" d="M6 3h12a2 2 0 0 1 2 2v11a2 2 0 0 1-1 1.7V20a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1v-1H8v1a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-2.3A2 2 0 0 1 4 16V5a2 2 0 0 1 2-2zm0 3v5h12V6zm1.5 7.5a1.3 1.3 0 1 0 0 2.6 1.3 1.3 0 0 0 0-2.6zm9 0a1.3 1.3 0 1 0 0 2.6 1.3 1.3 0 0 0 0-2.6z"/></svg>',
    'oteli': f'<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="{G}" d="M3 6h2v8h6V8h7a3 3 0 0 1 3 3v8h-2v-3H5v3H3zm5 3a2 2 0 1 1 0 4 2 2 0 0 1 0-4z"/></svg>',
    'esim': f'<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="{G}" d="M8 2h7l5 5v13a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm1 9v7h6v-7z"/></svg>',
    'strahovka': f'<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="{G}" d="M12 2l8 3v6c0 5-3.4 9.5-8 11-4.6-1.5-8-6-8-11V5zm-1.2 13.2l5.5-5.5-1.4-1.4-4.1 4.1-2-2-1.4 1.4z"/></svg>',
}

CSS = '''
body{background:linear-gradient(160deg,#e6f0fb 0%,#f3eefa 45%,#fdf1e8 100%) fixed;font-size:18px}
.w{max-width:1180px;padding:26px 22px 90px}
.lay{display:grid;grid-template-columns:minmax(0,1fr) 410px;gap:24px;align-items:start}
.side{position:sticky;top:18px;display:flex;flex-direction:column;gap:18px}.side .card{margin:0}
.back{background:#fff;border-radius:999px;padding:8px 18px;box-shadow:0 2px 8px rgba(22,41,74,.08);color:#16294a}
.card{border-radius:24px;box-shadow:0 10px 30px rgba(22,41,74,.08)}
article.card{padding:34px 40px;border-top:6px solid #d4a24c}
h1{font-size:36px;line-height:1.2;letter-spacing:-.3px}
.card h2{display:flex;gap:10px;align-items:center;font-size:23px}.card h2:before{content:"";width:6px;height:22px;background:#d4a24c;border-radius:3px;flex:none}
.date{display:inline-block;background:#f2f5fa;border-radius:999px;padding:4px 14px;font-size:14px}
.btn{display:flex;justify-content:center;align-items:center;gap:12px;text-decoration:none!important;text-align:center;font-weight:900;font-size:22px;line-height:1.25;border-radius:16px;padding:18px 20px;margin:0 0 18px;
 border:3px solid #d4a24c;box-shadow:inset 0 0 0 2px #0c0c0c,inset 0 0 0 3.5px rgba(255,213,74,.55),0 8px 20px rgba(0,0,0,.22);text-shadow:0 2px 0 #000,0 0 10px rgba(0,0,0,.6);letter-spacing:.2px;transition:transform .15s}
.btn svg{width:32px;height:32px;flex:none}.btn:hover{transform:translateY(-2px)}.side .btn{font-size:21px;padding:17px 14px;margin:0}
.btn.blk{background:linear-gradient(180deg,#333 0%,#111 55%,#050505 100%);color:#ffd54a}
.btn.navy{background:linear-gradient(135deg,#21418a,#16294a);color:#ffd54a;box-shadow:inset 0 0 0 2px #0e1b33,inset 0 0 0 3.5px rgba(255,213,74,.5),0 8px 20px rgba(22,41,74,.25)}
.svc{background:linear-gradient(160deg,#fff 0%,#fff3d1 100%);text-align:center;border:2px solid #d4a24c;box-shadow:inset 0 0 0 4px #fff,inset 0 0 0 5px rgba(212,162,76,.45),0 10px 30px rgba(22,41,74,.1)}
.svc .k{font-size:14px;color:#8a6d2b;font-weight:800;text-transform:uppercase;letter-spacing:1px;margin:0 0 12px}
.vid{border-top:6px solid #ff3b30}
.help{background:linear-gradient(150deg,#16294a 0%,#22437f 100%);color:#e9eef7;border:2px solid #d4a24c}
.help h2{color:#ffd54a;margin-top:0}.help h2:before{background:#ffd54a}
.help ul{list-style:none;padding:0;margin:0 0 18px}.help li{padding:6px 0 6px 30px;position:relative}.help li:before{content:"✓";position:absolute;left:4px;color:#ffd54a;font-weight:900}
.note{text-align:center;margin-top:28px}
@media(max-width:960px){.lay{grid-template-columns:1fr}.side{position:static}article.card{padding:22px 18px}h1{font-size:27px}.btn{font-size:20px;padding:16px}}
'''


def redesign(s):
    s = s.replace('</style>', CSS + '</style>', 1)
    # Telegram вверху — тёмно-синяя
    s = re.sub(r'<p style="margin:0 0 14px"><a class="go" href="(https://t\.me/[^"]+)"[^>]*>[^<]*</a></p>',
               lambda m: f'<a class="btn navy" href="{m.group(1)}" target="_blank" rel="noopener">{TG}Новости Испании каждый день — в Telegram</a>', s, count=1)
    a1 = s.index('<article'); a2 = s.index('</article>') + len('</article>')
    end = s.index('<p class="note">')
    rest = s[a2:end]
    side = []
    m = re.search(r'<a href="/go/([a-z]+)"[^>]*>(.*?) <span[^>]*>→</span></a>', rest)
    if m:
        key, label = m.group(1), m.group(2)
        side.append(f'<div class="card svc"><p class="k">Пригодится</p><a class="btn blk" href="/go/{key}" rel="sponsored noopener">{ICONS.get(key, "")}{label}</a></div>')
    w = re.search(r'href="(https://wa\.me/[^"]+)"', rest)
    if w:
        side.append('<div class="card help"><h2>Нужна помощь в Испании?</h2><ul><li>Аренда и покупка жилья</li><li>Разбор договора удалённо</li>'
                    f'<li>Проверенные юристы по ВНЖ и документам</li></ul><a class="btn blk" href="{w.group(1)}" target="_blank" rel="noopener">{WA}Написать в WhatsApp</a></div>')
    if '<h2>Видео по теме</h2>' in rest:
        v1 = rest.index('<div class="card"><h2>Видео по теме</h2>')
        v2 = rest.index('<div class="card"><h2>Нужна помощь', v1) if '<h2>Нужна помощь' in rest[v1:] else len(rest)
        side.append(rest[v1:v2].strip().replace('<div class="card">', '<div class="card vid">', 1))
    return s[:a1] + '<div class="lay">' + s[a1:a2] + '<aside class="side">\n' + '\n'.join(side) + '\n</aside></div>\n' + s[end:]


# ---------- 23.11.2026: Евгений одобрил образец — новый вид на все новости, статьи «Полезное» и страницы-списки ----------
POLEZNO_CSS = CSS + '''
.card h2:before{background:#d4a24c}.box{border-left-color:#d4a24c}
.help p{margin:0 0 16px}.help .btn+.btn{margin-top:12px}
.more h2{margin-top:0}.more a{display:block;padding:12px 0;border-bottom:1px solid #e6e9ef;text-decoration:none;font-weight:700;color:#16294a;font-size:16px;line-height:1.4}.more a:last-child{border:0}.more a:hover{color:#b8860b}
.muted{text-align:center;margin-top:28px}
'''


def redesign_polezno(s):
    s = s.replace('</style>', POLEZNO_CSS + '</style>', 1)
    a1 = s.index('<article'); a2 = s.index('</article>') + len('</article>')
    end = s.index('<p class="muted">')
    rest = s[a2:end]
    btns = []
    sp = re.search(r'<a class="go" href="(/[^"]*)">Написать специалисту</a>', rest)
    w = re.search(r'<a class="go wa" href="([^"]+)"', rest)
    t = re.search(r'<a class="go tg" href="([^"]+)"', rest)
    if w: btns.append(f'<a class="btn blk" href="{w.group(1)}" target="_blank" rel="noopener">{WA}Задать вопрос в WhatsApp</a>')
    if sp: btns.append(f'<a class="btn blk" href="{sp.group(1)}">Написать специалисту</a>')
    if t: btns.append(f'<a class="btn navy" href="{t.group(1)}" target="_blank" rel="noopener">{TG}Новости Испании в Telegram</a>')
    side = ['<div class="card help"><h2>Остались вопросы по своей ситуации?</h2><p>Напишите — дам контакт проверенного специалиста по вашему вопросу</p>' + ''.join(btns) + '</div>']
    m = re.search(r'<div class="card more">.*?</div>', rest, re.S)
    if m: side.append(m.group(0).replace(' style="margin-top:0"', ''))
    return s[:a1] + '<div class="lay">' + s[a1:a2] + '<aside class="side">\n' + '\n'.join(side) + '\n</aside></div>\n' + s[end:]


INDEX_CSS = '''
body{background:linear-gradient(160deg,#e6f0fb 0%,#f3eefa 45%,#fdf1e8 100%) fixed}
.w{max-width:980px;padding:26px 22px 90px}
.back{background:#fff;border-radius:999px;padding:8px 18px;box-shadow:0 2px 8px rgba(22,41,74,.08);color:#16294a}
.card{border-radius:24px;box-shadow:0 10px 30px rgba(22,41,74,.08)}
.card:first-of-type{border-top:6px solid #d4a24c}
h1{font-size:34px;line-height:1.2}
.card h2{display:flex;gap:10px;align-items:center}.card h2:before{content:"";width:6px;height:22px;background:#d4a24c;border-radius:3px;flex:none}
.list a{padding:16px 12px;border-radius:12px;transition:background .15s}.list a:hover{background:#fff8e6}
.btn{display:flex;justify-content:center;align-items:center;gap:12px;text-decoration:none!important;text-align:center;font-weight:900;font-size:21px;line-height:1.25;border-radius:16px;padding:16px 20px;margin:6px 0 14px;
 border:3px solid #d4a24c;background:linear-gradient(135deg,#21418a,#16294a);color:#ffd54a;box-shadow:inset 0 0 0 2px #0e1b33,inset 0 0 0 3.5px rgba(255,213,74,.5),0 8px 20px rgba(22,41,74,.25);text-shadow:0 2px 0 #000}
.btn svg{width:30px;height:30px;flex:none}
.muted,.note{text-align:center;margin-top:28px}
@media(max-width:640px){h1{font-size:26px}.btn{font-size:19px}}
'''


def redesign_index(s):
    s = s.replace('</style>', INDEX_CSS + '</style>', 1)
    s = re.sub(r'<p style="margin:0 0 12px"><a class="go" href="(https://t\.me/[^"]+)"[^>]*>([^<]*)</a></p>',
               lambda m: f'<a class="btn" href="{m.group(1)}" target="_blank" rel="noopener">{TG}{m.group(2)}</a>', s, count=1)
    return s


# ---------- 23.11.2026 (вечер): правая колонка одна для всех — меняющаяся реклама, «Нужна помощь», видео ----------
import urllib.parse as _up

ICONS['transfer'] = f'<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="{G}" d="M7 3h10v3h1.5A1.5 1.5 0 0 1 20 7.5V17a1 1 0 0 1-1 1h-1v1a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1v-1H9v1a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1v-1H5a1 1 0 0 1-1-1V7.5A1.5 1.5 0 0 1 5.5 6H7zm2 0v3h6V3zM6 9v4h12V9zm1.5 5.5a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm9 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/></svg>'
ICONS['bagazh'] = f'<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="{G}" d="M9 2h6a1 1 0 0 1 1 1v3h1a3 3 0 0 1 3 3v9a3 3 0 0 1-3 3v1h-2v-1H9v1H7v-1a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3h1V3a1 1 0 0 1 1-1zm1 2v2h4V4zM8 10v7h2v-7zm6 0v7h2v-7z"/></svg>'

# какие плашки крутим (ключ /go/<ключ>, надпись)
PROMOS = [
    ('avto', 'Аренда авто по Испании и Европе'),
    ('bilety', 'Дешёвые авиабилеты из Испании'),
    ('transfer', 'Трансфер из аэропорта по фиксированной цене'),
    ('oteli', 'Отели по всему миру'),
    ('esim', 'Интернет в поездке без роуминга'),
    ('bagazh', 'Оставить багаж в городе на пару часов'),
    ('kompensaciya', 'Задержали рейс — проверьте компенсацию'),
    ('avtobus', 'Билеты на автобусы по Испании и Европе'),
]

# видео для колонки (часы просмотра YouTube), крутим случайно
SIDE_VIDEOS = [
    ('sMPqoMeQARg', 'Год жизни в Испании с нуля: язык, документы, работа, школа'),
    ('GFh4QCWANTo', '15 штрафов в Испании, о которых узнают слишком поздно'),
    ('G_K6PE4DJ90', 'Где жить в Испании: климат и аренда в 15 городах'),
    ('aDXC1UsvBhI', 'Штрафы и аренда в Испании: 3000 € за ошибку'),
    ('C5Y5ka8njw8', 'Временная защита → ВНЖ на 4 года и ПМЖ: все пути'),
    ('6a1WSjx0vUY', 'Медицина в Испании 2026: сколько платить за лекарства и врача'),
]

SIDE_CSS = '''
.lay>article{grid-column:1;grid-row:1}.lay>.side{grid-column:2;grid-row:1}
.lay>:not(article):not(.side):not(.main){grid-column:1/-1;grid-row:2;font-size:11px;color:#8a94a0;text-align:center}
.lay>.main{grid-column:1;grid-row:1;min-width:0}
.ytb{position:relative;display:block;width:100%;border:0;padding:0;border-radius:16px;overflow:hidden;background:#000;cursor:pointer;aspect-ratio:16/9;font:inherit;text-align:left}
.ytb img{width:100%;height:100%;object-fit:cover;display:block;opacity:.85}
.ytb b{position:absolute;left:0;right:0;bottom:0;padding:26px 14px 12px;color:#fff;font-size:15px;line-height:1.35;background:linear-gradient(transparent,rgba(0,0,0,.8))}
.ytb .pl{position:absolute;left:50%;top:45%;width:64px;height:44px;margin:-22px 0 0 -32px;border-radius:12px;background:#f00}
.ytb .pl:after{content:"";position:absolute;left:26px;top:13px;border-left:16px solid #fff;border-top:9px solid transparent;border-bottom:9px solid transparent}
.ytb iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.vid h2{margin-top:0}
@media(max-width:960px){.lay>.side,.lay>.main,.lay>article{grid-column:1;grid-row:auto}}
'''
CSS += SIDE_CSS

_PROMO_JS = ('<script>(function(){var P=' + __import__('json').dumps([[k, l, ICONS.get(k, '')] for k, l in PROMOS], ensure_ascii=False) +
             ',V=' + __import__('json').dumps(SIDE_VIDEOS, ensure_ascii=False) +
             ';document.querySelectorAll(".promo").forEach(function(a){var p=P[Math.floor(Math.random()*P.length)];a.href="/go/"+p[0];a.innerHTML=p[2]+p[1]});'
             'document.querySelectorAll(".ytb[data-r]").forEach(function(b){var v=V[Math.floor(Math.random()*V.length)];b.dataset.id=v[0];b.querySelector("img").src="https://i.ytimg.com/vi/"+v[0]+"/hqdefault.jpg";b.querySelector("b").textContent=v[1]});'
             'document.querySelectorAll(".ytb").forEach(function(b){b.addEventListener("click",function(){b.innerHTML=\'<iframe src="https://www.youtube-nocookie.com/embed/\'+b.dataset.id+\'?autoplay=1&rel=0" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen title="YouTube"></iframe>\'},{once:true})})})();</script>')


def promo_card(key=None, label=None):
    """key задан — плашка по теме новости; нет — меняется при каждом заходе"""
    if key:
        return f'<div class="card svc"><p class="k">Пригодится</p><a class="btn blk" href="/go/{key}" rel="sponsored noopener">{ICONS.get(key, "")}{label}</a></div>'
    k, l = PROMOS[0]
    return f'<div class="card svc"><p class="k">Пригодится</p><a class="btn blk promo" href="/go/{k}" rel="sponsored noopener">{ICONS[k]}{l}</a></div>'


def help_card(wa_text, title='Нужна помощь в Испании?', tg=True):
    wa = 'https://wa.me/34624916605?text=' + _up.quote(wa_text)
    t = (f'<a class="btn navy" href="https://t.me/+yhlXtzU1hcU4OGNk" target="_blank" rel="noopener" style="margin-top:12px">{TG}Новости Испании в Telegram</a>' if tg else '')
    return (f'<div class="card help"><h2>{title}</h2><ul><li>Аренда и покупка жилья</li><li>Разбор договора удалённо</li>'
            f'<li>Проверенные юристы по ВНЖ и документам</li></ul><a class="btn blk" href="{wa}" target="_blank" rel="noopener">{WA}Написать в WhatsApp</a>{t}</div>')


def video_card(vid=None, name=None):
    r = '' if vid else ' data-r="1"'
    vid, name = (vid, name) if vid else SIDE_VIDEOS[0]
    return (f'<div class="card vid"><h2>Видео по теме</h2><button type="button" class="ytb"{r} data-id="{vid}" aria-label="Смотреть видео">'
            f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy"><span class="pl"></span><b>{name}</b></button></div>')


def _with_side(s, main_start, main_end, side):
    return s[:main_start] + '<div class="lay">' + s[main_start:main_end] + '<aside class="side">\n' + '\n'.join(side) + '\n</aside></div>\n' + s[main_end:]


def redesign(s):  # новость — переопределено: плашка по теме или меняющаяся
    s = s.replace('</style>', CSS + '</style>', 1)
    s = re.sub(r'<p style="margin:0 0 14px"><a class="go" href="(https://t\.me/[^"]+)"[^>]*>[^<]*</a></p>',
               lambda m: f'<a class="btn navy" href="{m.group(1)}" target="_blank" rel="noopener">{TG}Новости Испании каждый день — в Telegram</a>', s, count=1)
    a1 = s.index('<article'); a2 = s.index('</article>') + len('</article>')
    end = s.index('<p class="note">')
    rest = s[a2:end]
    m = re.search(r'<a href="/go/([a-z]+)"[^>]*>(.*?) <span[^>]*>→</span></a>', rest)
    title = re.search(r'<h1>(.*?)</h1>', s).group(1)
    side = [promo_card(m.group(1), m.group(2)) if m else promo_card(),
            help_card('Здравствуйте! Пишу с сайта, после новости «' + __import__('html').unescape(title)[:80] + '»', tg=False)]
    if '<h2>Видео по теме</h2>' in rest:
        v1 = rest.index('<div class="card"><h2>Видео по теме</h2>')
        v2 = rest.index('<div class="card"><h2>Нужна помощь', v1) if '<h2>Нужна помощь' in rest[v1:] else len(rest)
        side.append(rest[v1:v2].strip().replace('<div class="card">', '<div class="card vid">', 1))
    else:
        side.append(video_card())
    out = _with_side(s, a1, a2, side)
    a2b = out.index('</aside></div>') + len('</aside></div>\n')
    e2 = out.index('<p class="note">')
    out = out[:a2b] + out[e2:]   # старые блоки под статьёй убраны — всё в колонке
    return out.replace('</body>', _PROMO_JS + '</body>', 1)


def redesign_polezno(s):  # статья «Полезное» — переопределено
    s = s.replace('</style>', POLEZNO_CSS + SIDE_CSS + '</style>', 1)
    a1 = s.index('<article'); a2 = s.index('</article>') + len('</article>')
    end = s.index('<p class="muted">')
    rest = s[a2:end]
    title = __import__('html').unescape(re.search(r'<h1>(.*?)</h1>', s).group(1))
    side = [promo_card(), help_card('Здравствуйте! Пишу с сайта, после статьи «' + title[:80] + '»', title='Остались вопросы? Нужна помощь?')]
    vm = re.search(r'youtube-nocookie\.com/embed/([\w-]+)', s[a1:a2])
    side.append(video_card(vm.group(1), title) if vm else video_card())
    m = re.search(r'<div class="card more">.*?</div>', rest, re.S)
    if m: side.append(m.group(0).replace(' style="margin-top:0"', ''))
    out = s[:a1] + '<div class="lay">' + s[a1:a2] + '<aside class="side">\n' + '\n'.join(side) + '\n</aside></div>\n' + s[end:]
    return out.replace('</body>', _PROMO_JS + '</body>', 1)


def redesign_index(s, kind='novosti'):  # списки — переопределено: узкий список слева, колонка справа
    s = s.replace('</style>', INDEX_CSS + CSS + '.w{max-width:1180px}.lay{grid-template-columns:minmax(0,1fr) 400px}</style>', 1)
    s = re.sub(r'<p style="margin:0 0 12px"><a class="go" href="(https://t\.me/[^"]+)"[^>]*>([^<]*)</a></p>',
               lambda m: f'<a class="btn navy" href="{m.group(1)}" target="_blank" rel="noopener">{TG}{m.group(2)}</a>', s, count=1)
    b = s.index('class="back"'); b = s.index('</a>', b) + len('</a>\n')
    e = max(s.rfind('<p class="muted">'), s.rfind('<p class="note">'))
    if e < b: e = s.rindex('</div></body>')
    razdel = 'Новости' if kind == 'novosti' else 'Полезное'
    side = [promo_card(), help_card(f'Здравствуйте! Пишу с сайта, раздел «{razdel}»'), video_card()]
    out = s[:b] + '<div class="lay"><div class="main">' + s[b:e] + '</div><aside class="side">\n' + '\n'.join(side) + '\n</aside></div>\n' + s[e:]
    return out.replace('</body>', _PROMO_JS + '</body>', 1)
