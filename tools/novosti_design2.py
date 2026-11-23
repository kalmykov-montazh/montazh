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
.svc{background:linear-gradient(160deg,#fff 0%,#fff8e6 100%);text-align:center}
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
