<?php
// Російська версія сайту: /ru/, /ru/kurs-..., /ru/novyny/... (17.11.2026)
// Українська — основна і відкривається за замовчуванням (закон № 2704, ст. 27), тут — переклад тих самих сторінок
define('NEWS_LANG', 'ru');
require __DIR__ . '/i18n_lib.php';
date_default_timezone_set('Europe/Kyiv');
$p = trim(preg_replace('/[^a-z0-9\-\/]/', '', (string)($_GET['p'] ?? '')), '/');
$pages = ['' => 'index.html', 'kurs-dolara-kharkiv' => 'kurs-dolara-kharkiv.php', 'kurs-yevro-kharkiv' => 'kurs-yevro-kharkiv.php',
          'kurs-zlotoho-kharkiv' => 'kurs-zlotoho-kharkiv.php', 'novyny' => 'novyny.php'];
$uaPath = $p === '' ? '/' : '/' . $p;
$ruPath = $p === '' ? '/ru/' : '/ru/' . $p;
if (preg_match('#^novyny/([a-z0-9\-]+)$#', $p, $m)) { $_GET['n'] = $m[1]; $p = 'novyny'; }
if (!isset($pages[$p])) { header('Location: /ru/', true, 302); exit; }
$GLOBALS['I18N_PATHS'] = [$uaPath, $ruPath];
ob_start(function ($html) {
    $t = ltrim($html);
    if ($t === '' || $t[0] === '[' || $t[0] === '{') return $html;   // JSON (?format=json) — без змін
    return i18n_translate_html($html, $GLOBALS['I18N_PATHS'][0], $GLOBALS['I18N_PATHS'][1]);
});
if ($p === '') { header('Content-Type: text/html; charset=utf-8'); readfile(__DIR__ . '/index.html'); }
else include __DIR__ . '/' . $pages[$p];
