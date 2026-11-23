#!/usr/bin/env python3
# Новости на сайте kalmykovgroup.com/novosti/ (решение Евгения 13.11.2026: «делай новости… это основной трафик»).
# Источник — файлы новостных задач «000 ДД.ММ тема.txt» (папки «Новости утро/день/вечер», «Длинные», «Опубликовано»).
# Запуск: novosti_build.py <папка со скачанными .txt> <файл со списком имён из «На удаление»>
# Делает: sait/novosti/<slug>.html, sait/novosti/index.html, блок «Свежие новости» на главной, sitemap.xml,
# и _ссылки_новостей.txt (имя файла → адрес статьи) на Диск + копия sait/novosti/ssylki.txt на сайте (её читает задача комментариев).
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from novosti_design2 import redesign, redesign_index
import shutil
import json, re, sys, html, datetime, zoneinfo, urllib.parse
from pathlib import Path
DRIVE = '<script data-noptimize="1" data-cfasync="false" data-wpfc-render="false">(function(){var script=document.createElement("script");script.async=1;script.setAttribute("data-cmp-ab","2");script.src=\'https://tpembars.com/NjA0ODc0.js?t=604874\';document.head.appendChild(script);})();</script>'  # 22.11.2026: Travelpayouts Drive (партнёрские ссылки на туристических страницах)

SITE = Path(__file__).resolve().parent.parent / 'sait'
NEWS = SITE / 'novosti'
DATA = NEWS / '_data.json'
BASE = 'https://kalmykovgroup.com'
TZ = zoneinfo.ZoneInfo('Europe/Madrid')
MONTHS = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']
TR = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюяіїєґ',
  ['a','b','v','g','d','e','e','zh','z','i','y','k','l','m','n','o','p','r','s','t','u','f','h','ts','ch','sh','sch','','y','','e','yu','ya','i','yi','ye','g']))
NAME_RE = re.compile(r'(?:^|\s)000 (\d{2})\.(\d{2}) (.+)\.txt$')
STAMP_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})[ _](\d{2})[-:.]?(\d{2})')

def slugify(s):
    s = ''.join(TR.get(c, c) for c in s.lower())
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:60].strip('-') or 'novost'

def key_of(name):
    m = NAME_RE.search(name)
    return f'{m.group(1)}.{m.group(2)} {m.group(3).strip()}' if m else None

def year_for(dd, mm, now):
    y = now.year
    if mm == 12 and now.month == 1: y -= 1
    if mm == 1 and now.month == 12: y += 1
    return y

def clean_title(s):
    s = re.sub(r'^[^\w«"]+', '', s.strip())   # эмодзи и мигалка в начале
    return s.rstrip('.').strip()

def parse(text):
    lines = text.replace('\r\n', '\n').replace('﻿', '').split('\n')
    meta, i = {}, 0
    while i < len(lines) and (lines[i].startswith('@') or not lines[i].strip()):
        if lines[i].startswith('@') and ':' in lines[i]:
            k, v = lines[i][1:].split(':', 1); meta[k.strip()] = v.strip()
        i += 1
    body = lines[i:]
    # @threads+ и всё после — не для сайта
    for j, l in enumerate(body):
        if l.strip().startswith('@threads+'): body = body[:j]; break
    body = [l for l in body if not l.startswith('@')]
    head = body[0].strip() if body else ''
    paras, cur = [], []
    for l in body[1:]:
        if l.strip(): cur.append(l.strip())
        elif cur: paras.append(cur); cur = []
    if cur: paras.append(cur)
    return meta, head, paras

def esc(s): return html.escape(s, quote=True)

def parse_extra(text):
    """Файл «Новости сайт/ДД.ММ тема.txt»: разделы @что делать: / @подробнее: / @источники: (строки «ссылка | название»)"""
    sec, out = None, {'todo': [], 'more': [], 'src': []}
    cur = []
    def flush():
        if sec == 'more' and cur: out['more'].append(cur[:])
    for l in text.replace('\r\n', '\n').replace('\ufeff', '').split('\n'):
        t = l.strip()
        low = t.lower()
        if low.startswith('@что делать'): flush(); cur = []; sec = 'todo'; continue
        if low.startswith('@подробнее'): flush(); cur = []; sec = 'more'; continue
        if low.startswith('@источники'): flush(); cur = []; sec = 'src'; continue
        if not t:
            flush(); cur = []; continue
        if sec == 'todo': out['todo'].append(t.lstrip('-•–— ').strip())
        elif sec == 'more': cur.append(t)
        elif sec == 'src':
            url, _, name = t.partition('|')
            url = url.strip()
            if url.startswith('http'): out['src'].append([url, name.strip() or urllib.parse.urlparse(url).netloc])
    flush()
    return out if any(out.values()) else None

CSS = """*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:#16233a;font:17px/1.7 Manrope,Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.w{max-width:760px;margin:0 auto;padding:20px 16px 90px}a{color:#2f6fd6}
.back{display:inline-block;margin-bottom:14px;font-weight:700;text-decoration:none}
.card{background:#fff;border-radius:20px;padding:26px;box-shadow:0 2px 10px rgba(22,41,74,.07);margin-bottom:16px}
h1{font-size:28px;line-height:1.25;color:#16294a;margin:0 0 8px}h2{font-size:20px;color:#16294a;margin:0 0 10px}
.date{color:#5f6b7a;font-size:14px;margin:0 0 18px}.card p{margin:0 0 16px}.card p:last-child{margin:0}
.go{display:flex;justify-content:center;align-items:center;gap:8px;background:#ff6b4a;color:#fff;font-weight:700;text-decoration:none;border-radius:14px;padding:15px;font-size:16px;box-shadow:0 5px 0 #c94a2f;margin-top:14px}
.list a{display:block;text-decoration:none;color:#16233a;padding:14px 0;border-bottom:1px solid #dde3ea}.list a:last-child{border:0}
.list b{display:block;color:#16294a;font-size:17px;line-height:1.35}.list span{color:#5f6b7a;font-size:13px}
.note{font-size:13px;color:#64707b}.card h2{margin:24px 0 10px}.card ol,.card ul{margin:0 0 16px;padding-left:22px}.card li{margin:6px 0}.src{font-size:15px}
.yt{position:relative;display:block;width:100%;border:0;padding:0;border-radius:16px;overflow:hidden;background:#000;cursor:pointer;aspect-ratio:16/9;font:inherit;text-align:left}
.yt img{width:100%;height:100%;object-fit:cover;display:block;opacity:.85}
.yt b{position:absolute;left:0;right:0;bottom:0;padding:26px 14px 12px;color:#fff;font-size:15px;line-height:1.35;background:linear-gradient(transparent,rgba(0,0,0,.8))}
.yt .play{position:absolute;left:50%;top:45%;width:64px;height:44px;margin:-22px 0 0 -32px;border-radius:12px;background:#f00}
.yt .play::after{content:"";position:absolute;left:26px;top:13px;border-left:16px solid #fff;border-top:9px solid transparent;border-bottom:9px solid transparent}
.yt iframe{width:100%;height:100%;border:0;display:block}
.card>h2:first-child{margin-top:0}
@media (max-width:600px){h1{font-size:23px}.card{padding:18px}}"""

# 16.11.2026: под каждой новостью — лонг по теме (часы просмотра YouTube для монетизации).
# Первое совпадение по ключам в заголовке и тексте; иначе — «Год жизни в Испании с нуля».
VIDEOS = [
    (('врач', 'медицин', 'больниц', 'лекарств', 'аптек', 'sip', 'пациент'), '6a1WSjx0vUY', 'Медицина в Испании 2026: сколько платить за лекарства и врача'),
    (('временную защит', 'временной защит', 'временная защит', 'внж', 'nie', 'tie', 'беженц', 'украинц', 'резиденц', 'extranjer'), 'C5Y5ka8njw8', 'Временная защита → ВНЖ на 4 года и ПМЖ: все пути'),
    (('аренд', 'съём', 'съем', 'квартир', 'жиль', 'залог', 'депозит', 'арендатор', 'хозя', 'собственник', 'ипотек'), 'aDXC1UsvBhI', 'Штрафы и аренда в Испании: 3000 € за ошибку'),
    (('штраф', 'dgt', 'дорожн', 'на дорог', 'водител', 'машин', 'авто', 'полици', 'парков', 'бензин', 'топлив'), 'GFh4QCWANTo', '15 штрафов в Испании, о которых узнают слишком поздно'),
    (('город', 'климат', 'погод', 'переезд', 'где жить', 'жара', 'холод', 'зим'), 'G_K6PE4DJ90', 'Где жить в Испании: климат и аренда в 15 городах'),
]
VIDEO_DEFAULT = ('sMPqoMeQARg', 'Год жизни в Испании с нуля: язык, документы, работа, школа')

# 17.11.2026: под видео — строка «Подробно — в гайде» (бесплатные гайды с PDF, kalmykovgroup.com/gaidy/)
GUIDES = {
    'C5Y5ka8njw8': ('vnzh-posle-vremennoy-zashchity', 'ВНЖ после временной защиты'),
    'aDXC1UsvBhI': ('lovushki-arendy-v-ispanii', 'Ловушки аренды в Испании'),
    'GFh4QCWANTo': ('shtrafy-v-ispanii', 'Штрафы в Испании'),
    'G_K6PE4DJ90': ('gde-zhit-v-ispanii-klimat-i-arenda', 'Где жить в Испании: климат и аренда'),
}

def guide_html(vid):
    g = GUIDES.get(vid)
    if not g: return ''
    return f'<p class="note" style="margin-top:12px">Подробно и с PDF — в бесплатном гайде <a href="/gaidy/{g[0]}">«{esc(g[1])}»</a></p>'

def pick_video(it):
    text = (it['title'] + ' ' + ' '.join(' '.join(p) for p in it['paras'])).lower()
    title = it['title'].lower()
    for keys, vid, name in VIDEOS:      # сначала по заголовку
        if any(k in title for k in keys): return vid, name
    for keys, vid, name in VIDEOS[:4]:  # потом по тексту (климат/города — только по заголовку)
        if any(k in text for k in keys): return vid, name
    return VIDEO_DEFAULT

YT_JS = """<script>document.querySelectorAll('.yt').forEach(function(b){b.addEventListener('click',function(){b.innerHTML='<iframe src="https://www.youtube-nocookie.com/embed/'+b.dataset.id+'?autoplay=1&rel=0" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen title="YouTube"></iframe>'},{once:true})});</script>"""

def wa(text):
    return 'https://wa.me/34624916605?text=' + urllib.parse.quote(text)

def page(title, desc, canon, body, extra=''):
    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{BASE}/og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta property="og:url" content="{canon}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0a0a0d">
<script src="/pwa.js" defer></script>
<style>{CSS}</style>{extra}{DRIVE}</head>
<body><div class="w">
{body}
</div></body></html>
"""

def human_date(iso):
    d = datetime.datetime.fromisoformat(iso)
    return f'{d.day} {MONTHS[d.month-1]} {d.year}'

# 22.11.2026: строка с услугой по теме новости (как в Telegram-канале и комментариях Facebook) — через наши короткие ссылки /go/<услуга>
SVC = [
    (r'(отмен|задерж)\S*.{0,15}(рейс|вылет)|забаст\S*.{0,40}(аэропорт|авиа|пилот|ryanair|vueling|iberia)', 'kompensaciya', 'Задержали или отменили рейс — проверьте, положена ли компенсация'),
    (r'рейс|самол[её]т|аэропорт|авиа|лоукост|ryanair|vueling|iberia|wizz', 'bilety', 'Дешёвые авиабилеты из Испании'),
    (r'поезд|железн|электрич|автобус|renfe|\bave\b', 'avtobus', 'Билеты на автобусы по Испании и Европе'),
    (r'машин|авто|водител|дтп|\bdgt\b|прав[ао]? |бензин|трасс|itv|парков', 'avto', 'Аренда авто по Испании и Европе'),
    (r'страхов|аренд|квартир|жиль|ипотек|хозяин|жилец|недвижим|окупас|комунидад', 'strahovka', 'Страховка квартиры, здоровья, жизни — напишите специалисту'),
    (r'роуминг|мобильн|связь|интернет|сим-карт|\besim\b', 'esim', 'Интернет в поездке без роуминга'),
    (r'отпуск|турист|туризм|отел|путешеств|праздник|пасх|рождеств', 'oteli', 'Отели по всему миру'),
]
# 23.11.2026 (Евгений): кнопка как на главной — чёрный глянец, золотая надпись и золотая окантовка, без эмодзи;
# «Реклама» — маленькими буквами внизу страницы (SVC_NOTE в строке .note), а не у кнопки
SVC_STYLE = ('display:flex;justify-content:center;align-items:center;gap:10px;background:linear-gradient(180deg,#2b2b2b,#0c0c0c);'
             'color:#ffcf40;border:2px solid #d4a24c;border-radius:14px;padding:15px 18px;font-weight:800;font-size:16px;'
             'text-decoration:none;text-align:center;box-shadow:0 6px 16px rgba(0,0,0,.25)')
SVC_NOTE = '<br><span style="font-size:11px;color:#8a94a0">Реклама. Ссылка на сервис партнёрская, для вас цена такая же, как на его сайте</span>'
def svc_card(key, label):
    return f'<div class="card"><a href="/go/{key}" rel="sponsored noopener" style="{SVC_STYLE}">{esc(label)} <span style="color:#d4a24c">→</span></a></div>\n'
def svc_html(it):
    t = (it['title'] + ' ' + it.get('desc', '')).lower()
    for rx, key, label in SVC:
        if re.search(rx, t):
            return svc_card(key, label)
    return ''

def article_html(it):
    paras = ''.join('<p>' + '<br>'.join(esc(x) for x in p) + '</p>' for p in it['paras'])
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": it['title'][:110],
          "datePublished": it['published'], "dateModified": it['published'], "inLanguage": "ru",
          "image": [f'{BASE}/og.jpg'], "mainEntityOfPage": f"{BASE}/novosti/{it['slug']}",
          "author": {"@type": "Person", "name": "Ievgen Kalmykov", "alternateName": "Евгений Калмыков", "url": BASE + '/'},
          "publisher": {"@type": "Organization", "name": "Kalmykov Group", "url": BASE + '/',
                        "logo": {"@type": "ImageObject", "url": f'{BASE}/favicon.svg'}},
          "description": it['desc']}
    extra = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>'
    ex = it.get('extra') or {}
    if ex.get('more'):
        paras += '<h2>Подробнее</h2>' + ''.join('<p>' + '<br>'.join(esc(x) for x in p) + '</p>' for p in ex['more'])
    if ex.get('todo'):
        paras += '<h2>Что делать</h2><ol>' + ''.join(f'<li>{esc(x)}</li>' for x in ex['todo']) + '</ol>'
    if ex.get('src'):
        paras += '<h2>Источники</h2><ul class="src">' + ''.join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener nofollow">{esc(n)}</a></li>' for u, n in ex['src']) + '</ul>'
    vid, vname = pick_video(it)
    svc = svc_html(it)
    body = f"""<a class="back" href="/novosti/">← Все новости Испании</a>
<article class="card"><h1>{esc(it['title'])}</h1><p class="date">{human_date(it['published'])} · Евгений Калмыков, Валенсия</p>
<p style="margin:0 0 14px"><a class="go" href="https://t.me/+yhlXtzU1hcU4OGNk" target="_blank" rel="noopener" style="background:#2aa1da">📰 Новости Испании каждый день — в Telegram</a></p>
{paras}</article>
{svc}<div class="card"><h2>Видео по теме</h2><button type="button" class="yt" data-id="{vid}" aria-label="Смотреть: {esc(vname)}"><img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy"><span class="play"></span><b>{esc(vname)}</b></button>{guide_html(vid)}</div>
<div class="card"><h2>Нужна помощь в Испании?</h2><p>Аренда и покупка жилья, разбор договора удалённо, проверенные юристы по ВНЖ и документам. Напишите, что у вас за ситуация</p>
<a href="{wa('Здравствуйте! Пишу с сайта, после новости «' + it['title'][:80] + '»')}" target="_blank" rel="noopener" style="{SVC_STYLE};margin-top:14px">Написать в WhatsApp</a></div>
<p class="note"><a href="https://t.me/+yhlXtzU1hcU4OGNk" target="_blank" rel="noopener">Новости Испании каждый день — в Telegram-канале</a> · <a href="/">kalmykovgroup.com</a> · все соцсети и проверенные специалисты{SVC_NOTE if svc else ''}</p>
{YT_JS}"""
    if it.get('img'):   # 17.11.2026: фото из Facebook — вверху статьи и в превью соцсетей и Telegram
        body = body.replace(f"<article class=\"card\"><h1>", f"<article class=\"card\"><img src=\"{it['img']}\" alt=\"\" style=\"width:100%;border-radius:12px;margin:0 0 14px;display:block\" loading=\"lazy\"><h1>", 1)
    html_ = page(it['title'] + ' — новости Испании', it['desc'], f"{BASE}/novosti/{it['slug']}", body, extra)
    if it.get('img'):
        html_ = html_.replace(f'content="{BASE}/og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">', f'content="{BASE}{it["img"]}">')
        html_ = html_.replace(f"\"image\": [\"{BASE}/og.jpg\"]", f"\"image\": [\"{BASE}{it['img']}\"]")
    return html_

def index_html(items):
    rows = ''.join(f'<a href="/novosti/{it["slug"]}"><b>{esc(it["title"])}</b><span>{human_date(it["published"])}</span></a>' for it in items)
    body = f"""<a class="back" href="/">← Евгений Калмыков · главная</a>
<div class="card"><h1>Новости Испании</h1><p class="date">Жильё, аренда, ВНЖ и документы, деньги, транспорт — каждый день простыми словами</p>
<p style="margin:0 0 12px"><a class="go" href="https://t.me/+yhlXtzU1hcU4OGNk" target="_blank" rel="noopener" style="background:#2aa1da">Все новости в Telegram-канале</a></p>
<div class="list">{rows or '<p>Скоро здесь будут новости</p>'}</div></div>"""
    return page('Новости Испании — жильё, ВНЖ, деньги, законы | Евгений Калмыков',
                'Свежие новости Испании простыми словами: аренда и цены на жильё, ВНЖ и документы, деньги, законы, транспорт. Каждый день',
                f'{BASE}/novosti/', body)

def update_home(items):
    p = SITE / 'index.html'
    s = p.read_text(encoding='utf-8')
    a, b = '<!--novosti-->', '<!--/novosti-->'
    rows = ''.join(f'<li><a href="/novosti/{it["slug"]}">{esc(it["title"])}</a></li>' for it in items[:5])
    block = (f'{a}<section class="newsbox" style="background:var(--surface);border-radius:20px;padding:20px 24px">'
             f'<h2 style="margin:0 0 10px;font-family:var(--display);font-size:20px">Новости Испании</h2>'
             f'<ul style="margin:0;padding-left:20px;line-height:1.6">{rows}</ul>'
             f'<p style="margin:12px 0 0"><a href="/novosti/" style="font-weight:700">Все новости →</a> · <a href="https://t.me/+yhlXtzU1hcU4OGNk" target="_blank" rel="noopener" style="font-weight:700">Новости каждый день в Telegram →</a></p></section>{b}')
    if a in s:
        s = re.sub(re.escape(a) + '.*?' + re.escape(b), lambda m: block, s, flags=re.S)
    elif items:
        s = s.replace('  <footer>', '  ' + block + '\n  <footer>', 1)
    p.write_text(s, encoding='utf-8')

def update_sitemap(items):
    p = SITE / 'sitemap.xml'
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'\s*<url><loc>https://kalmykovgroup\.com/novosti/[^<]*</loc>.*?</url>', '', s)
    add = f'\n  <url><loc>{BASE}/novosti/</loc><lastmod>{items[0]["published"][:10] if items else "2026-11-13"}</lastmod></url>'
    add += ''.join(f'\n  <url><loc>{BASE}/novosti/{it["slug"]}</loc><lastmod>{it["published"][:10]}</lastmod></url>' for it in items)
    s = re.sub(r'\s*</urlset>\s*$', '', s)  # 21.11.2026: строка /montazh/ шла вплотную к </urlset> — новости в карту не попадали
    s = s + add + '\n</urlset>\n'
    p.write_text(s, encoding='utf-8')

# 17.11.2026: фото новости — то же, что робот поставил в Facebook. Робот пишет в журнал строку
# «ТЕКСТ … «<первые 50 знаков заголовка>» | фото: <имя>», фото после выхода лежит в «Брокер/Посты/Фото/использованные».
# Workflow кладёт хвост журнала в zhurnal.txt; здесь находим имя фото и копируем его (rclone) в sait/novosti/img/<slug>.jpg.
import subprocess
LOG_RE = re.compile(r'ТЕКСТ \S+ \S+ «(.+)» \| фото: (.+?) →')
def _norm(s): return re.sub(r'[^0-9a-zа-яё]+', '', clean_title(s).lower())
def attach_photos(data, zhurnal='zhurnal.txt'):
    if not Path(zhurnal).exists(): return False
    pairs = []
    for line in Path(zhurnal).read_text(encoding='utf-8', errors='replace').splitlines():
        m = LOG_RE.search(line)
        if m: pairs.append((_norm(m.group(1)), m.group(2).strip()))
    changed = False
    (NEWS / 'img').mkdir(exist_ok=True)
    for it in data.values():
        if it.get('img'): continue
        t = _norm(it['title'])
        name = next((ph for head, ph in reversed(pairs) if len(head) >= 15 and t.startswith(head[:40])), None)
        if not name: continue
        out = NEWS / 'img' / f"{it['slug']}.jpg"
        try:
            subprocess.run(['rclone', 'copyto', f'montazh:Брокер/Посты/Фото/использованные/{name}', '/tmp/ph_src'], check=True, timeout=120)
            try:
                from PIL import Image, ImageOps
                im = ImageOps.exif_transpose(Image.open('/tmp/ph_src')).convert('RGB')
                im.thumbnail((1200, 1200))
                im.save(str(out), 'JPEG', quality=82, optimize=True)
            except Exception as e2:
                print('сжать не вышло, кладу как есть:', str(e2)[:80])
                shutil.copyfile('/tmp/ph_src', str(out))
            it['img'] = f"/novosti/img/{it['slug']}.jpg"; it['photo'] = name; changed = True
            # 17.11.2026: горизонтальная копия 16:9 для Telegram-канала (фото на всю ширину, без белых полос)
            try:
                from PIL import Image
                (NEWS / 'img-wide').mkdir(exist_ok=True)
                im = Image.open(str(out)); w, h = im.size; nh = int(w * 9 / 16)
                if nh > h:
                    nw = int(h * 16 / 9); l = (w - nw) // 2; c = im.crop((l, 0, l + nw, h))
                else:
                    t = (h - nh) // 2; c = im.crop((0, t, w, t + nh))
                c.convert('RGB').save(str(NEWS / 'img-wide' / f"{it['slug']}.jpg"), 'JPEG', quality=86)
            except Exception as e3:
                print('широкое фото не вышло:', str(e3)[:80])
            print('фото', it['slug'], '←', name)
        except Exception as e:
            print('фото не взял', it['slug'], name, str(e)[:120])
    return changed

def main(src_dir, removed_list, extra_dir=None):
    now = datetime.datetime.now(TZ)
    NEWS.mkdir(parents=True, exist_ok=True)
    data = json.loads(DATA.read_text(encoding='utf-8')) if DATA.exists() else {}
    removed = set()
    if removed_list and Path(removed_list).exists():
        for n in Path(removed_list).read_text(encoding='utf-8').splitlines():
            k = key_of(n.strip().split('/')[-1])
            if k: removed.add(k)
    changed = False
    for k in list(data):
        it = data[k]
        age = now - datetime.datetime.fromisoformat(it['published'])
        if k in removed and age < datetime.timedelta(days=3):
            (NEWS / f"{it['slug']}.html").unlink(missing_ok=True); del data[k]; changed = True
            print('убрана', k)
    used = {it['slug'] for it in data.values()}
    for f in sorted(Path(src_dir).glob('*.txt')):
        k = key_of(f.name)
        if not k or k in data or k in removed: continue
        m = NAME_RE.search(f.name)
        dd, mm = int(m.group(1)), int(m.group(2))
        y = year_for(dd, mm, now)
        sm = STAMP_RE.match(f.name)
        if sm:
            pub = datetime.datetime(int(sm[1]), int(sm[2]), int(sm[3]), int(sm[4]), int(sm[5]), tzinfo=TZ)
        else:
            pub = now.replace(second=0, microsecond=0)
            if (pub.month, pub.day) != (mm, dd): pub = datetime.datetime(y, mm, dd, 12, 0, tzinfo=TZ)
        if now - pub > datetime.timedelta(days=10): continue   # старьё не тащим
        meta, head, paras = parse(f.read_text(encoding='utf-8', errors='replace'))
        if not head or not paras: continue
        title = clean_title(head)
        first = ' '.join(paras[0])
        desc = first if len(first) <= 155 else first[:152].rsplit(' ', 1)[0] + '…'
        slug = f'{y}-{mm:02d}-{dd:02d}-' + slugify(re.sub(r'^\d+\s+\S+:\s*', '', title) or m.group(3))
        base, n = slug, 2
        while slug in used: slug = f'{base}-{n}'; n += 1
        used.add(slug)
        data[k] = {'slug': slug, 'title': title, 'desc': desc, 'published': pub.isoformat(), 'paras': paras,
                   'source': f.name, 'emo': meta.get('значок', '').strip()}
        changed = True
        print('новая', k, '→', slug)
    if extra_dir and Path(extra_dir).exists():
        for f in Path(extra_dir).glob('*.txt'):
            m = re.match(r'(?:000 )?(\d{2}\.\d{2} .+)\.txt$', f.name)
            if not m or m.group(1).strip() not in data: continue
            ex = parse_extra(f.read_text(encoding='utf-8', errors='replace'))
            k = m.group(1).strip()
            if ex and data[k].get('extra') != ex:
                data[k]['extra'] = ex; changed = True; print('дополнено', k)
    if attach_photos(data): changed = True
    items = sorted(data.values(), key=lambda x: x['published'], reverse=True)
    for it in items:
        _h = redesign(article_html(it))   # 23.11.2026: новый вид для всех новостей (tools/novosti_design2.py)
        (NEWS / f"{it['slug']}.html").write_text(_h, encoding='utf-8')
    (NEWS / 'index.html').write_text(redesign_index(index_html(items)), encoding='utf-8')
    update_home(items); update_sitemap(items)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    links = ['обновлено ' + now.strftime('%Y-%m-%d %H:%M'), 'формат: ключ файла (ДД.ММ тема) | адрес статьи на сайте']
    links[1] = 'формат: ключ файла (ДД.ММ тема) | адрес статьи на сайте | полная (есть источники и «что делать») или коротко'
    links += [f"{k} | {BASE}/novosti/{data[k]['slug']} | {'полная' if data[k].get('extra') else 'коротко'}" for k in sorted(data, key=lambda k: data[k]['published'], reverse=True)[:40]]
    Path('_ссылки_новостей.txt').write_text('\n'.join(links) + '\n', encoding='utf-8')
    # 14.11.2026: тот же список на сайте — https://kalmykovgroup.com/novosti/ssylki.txt (поиск Google Диска
    # не видит файлы, записанные rclone, поэтому задача комментариев читает ссылки отсюда). Без строки «обновлено»,
    # чтобы файл менялся только с новой статьёй и не запускал лишнюю сборку Cloudflare.
    (NEWS / 'ssylki.txt').write_text('\n'.join(links[1:]) + '\n', encoding='utf-8')
    print('изменения' if changed else 'без изменений')
    # 22.11.2026: украинская главная — копия русской с переводом (tools/ua_build.py)
    try:
        import ua_build; ua_build.build()
    except Exception as e: print('ua_build:', e)
    try:  # 22.11.2026: /en/ и /es/ берут дизайн блока «Поездки» из index.html
        import intl_build; intl_build.main()
    except Exception as e: print('intl_build:', e)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, sys.argv[3] if len(sys.argv) > 3 else None)
