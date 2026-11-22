<?php
// Функции сайта (/go/, /p/, /tg/, /montazh/start) живут на Cloudflare. NetX передаёт запрос туда и отдаёт ответ (с 22.11.2026)
$up = 'https://kalmykovgroup.pages.dev' . $_SERVER['REQUEST_URI'];
$h = ['X-Forwarded-For: ' . ($_SERVER['REMOTE_ADDR'] ?? '')];
foreach (['CONTENT_TYPE' => 'Content-Type', 'HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN' => 'X-Telegram-Bot-Api-Secret-Token', 'HTTP_USER_AGENT' => 'User-Agent', 'HTTP_ACCEPT_LANGUAGE' => 'Accept-Language', 'HTTP_REFERER' => 'Referer'] as $k => $n)
  if (!empty($_SERVER[$k])) $h[] = "$n: " . $_SERVER[$k];
$c = curl_init($up);
$m = $_SERVER['REQUEST_METHOD'] ?? 'GET';
curl_setopt_array($c, [CURLOPT_RETURNTRANSFER => 1, CURLOPT_HEADER => 1, CURLOPT_FOLLOWLOCATION => 0, CURLOPT_TIMEOUT => 55, CURLOPT_CUSTOMREQUEST => $m, CURLOPT_HTTPHEADER => $h]);
if ($m !== 'GET' && $m !== 'HEAD') curl_setopt($c, CURLOPT_POSTFIELDS, file_get_contents('php://input'));
$r = curl_exec($c);
if ($r === false) { http_response_code(502); echo 'Временная ошибка, обновите страницу'; exit; }
$code = curl_getinfo($c, CURLINFO_HTTP_CODE); $hs = curl_getinfo($c, CURLINFO_HEADER_SIZE); curl_close($c);
http_response_code($code);
foreach (explode("\r\n", substr($r, 0, $hs)) as $l)
  if (preg_match('/^(location|content-type|cache-control|content-disposition):/i', $l)) header($l, false);
echo substr($r, $hs);
