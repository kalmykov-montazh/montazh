<?php
// Історія курсів для графіка на головній: по одному значенню на день (останнє за день)
date_default_timezone_set('Europe/Kyiv');
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: public, max-age=300');
$f = __DIR__ . '/_data/rates_hist.json';
$h = file_exists($f) ? json_decode(file_get_contents($f), true) : [];
if (!is_array($h)) $h = [];
$days = [];
foreach ($h as $x) {
    if (empty($x['t'])) continue;
    $d = substr($x['t'], 0, 10);
    $row = ['d' => $d];
    foreach (['USD', 'EUR', 'PLN'] as $k) if (isset($x[$k])) $row[$k] = $x[$k];
    $days[$d] = isset($days[$d]) ? array_merge($days[$d], $row) : $row;
}
ksort($days);
$days = array_values($days);
// Вчорашнє закриття — для стрілочок «від вчора»
$today = date('Y-m-d');
$prev = null;
foreach ($days as $r) if ($r['d'] < $today) $prev = $r;
echo json_encode(['days' => array_slice($days, -400), 'prev' => $prev], JSON_UNESCAPED_UNICODE);
