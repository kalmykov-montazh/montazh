import re, shutil
s = open('/tmp/claude-0/var/out/c.html', encoding='utf-8').read()

# 1. Значок для каждой услуги свой (весы, машина, ключ…)
si = r'''const SI={
 law:'<svg viewBox="0 0 24 24"><path d="M13 7.83c.85-.3 1.53-.98 1.83-1.83H18l-3 7c0 1.66 1.57 3 3.5 3s3.5-1.34 3.5-3l-3-7h2V4h-6.17c-.41-1.17-1.52-2-2.83-2s-2.42.83-2.83 2H3v2h2l-3 7c0 1.66 1.57 3 3.5 3S9 14.66 9 13L6 6h3.17c.3.85.98 1.53 1.83 1.83V19H2v2h20v-2h-9V7.83zM20.37 13h-3.74l1.87-4.36L20.37 13zm-13 0H3.63L5.5 8.64 7.37 13zM12 6c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/></svg>',
 bank:'<svg viewBox="0 0 24 24"><path d="M12 2 2 7v2h20V7L12 2ZM4 11v7h3v-7H4Zm6.5 0v7h3v-7h-3ZM17 11v7h3v-7h-3ZM2 20v2h20v-2H2Z"/></svg>',
 car:'<svg viewBox="0 0 24 24"><path d="M5 11l1.6-4.5A2 2 0 0 1 8.5 5h7a2 2 0 0 1 1.9 1.5L19 11a2 2 0 0 1 2 2v5h-2v2h-3v-2H8v2H5v-2H3v-5a2 2 0 0 1 2-2Zm2.2 0h9.6l-1.1-3.5H8.3L7.2 11ZM6.5 13a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm11 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z"/></svg>',
 mort:'<svg viewBox="0 0 24 24"><path d="M12 3 2 11.5h3V21h14v-9.5h3L12 3Zm-2.5 8a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3Zm5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3Zm.6-3.6 1 1-6.2 6.2-1-1 6.2-6.2Z"/></svg>',
 key:'<svg viewBox="0 0 24 24"><path d="M7 14a5 5 0 1 1 4.6-7H22v4h-2v3h-3v-3h-5.4A5 5 0 0 1 7 14Zm0-3a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"/></svg>',
 manage:'<svg viewBox="0 0 24 24"><path d="M12 3 2 11.5h3V21h6v-2.1a5 5 0 0 1 0-5.8V11h2v2.1a5 5 0 0 1 6 0V11.5h3L12 3Zm4 11a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm0 2a1 1 0 1 1 0 2 1 1 0 0 1 0-2Z"/></svg>',
 tools:'<svg viewBox="0 0 24 24"><path d="M14.7 3.3a5 5 0 0 0-6.4 6.4L2 16v4h4l6.3-6.3a5 5 0 0 0 6.4-6.4l-3 3-2.8-.6-.6-2.8 3-3-.6-.6Z"/></svg>',
 sofa:'<svg viewBox="0 0 24 24"><path d="M6 6h12a2 2 0 0 1 2 2v2.2a2.5 2.5 0 0 1 2 2.4V18h-2v2h-2v-2H6v2H4v-2H2v-5.4a2.5 2.5 0 0 1 2-2.4V8a2 2 0 0 1 2-2Zm0 4.2c1.2.3 2 1.3 2 2.4V14h8v-1.4c0-1.1.8-2.1 2-2.4V8H6v2.2Z"/></svg>',
 window:'<svg viewBox="0 0 24 24"><path d="M3 3h18v2h-1v14h1v2H3v-2h1V5H3V3Zm3 2v14h5V5H6Zm7 0v14h5V5h-5Z"/></svg>',
 snow:'<svg viewBox="0 0 24 24"><path d="M11 2h2v4.2l2.5-1.5 1 1.7L13 8.5V11h2.5l2.1-3.5 1.7 1L17.8 11H22v2h-4.2l1.5 2.5-1.7 1L15.5 13H13v2.5l3.5 2.1-1 1.7L13 17.8V22h-2v-4.2l-2.5 1.5-1-1.7 3.5-2.1V13H8.5l-2.1 3.5-1.7-1L6.2 13H2v-2h4.2L4.7 8.5l1.7-1L8.5 11H11V8.5L7.5 6.4l1-1.7L11 6.2V2Z"/></svg>',
 cal:'<svg viewBox="0 0 24 24"><path d="M7 2h2v2h6V2h2v2h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2V2ZM5 9v11h14V9H5Zm2 2h4v4H7v-4Z"/></svg>',
 video:'<svg viewBox="0 0 24 24"><path d="M4 5h11a2 2 0 0 1 2 2v2.5l4-2.5v10l-4-2.5V17a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z"/></svg>',
 ask:'<svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm1 15h-2v-2h2v2Zm2.1-7.7-.9.9c-.7.7-1.2 1.3-1.2 2.8h-2v-.5c0-1.1.5-2.1 1.2-2.8l1.2-1.3c.4-.4.6-.9.6-1.4a2 2 0 0 0-4 0H8a4 4 0 0 1 8 0c0 .9-.4 1.7-.9 2.3Z"/></svg>'
};
const pickIcon=t=>/Юрист/.test(t)?SI.law:/Легализ/.test(t)?SI.bank:/Растамож/.test(t)?SI.car:/Ипотек/.test(t)?SI.mort:/Аренда/.test(t)?SI.key:/Управлен/.test(t)?SI.manage:/Ремонт/.test(t)?SI.tools:/Мебель/.test(t)?SI.sofa:/Шторы/.test(t)?SI.window:/Кондиц/.test(t)?SI.snow:/ситу/i.test(t)?SI.cal:/Монтаж/.test(t)?SI.video:SI.ask;
const grid='''
s = s.replace('const grid=', si, 1)
s = s.replace('<span class="ci">${GI[g]}</span>', '<span class="ci">${pickIcon(t)}</span>', 1)

# 2. «Как это работает» — 3 шага в карточке консультации
steps = '''    <ol class="steps">
      <li><b>1</b><span>Пишете в WhatsApp или Telegram, коротко ситуацию</span></li>
      <li><b>2</b><span>Присылаете договор — фото или файл</span></li>
      <li><b>3</b><span>Получаете письменный разбор и что делать дальше</span></li>
    </ol>
    <div class="prices">'''
s = s.replace('    <div class="prices">', steps, 1)

# 3. Под кнопкой консультации — Telegram как второй путь
s = s.replace('<a class="go" id="consultgo" target="_blank" rel="noopener">Записаться на консультацию</a>',
 '<div class="gorow"><a class="go" id="consultgo" target="_blank" rel="noopener">Записаться на консультацию</a><a class="tgalt" href="https://t.me/Kalmykov_broker" target="_blank" rel="noopener">или написать в Telegram</a></div>', 1)

# 4. Ответ про скорость — как сказал Евгений
s = s.replace('Обычно в тот же день. Если срочно — так и напишите', 'Стараюсь в тот же день, если написали не ночью. Если срочно — так и напишите')

css = '''
.card .ci{width:44px;height:44px;border-radius:12px}
.card .ci svg{width:25px;height:25px}
.steps{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.steps li{display:flex;gap:10px;align-items:flex-start;padding:12px;border-radius:12px;background:var(--surface);border:1px dashed color-mix(in srgb,var(--accent) 45%,var(--line));padding-left:12px}
.steps li::before{display:none}
.steps b{flex:none;width:28px;height:28px;border-radius:50%;display:grid;place-items:center;background:var(--accent);color:#fff;font-size:14px}
.steps span{font-size:14px;line-height:1.4}
.gorow{display:flex;flex-wrap:wrap;align-items:center;gap:14px}
.tgalt{color:var(--sea);font-weight:700;font-size:15px}
footer{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px}
@media (max-width:600px){.steps{grid-template-columns:1fr}.gorow{flex-direction:column;align-items:stretch}.tgalt{text-align:center}}
footer{'''
s = s.replace('\nfooter{', css, 1)

# 5. Значок вкладки и картинка для ссылки в мессенджерах
s = s.replace('<title>', '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n<title>', 1)
s = s.replace('content="https://kalmykov-realty.netlify.app/cover.jpg"', 'content="https://kalmykov-realty.netlify.app/share.jpg"')
open('/tmp/claude-0/var/out/final.html', 'w', encoding='utf-8').write(s)

fav = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#0f5a80"/><path d="M0 46c10-6 22-6 32 0s22 6 32 0v18H0Z" fill="#1683a8"/><text x="32" y="41" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-weight="700" font-size="34" fill="#fff">К</text></svg>'''
open('/tmp/claude-0/var/out/favicon.svg', 'w').write(fav)
print('ok')
