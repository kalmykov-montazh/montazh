<?php
// Переклад сторінок на російську для /ru/... (17.11.2026). Словник — i18n_dict.json (той самий, що в i18n.js)
// D — точні збіги цілого тексту, S — фрази всередині тексту (з межами слів), довші спочатку

function i18n_dict() {
    static $d = null;
    if ($d === null) {
        $d = json_decode((string)@file_get_contents(__DIR__ . '/i18n_dict.json'), true);
        if (!is_array($d)) $d = ['D' => [], 'S' => []];
    }
    return $d;
}

// Переклад звичайного рядка (без HTML)
function i18n_tr($s) {
    $t = trim(preg_replace('/\s+/u', ' ', (string)$s));
    if ($t === '') return $s;
    $d = i18n_dict();
    if (isset($d['D'][$t])) return $d['D'][$t];
    $o = $t;
    $L = 'а-яА-ЯіІїЇєЄґҐёЁa-zA-Z';
    foreach ($d['S'] as $pair) {
        if (mb_strpos($o, $pair[0]) === false) continue;
        $ru = $pair[1];
        $o = preg_replace_callback('/(^|[^' . $L . '])' . preg_quote($pair[0], '/') . '(?![' . $L . '])/u',
            function ($m) use ($ru) { return $m[1] . $ru; }, $o);
    }
    return $o === $t ? $s : $o;
}

// Переклад текстового вузла HTML (з сутностями)
function i18n_tr_html($raw) {
    if (trim($raw) === '' || !preg_match('/[А-Яа-яІіЇїЄєҐґ]/u', $raw)) return $raw;
    $plain = html_entity_decode($raw, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    $ru = i18n_tr($plain);
    if ($ru === $plain) return $raw;
    preg_match('/^\s*/u', $raw, $a); preg_match('/\s*$/u', $raw, $b);
    return $a[0] . htmlspecialchars(trim($ru), ENT_NOQUOTES, 'UTF-8') . $b[0];
}

function i18n_json_walk($v, $k = null) {
    if (is_array($v)) { foreach ($v as $kk => $vv) $v[$kk] = i18n_json_walk($vv, $kk); return $v; }
    if ($k === 'inLanguage') return 'ru';
    return is_string($v) ? i18n_tr($v) : $v;
}

// Посилання всередині сайту → російська версія
function i18n_ru_href($h) {
    if ($h === '' || $h[0] !== '/' || substr($h, 0, 2) === '//' || preg_match('#^/ru(/|$|\?)#', $h)) return $h;
    $parts = preg_split('/(?=[?#])/', $h, 2);
    $path = $parts[0]; $rest = $parts[1] ?? '';
    if ($path === '/novyny.php') $path = '/novyny';
    if ($path === '/index.html') $path = '/';
    $last = basename($path);
    if (strpos($last, '.') !== false) return $h;   // файли: картинки, js, css
    return ($path === '/' ? '/ru/' : '/ru' . $path) . $rest;
}

function i18n_tag($tag) {
    if (preg_match('/^<html\b/i', $tag)) return preg_replace('/\blang="uk"/', 'lang="ru"', $tag);
    $tag = preg_replace_callback('/\b(content|placeholder|title|aria-label|alt)="([^"]*)"/u', function ($m) {
        if (!preg_match('/[А-Яа-яІіЇїЄєҐґ]/u', $m[2])) return $m[0];
        $plain = html_entity_decode($m[2], ENT_QUOTES | ENT_HTML5, 'UTF-8');
        return $m[1] . '="' . htmlspecialchars(i18n_tr($plain), ENT_QUOTES, 'UTF-8') . '"';
    }, $tag);
    if (strpos($tag, 'og:locale') !== false) $tag = str_replace('uk_UA', 'ru_UA', $tag);
    if (preg_match('/rel="canonical"|property="og:url"/', $tag))
        $tag = preg_replace('#(https://obmen-gagarina\.site)(?!/ru(/|"))(/[^"]*)?"#', '$1/ru$3"', $tag);
    if (preg_match('/^<a\b|^<link\b/i', $tag) && !preg_match('/rel="(canonical|alternate|icon|apple-touch-icon|manifest|stylesheet|preconnect)"/', $tag))
        $tag = preg_replace_callback('/\bhref="([^"]*)"/', function ($m) { return 'href="' . i18n_ru_href($m[1]) . '"'; }, $tag);
    return $tag;
}

function i18n_translate_html($html, $uaPath, $ruPath) {
    $parts = preg_split('/(<script\b[^>]*>.*?<\/script>|<style\b[^>]*>.*?<\/style>|<!--.*?-->|<[^>]+>)/is', $html, -1, PREG_SPLIT_DELIM_CAPTURE);
    $out = '';
    foreach ($parts as $p) {
        if ($p === '') continue;
        if (stripos($p, '<script') === 0) {
            if (stripos($p, 'application/ld+json') !== false && preg_match('/^(<script[^>]*>)(.*)(<\/script>)$/is', $p, $m)) {
                $j = json_decode($m[2], true);
                $p = is_array($j) ? $m[1] . json_encode(i18n_json_walk($j), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . $m[3] : $p;
            } else {
                $p = str_replace("fetch('/novyny.php?format=json", "fetch('/ru/novyny?format=json", $p);
            }
        } elseif (stripos($p, '<style') === 0 || strpos($p, '<!--') === 0) {
            // без змін
        } elseif ($p[0] === '<') {
            $p = i18n_tag($p);
        } else {
            $p = i18n_tr_html($p);
        }
        $out .= $p;
    }
    $site = 'https://obmen-gagarina.site';
    $head = '<link rel="alternate" hreflang="uk" href="' . $site . $uaPath . '">' . "\n"
          . '<link rel="alternate" hreflang="ru" href="' . $site . $ruPath . '">' . "\n"
          . '<link rel="alternate" hreflang="x-default" href="' . $site . $uaPath . '">' . "\n"
          . '<script>window.I18N=' . json_encode(i18n_dict(), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . ';</script>' . "\n";
    $out = preg_replace('/<\/head>/i', $head . '</head>', $out, 1);
    if (strpos($out, '/i18n.js') === false)
        $out = preg_replace('/<\/body>/i', '<script src="/i18n.js?v=3" defer></script>' . "\n" . '</body>', $out, 1);
    return $out;
}
