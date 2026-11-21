<?php
// Розділ «Корисне» (21.11.2026): статті беремо з GitHub (публічний репозиторій), кеш у _data/korysne.json на 20 хвилин.
// Нові статті кладе задача Claude у obmen-korysne/_src і збирає articles.json — на сайті нічого правити не треба.
require_once __DIR__ . '/news_lib.php';
const KORYSNE_SRC = 'https://raw.githubusercontent.com/kalmykov-montazh/montazh/main/obmen-korysne/articles.json';
function korysne_ru() { return defined('NEWS_LANG') && NEWS_LANG === 'ru'; }
function korysne_all() {
    $f = __DIR__ . '/_data/korysne.json';
    $old = file_exists($f) ? json_decode(file_get_contents($f), true) : null;
    if (!is_array($old) || time() - filemtime($f) > 1200) {
        $ctx = stream_context_create(['http' => ['timeout' => 5, 'header' => "User-Agent: obmen-gagarina\r\n"]]);
        $raw = @file_get_contents(KORYSNE_SRC . '?t=' . floor(time() / 1200), false, $ctx);
        $new = $raw ? json_decode($raw, true) : null;
        if (is_array($new)) { @file_put_contents($f, json_encode($new, JSON_UNESCAPED_UNICODE)); $old = $new; }
        elseif (file_exists($f)) @touch($f);
    }
    $a = is_array($old) ? $old : [];
    if (korysne_ru()) foreach ($a as $i => $n) { $a[$i]['title'] = $n['title_ru']; $a[$i]['desc'] = $n['desc_ru']; $a[$i]['html'] = $n['html_ru']; }
    return $a;
}
function korysne_get($slug) { foreach (korysne_all() as $n) if ($n['slug'] === $slug) return $n; return null; }
function korysne_url($n) { return SITE_URL . (korysne_ru() ? '/ru' : '') . '/korysne/' . $n['slug']; }
