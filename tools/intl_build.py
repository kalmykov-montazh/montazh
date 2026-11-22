#!/usr/bin/env python3
# Английская (/en/) и испанская (/es/) версии kalmykovgroup.com — решение Евгения 22.11.2026.
# Международный сайт: ТОЛЬКО международные сервисы (билеты, отели, авто, трансферы, eSIM, экскурсии,
# компенсация за рейс). Никакой недвижимости, разборов договоров, ипотеки, страховки и личных партнёров.
# Дизайн берётся из sait/index.html (стили + блок «Поездки» между <!--trip--> и <!--/trip-->), тексты переводятся.
#
# Статьи: sait/en/_src/<адрес>.md и sait/es/_src/<адрес>.md — формат как в «Полезном» (tools/polezno_build.py):
#   шапка «ключ: значение» до строки «---»: title, description, date (ГГГГ-ММ-ДД), tema, kind (guide|news),
#   cta (через запятую: flights, hotels, car, transfer, esim, tours, claim, trains) — кнопки сервисов внизу статьи,
#   alt_ru / alt_en / alt_es — адрес той же статьи на другом языке (для переключателя и hreflang).
#   Текст: «## Заголовок», абзацы через пустую строку, «- пункт», «1. шаг», «> плашка», **жирный**, [текст](ссылка)
#
# Запуск: python3 tools/intl_build.py — делает /en/, /es/, статьи, списки, юр. страницы, sitemap.xml
import re, html, json, datetime, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from polezno_build import render, inline, esc          # тот же разбор текста статей
from ua_build import translate                         # тот же переводчик блока «Поездки»

SITE = Path(__file__).resolve().parent.parent / 'sait'
BASE = 'https://kalmykovgroup.com'
I18N = SITE / '_i18n'
TODAY = datetime.date.today().isoformat()

# ── партнёрские ссылки по языкам ─────────────────────────────────────────────────────────────
def dc(lang, path=''):  # DiscoverCars: /es/<путь> — по-испански, без префикса — по-английски
    return f'https://www.discovercars.com/{"es/" if lang == "es" else ""}{path}?a_aid=kalmykovgroup'.replace('.com/?', '.com/?')

def partners(lang):
    en = lang == 'en'
    return {
        'flights': ('Aviasales', f'https://www.aviasales.com/?marker=809770.{lang}&locale={lang}&currency=eur',
                    'Compare hundreds of airlines and agencies' if en else 'Compara cientos de aerolíneas y agencias'),
        'hotels': ('Trip.com', 'https://trip.tpk.ro/uSJdIAwK?erid=2Vtzqwjgr3R',
                   'Hotels and apartments worldwide, many with free cancellation' if en else 'Hoteles y apartamentos en todo el mundo, muchos con cancelación gratuita'),
        'car': ('DiscoverCars', dc(lang),
                'All rental companies in one search, free cancellation up to 48 h' if en else 'Todas las empresas de alquiler en una búsqueda, cancelación gratuita hasta 48 h'),
        'car_vlc': ('DiscoverCars', dc(lang, 'spain/valencia/vlc'),
                    'Cars at Valencia Airport, free cancellation' if en else 'Coches en el aeropuerto de Valencia, cancelación gratuita'),
        'transfer': ('Kiwitaxi', 'https://kiwitaxi.tpk.ro/MxN3zjHJ?erid=2VtzqvZxcw9',
                     'Fixed price, driver meets you with a name sign' if en else 'Precio fijo, el conductor te espera con un cartel'),
        'pickup': ('Welcome Pickups', 'https://tpk.ro/JMVdf3FU?erid=2VtzqvbScDV',
                   'English-speaking driver waiting at arrivals' if en else 'Conductor esperando en la zona de llegadas'),
        'esim': ('Yesim', 'https://yesim.tpk.ro/PINKVK34?erid=2VtzqvYUdeo',
                 'eSIM data for Spain and 200+ countries' if en else 'eSIM con datos para España y más de 200 países'),
        'esim2': ('Airalo', 'https://airalo.tpk.ro/VEBEeOcy?erid=2VtzqveQanB',
                  'The best-known eSIM store: Spain or all of Europe' if en else 'La tienda de eSIM más conocida: España o toda Europa'),
        'tours': ('GetYourGuide', 'https://getyourguide.tpk.ro/YzOdxjGC?erid=2VtzqwNw26b',
                  'Tours, tickets and day trips with free cancellation' if en else 'Tours, entradas y excursiones con cancelación gratuita'),
        'claim': ('Compensair', 'https://compensair.tpk.ro/lAi8i3Do?erid=2VtzqvygRSf',
                  'Check in 2 minutes if you are owed up to €600' if en else 'Comprueba en 2 minutos si te corresponden hasta 600 €'),
        'car2': ('Economybookings', 'https://economybookings.tpk.ro/P0O35S8l',
                 'Another car rental comparison, airports and cities' if en else 'Otro comparador de alquiler de coches, aeropuertos y ciudades'),
    }
CTA_ALIAS = {'esim': ['esim', 'esim2'], 'transfer': ['transfer', 'pickup'], 'car': ['car', 'car2'],
             'car_vlc': ['car_vlc', 'car2']}

# ── тексты интерфейса ─────────────────────────────────────────────────────────────────────────
UI = {
 'en': dict(
   html_lang='en', og='en_GB', dir='en', art='guides', name='Ievgen Kalmykov',
   title='Kalmykov Group — cheaper travel to and around Spain: flights, hotels, cars, eSIM',
   desc='Practical guides for travelling to and living in Spain from Valencia, plus the booking services we use ourselves: flights, hotels, car rental, airport transfers, eSIM and tours',
   tagline='Valencia, Spain · travel tips and tools',
   subs='<b>20,000+</b> people follow us on social media',
   arts_h='Guides for travelling to Spain', news_h='Spain news for travellers', all_arts='All guides →',
   about_h='About', about='Kalmykov Group is a project by Ievgen Kalmykov, a blogger based in Valencia, Spain. We write practical, up-to-date guides for people travelling to Spain or moving here, and point you to booking services that work well: so you pay less and avoid surprises at the airport, the car rental desk or the hotel.',
   ad='Some links on this site are affiliate links: if you book through them, we may earn a commission at no extra cost to you. This is how the site stays free.',
   legal='Legal notice & privacy', socials='Our social media (in Russian)',
   back='← All guides', home='← Home', updated='Updated', read_also='More guides', book_h='Book it here',
   list_title='Guides for travelling to Spain — Kalmykov Group', list_desc='Airport transfers, car rental, eSIM, trains, flight delays and entry rules — practical guides for Spain',
   news_lbl='News', guide_lbl='Guide', empty='First guides are on the way',
 ),
 'es': dict(
   html_lang='es', og='es_ES', dir='es', art='guias', name='Evgenio Kalmykov',
   title='Kalmykov Group — viajar a España y por España más barato: vuelos, hoteles, coches, eSIM',
   desc='Guías prácticas desde Valencia para viajar a España o mudarte aquí, y los servicios de reserva que usamos nosotros mismos: vuelos, hoteles, alquiler de coches, traslados, eSIM y tours',
   tagline='Valencia, España · viajes y vida en España',
   subs='<b>20 000+</b> personas nos siguen en redes',
   arts_h='Guías para viajar y vivir en España', news_h='Noticias de España', all_arts='Todas las guías →',
   about_h='Quiénes somos', about='Kalmykov Group es el proyecto de Evgenio Kalmykov, bloguero que vive en Valencia (España). Escribimos guías prácticas y actualizadas para quienes viajan a España o se mudan aquí, y te indicamos servicios de reserva que funcionan bien: para que pagues menos y no tengas sorpresas en el aeropuerto, en el mostrador de alquiler o en el hotel.',
   ad='Algunos enlaces de esta web son de afiliados: si reservas a través de ellos, podemos recibir una comisión sin coste adicional para ti. Así la web sigue siendo gratuita.',
   legal='Aviso legal y privacidad', socials='Nuestras redes (en ruso)',
   back='← Todas las guías', home='← Inicio', updated='Actualizado', read_also='Más guías', book_h='Resérvalo aquí',
   list_title='Guías para viajar y vivir en España — Kalmykov Group', list_desc='Aeropuerto, alquiler de coche, eSIM, trenes, vuelos retrasados, nacionalidad: guías prácticas sobre España',
   news_lbl='Noticia', guide_lbl='Guía', empty='Las primeras guías llegan pronto',
   teaser_h='Próximamente: guía «Nacionalidad española en 2 años»', teaser='Para latinoamericanos que viven en España: requisitos, documentos, examen CCSE y plazos, paso a paso. Disponible en diciembre',
 ),
}
SOC = [('Facebook', 'https://kalmykovgroup.com/fb'), ('Instagram', 'https://kalmykovgroup.com/ig'),
       ('TikTok', 'https://kalmykovgroup.com/tt'), ('YouTube', 'https://www.youtube.com/@kalmykov_evgeniy')]

def langsw(cur, alts):
    # alts: {'ru': '/', 'ua': '/ua', 'en': '/en/', 'es': '/es/'}
    if len(alts) < 2: return ''
    out = []
    for code, lab, hl in [('ru', 'RU', 'ru'), ('ua', 'UA', 'uk'), ('en', 'EN', 'en'), ('es', 'ES', 'es')]:
        if code not in alts: continue
        on = ' class="on"' if code == cur else ''
        out.append(f'<a{on} href="{alts[code]}" lang="{hl}" hreflang="{hl}">{lab}</a>')
    return '<nav class="langsw" aria-label="Language">' + ''.join(out) + '</nav>'

def hreflang(alts):
    m = {'ru': 'ru', 'ua': 'uk', 'en': 'en', 'es': 'es'}
    s = ''.join(f'<link rel="alternate" hreflang="{m[k]}" href="{BASE}{v}">' for k, v in alts.items())
    if 'en' in alts: s += f'<link rel="alternate" hreflang="x-default" href="{BASE}{alts["en"]}">'
    return s

# ── стили главной (берём из index.html, чтобы дизайн совпадал) ──────────────────────────────
def home_assets():
    s = (SITE / 'index.html').read_text(encoding='utf-8')
    head = s[s.index('<head>'):s.index('</head>')]
    styles = ''.join(re.findall(r'<style\b[^>]*>.*?</style>', head, re.S))
    links = ''.join(re.findall(r'<link rel="(?:preconnect|stylesheet)"[^>]*>', head))
    trip = s[s.index('<!--trip-->'):s.index('<!--/trip-->') + len('<!--/trip-->')]
    # скрипт сразу после блока: карта цен Aviasales (подгрузка при прокрутке), промокоды, сроки акций
    m = re.match(r'\s*<script>.*?</script>', s[s.index('<!--/trip-->') + len('<!--/trip-->'):], re.S)
    if m: trip += m.group(0)
    flf = re.search(r"<script>\(function\(\)\{var f=document.getElementById\('flf'\).*?</script>", s, re.S).group(0)
    return styles, links, trip, flf

def trip_block(lang, trip):
    d = json.loads((I18N / f'{lang}.json').read_text(encoding='utf-8'))
    b, miss = translate(trip, d)
    en = lang == 'en'
    b = re.sub(r'\s*<a href="/strahovka/">.*?</a>', '', b, flags=re.S)                 # страховка — наш личный партнёр
    b = re.sub(r'<a class="avapp".*?</a>', '', b, flags=re.S)                           # приложение Aviasales (RU)
    b = b.replace('https://tripster.tpk.ro/tejFlUxc?erid=2Vtzqw2eQ1M', 'https://getyourguide.tpk.ro/YzOdxjGC?erid=2VtzqwNw26b')
    b = b.replace('href="/poezdki/"', f'href="/{UI[lang]["dir"]}/{UI[lang]["art"]}/"')
    b = b.replace('www.discovercars.com/ru/', 'www.discovercars.com/' + ('' if en else 'es/'))
    b = b.replace('locale=ru', f'locale={lang}')
    b = b.replace('aviasales.tpk.ro/Y9TqwkLa?erid=2VtzqvviSsy', f'www.aviasales.com/?marker=809770.{lang}&amp;locale={lang}&amp;currency=eur')
    miss = [x for x in miss if x in b]
    return b, miss

def write_css():
    # общие стили всех страниц /en/ и /es/: стили главной + стили статей, одним файлом (кэшируется браузером)
    styles, _, _, _ = home_assets()
    css = ''.join(re.findall(r'<style\b[^>]*>(.*?)</style>', styles + ART_CSS, re.S))
    (SITE / 'intl.css').write_text(css, encoding='utf-8')

def page_head(lang, title, desc, canon, alts, extra=''):
    _, links, _, _ = home_assets()
    links += f'<link rel="stylesheet" href="/intl.css?v={TODAY}">'
    return (f'<!doctype html>\n<html lang="{UI[lang]["html_lang"]}">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'<title>{esc(title)}</title>\n<meta name="description" content="{esc(desc)}">\n'
            f'<link rel="canonical" href="{BASE}{canon}">\n{hreflang(alts)}\n'
            f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">'
            f'<meta property="og:type" content="website"><meta property="og:locale" content="{UI[lang]["og"]}">'
            f'<meta property="og:url" content="{BASE}{canon}"><meta property="og:image" content="{BASE}/og.jpg">'
            '<meta name="twitter:card" content="summary_large_image">\n'
            '<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" href="/favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
            f'{links}\n{extra}</head>\n')

# ── статьи ────────────────────────────────────────────────────────────────────────────────────
def load(lang):
    src = SITE / lang / '_src'
    items = []
    if not src.exists(): return items
    for p in sorted(src.glob('*.md')):
        text = p.read_text(encoding='utf-8').replace('\r\n', '\n')
        head, _, body = text.partition('\n---\n')
        m = {}
        for l in head.split('\n'):
            if ':' in l:
                k, v = l.split(':', 1); m[k.strip().lower()] = v.strip()
        m['slug'] = p.stem; m['body'] = body.strip()
        m.setdefault('date', TODAY); m.setdefault('kind', 'guide')
        items.append(m)
    items.sort(key=lambda x: x['date'], reverse=True)
    return items

def art_url(lang, slug): return f'/{lang}/{UI[lang]["art"]}/{slug}'

ART_CSS = '''<style>
.art{background:#fff;border-radius:20px;padding:26px 28px;box-shadow:0 2px 10px rgba(22,41,74,.07);margin:16px 0;font-size:17px;line-height:1.65}
.art h1{font-family:var(--display);font-size:30px;line-height:1.2;color:#16294a;margin:4px 0 8px}
.art h2{font-family:var(--display);font-size:21px;color:#16294a;margin:26px 0 8px}
.art .meta{color:#5f6b7a;font-size:14px;margin:0 0 14px}.art .kind{display:inline-block;background:#0f4c5c;color:#ffd54a;font-weight:700;font-size:12px;border-radius:99px;padding:3px 10px;margin-right:8px}
.art .box{background:#fff8e1;border-left:4px solid #f5b400;border-radius:10px;padding:12px 14px;margin:14px 0}
.art ol.steps{display:block;list-style:decimal;padding-left:26px;margin:10px 0}.art ol.steps li::before{display:none!important;content:none!important}.art ol.steps li{display:list-item;padding:0;background:none;border:0;border-radius:0}.art li{margin:4px 0}
.book{margin:22px 0 4px;padding:18px;border-radius:18px;background:linear-gradient(135deg,#0f4c5c,#13806f);border:3px solid #ffd54a}
.book h2{margin:0 0 10px!important;color:#ffd54a!important;font-size:19px!important}
.book a{display:flex;justify-content:space-between;align-items:center;gap:12px;background:#fff;border-radius:12px;padding:12px 14px;margin:8px 0;text-decoration:none;color:#16233a}
.book a b{font-size:16px}.book a span{font-size:13.5px;color:#5f6b7a}.book a em{font-style:normal;font-weight:800;color:#fff;background:linear-gradient(180deg,#2b2b2b,#0c0c0c);border:2px solid #d4a24c;border-radius:10px;padding:7px 12px;white-space:nowrap}
.adn{font-size:12.5px;color:#7a8594;margin-top:14px}
.alist{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.alist a{display:block;background:#fff;border-radius:14px;padding:14px 16px;text-decoration:none;color:#16233a;box-shadow:0 1px 6px rgba(22,41,74,.07)}
.alist a b{display:block;font-size:16.5px;color:#16294a}.alist a span{display:block;font-size:14px;color:#5f6b7a;margin-top:3px}
.alist small{display:inline-block;font-size:11.5px;font-weight:800;color:#0f4c5c;text-transform:uppercase;letter-spacing:.04em;margin-bottom:2px}
.ifoot{margin:26px 0 10px;padding:18px 4px;color:#5f6b7a;font-size:14px;line-height:1.6;border-top:1px solid #dde3ea}
.ifoot a{color:#16294a;font-weight:700}
.teaser{margin:16px 0;padding:18px 20px;border-radius:18px;background:linear-gradient(180deg,#2b2b2b,#0c0c0c);border:2px solid #d4a24c;color:#e9dcc0}
.teaser b{display:block;color:#ffcf40;font-size:18px;margin-bottom:4px}
.langsw a{text-decoration:none}.topbar{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:14px 0 0}.topbar>a{font-weight:800;text-decoration:none;color:#16294a}.topbar .langsw{position:static;box-shadow:0 1px 4px rgba(0,0,0,.12)}
</style>'''

def book_box(lang, cta):
    P = partners(lang)
    keys = []
    for c in [x.strip() for x in cta.split(',') if x.strip()]:
        for k in CTA_ALIAS.get(c, [c]):
            if k in P and k not in keys: keys.append(k)
    if not keys: return ''
    go = 'Open' if lang == 'en' else 'Ver'
    rows = ''.join(f'<a href="{esc(P[k][1])}" target="_blank" rel="sponsored noopener"><span><b>{esc(P[k][0])}</b><br><span>{esc(P[k][2])}</span></span><em>{go} →</em></a>' for k in keys)
    return f'<div class="book"><h2>{UI[lang]["book_h"]}</h2>{rows}</div>'

def alts_for(lang, a):
    al = {}
    if a.get('alt_ru'): al['ru'] = '/polezno/' + a['alt_ru']
    for l in ('en', 'es'):
        if l == lang: al[l] = art_url(lang, a['slug'])
        elif a.get('alt_' + l): al[l] = art_url(l, a['alt_' + l])
    return al

def article_page(lang, a, items):
    u = UI[lang]
    canon = art_url(lang, a['slug'])
    alts = alts_for(lang, a)
    ld = {"@context": "https://schema.org", "@type": "NewsArticle" if a['kind'] == 'news' else "Article",
          "headline": a['title'], "description": a.get('description', ''), "inLanguage": lang,
          "datePublished": a['date'], "dateModified": a.get('updated', a['date']),
          "author": {"@type": "Person", "name": u['name']}, "publisher": {"@type": "Organization", "name": "Kalmykov Group", "url": BASE},
          "mainEntityOfPage": BASE + canon}
    head = page_head(lang, a['title'] + ' | Kalmykov Group', a.get('description', ''), canon, alts,
                     f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n')
    more = [x for x in items if x['slug'] != a['slug']][:4]
    more_html = ''.join(f'<li><a href="{art_url(lang, x["slug"])}"><b>{esc(x["title"])}</b></a></li>' for x in more)
    kind = u['news_lbl'] if a['kind'] == 'news' else u['guide_lbl']
    return (head + '<body class="v-c"><div class="wrap">'
            f'<div class="topbar"><a href="/{lang}/{u["art"]}/" >{u["back"]}</a>{langsw(lang, alts)}</div>'
            f'<article class="art"><p class="meta"><span class="kind">{kind}</span>{u["updated"]}: {a.get("updated", a["date"])}</p>'
            f'<h1>{esc(a["title"])}</h1>{render(a["body"])}{book_box(lang, a.get("cta", ""))}<p class="adn">{u["ad"]}</p></article>'
            + (f'<section class="art"><h2 style="margin-top:0">{u["read_also"]}</h2><ul class="alist">{more_html}</ul></section>' if more else '')
            + foot(lang) + '</div></body></html>\n')

def foot(lang):
    u = UI[lang]
    soc = ' · '.join(f'<a href="{h}" target="_blank" rel="noopener">{n}</a>' for n, h in SOC)
    return (f'<footer class="ifoot"><p>{u["ad"]}</p><p>{u["socials"]}: {soc}</p>'
            f'<p>Kalmykov Group · Valencia, España · <a href="/{lang}/legal">{u["legal"]}</a> · <a href="mailto:hola@kalmykovgroup.com">hola@kalmykovgroup.com</a></p></footer>')

def alist(lang, items, n=None):
    u = UI[lang]
    if not items: return f'<p>{u["empty"]}</p>'
    rows = ''.join(f'<li><a href="{art_url(lang, x["slug"])}"><small>{u["news_lbl"] if x["kind"] == "news" else u["guide_lbl"]}</small><b>{esc(x["title"])}</b><span>{esc(x.get("description", ""))}</span></a></li>' for x in items[:n] if True)
    return f'<ul class="alist">{rows}</ul>'

def list_page(lang, items):
    u = UI[lang]
    canon = f'/{lang}/{u["art"]}/'
    alts = {'ru': '/polezno/', 'en': '/en/guides/', 'es': '/es/guias/'}
    head = page_head(lang, u['list_title'], u['list_desc'], canon, alts)
    return (head + '<body class="v-c"><div class="wrap">'
            f'<div class="topbar"><a href="/{lang}/" >{u["home"]}</a>{langsw(lang, alts)}</div>'
            f'<section class="art"><h1>{u["arts_h"]}</h1>{alist(lang, items)}</section>' + foot(lang) + '</div></body></html>\n')

def home_page(lang, items):
    u = UI[lang]
    styles, links, trip, flf = home_assets()
    tb, miss = trip_block(lang, trip)
    flf = flf.replace('locale=ru', f'locale={lang}').replace("marker=809770.form", f"marker=809770.{lang}form")
    alts = {'ru': '/', 'ua': '/ua', 'en': '/en/', 'es': '/es/'}
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Kalmykov Group", "url": BASE + f'/{lang}/', "inLanguage": lang}
    head = page_head(lang, u['title'], u['desc'], f'/{lang}/', alts,
                     f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n')
    guides = [x for x in items if x['kind'] != 'news']; news = [x for x in items if x['kind'] == 'news']
    body = ('<body class="v-c"><div class="wrap"><div>'
            f'<div class="cover">{langsw(lang, alts)}<img src="/cover.jpg" alt="Costa Blanca"></div>'
            f'<div class="profile"><img class="avatar" src="/photo.jpeg" alt="{u["name"]}"><div class="who"><h1>{u["name"]}</h1>'
            f'<p class="path"><b class="brand">Kalmykov Group</b> · {u["tagline"]}</p><p class="subs">{u["subs"]}</p></div></div></div>'
            + tb
            + (f'<div class="teaser"><b>{u["teaser_h"]}</b>{u["teaser"]}</div>' if u.get('teaser_h') else '')
            + f'<section class="art" id="guides"><h2 style="margin-top:0">{u["arts_h"]}</h2>{alist(lang, guides, 8)}<p style="margin:12px 0 0"><a href="/{lang}/{u["art"]}/" style="font-weight:700">{u["all_arts"]}</a></p></section>'
            + (f'<section class="art"><h2 style="margin-top:0">{u["news_h"]}</h2>{alist(lang, news, 5)}</section>' if news else '')
            + f'<section class="art"><h2 style="margin-top:0">{u["about_h"]}</h2><p style="margin:0">{u["about"]}</p></section>'
            + foot(lang) + '</div>'
            + '<script>(function(){var h=document.getElementById("hub");if(h){h.querySelectorAll(".hub-tabs button").forEach(function(b){b.addEventListener("click",function(){h.querySelectorAll(".hub-tabs button").forEach(function(x){x.classList.toggle("on",x===b)});h.querySelectorAll(".hp").forEach(function(p){p.classList.toggle("on",p.dataset.p===b.dataset.t)})})})}})()</script>'
            + flf + '</body></html>\n')
    return head + body, miss

# ── юридическая страница ─────────────────────────────────────────────────────────────────────
LEGAL = {
 'en': ('Legal notice, privacy and cookies', '''## Legal notice
Owner of this website: Ievgen Kalmykov (Kalmykov Group), Valencia, Spain. Contact: hola@kalmykovgroup.com · WhatsApp +34 624 916 605. Tax ID: will be shown after registration as self-employed (autónomo).

This website publishes travel information about Spain and links to third-party booking services (flights, hotels, car rental, transfers, eSIM, tours, flight compensation). We do not sell these services ourselves: bookings, payments and customer service are handled by each provider under its own terms. Information on this site is for guidance only; prices, rules and timetables can change — always check the provider's website before booking.

## Affiliate links
Some links are affiliate links (Travelpayouts network, DiscoverCars and others). If you book through them, we may receive a commission. The price for you is the same as on the provider's website.

## Privacy
This site has no registration and no forms that store personal data. If you write to us by email or WhatsApp, we use your message only to reply (art. 6.1.a GDPR) and keep it only as long as needed. You can ask for access, correction or deletion of your data at the contact above and complain to the Spanish Data Protection Agency (aepd.es).

## Cookies
We do not set our own cookies and do not run our own analytics. The search forms and the price map on the home page are loaded from Travelpayouts and may use their own cookies; when you open a provider's website, that provider applies its own cookie policy.'''),
 'es': ('Aviso legal, privacidad y cookies', '''## Aviso legal
Titular de este sitio web: Ievgen Kalmykov (Kalmykov Group), Valencia, España. Contacto: hola@kalmykovgroup.com · WhatsApp +34 624 916 605. NIF/NIE: se indicará tras el alta como autónomo. En cumplimiento de la Ley 34/2002 (LSSI-CE).

Este sitio publica información de viaje sobre España y enlaces a servicios de reserva de terceros (vuelos, hoteles, alquiler de coches, traslados, eSIM, tours, reclamaciones de vuelos). No vendemos estos servicios: las reservas, los pagos y la atención al cliente corren a cargo de cada proveedor según sus propias condiciones. La información es orientativa; precios, normas y horarios pueden cambiar: compruébalos siempre en la web del proveedor antes de reservar.

## Enlaces de afiliados
Algunos enlaces son de afiliados (red Travelpayouts, DiscoverCars y otros). Si reservas a través de ellos, podemos recibir una comisión. El precio para ti es el mismo que en la web del proveedor.

## Privacidad
Este sitio no tiene registro ni formularios que guarden datos personales. Si nos escribes por correo o WhatsApp, usamos tu mensaje solo para responderte (art. 6.1.a RGPD) y lo conservamos el tiempo necesario. Puedes pedir acceso, rectificación o supresión de tus datos en el contacto indicado y reclamar ante la Agencia Española de Protección de Datos (aepd.es).

## Cookies
No instalamos cookies propias ni usamos analítica propia. Los buscadores y el mapa de precios de la página de inicio se cargan desde Travelpayouts y pueden usar sus propias cookies; al abrir la web de un proveedor, se aplica su política de cookies.'''),
}

def legal_page(lang):
    t, body = LEGAL[lang]
    alts = {'en': '/en/legal', 'es': '/es/legal'}
    return (page_head(lang, t + ' — Kalmykov Group', t, f'/{lang}/legal', alts)
            + f'<body class="v-c"><div class="wrap"><p style="margin:14px 0 0"><a href="/{lang}/" style="font-weight:700;text-decoration:none">{UI[lang]["home"]}</a></p>'
            f'<article class="art"><h1>{t}</h1>{render(body)}</article></div></body></html>\n')

# ── sitemap ───────────────────────────────────────────────────────────────────────────────────
def update_sitemap(all_urls):
    p = SITE / 'sitemap.xml'
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'\s*<url><loc>https://kalmykovgroup\.com/(?:en|es)/[^<]*</loc>.*?</url>', '', s, flags=re.S)
    add = ''.join(f'\n<url><loc>{BASE}{u}</loc><lastmod>{d}</lastmod></url>' for u, d in all_urls)
    s = s.replace('</urlset>', add + '\n</urlset>')
    p.write_text(s, encoding='utf-8')

def main():
    write_css()
    urls = []
    report = []
    for lang in ('en', 'es'):
        items = load(lang)
        d = SITE / lang; (d / UI[lang]['art']).mkdir(parents=True, exist_ok=True)
        keep = {x['slug'] for x in items}
        for f in (d / UI[lang]['art']).glob('*.html'):
            if f.stem not in keep and f.name != 'index.html': f.unlink()
        for a in items:
            (d / UI[lang]['art'] / f'{a["slug"]}.html').write_text(article_page(lang, a, items), encoding='utf-8')
            urls.append((art_url(lang, a['slug']), a.get('updated', a['date'])))
        (d / UI[lang]['art'] / 'index.html').write_text(list_page(lang, items), encoding='utf-8')
        h, miss = home_page(lang, items)
        (d / 'index.html').write_text(h, encoding='utf-8')
        (d / 'legal.html').write_text(legal_page(lang), encoding='utf-8')
        urls += [(f'/{lang}/', TODAY), (f'/{lang}/{UI[lang]["art"]}/', TODAY)]
        report.append(f'{lang}: {len(items)} статей' + (f', без перевода в блоке «Поездки»: {miss}' if miss else ''))
    update_sitemap(urls)
    print('; '.join(report))

if __name__ == '__main__':
    main()
