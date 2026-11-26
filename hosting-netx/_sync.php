<?php
date_default_timezone_set('Europe/Madrid');
// Сайт kalmykovgroup.com на NetX (с 22.11.2026). Берёт папку sait/ из GitHub (kalmykov-montazh/montazh, ветка main)
// и раскладывает сюда. Запуск: задание cron раз в 3 минуты или открыть https://kalmykovgroup.com/_sync.php
// Функции (functions/) остаются на Cloudflare — их зовёт _proxy.php. Свои файлы (_sync, _proxy, _s, .htaccess, _data) не трогает.
set_time_limit(280);
$ROOT = __DIR__; $REPO = 'kalmykov-montazh/montazh'; $BR = 'main'; $PREFIX = 'sait';
$SKIP = '#^(functions/|_kg/|netlify\.toml$|_redirects$|_headers$|_sync|_proxy|_s\.php$|\.htaccess$|_data/)#';
@mkdir("$ROOT/_data", 0755, true);
$lock = fopen("$ROOT/_data/sync.lock", 'c');
if (!flock($lock, LOCK_EX | LOCK_NB)) exit("занято\n");
$stFile = "$ROOT/_data/sync.json";
$st = is_file($stFile) ? json_decode(file_get_contents($stFile), true) : [];
$force = isset($_GET['force']) || (isset($argv[1]) && $argv[1] === 'force');
if (PHP_SAPI !== 'cli' && !$force && time() - ($st['t'] ?? 0) < 20) exit("рано\n");
function req($url, $etag = null, &$code = 0, &$newEtag = null) {
  $h = ['User-Agent: kalmykovgroup-sync', 'Accept: application/vnd.github+json'];
  if ($etag) $h[] = "If-None-Match: $etag";
  $c = curl_init($url);
  curl_setopt_array($c, [CURLOPT_RETURNTRANSFER => 1, CURLOPT_HTTPHEADER => $h, CURLOPT_TIMEOUT => 60, CURLOPT_HEADER => 1, CURLOPT_FOLLOWLOCATION => 1]);
  $r = curl_exec($c); $code = curl_getinfo($c, CURLINFO_HTTP_CODE); $hs = curl_getinfo($c, CURLINFO_HEADER_SIZE); curl_close($c);
  if ($r === false) return null;
  if (preg_match('/^etag:\s*(\S+)/im', substr($r, 0, $hs), $m)) $newEtag = trim($m[1]);
  return substr($r, $hs);
}
function out($st, $stFile, $msg) { $st['t'] = time(); $st['msg'] = date('Y-m-d H:i:s') . ' ' . $msg; file_put_contents($stFile, json_encode($st, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)); echo $msg, "\n"; exit; }
$b = req("https://api.github.com/repos/$REPO/branches/$BR", $force ? null : ($st['etag'] ?? null), $code, $etag);
if ($code == 304) out($st, $stFile, 'без изменений');
if ($code != 200 || !$b) out($st, $stFile, "GitHub ответил $code");
$st['etag'] = $etag;
$j = json_decode($b, true); $commit = $j['commit']['sha']; $rootTree = $j['commit']['commit']['tree']['sha'];
$t = json_decode(req("https://api.github.com/repos/$REPO/git/trees/$rootTree", null, $code), true);
$saitSha = null; foreach ($t['tree'] ?? [] as $e) if ($e['path'] === $PREFIX) $saitSha = $e['sha'];
if (!$saitSha) out($st, $stFile, "нет папки $PREFIX ($code)");
if (!$force && ($st['sait'] ?? '') === $saitSha && is_file("$ROOT/.htaccess")) out($st, $stFile, 'папка сайта не менялась');
$t = json_decode(req("https://api.github.com/repos/$REPO/git/trees/$saitSha?recursive=1", null, $code), true);
if (empty($t['tree'])) out($st, $stFile, "не прочитал список файлов ($code)");
$old = $st['files'] ?? []; $new = []; $n = 0; $err = 0;
foreach ($t['tree'] as $e) {
  if ($e['type'] !== 'blob' || preg_match($SKIP, $e['path'])) continue;
  $p = $e['path']; $new[$p] = $e['sha'];
  if (($old[$p] ?? '') === $e['sha'] && is_file("$ROOT/$p")) continue;
  $url = "https://raw.githubusercontent.com/$REPO/$commit/$PREFIX/" . implode('/', array_map('rawurlencode', explode('/', $p)));
  $data = req($url, null, $code);
  if ($code != 200 || $data === null) { $err++; unset($new[$p]); continue; }
  @mkdir(dirname("$ROOT/$p"), 0755, true);
  file_put_contents("$ROOT/$p.tmp", $data); rename("$ROOT/$p.tmp", "$ROOT/$p"); $n++;
}
$del = 0;
foreach ($old as $p => $s) if (!isset($new[$p]) && !preg_match($SKIP, $p) && is_file("$ROOT/$p")) { unlink("$ROOT/$p"); $del++; }
// .htaccess: короткие ссылки из _redirects + общие правила
// 26.11.2026: PDF закрыты от Google (X-Robots-Tag noindex) — дублировали гайды, а бесплатное выдаём через бота
$red = req("https://raw.githubusercontent.com/$REPO/$commit/$PREFIX/_redirects", null, $code);
$short = [];
if ($code == 200) foreach (explode("\n", $red) as $l) {
  if (preg_match('#^/([a-z0-9-]+)\s+/(\S*)\s+200#', trim($l), $m)) $short[] = 'RewriteRule ^' . $m[1] . '/?$ _s.php?src=' . $m[1] . '&f=' . ($m[2] === 'ua' ? 'ua.html' : 'index.html') . ' [L,QSA]';
}
$https = is_file("$ROOT/_data/https.on");
$ht = "# Сгенерировано _sync.php — руками не править\nOptions -Indexes\nDirectoryIndex index.html index.php\nAddDefaultCharset UTF-8\nAddCharset UTF-8 .txt .html .xml .vcf\nAddType application/manifest+json .webmanifest\nRewriteEngine On\n";
if ($https) $ht .= "RewriteCond %{HTTPS} !=on\nRewriteCond %{HTTP:X-Forwarded-Proto} !https\nRewriteRule ^ https://kalmykovgroup.com%{REQUEST_URI} [L,R=301]\n";
$ht .= "RewriteCond %{HTTP_HOST} ^www\\. [NC]\nRewriteRule ^ https://kalmykovgroup.com%{REQUEST_URI} [L,R=301]\n";
$ht .= "RewriteRule ^\\.well-known/ - [L]\nRewriteRule ^_data(/|$) - [F,L]\nRewriteRule ^(go|p|tg)/ _proxy.php [L]\nRewriteRule ^montazh/start/?$ _proxy.php [L]\n";
$ht .= implode("\n", $short) . "\n";
$ht .= "RewriteCond %{REQUEST_FILENAME} !-f\nRewriteCond %{REQUEST_FILENAME}.html -f\nRewriteRule ^(.+?)/?$ $1.html [L]\n";
$ht .= "RewriteCond %{REQUEST_FILENAME} !-f\nRewriteCond %{REQUEST_FILENAME} !-d\nRewriteRule ^ index.html [L]\n";
$ht .= "<Files \"ssylki.txt\">\nHeader set X-Robots-Tag \"noindex\"\nHeader set Cache-Control \"no-cache\"\n</Files>\n<FilesMatch \"^tg-.*\\.jpg$\">\nHeader set Access-Control-Allow-Origin \"*\"\n</FilesMatch>\n<FilesMatch \"\\.pdf$\">\nHeader set X-Robots-Tag \"noindex, nofollow\"\n</FilesMatch>\n<FilesMatch \"\\.(html|txt|xml)$\">\nHeader set Cache-Control \"no-cache\"\n</FilesMatch>\n";
file_put_contents("$ROOT/.htaccess.tmp", $ht); rename("$ROOT/.htaccess.tmp", "$ROOT/.htaccess");
if (!$err) $st['sait'] = $saitSha;
$st['files'] = $new; $st['commit'] = $commit;
out($st, $stFile, "обновлено файлов $n, удалено $del, ошибок $err, коммит " . substr($commit, 0, 7));
