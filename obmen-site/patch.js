// Патч index.html обменки (16.11.2026). Вход: исходный текст, выход: новый текст или ошибка.
window.obmenPatch = function (src) {
  let s = src;
  const log = [];
  function rep(a, b, name) {
    const n = s.split(a).length - 1;
    if (n !== 1) throw new Error('Не найдено ровно 1 раз: ' + name + ' (' + n + ')');
    s = s.replace(a, () => b);
    log.push(name);
  }
  const TG = 'https://t.me/+osaN6D0LEPBlNzA6';
  const TGSVG = '<svg viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.248-1.97 9.289c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12L7.17 14.191l-2.95-.924c-.64-.203-.653-.64.136-.948l11.526-4.444c.534-.194 1.002.131.68.373z"/></svg>';
  const PHSVG = '<svg viewBox="0 0 24 24"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg>';

  // ── HEAD: превью, иконки, приложение, FAQ для Google ──
  rep('<meta property="og:type" content="website">',
    '<meta property="og:type" content="website">\n' +
    '<meta property="og:image" content="https://obmen-gagarina.site/og.png">\n' +
    '<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n' +
    '<meta property="og:locale" content="uk_UA">\n' +
    '<meta name="twitter:card" content="summary_large_image">\n' +
    '<meta name="twitter:image" content="https://obmen-gagarina.site/og.png">\n' +
    '<meta name="theme-color" content="#0F0F0F">\n' +
    '<link rel="manifest" href="/manifest.webmanifest">\n' +
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n' +
    '<meta name="apple-mobile-web-app-title" content="Обмін Гагаріна">\n' +
    '<script type="application/ld+json">' + JSON.stringify({
      '@context': 'https://schema.org', '@type': 'FAQPage',
      mainEntity: FAQ.map(q => ({ '@type': 'Question', name: q[0], acceptedAnswer: { '@type': 'Answer', text: q[1].replace(/<[^>]+>/g, '') } }))
    }) + '</script>', 'head');
  rep(/<link rel="icon" href="data:image\/svg\+xml[^\n]*\n/.exec(s)[0],
    '<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48.png">\n<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">\n', 'favicon');

  // ── CSS ──
  rep('</style>\n</head>', CSS + '\n</style>\n</head>', 'css');

  // ── ШАПКА: телефон на телефоне ──
  rep('    <a class="tg-btn" href="' + TG + '" target="_blank" rel="noopener">',
    '    <div class="hbtns"><a class="hcall" href="tel:+380503130002" aria-label="Подзвонити">' + PHSVG + '<span>050 313 00 02</span></a>\n' +
    '    <a class="tg-btn" href="' + TG + '" target="_blank" rel="noopener">', 'header-call');
  rep('      Telegram\n    </a>\n  </div>\n</header>', '      Telegram\n    </a></div>\n  </div>\n</header>', 'header-close');

  // ── Заголовок курсов короче ──
  rep('<div class="rates-title">💹 Курси валют · Опт від $500</div>',
    '<div class="rates-title">Курси валют <span class="opt-badge">опт від $500</span></div>', 'title');
  rep('<th style="text-align:right">Зміна</th>', '<th style="text-align:right">Від учора</th>', 'th');

  // ── Telegram: число подписчиков ──
  rep('<span>Курс у Telegram — оновлюється регулярно<small>Курс на момент публікації, новини, підсумки за тиждень, місяць і рік</small></span>',
    '<span>Курс у Telegram — оновлюється регулярно<small><b id="tg-subs"></b>Курс на момент публікації, новини, підсумки за тиждень, місяць і рік</small></span>', 'tg-subs');

  // ── ГРАФИК после блока курсов, сповіщення свернуть ──
  rep('<!-- ALERTS -->\n<div style="background:var(--dark);padding:28px 4vw 0">\n  <div style="max-width:1600px;margin:0 auto">\n    <div class="card card-green">\n      <div class="section-label">🔔 Сповіщення про курс</div>',
    CHART_HTML + '\n<!-- ALERTS -->\n<div style="background:var(--dark);padding:20px 4vw 0">\n  <div style="max-width:1600px;margin:0 auto">\n    <details class="card card-green al-det">\n      <summary class="section-label">🔔 Сповіщення про курс <span class="al-more">відкрити</span></summary>', 'alerts-open');
  rep('      <div class="anote">ℹ️ Дозвольте сповіщення коли браузер запитає. Курс перевіряється кожні 5 хвилин поки сторінка відкрита.</div>\n    </div>',
    '      <div class="anote">ℹ️ Дозвольте сповіщення коли браузер запитає. Курс перевіряється кожні 5 хвилин поки сторінка відкрита.</div>\n    </details>', 'alerts-close');
  ['🇺🇸 USD — купівля', '🇺🇸 USD — продаж', '🇪🇺 EUR — купівля', '🇪🇺 EUR — продаж', '🇵🇱 PLN — купівля', '🇵🇱 PLN — продаж',
    '🇺🇦 Гривня (UAH)', '🇺🇸 Долар (USD)', '🇪🇺 Євро (EUR)', '🇵🇱 Злотий (PLN)'].forEach(t => rep('>' + t + '<', '>' + t.slice(5) + '<', 'opt ' + t.slice(5)));

  // ── Убрать дубль большого блока Telegram ──
  const tgStart = s.indexOf('<!-- TELEGRAM -->'), tgEnd = s.indexOf('<!-- INFO + MAP -->');
  if (tgStart < 0 || tgEnd < tgStart) throw new Error('telegram block');
  s = s.slice(0, tgStart) + FAQ_HTML + '\n' + s.slice(tgEnd); log.push('tg-promo -> faq');

  // ── Подвал ──
  rep('© 2025 Обмін Валют на Гагаріна', '© 2026 Обмін Валют на Гагаріна', 'year');

  // ── Нижняя панель + окно с номерами ──
  rep('<div ondblclick="openAdmin()" style="position:fixed;bottom:0;right:0;width:50px;height:50px;z-index:500;opacity:0;cursor:default"></div>',
    '<div class="adm-zone" ondblclick="openAdmin()" style="position:fixed;bottom:0;right:0;width:50px;height:50px;z-index:500;opacity:0;cursor:default"></div>\n' +
    '<nav class="bbar"><button type="button" class="bb-call" onclick="document.getElementById(\'callpop\').classList.add(\'open\')">' + PHSVG + 'Подзвонити</button>' +
    '<a class="bb-tg" href="' + TG + '" target="_blank" rel="noopener">' + TGSVG + 'Telegram</a></nav>\n' +
    '<div class="callpop" id="callpop" onclick="if(event.target===this)this.classList.remove(\'open\')"><div class="cp-box">' +
    '<div class="cp-t">Зателефонуйте — зафіксуємо курс на 1 годину</div>' +
    '<a href="tel:+380503130002">' + PHSVG + '+380 50 313 00 02</a><a href="tel:+380684580002">' + PHSVG + '+380 68 458 00 02</a>' +
    '<button type="button" onclick="document.getElementById(\'callpop\').classList.remove(\'open\')">Закрити</button></div></div>', 'bbar');

  // ── Флаги картинками ──
  rep("{key:'USD',    flag:'🇺🇸',", "{key:'USD',    flag:FLAGS.US,", 'flag us');
  rep("{key:'EUR',    flag:'🇪🇺',", "{key:'EUR',    flag:FLAGS.EU,", 'flag eu');
  rep("{key:'PLN',    flag:'🇵🇱',", "{key:'PLN',    flag:FLAGS.PL,", 'flag pl');
  rep("{key:'EURUSD', flag:'💱', ", "{key:'EURUSD', flag:FLAGS.X, ", 'flag x');
  rep("    {ccy:'UAH', flag:'🇺🇦',", "    {ccy:'UAH', flag:FLAGS.UA,", 'cflag ua');
  rep("    {ccy:'USD', flag:'🇺🇸',", "    {ccy:'USD', flag:FLAGS.US,", 'cflag us');
  rep("    {ccy:'EUR', flag:'🇪🇺',", "    {ccy:'EUR', flag:FLAGS.EU,", 'cflag eu');
  rep("    {ccy:'PLN', flag:'🇵🇱',", "    {ccy:'PLN', flag:FLAGS.PL,", 'cflag pl');
  rep("let PASS = sessionStorage.getItem('admin_pw') || '';", FLAGS_JS + "\nlet PASS = sessionStorage.getItem('admin_pw') || '';", 'flags js');

  // ── Стрелки «від учора» (по журналу курсов) ──
  rep("    let trend = '<span class=\"trend-flat\">—</span>';\n    if (p && p[c.key]) {",
    "    let trend = '<span class=\"trend-flat\">—</span>';\n    const y = window.YEST && YEST[c.key];\n    const chg = (cur, old) => { if (old == null) return ''; const d = +(cur - old).toFixed(c.dec); return d > 0 ? ` <span class=\"chg up\">▲${d.toFixed(c.dec)}</span>` : d < 0 ? ` <span class=\"chg dn\">▼${Math.abs(d).toFixed(c.dec)}</span>` : ''; };\n    const cb0 = y ? chg(r[c.key].buy, y[0]) : '', cs0 = y ? chg(r[c.key].sell, y[1]) : '';\n    if (y) { const d = +(r[c.key].buy - y[0]).toFixed(c.dec); trend = d > 0 ? `<span class=\"trend-up\">▲ +${d.toFixed(c.dec)}</span><div class=\"trend-prev\">учора: ${y[0].toFixed(c.dec)}</div>` : d < 0 ? `<span class=\"trend-down\">▼ -${Math.abs(d).toFixed(c.dec)}</span><div class=\"trend-prev\">учора: ${y[0].toFixed(c.dec)}</div>` : '<span class=\"trend-flat\">— без змін</span>'; }\n    else if (p && p[c.key]) {", 'trend');
  rep('<div class="rate-label">купівля</div></td>\n      <td><div class="rate-num sell">${sell}</div><div class="rate-label">продаж</div></td>',
    '<div class="rate-label">купівля${cb0}</div></td>\n      <td><div class="rate-num sell">${sell}</div><div class="rate-label">продаж${cs0}</div></td>', 'labels');

  // ── Статус «відкрито» по киевскому времени ──
  rep("const now = new Date(), h = now.getHours(), m = now.getMinutes(), mins = h*60+m;",
    "const kv = new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Kyiv',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date()).split(':'), mins = (+kv[0])*60 + (+kv[1]);", 'kyiv time');

  // ── Скрипт графика и подписчиков ──
  rep('<script src="/fest.js?v=20261111b" defer></script>', CHART_JS + '\n<script src="/fest.js?v=20261111b" defer></script>', 'chart js');

  return { html: s, log };
};

const FAQ = [
  ['Як зафіксувати курс?', 'Подивіться курс на сайті й зателефонуйте: <a href="tel:+380503130002">+380 50 313 00 02</a> або <a href="tel:+380684580002">+380 68 458 00 02</a>. Уточнимо суму й наявність валюти, курс тримаємо 1 годину — за цей час приїжджайте.'],
  ['Чому курс на меншу суму інший?', 'На сайті оптовий курс для обміну від $500. Якщо сума менша — купівля на 0,10 грн дешевше, продаж на 0,10 грн дорожче.'],
  ['Чи приймаєте зношені купюри?', 'Так, практично будь-які зношені й пошкоджені купюри. Комісія залежить від стану купюри, домовляємося індивідуально.'],
  ['Чи можна заздалегідь дізнатися, чи є потрібна сума?', 'Так, зателефонуйте — підкажемо, чи є потрібна валюта і сума, і відкладемо її для вас.'],
  ['Де ви знаходитесь і чи є де поставити авто?', 'Харків, Аерокосмічний проспект (Гагаріна), 41/2, район скляного переходу. Поруч велика парковка.'],
  ['Ви працюєте у вихідні?', 'Так, щодня з 09:00 до 18:45, без вихідних.'],
  ['Чи працюєте з криптовалютою?', 'Ні. Працюємо лише з готівковою валютою: долар, євро, злотий.']
];

const FAQ_HTML = '<!-- FAQ -->\n<div style="background:var(--dark);padding:28px 4vw">\n  <div style="max-width:1600px;margin:0 auto">\n    <div class="card card-gold">\n      <div class="section-label">❓ Питання й відповіді</div>\n      <div class="faq">' +
  FAQ.map(q => '<details><summary>' + q[0] + '</summary><p>' + q[1] + '</p></details>').join('') +
  '</div>\n    </div>\n  </div>\n</div>\n';

const CHART_HTML = `<!-- CHART -->
<div id="chart-wrap" style="background:var(--dark);padding:24px 4vw 0;display:none">
  <div style="max-width:1600px;margin:0 auto">
    <div class="card card-gold">
      <div class="section-label">📈 Як змінювався курс</div>
      <div class="ch-ctrl">
        <div class="ch-tabs" id="ch-ccy"><button data-v="USD" class="on">Долар</button><button data-v="EUR">Євро</button></div>
        <div class="ch-tabs" id="ch-per"><button data-v="7" class="on">Тиждень</button><button data-v="31">Місяць</button><button data-v="366">Рік</button></div>
      </div>
      <div class="ch-box"><svg id="ch-svg" viewBox="0 0 600 220" preserveAspectRatio="none"></svg><div class="ch-x" id="ch-x"></div></div>
      <div class="ch-leg"><span class="lg-b">● купівля</span><span class="lg-s">● продаж</span></div>
      <div class="ch-stats" id="ch-stats"></div>
    </div>
  </div>
</div>`;

const FLAGS_JS = `const FLAGS = {
  US:'<svg class="flag" viewBox="0 0 30 20"><rect width="30" height="20" fill="#B22234"/><g fill="#fff"><rect y="1.54" width="30" height="1.54"/><rect y="4.62" width="30" height="1.54"/><rect y="7.69" width="30" height="1.54"/><rect y="10.77" width="30" height="1.54"/><rect y="13.85" width="30" height="1.54"/><rect y="16.92" width="30" height="1.54"/></g><rect width="12" height="10.77" fill="#3C3B6E"/></svg>',
  EU:'<svg class="flag" viewBox="0 0 30 20"><rect width="30" height="20" fill="#003399"/><g fill="#FC0">'+Array.from({length:12},(_,i)=>{const a=i*Math.PI/6;return '<circle cx="'+(15+6*Math.sin(a)).toFixed(2)+'" cy="'+(10-6*Math.cos(a)).toFixed(2)+'" r="1"/>'}).join('')+'</g></svg>',
  PL:'<svg class="flag" viewBox="0 0 30 20"><rect width="30" height="10" fill="#fff"/><rect y="10" width="30" height="10" fill="#DC143C"/></svg>',
  UA:'<svg class="flag" viewBox="0 0 30 20"><rect width="30" height="10" fill="#0057B7"/><rect y="10" width="30" height="10" fill="#FFD700"/></svg>',
  X:'<svg class="flag" viewBox="0 0 30 20"><rect width="30" height="20" rx="3" fill="#2a2a2a"/><text x="15" y="14.5" font-size="11" font-weight="700" text-anchor="middle" fill="#D4A843" font-family="Arial">€/$</text></svg>'
};`;

const CHART_JS = `<script>
// Графік курсу, стрілочки «від учора», підписники Telegram
(function(){
  var H=null, ccy='USD', per=7;
  function fmtD(d){var p=d.split('-');return p[2]+'.'+p[1]}
  function draw(){
    if(!H) return;
    var all=H.days.filter(function(x){return x[ccy]});
    var from=new Date(Date.now()-per*864e5).toISOString().slice(0,10);
    var a=all.filter(function(x){return x.d>=from});
    if(a.length<2) a=all.slice(-2);
    if(a.length<2) return;
    var vals=[];a.forEach(function(x){vals.push(x[ccy][0],x[ccy][1])});
    var mn=Math.min.apply(null,vals), mx=Math.max.apply(null,vals), pad=Math.max((mx-mn)*0.15,0.05); mn-=pad; mx+=pad;
    var W=600,Hh=220, n=a.length;
    function X(i){return n===1?W/2:10+i*(W-20)/(n-1)} function Y(v){return 10+(mx-v)/(mx-mn)*(Hh-20)}
    function line(k,cls){return '<polyline class="'+cls+'" points="'+a.map(function(x,i){return X(i).toFixed(1)+','+Y(x[ccy][k]).toFixed(1)}).join(' ')+'"/>'}
    var grid='';for(var g=0;g<4;g++){var v=mn+(mx-mn)*(g+0.5)/4;grid+='<line class="gr" x1="0" x2="600" y1="'+Y(v).toFixed(1)+'" y2="'+Y(v).toFixed(1)+'"/><text class="gt" x="4" y="'+(Y(v)-3).toFixed(1)+'">'+v.toFixed(2)+'</text>'}
    var dots=n<=40?a.map(function(x,i){return '<circle class="db" cx="'+X(i).toFixed(1)+'" cy="'+Y(x[ccy][0]).toFixed(1)+'" r="3"/><circle class="ds" cx="'+X(i).toFixed(1)+'" cy="'+Y(x[ccy][1]).toFixed(1)+'" r="3"/>'}).join(''):'';
    document.getElementById('ch-svg').innerHTML=grid+line(0,'lb')+line(1,'ls')+dots;
    var step=Math.max(1,Math.ceil(n/6)), xs='';
    a.forEach(function(x,i){if(i%step===0||i===n-1) xs+='<span style="left:'+(X(i)/6).toFixed(1)+'%">'+fmtD(x.d)+'</span>'});
    document.getElementById('ch-x').innerHTML=xs;
    var f=a[0][ccy], l=a[n-1][ccy];
    var bs=a.map(function(x){return x[ccy][0]}), ss=a.map(function(x){return x[ccy][1]});
    function ch(o,c){var d=+(c-o).toFixed(2);return d>0?'<b class="up">▲ '+d.toFixed(2)+'</b>':d<0?'<b class="dn">▼ '+Math.abs(d).toFixed(2)+'</b>':'<b>без змін</b>'}
    var since=a[0].d>from?' (з '+fmtD(a[0].d)+')':'';
    document.getElementById('ch-stats').innerHTML=
      '<div><span>Купівля'+since+'</span>'+f[0].toFixed(2)+' → '+l[0].toFixed(2)+' '+ch(f[0],l[0])+'<small>мін '+Math.min.apply(null,bs).toFixed(2)+' · макс '+Math.max.apply(null,bs).toFixed(2)+'</small></div>'+
      '<div><span>Продаж'+since+'</span>'+f[1].toFixed(2)+' → '+l[1].toFixed(2)+' '+ch(f[1],l[1])+'<small>мін '+Math.min.apply(null,ss).toFixed(2)+' · макс '+Math.max.apply(null,ss).toFixed(2)+'</small></div>';
  }
  function tabs(id,cb){document.querySelectorAll('#'+id+' button').forEach(function(b){b.onclick=function(){document.querySelectorAll('#'+id+' button').forEach(function(x){x.classList.remove('on')});b.classList.add('on');cb(b.dataset.v);draw()}})}
  tabs('ch-ccy',function(v){ccy=v}); tabs('ch-per',function(v){per=+v});
  fetch('/history.php').then(function(r){return r.json()}).then(function(j){
    H=j; if(j.prev){window.YEST={USD:j.prev.USD,EUR:j.prev.EUR,PLN:j.prev.PLN}; if(typeof renderTable==='function') renderTable();}
    if(j.days&&j.days.length>1){document.getElementById('chart-wrap').style.display='block';draw();}
  }).catch(function(){});
  fetch('/tg_count.php').then(function(r){return r.json()}).then(function(j){if(j.n){document.getElementById('tg-subs').textContent='Вже '+j.n+' підписників · '}}).catch(function(){});
})();
</script>`;

const CSS = `
/* ══ 16.11.2026: флаги, шапка, нижня панель, графік, FAQ, коротша сторінка ══ */
.flag{width:30px;height:20px;border-radius:3px;display:block;box-shadow:0 0 0 1px rgba(255,255,255,.12)}
.ccard .cf2 .flag{width:26px;height:17px}
.opt-badge{font-family:'Inter',sans-serif;font-size:.72rem;font-weight:800;letter-spacing:.04em;color:#000;background:var(--gold);border-radius:20px;padding:3px 10px;text-transform:none}
.chg{font-size:.72rem;font-weight:800;letter-spacing:0;text-transform:none}
.chg.up,.ch-stats .up{color:var(--green)} .chg.dn,.ch-stats .dn{color:var(--red)}
.hbtns{display:flex;gap:8px;align-items:center}
.hcall{display:none;align-items:center;gap:6px;background:var(--gold);color:#000;font-weight:800;font-size:.85rem;padding:8px 12px;border-radius:6px;text-decoration:none}
.hcall svg{width:16px;height:16px;fill:#000;flex:none}
.bbar{display:none}
.callpop{position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:1200;display:none;align-items:flex-end;justify-content:center;padding:16px}
.callpop.open{display:flex}
.cp-box{background:var(--dark2);border:1px solid rgba(212,168,67,.4);border-radius:16px;padding:20px;width:100%;max-width:420px;display:flex;flex-direction:column;gap:10px}
.cp-t{font-weight:700;color:var(--muted);font-size:.9rem;text-align:center;margin-bottom:4px}
.cp-box a{display:flex;align-items:center;justify-content:center;gap:10px;background:var(--gold);color:#000;font-weight:800;font-size:1.15rem;padding:15px;border-radius:12px;text-decoration:none}
.cp-box a svg{width:20px;height:20px;fill:#000}
.cp-box button{background:none;border:1px solid #333;color:var(--muted);border-radius:12px;padding:12px;font-size:.95rem;font-weight:700;cursor:pointer}
.al-det summary{cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0}
.al-det summary::-webkit-details-marker{display:none}
.al-det[open] summary{margin-bottom:12px}
.al-more{font-family:'Inter',sans-serif;font-size:.78rem;color:var(--muted);font-weight:700;letter-spacing:0}
.al-det[open] .al-more{display:none}
#tg-subs{font-weight:800}
.ch-ctrl{display:flex;gap:10px;flex-wrap:wrap;justify-content:space-between;margin:10px 0 14px}
.ch-tabs{display:flex;background:var(--dark3);border-radius:10px;padding:3px}
.ch-tabs button{background:none;border:none;color:var(--muted);font-weight:700;font-size:.85rem;padding:8px 14px;border-radius:8px;cursor:pointer;font-family:'Inter',sans-serif}
.ch-tabs button.on{background:var(--gold);color:#000}
.ch-box{position:relative;padding-bottom:22px}
#ch-svg{width:100%;height:220px;display:block}
#ch-svg .lb{fill:none;stroke:var(--green);stroke-width:2.5;vector-effect:non-scaling-stroke}
#ch-svg .ls{fill:none;stroke:var(--gold2);stroke-width:2.5;vector-effect:non-scaling-stroke}
#ch-svg .db{fill:var(--green)} #ch-svg .ds{fill:var(--gold2)}
#ch-svg .gr{stroke:rgba(255,255,255,.07);vector-effect:non-scaling-stroke}
#ch-svg .gt{fill:var(--muted2);font-size:11px;font-family:Inter,sans-serif}
.ch-x{position:absolute;left:0;right:0;bottom:0;height:18px}
.ch-x span{position:absolute;transform:translateX(-50%);font-size:.72rem;color:var(--muted);white-space:nowrap}
.ch-x span:first-child{transform:none} .ch-x span:last-child{transform:translateX(-100%)}
.ch-leg{display:flex;gap:16px;font-size:.8rem;font-weight:700;margin-top:6px}
.lg-b{color:var(--green)} .lg-s{color:var(--gold2)}
.ch-stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}
.ch-stats div{background:var(--dark3);border-radius:10px;padding:12px 14px;font-weight:800;font-size:1rem}
.ch-stats span{display:block;font-size:.72rem;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px}
.ch-stats small{display:block;font-size:.75rem;color:var(--muted);font-weight:600;margin-top:4px}
.faq details{border-bottom:1px solid #222;padding:14px 0}
.faq details:last-child{border-bottom:none}
.faq summary{cursor:pointer;font-weight:700;font-size:1rem;list-style:none;display:flex;justify-content:space-between;gap:12px}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:'+';color:var(--gold);font-size:1.3rem;line-height:1}
.faq details[open] summary::after{content:'−'}
.faq p{margin-top:10px;color:var(--muted);line-height:1.7;font-size:.94rem}
.faq a{color:var(--gold);font-weight:700;text-decoration:none}
@media(max-width:900px){
  .hcall{display:inline-flex}
  .tg-btn{padding:8px 10px}
  .bbar{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:600;gap:8px;padding:8px 10px calc(8px + env(safe-area-inset-bottom));background:rgba(15,15,15,.96);border-top:1px solid rgba(212,168,67,.35);backdrop-filter:blur(6px)}
  .bbar>*{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;border:none;border-radius:12px;padding:13px 8px;font-family:'Inter',sans-serif;font-size:1rem;font-weight:800;text-decoration:none;cursor:pointer}
  .bbar svg{width:20px;height:20px;flex:none}
  .bb-call{background:var(--gold);color:#000} .bb-call svg{fill:#000}
  .bb-tg{background:var(--blue);color:#fff} .bb-tg svg{fill:#fff}
  body{padding-bottom:76px}
  .adm-zone{bottom:76px!important}
}
@media(max-width:650px){
  .logo{font-size:1.25rem}
  .hcall span{display:none}
  .hcall{padding:8px 10px}
  .rates-title{font-size:1.25rem}
  .svc-grid{grid-template-columns:1fr 1fr;gap:10px}
  .svc-card{padding:16px 14px}
  .svc-icon{font-size:1.5rem;margin-bottom:8px}
  .svc-card h3{font-size:.68rem;letter-spacing:.08em;margin-bottom:6px}
  .svc-card p{font-size:.8rem;line-height:1.5}
  .info-grid{grid-template-columns:1fr 1fr;gap:10px}
  .ic{padding:16px 14px}
  .ic p{font-size:.85rem}
  #ch-svg{height:180px}
  .ch-tabs button{padding:7px 10px;font-size:.8rem}
  .ch-stats div{font-size:.9rem;padding:10px}
  #news-list{grid-template-columns:1fr}
  .cr{grid-template-columns:repeat(3,1fr);gap:8px}
  .ccard{padding:10px 8px}
  .ccard .ca{font-size:1.35rem}
  .ccard .cs{display:none}
  .card .section-label{font-size:1.3rem}
  .al-det .al-more{font-size:.72rem}
  .calc-row .fi{flex:1;min-width:0;width:auto!important}
}
`;
