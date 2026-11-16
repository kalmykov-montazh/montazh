<?php
// Картинка-превью з поточним курсом (для посилань у Telegram, Viber, Facebook). Кеш до зміни курсу
date_default_timezone_set('Europe/Kyiv');
$r = json_decode(@file_get_contents(__DIR__ . '/rates.json'), true);
$cache = __DIR__ . '/_data/og_cache.png';
$key = __DIR__ . '/_data/og_cache.key';
$k = md5(json_encode($r) . '3');
header('Content-Type: image/png');
header('Cache-Control: public, max-age=600');
if (file_exists($cache) && @file_get_contents($key) === $k) { readfile($cache); exit; }
$im = @imagecreatefrompng(__DIR__ . '/og_bg.png');
if (!$im || !$r) { readfile(__DIR__ . '/og.png'); exit; }
$f8 = __DIR__ . '/og_f800.ttf'; $f6 = __DIR__ . '/og_f600.ttf';
$green = imagecolorallocate($im, 0, 214, 143);
$white = imagecolorallocate($im, 255, 255, 255);
$mut = imagecolorallocate($im, 147, 160, 184);
function rtext($im, $size, $x, $y, $col, $font, $t) {
    $b = imagettfbbox($size, 0, $font, $t);
    imagettftext($im, $size, 0, $x - ($b[2] - $b[0]), $y, $col, $font, $t);
}
$rows = ['USD', 'EUR', 'PLN'];
foreach ($rows as $i => $c) {
    if (!isset($r[$c])) continue;
    $y = 255 + $i * 85 + 52;
    rtext($im, 42, 720, $y, $green, $f8, number_format($r[$c]['buy'], 2, '.', ''));
    rtext($im, 42, 1090, $y, $white, $f8, number_format($r[$c]['sell'], 2, '.', ''));
}
$upd = !empty($r['updated']) ? 'Курс на ' . substr($r['updated'], 0, 5) . ' ' . substr($r['updated'], 11, 5) : 'Курс сьогодні';
imagettftext($im, 17, 0, 100, 232, $mut, $f6, $upd . ' · опт від $500');
ob_start(); imagepng($im); $png = ob_get_clean(); imagedestroy($im);
@file_put_contents($cache, $png); @file_put_contents($key, $k);
echo $png;
