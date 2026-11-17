<?php
// Карта сайту для Google, оновлюється сама з кожною новиною
// З 17.11.2026: українська і російська версії з hreflang (uk — основна і x-default, ru — /ru/...)
require __DIR__ . '/news_lib.php';
header('Content-Type: application/xml; charset=utf-8');
$all = news_all();
$last = $all ? date('Y-m-d', strtotime($all[0]['date'])) : date('Y-m-d', filemtime(__DIR__ . '/index.html'));
$rd = date('Y-m-d', filemtime(__DIR__ . '/rates.json'));
function sm_pair($ua, $ru, $lastmod, $freq, $prio) {
    $alt = '<xhtml:link rel="alternate" hreflang="uk" href="' . e(SITE_URL . $ua) . '"/>'
         . ($ru ? '<xhtml:link rel="alternate" hreflang="ru" href="' . e(SITE_URL . $ru) . '"/>' : '')
         . '<xhtml:link rel="alternate" hreflang="x-default" href="' . e(SITE_URL . $ua) . '"/>';
    $tail = '<lastmod>' . $lastmod . '</lastmod>' . ($freq ? '<changefreq>' . $freq . '</changefreq>' : '') . '<priority>' . $prio . '</priority>';
    $out = '<url><loc>' . e(SITE_URL . $ua) . '</loc>' . ($ru ? $alt : '') . $tail . "</url>\n";
    if ($ru) $out .= '<url><loc>' . e(SITE_URL . $ru) . '</loc>' . $alt . $tail . "</url>\n";
    return $out;
}
echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">' . "\n";
echo sm_pair('/', '/ru/', $rd, 'daily', '1.0');
foreach (['kurs-dolara-kharkiv', 'kurs-yevro-kharkiv', 'kurs-zlotoho-kharkiv'] as $pg) echo sm_pair('/' . $pg, '/ru/' . $pg, $rd, 'hourly', '0.9');
echo sm_pair('/novyny', '/ru/novyny', $last, 'daily', '0.8');
foreach ($all as $n) {
    $ru = (!empty($n['title_ru']) && !empty($n['text_ru'])) ? '/ru/novyny/' . $n['slug'] : null;
    echo sm_pair('/novyny/' . $n['slug'], $ru, date('Y-m-d', strtotime($n['date'])), '', '0.6');
}
echo '</urlset>';
