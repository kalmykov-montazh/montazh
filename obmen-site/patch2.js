// Патч 2 (16.11.2026 вечер): трекинг кнопок, «Поділитися курсом», курс на вкладке, «відкриємось о 9:00», превью с курсом, страницы евро/злотого
window.obmenPatch2 = {
  index: function (src) {
    let s = src; const log = [];
    function rep(a, b, name) { const n = s.split(a).length - 1; if (n !== 1) throw new Error('index: ' + name + ' (' + n + ')'); s = s.replace(a, () => b); log.push(name); }
    rep('<meta property="og:image" content="https://obmen-gagarina.site/og.png">', '<meta property="og:image" content="https://obmen-gagarina.site/og.php">', 'og');
    rep('<meta name="twitter:image" content="https://obmen-gagarina.site/og.png">', '<meta name="twitter:image" content="https://obmen-gagarina.site/og.php">', 'tw');
    rep("el.textContent = isOpen ? '🟢 Зараз відкрито' : '🔴 Зараз зачинено';",
        "el.textContent = isOpen ? '🟢 Відкрито до 18:45' : (mins < 9*60 ? '🔴 Зачинено · відкриємось о 9:00' : '🔴 Зачинено · завтра з 9:00');", 'hours');
    rep("  if (r.updated) document.getElementById('last-updated').textContent = 'Оновлено: ' + r.updated;",
        "  if (r.updated) document.getElementById('last-updated').textContent = 'Оновлено: ' + r.updated;\n  try { document.title = '$ ' + r.USD.buy.toFixed(2) + ' / ' + r.USD.sell.toFixed(2) + ' — Обмін Валют на Гагаріна | Харків'; } catch(e) {}", 'title');
    rep('    <div class="fix-steps">',
        '    <button type="button" id="share-btn" class="share-btn" onclick="shareRates()"><svg viewBox="0 0 24 24"><path d="M18 16a3 3 0 0 0-2.4 1.2l-6.7-3.4a3 3 0 0 0 0-1.6l6.7-3.4A3 3 0 1 0 15 7c0 .3 0 .6.1.8L8.4 11.2a3 3 0 1 0 0 1.6l6.7 3.4A3 3 0 1 0 18 16z"/></svg>Поділитися курсом</button>\n    <div class="fix-steps">', 'share html');
    rep('// ── ГОДИННИК ──',
        "// ── ПОДІЛИТИСЯ КУРСОМ ──\nfunction shareRates() {\n  const r = currentRates; if (!r) return;\n  const f = (v) => v.toFixed(2);\n  const text = 'Курс на Гагаріна (Харків)' + (r.updated ? ', ' + r.updated : '') + ':\\nДолар ' + f(r.USD.buy) + ' / ' + f(r.USD.sell) + '\\nЄвро ' + f(r.EUR.buy) + ' / ' + f(r.EUR.sell) + '\\nЗлотий ' + f(r.PLN.buy) + ' / ' + f(r.PLN.sell) + '\\nОпт від $500';\n  const url = 'https://obmen-gagarina.site/?src=share';\n  if (navigator.share) { navigator.share({ text: text, url: url }).catch(function(){}); }\n  else { window.open('https://t.me/share/url?url=' + encodeURIComponent(url) + '&text=' + encodeURIComponent(text), '_blank'); }\n}\n\n// ── ГОДИННИК ──", 'share js');
    rep('.flag{width:30px;', '.share-btn{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;margin-top:14px;background:transparent;border:1.5px solid var(--gold);color:var(--gold);font-family:\'Inter\',sans-serif;font-size:1rem;font-weight:800;padding:13px;border-radius:12px;cursor:pointer}\n.share-btn svg{width:20px;height:20px;fill:var(--gold)}\n.cur-links{margin-top:10px;font-size:.85rem}.cur-links a{color:var(--gold);text-decoration:none;font-weight:700;margin:0 6px;white-space:nowrap}\n.flag{width:30px;', 'css');
    rep('<p style="margin-top:6px">Працюємо лише з готівковою валютою. Операції з криптовалютою не здійснюємо</p>',
        '<p style="margin-top:6px">Працюємо лише з готівковою валютою. Операції з криптовалютою не здійснюємо</p><p class="cur-links">Курс у Харкові сьогодні: <a href="/kurs-dolara-kharkiv">долар</a><a href="/kurs-yevro-kharkiv">євро</a><a href="/kurs-zlotoho-kharkiv">злотий</a></p>', 'footer links');
    rep('<script src="/fest.js?v=20261111b" defer></script>', '<script src="/track.js?v=1" defer></script>\n<script src="/fest.js?v=20261111b" defer></script>', 'track');
    return { html: s, log };
  },
  kurs: function (src, cc) {
    let s = src; const log = [];
    function rep(a, b, name, all) { const n = s.split(a).length - 1; if (all ? n < 1 : n !== 1) throw new Error('kurs ' + cc + ': ' + name + ' (' + n + ')'); s = all ? s.split(a).join(b) : s.replace(a, () => b); log.push(name); }
    rep('© 2025', '© 2026', 'year');
    rep('<h2 class="s">Як зафіксувати курс</h2>', '<div class="cta" style="margin-top:0"><a href="/kurs-dolara-kharkiv" style="background:transparent;border:1px solid var(--gold);color:var(--gold)">Курс долара</a><a href="/kurs-yevro-kharkiv" style="background:transparent;border:1px solid var(--gold);color:var(--gold)">Курс євро</a><a href="/kurs-zlotoho-kharkiv" style="background:transparent;border:1px solid var(--gold);color:var(--gold)">Курс злотого</a></div>\n<h2 class="s">Як зафіксувати курс</h2>', 'links');
    rep('<meta property="og:locale" content="uk_UA">', '<meta property="og:locale" content="uk_UA">\n<meta property="og:image" content="https://obmen-gagarina.site/og.php">', 'og');
    rep('</body>', '<script src="/track.js?v=1" defer></script>\n</body>', 'track');
    if (cc === 'USD') return { html: s, log };
    const C = cc === 'EUR'
      ? { gen: 'євро', url: 'kurs-yevro-kharkiv', where: 'Де обміняти євро в Харкові?', h2: 'Де обміняти євро у Харкові' }
      : { gen: 'злотого', url: 'kurs-zlotoho-kharkiv', where: 'Де обміняти злоті в Харкові?', h2: 'Де обміняти злоті у Харкові' };
    rep("$usd = $r['USD'] ?? null;", "$usd = $r['" + cc + "'] ?? null;", 'key');
    rep("'Курс долара в Харкові сьогодні, '", "'Курс " + C.gen + " в Харкові сьогодні, '", 'title');
    rep("'Курс долара в Харкові на сьогодні'", "'Курс " + C.gen + " в Харкові на сьогодні'", 'desc');
    rep("'/kurs-dolara-kharkiv';", "'/" + C.url + "';", 'canon');
    rep("'Який курс долара в Харкові сьогодні?'", "'Який курс " + C.gen + " в Харкові сьогодні?'", 'faq1');
    rep("'У нашому обміннику на Гагаріна зараз купівля долара '", "'У нашому обміннику на Гагаріна зараз купівля " + C.gen + " '", 'faq1b');
    rep("fmt($usd['buy'], 'USD')", "fmt($usd['buy'], '" + cc + "')", 'fmt1', true);
    rep("fmt($usd['sell'], 'USD')", "fmt($usd['sell'], '" + cc + "')", 'fmt2', true);
    rep("'Де обміняти долари в Харкові?'", "'" + C.where + "'", 'faq2');
    rep('› Курс долара в Харкові</div>', '› Курс ' + C.gen + ' в Харкові</div>', 'crumbs');
    rep('<h1>Курс долара в Харкові сьогодні</h1>', '<h1>Курс ' + C.gen + ' в Харкові сьогодні</h1>', 'h1');
    rep('<h2 class="s">Де обміняти долар у Харкові</h2>', '<h2 class="s">' + C.h2 + '</h2>', 'h2');
    return { html: s, log };
  },
  stats: function (src) {
    let s = src; const log = [];
    function rep(a, b, name) { const n = s.split(a).length - 1; if (n !== 1) throw new Error('stats: ' + name + ' (' + n + ')'); s = s.replace(a, () => b); log.push(name); }
    rep("$days = []; $src = [];", "$clk = []; $days = []; $src = [];", 'init');
    rep("    [$dt, $vid, $s, $p, $m] = $r; $d = substr($dt, 0, 10);\n",
        "    [$dt, $vid, $s, $p, $m] = $r; $d = substr($dt, 0, 10);\n    if (strpos($p, '/click/') === 0) { if ($d >= $from30) { $k = substr($p, 7); if (!isset($clk[$k])) $clk[$k] = ['n' => 0, 'u' => [], 's' => []]; $clk[$k]['n']++; $clk[$k]['u'][$d.$vid] = 1; $clk[$k]['s'][$s] = ($clk[$k]['s'][$s] ?? 0) + 1; } continue; }\n", 'loop');
    rep('<h2>Откуда приходят (30 дней)</h2>',
        '<h2>Нажатия на кнопки (30 дней)</h2>\n<p class="m">Считаем с 16.11.2026. «Позвонили» — человек нажал на номер телефона (на сайте или в окне «Подзвонити»).</p>\n<table><tr><th>Кнопка</th><th class="n">Нажатий</th><th class="n">Людей</th><th>Откуда пришли эти люди</th></tr>\n<?php $cn = [\'tel\'=>\'📞 Позвонили (нажали номер)\',\'call-btn\'=>\'Нажали «Подзвонити» внизу\',\'telegram\'=>\'Telegram\',\'instagram\'=>\'Instagram\',\'facebook\'=>\'Facebook\',\'route\'=>\'Проложить маршрут\',\'share\'=>\'Поделились курсом\'];\nuasort($clk, function($a, $b) { return $b[\'n\'] <=> $a[\'n\']; });\nforeach ($clk as $k => $x) { arsort($x[\'s\']); $ss = []; foreach (array_slice($x[\'s\'], 0, 5, true) as $sk => $sv) $ss[] = h($names[$sk] ?? $sk) . \' — \' . $sv; echo \'<tr><td>\'.h($cn[$k] ?? $k).\'</td><td class="n">\'.$x[\'n\'].\'</td><td class="n">\'.count($x[\'u\']).\'</td><td class="m">\'.implode(\'<br>\', $ss).\'</td></tr>\'; }\nif (!$clk) echo \'<tr><td colspan="4" class="m">Пока нажатий нет</td></tr>\'; ?>\n</table>\n<h2>Откуда приходят (30 дней)</h2>', 'section');
    return { html: s, log };
  },
  htaccess: function (src) {
    const a = 'RewriteRule ^kurs-dolara-kharkiv/?$ kurs-dolara-kharkiv.php [L,QSA]\n';
    if (src.split(a).length !== 2) throw new Error('htaccess');
    return src.replace(a, a + 'RewriteRule ^kurs-yevro-kharkiv/?$ kurs-yevro-kharkiv.php [L,QSA]\nRewriteRule ^kurs-zlotoho-kharkiv/?$ kurs-zlotoho-kharkiv.php [L,QSA]\n');
  },
  sitemap: function (src) {
    const a = "echo '<url><loc>' . SITE_URL . '/novyny</loc>";
    if (src.split(a).length !== 2) throw new Error('sitemap');
    const line = (u) => "echo '<url><loc>' . SITE_URL . '/" + u + "</loc><lastmod>' . date('Y-m-d', filemtime(__DIR__ . '/rates.json')) . '</lastmod><changefreq>hourly</changefreq><priority>0.9</priority></url>' . \"\\n\";\n";
    return src.replace(a, line('kurs-yevro-kharkiv') + line('kurs-zlotoho-kharkiv') + a);
  }
};
