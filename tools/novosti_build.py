#!/usr/bin/env python3
# Новости на сайте kalmykovgroup.com/novosti/ (решение Евгения 13.11.2026: «делай новости… это основной трафик»).
# Источник — файлы новостных задач «000 ДД.ММ тема.txt» (папки «Новости утро/день/вечер», «Длинные», «Опубликовано»).
# Запуск: novosti_build.py <папка со скачанными .txt> <файл со списком имён из «На удаление»>
# Делает: sait/novosti/<slug>.html, sait/novosti/index.html, блок «Свежие новости» на главной, sitemap.xml,
# и _ссылки_новостей.txt (имя файла → адрес статьи) — его читают задачи Claude через Google Диск.
import json, re, sys, html, datetime, zoneinfo, urllib.parse
from pathlib import Path

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

CSS = """*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:#16233a;font:17px/1.7 Manrope,Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.w{max-width:760px;margin:0 auto;padding:20px 16px 90px}a{color:#2f6fd6}
.back{display:inline-block;margin-bottom:14px;font-weight:700;text-decoration:none}
.card{background:#fff;border-radius:20px;padding:26px;box-shadow:0 2px 10px rgba(22,41,74,.07);margin-bottom:16px}
h1{font-size:28px;line-height:1.25;color:#16294a;margin:0 0 8px}h2{font-size:20px;color:#16294a;margin:0 0 10px}
.date{color:#5f6b7a;font-size:14px;margin:0 0 18px}.card p{margin:0 0 16px}.card p:last-child{margin:0}
.go{display:flex;justify-content:center;align-items:center;gap:8px;background:#ff6b4a;color:#fff;font-weight:700;text-decoration:none;border-radius:14px;padding:15px;font-size:16px;box-shadow:0 5px 0 #c94a2f;margin-top:14px}
.list a{display:block;text-decoration:none;color:#16233a;padding:14px 0;border-bottom:1px solid #dde3ea}.list a:last-child{border:0}
.list b{display:block;color:#16294a;font-size:17px;line-height:1.35}.list span{color:#5f6b7a;font-size:13px}
.note{font-size:13px;color:#64707b}
@media (max-width:600px){h1{font-size:23px}.card{padding:18px}}"""

def wa(text):
    return 'https://wa.me/34624916605?text=' + urllib.parse.quote(text)

def page(title, desc, canon, body, extra=''):
    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{BASE}/share.jpg"><meta property="og:url" content="{canon}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>{CSS}</style>{extra}</head>
<body><div class="w">
{body}
</div></body></html>
"""

def human_date(iso):
    d = datetime.datetime.fromisoformat(iso)
    return f'{d.day} {MONTHS[d.month-1]} {d.year}'

def article_html(it):
    paras = ''.join('<p>' + '<br>'.join(esc(x) for x in p) + '</p>' for p in it['paras'])
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": it['title'][:110],
          "datePublished": it['published'], "dateModified": it['published'], "inLanguage": "ru",
          "image": [f'{BASE}/share.jpg'], "mainEntityOfPage": f"{BASE}/novosti/{it['slug']}",
          "author": {"@type": "Person", "name": "Ievgen Kalmykov", "alternateName": "Евгений Калмыков", "url": BASE + '/'},
          "publisher": {"@type": "Organization", "name": "Kalmykov Group", "url": BASE + '/',
                        "logo": {"@type": "ImageObject", "url": f'{BASE}/favicon.svg'}},
          "description": it['desc']}
    extra = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>'
    body = f"""<a class="back" href="/novosti/">← Все новости Испании</a>
<article class="card"><h1>{esc(it['title'])}</h1><p class="date">{human_date(it['published'])} · Евгений Калмыков, Валенсия</p>
{paras}</article>
<div class="card"><h2>Нужна помощь в Испании?</h2><p>Аренда и покупка жилья, разбор договора удалённо, проверенные юристы по ВНЖ и документам. Напишите, что у вас за ситуация</p>
<a class="go" href="{wa('Здравствуйте! Пишу с сайта, после новости «' + it['title'][:80] + '»')}" target="_blank" rel="noopener">Написать в WhatsApp</a></div>
<p class="note"><a href="/">kalmykovgroup.com</a> · все соцсети и проверенные специалисты</p>"""
    return page(it['title'] + ' — новости Испании', it['desc'], f"{BASE}/novosti/{it['slug']}", body, extra)

def index_html(items):
    rows = ''.join(f'<a href="/novosti/{it["slug"]}"><b>{esc(it["title"])}</b><span>{human_date(it["published"])}</span></a>' for it in items)
    body = f"""<a class="back" href="/">← Евгений Калмыков · главная</a>
<div class="card"><h1>Новости Испании</h1><p class="date">Жильё, аренда, ВНЖ и документы, деньги, транспорт — каждый день простыми словами</p>
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
             f'<p style="margin:12px 0 0"><a href="/novosti/" style="font-weight:700">Все новости →</a></p></section>{b}')
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
    s = s.replace('\n</urlset>', add + '\n</urlset>')
    p.write_text(s, encoding='utf-8')

def main(src_dir, removed_list):
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
                   'source': f.name}
        changed = True
        print('новая', k, '→', slug)
    items = sorted(data.values(), key=lambda x: x['published'], reverse=True)
    for it in items:
        (NEWS / f"{it['slug']}.html").write_text(article_html(it), encoding='utf-8')
    (NEWS / 'index.html').write_text(index_html(items), encoding='utf-8')
    update_home(items); update_sitemap(items)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    links = ['обновлено ' + now.strftime('%Y-%m-%d %H:%M'), 'формат: ключ файла (ДД.ММ тема) | адрес статьи на сайте']
    links += [f"{k} | {BASE}/novosti/{data[k]['slug']}" for k in sorted(data, key=lambda k: data[k]['published'], reverse=True)[:40]]
    Path('_ссылки_новостей.txt').write_text('\n'.join(links) + '\n', encoding='utf-8')
    print('изменения' if changed else 'без изменений')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
