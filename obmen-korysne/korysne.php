<?php
// Розділ «Корисне»: /korysne — список, /korysne/<slug> — стаття (21.11.2026). Російська — через ru.php (/ru/korysne)
require __DIR__ . '/korysne_lib.php';
$ru = korysne_ru();
function t($ua, $ru) { return korysne_ru() ? $ru : $ua; }
$slug = preg_replace('/[^a-z0-9\-]/', '', (string)($_GET['n'] ?? ''));
$all = korysne_all();
$item = $slug ? korysne_get($slug) : null;
if ($slug && !$item) http_response_code(404);
if ($item) { $title = $item['title'] . t(' — Обмін валют на Гагаріна, Харків', ' — Обмен валют на Гагарина, Харьков'); $desc = $item['desc']; $canon = SITE_URL . '/korysne/' . $item['slug']; }
else { $title = t('Корисне про валюту: як перевірити купюри, зношені долари, обмін — Харків', 'Полезное о валюте: как проверить купюры, изношенные доллары, обмен — Харьков');
       $desc = t('Короткі відповіді на часті питання про долари, євро і злоті: як перевірити купюру, що робити зі зношеними грошима, як обміняти велику суму', 'Короткие ответы на частые вопросы о долларах, евро и злотых: как проверить купюру, что делать с изношенными деньгами, как обменять крупную сумму');
       $canon = SITE_URL . '/korysne'; }
$r = current_rates();
?><!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title><?= e($title) ?></title>
<meta name="description" content="<?= e($desc) ?>">
<link rel="canonical" href="<?= e($canon) ?>">
<?php if ($slug && !$item) echo '<meta name="robots" content="noindex">'; ?>
<meta property="og:type" content="<?= $item ? 'article' : 'website' ?>">
<meta property="og:title" content="<?= e($item ? $item['title'] : $title) ?>">
<meta property="og:description" content="<?= e($desc) ?>">
<meta property="og:url" content="<?= e($canon) ?>">
<meta property="og:locale" content="uk_UA">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💱</text></svg>">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<?php if ($item): ?>
<script type="application/ld+json"><?= json_encode(['@context' => 'https://schema.org', '@type' => 'Article', 'headline' => $item['title'], 'datePublished' => $item['date'], 'dateModified' => ($item['updated'] ?? $item['date']), 'description' => $desc, 'mainEntityOfPage' => korysne_url($item), 'inLanguage' => $ru ? 'ru' : 'uk', 'author' => ['@type' => 'Organization', 'name' => 'Обмін Валют на Гагаріна'], 'publisher' => ['@type' => 'Organization', 'name' => 'Обмін Валют на Гагаріна', 'url' => SITE_URL]], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?></script>
<?php $fq = $ru ? ($item['faq_ru'] ?? null) : ($item['faq'] ?? null); if ($fq): /* 26.11.2026 FAQPage */ ?><script type="application/ld+json"><?= json_encode($fq, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?></script><?php endif; ?>
<?php endif; ?>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--gold:#D4A843;--gold2:#F0C050;--dark:#080808;--dark2:#0F0F0F;--dark3:#181818;--muted:#888;--green:#00D68F;--blue:#229ED9}
body{background:var(--dark);color:#fff;font-family:'Inter',sans-serif;min-height:100vh}
header{background:var(--dark2);border-bottom:2px solid var(--gold);padding:0 16px}
.hi{max-width:900px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:60px;gap:12px}
.logo{font-family:'Bebas Neue',sans-serif;font-size:1.6rem;letter-spacing:.1em;text-decoration:none}.logo .l1{color:var(--gold)}.logo .l2{color:#fff}
.tg-btn{background:var(--blue);color:#fff;font-size:.82rem;font-weight:700;padding:8px 14px;border-radius:6px;text-decoration:none}
main{max-width:900px;margin:0 auto;padding:28px 16px 40px}
.crumbs{font-size:.82rem;color:var(--muted);margin-bottom:18px}.crumbs a{color:var(--muted)}
h1{font-family:'Bebas Neue',sans-serif;font-size:clamp(1.9rem,5vw,2.8rem);letter-spacing:.04em;line-height:1.1;color:#fff;margin-bottom:10px}
.date{color:var(--muted);font-size:.85rem;margin-bottom:22px}
article p,article li{font-size:1.05rem;line-height:1.75;color:#ddd}article p{margin-bottom:16px}
article h2{font-family:'Bebas Neue',sans-serif;letter-spacing:.05em;color:var(--gold);font-size:1.6rem;margin:26px 0 10px}
article ul,article ol{padding-left:22px;margin:0 0 16px}article li{margin:6px 0}article b{color:#fff}
article .box{background:var(--dark2);border-left:4px solid var(--gold);border-radius:8px;padding:14px 16px;margin:14px 0 18px;color:#eee;line-height:1.7}
.list a.it{display:block;background:var(--dark2);border:1px solid #1e1e1e;border-radius:12px;padding:18px 20px;margin-bottom:12px;text-decoration:none;color:#fff;transition:border-color .2s}
.list a.it:hover{border-color:rgba(212,168,67,.4)}
.it b{display:block;font-size:1.1rem;margin-bottom:6px}.it p{color:#aaa;font-size:.92rem;line-height:1.6;margin-top:6px}
.rbox{background:var(--dark2);border:1px solid rgba(212,168,67,.25);border-radius:12px;padding:18px 20px;margin:26px 0}
.rbox h2{font-family:'Bebas Neue',sans-serif;letter-spacing:.06em;color:var(--gold);font-size:1.4rem;margin-bottom:10px}
.rt{width:100%;border-collapse:collapse}.rt td,.rt th{padding:8px 6px;border-bottom:1px solid #222;text-align:right;font-size:.95rem}.rt td:first-child,.rt th:first-child{text-align:left}.rt th{color:var(--muted);font-weight:600;font-size:.78rem}
.note{color:var(--muted);font-size:.8rem;margin-top:10px;line-height:1.6}
.cta{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.cta a{background:var(--gold);color:#000;font-weight:800;text-decoration:none;padding:11px 18px;border-radius:8px;font-size:.92rem}.cta a.tg{background:var(--blue);color:#fff}
.more a{display:block;color:var(--gold);text-decoration:none;padding:8px 0;border-bottom:1px solid #1a1a1a}
.empty{color:var(--muted)}
footer{border-top:1px solid #111;padding:22px 16px;text-align:center;background:var(--dark2);color:var(--muted);font-size:.8rem;line-height:1.7}
</style>
</head>
<body>
<header><div class="hi"><a class="logo" href="/"><span class="l1">ОБМІН</span> <span class="l2">ГАГАРІНА</span></a><a class="tg-btn" href="https://t.me/+osaN6D0LEPBlNzA6" target="_blank" rel="noopener">Telegram</a></div></header>
<main>
<?php if ($item): ?>
<div class="crumbs"><a href="/"><?= t('Головна', 'Главная') ?></a> › <a href="/korysne"><?= t('Корисне', 'Полезное') ?></a></div>
<article>
<h1><?= e($item['title']) ?></h1>
<div class="date"><?= e(news_date_ua($item['date'])) ?></div>
<?= $item['html'] ?>
</article>
<?php $other = array_filter($all, function ($n) use ($item) { return $n['slug'] !== $item['slug']; });
if ($other) { echo '<div class="rbox more"><h2>' . t('Ще корисне', 'Ещё полезное') . '</h2>';
  foreach (array_slice($other, 0, 5) as $n) echo '<a href="/korysne/' . e($n['slug']) . '">→ ' . e($n['title']) . '</a>';
  echo '<a href="/novyny">→ ' . t('Новини про курс валют', 'Новости о курсе валют') . '</a></div>'; } ?>
<?php elseif ($slug): ?>
<h1><?= t('Статтю не знайдено', 'Статья не найдена') ?></h1><p class="empty"><a href="/korysne" style="color:var(--gold)"><?= t('Усі статті', 'Все статьи') ?></a></p>
<?php else: ?>
<div class="crumbs"><a href="/"><?= t('Головна', 'Главная') ?></a> › <?= t('Корисне', 'Полезное') ?></div>
<h1><?= t('Корисне про валюту', 'Полезное о валюте') ?></h1>
<p class="date"><?= t('Як перевірити купюру, що робити зі зношеними грошима, як обміняти велику суму — коротко і по суті', 'Как проверить купюру, что делать с изношенными деньгами, как обменять крупную сумму — коротко и по делу') ?></p>
<div class="list">
<?php if (!$all) echo '<p class="empty">' . t('Статті скоро з’являться', 'Статьи скоро появятся') . '</p>';
foreach ($all as $n) echo '<a class="it" href="/korysne/' . e($n['slug']) . '"><b>' . e($n['title']) . '</b><p>' . e($n['desc']) . '</p></a>'; ?>
</div>
<?php endif; ?>
<?php if ($r): ?>
<div class="rbox">
<h2><?= t('Курс у нашому обміннику зараз', 'Курс в нашем обменнике сейчас') ?></h2>
<table class="rt"><tr><th><?= t('Валюта', 'Валюта') ?></th><th><?= t('Купівля', 'Покупка') ?></th><th><?= t('Продаж', 'Продажа') ?></th></tr>
<?php foreach (['USD' => t('🇺🇸 Долар', '🇺🇸 Доллар'), 'EUR' => t('🇪🇺 Євро', '🇪🇺 Евро'), 'PLN' => t('🇵🇱 Злотий', '🇵🇱 Злотый')] as $k => $nm) if (isset($r[$k])) echo '<tr><td>' . $nm . '</td><td>' . number_format($r[$k]['buy'], 2, '.', '') . '</td><td>' . number_format($r[$k]['sell'], 2, '.', '') . '</td></tr>'; ?>
</table>
<p class="note"><?= t('Курси для обміну від $500', 'Курсы для обмена от $500') ?><?= !empty($r['updated']) ? t(' · оновлено ', ' · обновлено ') . e($r['updated']) : '' ?>. <?= t('Харків, Аерокосмічний просп. (Гагаріна), 41/2 · щодня 09:00–18:45', 'Харьков, Аэрокосмический просп. (Гагарина), 41/2 · ежедневно 09:00–18:45') ?></p>
<div class="cta"><a href="tel:+380503130002">📞 +380 50 313 00 02</a><a href="tel:+380684580002">📞 +380 68 458 00 02</a><a class="tg" href="https://t.me/+osaN6D0LEPBlNzA6" target="_blank" rel="noopener"><?= t('Курси в Telegram', 'Курсы в Telegram') ?></a></div>
</div>
<?php endif; ?>
</main>
<footer>© 2026 <?= t('Обмін Валют на Гагаріна · Харків · Всі курси носять інформаційний характер<br>Працюємо лише з готівковою валютою. Операції з криптовалютою не здійснюємо', 'Обмен Валют на Гагарина · Харьков · Все курсы носят информационный характер<br>Работаем только с наличной валютой. Операции с криптовалютой не осуществляем') ?></footer>
<script>
(function(){try{var q=new URLSearchParams(location.search);var d=JSON.stringify({p:location.pathname,r:document.referrer,s:q.get('src')||q.get('utm_source')||''});if(navigator.sendBeacon){navigator.sendBeacon('/hit.php',new Blob([d],{type:'application/json'}))}else{fetch('/hit.php',{method:'POST',body:d,keepalive:true})}}catch(e){}})();
</script>
<script src="/i18n.js?v=4" defer></script>
</body>
</html>
