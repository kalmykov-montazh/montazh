# 16.11.2026 (Евгений 19:36: «рилсы из каруселей… которые ещё не опубликованные… поменяй музыку»):
# во всех ещё не вышедших видео из каруселей своя синтезированная музыка меняется на FreePD (CC0).
#   python3 scripts/karusel/zamena_muzyki.py [--dry]
# Что меняется (видео не перекодируется, только звук):
#  1) reel.mp4 — если рилс этой папки ещё впереди (_рилс.json «at» или задание FB «*_fb_РИЛС <папка>.json» в будущем);
#     в Blotato у отложенных Instagram/TikTok этого рилса видео заменяется на новое (PATCH /schedules);
#  2) shorts.mp4 — если карусель ещё впереди (karusel.json «at»); в Blotato у отложенного YouTube видео заменяется.
# Facebook робот берёт файл с Диска в момент публикации — ему хватает замены файла.
# Старые файлы — «Брокер/работа/Рилсы каруселей — старая музыка (16.11.2026)/<папка>/».
import json, sys, os, subprocess, pathlib, datetime, re, urllib.request, urllib.error
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from slajdshou import freepd_audio, FREEPD

DRY = '--dry' in sys.argv
# 25.11.2026: --tolko=<часть названия трека> — менять только там, где в _музыка.txt стоит этот трек
# (City Sunshine получил заявку Content ID на YouTube). Без ключа — как раньше, все невышедшие.
TOLKO = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--tolko=')), '').lower()
K = 'montazh:Брокер/Посты/Карусели'
ZAD = 'montazh:Брокер/К публикации/_задания'
BK = 'montazh:Брокер/работа/Рилсы каруселей — старая музыка (16.11.2026)' + (' — City Sunshine 25.11' if any(a.startswith('--tolko=') for a in sys.argv) else '')
API = 'https://backend.blotato.com/v2'
KEY = open('key.txt', encoding='utf-8-sig').read().strip()
NOW = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=20)


def sh(*a): return subprocess.run(a, capture_output=True, text=True)


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={'blotato-api-key': KEY, 'Content-Type': 'application/json', 'accept': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=120) as resp: return json.loads(resp.read() or b'{}')
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path}: {e.code} {e.read()[:300].decode('utf-8', 'replace')}")


def upload(p):
    up = req('POST', '/media/uploads', {'filename': 'video.mp4'})
    r = urllib.request.Request(up['presignedUrl'], data=p.read_bytes(), method='PUT', headers={'Content-Type': 'video/mp4'})
    with urllib.request.urlopen(r, timeout=1800) as resp:
        if resp.status >= 300: raise RuntimeError(f'загрузка {p}: {resp.status}')
    return up['publicUrl']


def schedules():
    items, cur = [], None
    while True:
        r = req('GET', '/schedules?limit=50' + (f'&cursor={cur}' if cur else ''))
        items += r.get('items', []); cur = r.get('cursor')
        if not cur: return items


def ts(x):
    try:
        d = datetime.datetime.fromisoformat(str(x).replace('Z', '+00:00'))
        return d if d.tzinfo else d.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=1)))
    except Exception: return None


def jcat(path):
    p = sh('rclone', 'cat', path)
    try: return json.loads(p.stdout.lstrip('﻿')) if p.returncode == 0 and p.stdout.strip() else None
    except Exception: return None


def dur(v): return float(sh('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(v)).stdout or 0)


SCHED = schedules()
print(f'Blotato: в расписании {len(SCHED)} постов')
zad = sh('rclone', 'lsf', ZAD, '--files-only').stdout.splitlines()
folders = [f.rstrip('/') for f in sh('rclone', 'lsf', K, '--dirs-only').stdout.splitlines()]
W = pathlib.Path('zm'); W.mkdir(exist_ok=True)
res, n_trek = [], 0
for name in sorted(folders):
    files = sh('rclone', 'lsf', f'{K}/{name}', '--files-only').stdout.splitlines()
    ril = jcat(f'{K}/{name}/_рилс.json') if '_рилс.json' in files else None
    kar = jcat(f'{K}/{name}/karusel.json') if 'karusel.json' in files else None
    reel_at = [ts(ril['at'])] if ril and ril.get('at') else []
    for z in zad:  # задание FB «ГГГГ-ММ-ДД_ЧЧММ_fb_РИЛС <папка>.json»
        m = re.match(r'(\d{4}-\d\d-\d\d)_(\d\d)(\d\d)_fb_РИЛС (.+)\.json$', z)
        if m and m.group(4) == name:
            reel_at.append(datetime.datetime.fromisoformat(f'{m.group(1)}T{m.group(2)}:{m.group(3)}:00+01:00'))
    reel_at = [a for a in reel_at if a and a > NOW]
    kar_at = ts(kar.get('at')) if kar and kar.get('at') else None
    jobs = []
    if reel_at and 'reel.mp4' in files: jobs.append(('reel.mp4', ('instagram', 'tiktok'), reel_at))
    if kar_at and kar_at > NOW and 'shorts.mp4' in files: jobs.append(('shorts.mp4', ('youtube',), [kar_at]))
    if not jobs: continue
    if TOLKO:
        mt = sh('rclone', 'cat', f'{K}/{name}/_музыка.txt').stdout if '_музыка.txt' in files else ''
        if TOLKO not in mt.lower(): continue
    trek = n_trek % len(FREEPD); n_trek += 1
    for fn, nets, ats in jobs:
        r = {'papka': name, 'fail': fn, 'kogda': [a.isoformat() for a in ats], 'trek': FREEPD[trek]}
        hits = [s for s in SCHED if ((s.get('draft') or {}).get('target') or {}).get('targetType') in nets
                and any(ts(s.get('scheduledAt') or s.get('scheduledTime')) and
                        abs(ts(s.get('scheduledAt') or s.get('scheduledTime')) - a) <= datetime.timedelta(minutes=3) for a in ats)]
        r['blotato_naideno'] = [f"{(s['draft'].get('target') or {}).get('targetType')} {s['id']} «{((s['draft'].get('content') or {}).get('text') or '')[:30]}»" for s in hits]
        if DRY: res.append(r); print(json.dumps(r, ensure_ascii=False)); continue
        try:
            v = W / f'{name}_{fn}'; o = W / f'{name}_new_{fn}'; wav = W / f'{name}_{fn}.wav'
            sh('rclone', 'copyto', f'{K}/{name}/{fn}', str(v))
            d = dur(v)
            src = freepd_audio(d, trek, str(wav))
            if not src: raise RuntimeError('трек не скачался')
            p = sh('ffmpeg', '-y', '-loglevel', 'error', '-i', str(v), '-i', str(wav), '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                   '-c:a', 'aac', '-b:a', '160k', '-t', f'{d:.3f}', '-movflags', '+faststart', str(o))
            if p.returncode: raise RuntimeError('ffmpeg: ' + p.stderr[-200:])
            r['dlit'] = f'{d:.1f} → {dur(o):.1f}'
            vol = sh('ffmpeg', '-hide_banner', '-i', str(o), '-af', 'volumedetect', '-f', 'null', '-').stderr
            r['zvuk'] = ' '.join(l.split('] ')[-1] for l in vol.splitlines() if 'mean_volume' in l)
            sh('rclone', 'copyto', str(v), f'{BK}/{name}/{fn}')
            if sh('rclone', 'copyto', str(o), f'{K}/{name}/{fn}').returncode: raise RuntimeError('не залилось на Диск')
            (W / 'm.txt').write_text(f'FreePD {src} (CC0), замена {datetime.date.today():%d.%m.%Y}, файл {fn}\n', encoding='utf-8')
            sh('rclone', 'copyto', str(W / 'm.txt'), f'{K}/{name}/_музыка.txt')
            if hits:
                url = upload(o); done = []
                for s in hits:
                    nd = json.loads(json.dumps(s['draft'])); nd.setdefault('content', {})['mediaUrls'] = [url]
                    req('PATCH', f"/schedules/{s['id']}", {'patch': {'draft': nd}}); done.append(s['id'])
                r['blotato_zameneno'] = done
            r['OK'] = True
        except Exception as ex:
            r['OSHIBKA'] = str(ex)[:300]
        res.append(r); print(json.dumps(r, ensure_ascii=False))
print(f'ИТОГО: {len(res)} файлов, ошибок {sum(1 for r in res if "OSHIBKA" in r)}')
