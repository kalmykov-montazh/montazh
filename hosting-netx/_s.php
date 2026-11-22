<?php
date_default_timezone_set('Europe/Madrid');
// Короткие ссылки из шапок соцсетей (/ig, /fb, /tt…): записываем переход и показываем страницу (с 22.11.2026, вместо счётчика Cloudflare)
$src = preg_replace('/[^a-z0-9-]/', '', $_GET['src'] ?? '');
$f = ($_GET['f'] ?? '') === 'ua.html' ? 'ua.html' : 'index.html';
@mkdir(__DIR__ . '/_data', 0755, true);
$ref = str_replace(["\t", "\n"], ' ', substr($_SERVER['HTTP_REFERER'] ?? '', 0, 200));
$ua = (stripos($_SERVER['HTTP_USER_AGENT'] ?? '', 'mobi') !== false) ? 'тел' : 'комп';
file_put_contents(__DIR__ . '/_data/hits-' . date('Y-m') . '.log', date('Y-m-d H:i:s') . "\t$src\t$ua\t$ref\n", FILE_APPEND | LOCK_EX);
header('Content-Type: text/html; charset=utf-8'); header('Cache-Control: no-cache');
readfile(__DIR__ . '/' . $f);
