<?php
// Кількість підписників Telegram-каналу (кеш 6 годин)
header('Content-Type: application/json; charset=utf-8');
$cf = __DIR__ . '/_data/tg_count.json';
$c = file_exists($cf) ? json_decode(file_get_contents($cf), true) : null;
if ($c && time() - ($c['ts'] ?? 0) < 21600) { echo json_encode(['n' => $c['n']]); exit; }
$n = $c['n'] ?? null;
$ctx = stream_context_create(['http' => ['timeout' => 6, 'header' => "User-Agent: Mozilla/5.0\r\n"]]);
$html = @file_get_contents('https://t.me/obmen_gagarina', false, $ctx);
if ($html && preg_match('/tgme_page_extra">\s*([\d\s ]+)\s*(subscriber|member|підписник|подписчик)/u', $html, $m)) {
    $n = (int)preg_replace('/\D/', '', $m[1]);
}
if ($n) file_put_contents($cf, json_encode(['n' => $n, 'ts' => time()]));
echo json_encode(['n' => $n]);
