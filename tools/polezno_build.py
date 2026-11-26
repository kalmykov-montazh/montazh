#!/usr/bin/env python3
# Раздел «Полезное» на сайте kalmykovgroup.com/polezno/ (решение Евгения 21.11.2026: «да, и задачу под статьи»).
# Статья = ответ на вопрос, который люди ищут в Google годами (не новость). Делаются из снятых роликов и постов.
# Источник: sait/polezno/_src/<адрес>.md — шапка «ключ: значение» до строки «---», дальше текст:
#   «## Заголовок», абзацы через пустую строку, «- пункт», «1. шаг», «> жёлтая плашка», **жирный**, [текст](ссылка)
# Ключи шапки: title, description, date (ГГГГ-ММ-ДД), tema (Аренда/Документы/Деньги/Транспорт/Жизнь…),
#   partner (адрес страницы партнёра без «/», например yuristy — кнопка появится, когда страница есть), video (id YouTube)
# Запуск: python3 tools/polezno_build.py — делает страницы, список /polezno/, блок «Полезное» на главной, sitemap.xml
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from novosti_design2 import redesign_polezno, redesign_index  # 23.11.2026 новый вид
import re, html, json, datetime, urllib.parse
from pathlib import Path
DRIVE = ''  # 23.11.2026: Travelpayouts Drive ОТКЛЮЧЁН — перекидывал людей на Яндекс Путешествия (Targeted Offers). Не возвращать

SITE = Path(__file__).resolve().parent.parent / 'sait'
DIR = SITE / 'polezno'
SRC = DIR / '_src'
BASE = 'https://kalmykovgroup.com'
TG_SITE = 'https://t.me/+yhlXtzU1hcU4OGNk'   # пригласительная «Сайт» канала новостей
MONTHS = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']
GAIDY = [  # большие гайды с PDF (раздел /gaidy/, делались вручную)
    ('/gaidy/shtrafy-v-ispanii', 'Штрафы в Испании: 15 самых частых'),
    ('/gaidy/vnzh-posle-vremennoy-zashchity', 'Временная защита → ВНЖ на 4 года'),
    ('/gaidy/lovushki-arendy-v-ispanii', '17 ловушек аренды'),
    ('/gaidy/pochemu-slozhno-snyat-kvartiru-v-ispanii', 'Почему сложно снять квартиру'),
    ('/gaidy/gde-zhit-v-ispanii-klimat-i-arenda', 'Где жить: климат и цены аренды'),
]

def esc(s): return html.escape(s, quote=True)

def inline(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    def link(m):
        url = html.unescape(m.group(2))
        ext = url.startswith('http') and 'kalmykovgroup.com' not in url
        return f'<a href="{esc(url)}"' + (' target="_blank" rel="noopener"' if ext else '') + f'>{m.group(1)}</a>'
    return re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', link, s)

def parse(path):
    text = path.read_text(encoding='utf-8').replace('\r\n', '\n').replace('﻿', '')
    head, _, body = text.partition('\n---\n')
    meta = {}
    for l in head.split('\n'):
        if ':' in l:
            k, v = l.split(':', 1); meta[k.strip().lower()] = v.strip()
    meta['slug'] = path.stem
    meta['body'] = body.strip()
    meta.setdefault('tema', 'Жизнь')
    meta.setdefault('date', datetime.date.today().isoformat())
    return meta

def render(body):
    out, block, kind = [], [], None
    def flush():
        nonlocal block, kind
        if not block: return
        if kind == 'p': out.append('<p>' + '<br>'.join(inline(x) for x in block) + '</p>')
        elif kind == 'ul': out.append('<ul>' + ''.join(f'<li>{inline(x)}</li>' for x in block) + '</ul>')
        elif kind == 'ol': out.append('<ol class="steps">' + ''.join(f'<li>{inline(x)}</li>' for x in block) + '</ol>')
        elif kind == 'box': out.append('<div class="box">' + '<br>'.join(inline(x) for x in block) + '</div>')
        block, kind = [], None
    for raw in body.split('\n'):
        l = raw.strip()
        if not l: flush(); continue
        if l.startswith('### '): flush(); out.append(f'<h3>{inline(l[4:])}</h3>'); continue  # 26.11.2026: вопросы FAQ
        if l.startswith('## '): flush(); out.append(f'<h2>{inline(l[3:])}</h2>'); continue
        m = re.match(r'^(- |• |\d+[.)] |> )(.*)', l)
        k = {'- ': 'ul', '• ': 'ul', '> ': 'box'}.get(m.group(1), 'ol') if m else 'p'
        if k != kind: flush(); kind = k
        block.append(m.group(2) if m else l)
    flush()
    return '\n'.join(out)

FAQ_RE = re.compile(r'(частые вопросы|часто задаваемые|часті питання|поширені питання|faq|frequently asked|preguntas frecuentes)', re.I)

def faq_ld(body):
    # 26.11.2026 (SEO, решение Евгения «раскручиваем через Google»): блок «## Частые вопросы» + «### Вопрос» + ответ
    # превращается в разметку FAQPage — Google может показывать вопросы прямо в выдаче
    qa, on, q, ans = [], False, None, []
    def push():
        if q and ans: qa.append({'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': ' '.join(ans)}})
    for raw in body.split('\n'):
        l = raw.strip()
        if l.startswith('## ') and not l.startswith('### '):
            push(); q, ans = None, []; on = bool(FAQ_RE.search(l)); continue
        if not on: continue
        if l.startswith('### '): push(); q, ans = re.sub(r'\*\*', '', l[4:]).strip(), []; continue
        if l and q:
            t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', re.sub(r'\*\*', '', re.sub(r'^(- |• |\d+[.)] |> )', '', l)))
            ans.append(t)
    push()
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': qa} if len(qa) >= 2 else None

MONTHS_UA = ['січня','лютого','березня','квітня','травня','червня','липня','серпня','вересня','жовтня','листопада','грудня']

def date_ru(iso, lang='ru'):
    d = datetime.date.fromisoformat(iso[:10]); return f'{d.day} {(MONTHS_UA if lang == "uk" else MONTHS)[d.month-1]} {d.year}'

def wa(text): return 'https://wa.me/34624916605?text=' + urllib.parse.quote(text)

CSS = '''*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:#16233a;font:17px/1.65 Manrope,Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.w{max-width:820px;margin:0 auto;padding:20px 16px 90px}a{color:#2f6fd6}.back{display:inline-block;margin-bottom:14px;font-weight:700;text-decoration:none}
.card{background:#fff;border-radius:20px;padding:26px;box-shadow:0 2px 10px rgba(22,41,74,.07);margin-bottom:16px}
h1{font-size:28px;line-height:1.25;color:#16294a;margin:0 0 8px}.card h2{font-size:21px;color:#16294a;margin:26px 0 10px;display:flex;gap:9px;align-items:center}
.card h2:before{content:"";width:6px;height:18px;background:#f5c518;border-radius:2px;flex:none}.date{color:#5f6b7a;font-size:14px;margin:0 0 16px}
.card h3{font-size:18px;color:#16294a;margin:18px 0 6px}.lead{font-size:18px}.card p{margin:0 0 14px}.steps{padding-left:22px}.card li{margin:6px 0}
.box{background:#fff8db;border-left:5px solid #f5c518;padding:14px 16px;margin:12px 0 16px;border-radius:6px}
.tag{display:inline-block;background:#eef2f8;color:#16294a;border-radius:999px;padding:2px 12px;font-size:13px;font-weight:700;text-decoration:none;margin-bottom:10px}
.cta2{background:#16294a;color:#fff;border-radius:20px;padding:24px;margin:16px 0}.cta2 b{display:block;font-size:20px;margin-bottom:8px;color:#f5c518}
.btns{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}.go{display:inline-flex;align-items:center;justify-content:center;gap:8px;background:#ff6b4a;color:#fff;font-weight:700;text-decoration:none;border-radius:14px;padding:14px 18px;box-shadow:0 5px 0 #c94a2f}
.go.tg{background:#2aa1da;box-shadow:0 5px 0 #1b78a6}.go.wa{background:#25d366;box-shadow:0 5px 0 #179c4a}
.more a{display:block;padding:12px 0;border-bottom:1px solid #dde3ea;text-decoration:none;font-weight:700;color:#16294a}.more a:last-child{border:0}
.yt{position:relative;padding-top:56.25%;border-radius:14px;overflow:hidden;margin:6px 0 14px}.yt iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.muted{color:#64707b;font-size:14px}.list a{display:block;padding:12px 0;border-bottom:1px solid #dde3ea;text-decoration:none;color:#16294a}.list a b{display:block}.list a span{color:#64707b;font-size:14px}
@media (max-width:640px){h1{font-size:23px}.card{padding:18px}}'''

def head(title, desc, canon, ld, alts=''):
    return (f'<!doctype html>\n<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">\n'
            f'<link rel="canonical" href="{canon}">{alts}<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">\n'
            f'<meta property="og:image" content="{BASE}/og.jpg"><meta name="twitter:card" content="summary_large_image"><meta property="og:url" content="{canon}">\n'
            '<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="#0a0a0d"><script src="/pwa.js" defer></script>\n'
            f'<style>{CSS}</style><script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>{DRIVE}</head>\n')

UA_SRC = DIR / '_src_ua'   # 26.11.2026: украинские версии статей (тот же адрес файла, что у русской)

def alt_links(a, ua_ok):
    # hreflang между языками одной статьи: ru /polezno/<a>, uk /polezno/ua/<a>, en/es по alt_en / alt_es
    al = {'ru': f'{BASE}/polezno/{a["slug"]}'}
    if ua_ok: al['uk'] = f'{BASE}/polezno/ua/{a["slug"]}'
    if a.get('alt_en'): al['en'] = f'{BASE}/en/guides/{a["alt_en"]}'
    if a.get('alt_es'): al['es'] = f'{BASE}/es/guias/{a["alt_es"]}'
    if len(al) < 2: return ''
    return ''.join(f'<link rel="alternate" hreflang="{k}" href="{v}">' for k, v in al.items())

def article(a, items, lang='ru', ua_ok=False):
    canon = f'{BASE}/polezno/{a["slug"]}' if lang == 'ru' else f'{BASE}/polezno/ua/{a["slug"]}'
    ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': a['title'][:110], 'description': a.get('description', ''),
          'datePublished': a['date'], 'dateModified': a.get('updated', a['date']), 'inLanguage': 'uk' if lang == 'uk' else 'ru',
          'author': {'@type': 'Person', 'name': 'Ievgen Kalmykov', 'url': BASE + '/'},
          'publisher': {'@type': 'Organization', 'name': 'Kalmykov Group', 'url': BASE + '/'}, 'mainEntityOfPage': canon}
    fq = faq_ld(a['body'])
    if fq: ld = [ld, fq]
    video = f'<div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/{esc(a["video"])}" title="{esc(a["title"])}" loading="lazy" allowfullscreen></iframe></div>' if a.get('video') else ''
    btns = []
    p = a.get('partner', '').strip('/ ')
    if p and ((SITE / p).is_dir() or (SITE / f'{p}.html').exists()):
        btns.append(f'<a class="go" href="/{esc(p)}">Написать специалисту</a>')
    btns.append(f'<a class="go wa" href="{esc(wa("Здравствуйте! Пишу с сайта, после статьи «" + a["title"] + "»"))}" target="_blank" rel="noopener">Задать вопрос в WhatsApp</a>')
    btns.append(f'<a class="go tg" href="{TG_SITE}" target="_blank" rel="noopener">Новости Испании в Telegram</a>')
    # 23.11.2026 (Евгений): строку «Реклама…» не показываем в тексте статьи — переносим вниз страницы мелким шрифтом
    body_lines, ad = [], ''
    for l in a['body'].split('\n'):
        if l.strip().startswith('Реклама'): ad = l.strip()
        else: body_lines.append(l)
    body = '\n'.join(body_lines)
    ad_html = f'<br><span style="font-size:11px;color:#8a94a0">{esc(ad)}</span>' if ad else ''
    same = [x for x in items if x['slug'] != a['slug'] and x['tema'] == a['tema']]
    other = [x for x in items if x['slug'] != a['slug'] and x['tema'] != a['tema']]
    if lang == 'uk':  # 26.11.2026: в украинской статье — украинские заголовки и украинские версии, где они есть
        more = ''.join(f'<a href="/polezno/{"ua/" if (UA_SRC / (x["slug"] + ".md")).exists() else ""}{x["slug"]}">→ {esc(x.get("ua_title") or x["title"])}</a>' for x in (same + other)[:5])
    else:
        more = ''.join(f'<a href="/polezno/{x["slug"]}">→ {esc(x["title"])}</a>' for x in (same + other)[:5])
    more += ''.join(f'<a href="{u}">→ {esc(t)} (гайд с PDF)</a>' for u, t in GAIDY[:2])
    return (head(a['title'], a.get('description', ''), canon, ld, alt_links(a, ua_ok)) +
            f'<body><div class="w"><a class="back" href="/polezno/">← Полезное</a>\n'
            f'<article class="card"><a class="tag" href="/polezno/#{esc(a["tema"])}">{esc(a["tema"])}</a><h1>{esc(a["title"])}</h1>'
            f'<p class="date">{date_ru(a.get("updated", a["date"]), lang)} · {"Євген Калмиков, Валенсія" if lang == "uk" else "Евгений Калмыков, Валенсия"}</p>\n{video}{render(body)}\n</article>\n'
            f'<div class="cta2"><b>Остались вопросы по своей ситуации?</b>Напишите — дам контакт проверенного специалиста по вашему вопросу. '
            f'<div class="btns">{"".join(btns)}</div></div>\n'
            f'<div class="card more"><h2 style="margin-top:0">Ещё по теме</h2>{more}</div>\n'
            f'<p class="muted">Информация общая и не заменяет консультацию юриста. Законы меняются — дата проверки указана сверху. · <a href="/">kalmykovgroup.com</a>{ad_html}</p>\n'
            '</div></body></html>\n')

def index(items):
    canon = f'{BASE}/polezno/'
    ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'Полезное о жизни в Испании', 'url': canon}
    temy = []
    for x in items:
        if x['tema'] not in temy: temy.append(x['tema'])
    groups = ''.join(
        f'<div class="card list" id="{esc(t)}"><h2 style="margin-top:0">{esc(t)}</h2>' +
        ''.join(f'<a href="/polezno/{x["slug"]}"><b>{esc(x["title"])}</b><span>{esc(x.get("description", ""))}</span></a>' for x in items if x['tema'] == t) +
        '</div>' for t in temy)
    gaidy = ''.join(f'<a href="{u}"><b>{esc(t)}</b></a>' for u, t in GAIDY)
    return (head('Полезное о жизни в Испании — аренда, документы, деньги, быт', 'Короткие понятные ответы на частые вопросы о жизни в Испании: аренда, залог, прописка, ВНЖ, банки, транспорт. Проверено по законам и официальным источникам.', canon, ld) +
            '<body><div class="w"><a class="back" href="/">← kalmykovgroup.com</a>\n'
            '<div class="card"><h1>Полезное о жизни в Испании</h1><p class="lead" style="margin:0">Короткие ответы на вопросы, которые задают чаще всего: аренда, документы, деньги, быт. Каждая статья проверена по закону и официальным источникам, дата проверки — в начале статьи.</p></div>\n'
            f'<div class="card list"><h2 style="margin-top:0">Большие гайды с PDF</h2>{gaidy}</div>\n{groups}\n'
            f'<p class="muted"><a href="/novosti/">Новости Испании</a> · <a href="{TG_SITE}" target="_blank" rel="noopener">Новости каждый день в Telegram</a> · <a href="/">kalmykovgroup.com</a></p>\n'
            '</div></body></html>\n')

def update_home(items):
    p = SITE / 'index.html'
    s = p.read_text(encoding='utf-8')
    li = ''.join(f'<li><a href="/polezno/{x["slug"]}">{esc(x["title"])}</a></li>' for x in items[:5])
    li += ''.join(f'<li><a href="{u}">{esc(t)}</a></li>' for u, t in GAIDY[:max(0, 5 - len(items))])
    block = ('<!--gaidy--><section class="newsbox" style="background:var(--surface);border-radius:20px;padding:20px 24px;margin-top:16px">'
             '<h2 style="margin:0 0 10px;font-family:var(--display);font-size:20px">Полезное о жизни в Испании</h2>'
             f'<ul style="margin:0;padding-left:20px;line-height:1.6">{li}</ul>'
             '<p style="margin:12px 0 0"><a href="/polezno/" style="font-weight:700">Все статьи →</a> · <a href="/gaidy/" style="font-weight:700">Гайды с PDF →</a></p></section><!--/gaidy-->')
    s2 = re.sub(r'<!--gaidy-->.*?<!--/gaidy-->', lambda m: block, s, flags=re.S)
    if s2 != s: p.write_text(s2, encoding='utf-8')

def update_sitemap(items):
    p = SITE / 'sitemap.xml'
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'\s*<url><loc>https://kalmykovgroup\.com/polezno/[^<]*</loc>.*?</url>', '', s)
    s = re.sub(r'\s*</urlset>\s*$', '', s)
    s = re.sub(r'</url><url>', '</url>\n  <url>', s)
    last = max((x.get('updated', x['date']) for x in items), default=datetime.date.today().isoformat())
    add = f'\n  <url><loc>{BASE}/polezno/</loc><lastmod>{last[:10]}</lastmod></url>'
    add += ''.join(f'\n  <url><loc>{BASE}/polezno/{x["slug"]}</loc><lastmod>{x.get("updated", x["date"])[:10]}</lastmod></url>' for x in items)
    if UA_SRC.is_dir():
        add += ''.join(f'\n  <url><loc>{BASE}/polezno/ua/{f.stem}</loc><lastmod>{x.get("updated", x["date"])[:10]}</lastmod></url>' for x in items for f in [UA_SRC / (x['slug'] + '.md')] if f.exists())
    p.write_text(s + add + '\n</urlset>\n', encoding='utf-8')

def build_ua(items, ua):
    # 26.11.2026: украинская версия статьи /polezno/ua/<адрес> — текст из _src/_src_ua/<адрес>.md (своя шапка title/description),
    # оформление и кнопки — как у русской, подписи переводятся словарём sait/_i18n/ua.json (ua_build.translate)
    out = DIR / 'ua'; out.mkdir(exist_ok=True)
    for f in out.glob('*.html'):
        if f.stem not in ua: f.unlink()
    if not ua: return
    import ua_build
    d = json.loads((SITE / '_i18n' / 'ua.json').read_text(encoding='utf-8'))
    miss_all = []
    for slug, u in ua.items():
        ru = next((x for x in items if x['slug'] == slug), None)
        if not ru: continue
        a = {**ru, **{k: v for k, v in u.items() if k in ('title', 'description', 'body', 'updated')}}
        h = redesign_polezno(article(a, items, lang='uk', ua_ok=True))
        h, miss = ua_build.translate(h, d)
        h = h.replace('<html lang="ru"', '<html lang="uk"').replace('href="/polezno/"', 'href="/ua"')
        (out / f'{slug}.html').write_text(h, encoding='utf-8')
        miss_all += miss
    miss_all = [m for m in dict.fromkeys(miss_all) if len(m) < 90]
    if miss_all: print('UA статьи — без перевода подписи:', miss_all[:15])

def main():
    items = sorted((parse(f) for f in SRC.glob('*.md')), key=lambda x: (x.get('updated', x['date']), x['date']), reverse=True)
    fix = lambda h: h
    keep = {x['slug'] for x in items}
    for f in DIR.glob('*.html'):
        if f.stem not in keep and f.name != 'index.html': f.unlink()
    ua = {f.stem: parse(f) for f in UA_SRC.glob('*.md')} if UA_SRC.is_dir() else {}
    for a in items:
        (DIR / f'{a["slug"]}.html').write_text(fix(redesign_polezno(article(a, items, ua_ok=a['slug'] in ua))), encoding='utf-8')
    build_ua(items, ua)
    (DIR / 'index.html').write_text(fix(redesign_index(index(items), 'polezno')), encoding='utf-8')
    update_home(items); update_sitemap(items)
    try:  # 26.11.2026: украинский заголовок статьи (ключ шапки ua_title) — для украинской главной
        import novosti_build; novosti_build.save_ua_titles({a['title']: a['ua_title'] for a in items if a.get('ua_title')})
    except Exception as e: print('ua_title:', e)
    print(f'Полезное: {len(items)} статей')
    # 22.11.2026: украинская главная — копия русской с переводом (tools/ua_build.py)
    try:
        import ua_build; ua_build.build()
    except Exception as e: print('ua_build:', e)
    try:  # 22.11.2026: /en/ и /es/ берут дизайн блока «Поездки» из index.html
        import intl_build; intl_build.main()
    except Exception as e: print('intl_build:', e)

if __name__ == '__main__':
    main()
