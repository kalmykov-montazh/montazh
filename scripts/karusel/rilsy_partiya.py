# 14.11.2026 (Евгений 00:02: «делай все 5»): рилсы с музыкой из старых каруселей — пачкой.
#   python3 scripts/karusel/rilsy_partiya.py karuseli/rilsy_1411.json
# Для каждой папки «Брокер/Посты/Карусели/<папка>»:
#  1) собрать reel.mp4 (slajdshou.py: музыка, наезд, сайт, петля) и положить в папку на Диск;
#  2) Blotato: Instagram Reels + TikTok видео на "at", записать _рилс.json (его смотрит сторож);
#  3) "youtube_update": карусель ещё не вышла — в её отложенном YouTube Shorts заменить видео на новое (со звуком),
#     и shorts.mp4 на Диске заменить тоже;
#  4) Facebook — задание роботу «Брокер/К публикации/_задания/ГГГГ-ММ-ДД_ЧЧММ_fb_РИЛС <папка>.json»
#     (kind arenda = рилс из папки карусели + группы в окне Reels, mode live).
# Итог — out/итог.json и кадры out/*.jpg (для проверки Claude).
import json, sys, os, subprocess, pathlib, datetime, urllib.request, urllib.error, shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
API = 'https://backend.blotato.com/v2'
ACC = {'instagram': '80093', 'tiktok': '65164', 'youtube': '54490'}
KEY = open('key.txt', encoding='utf-8-sig').read().strip()
OUT = pathlib.Path('out'); OUT.mkdir(exist_ok=True)
TT = {'targetType': 'tiktok', 'privacyLevel': 'PUBLIC_TO_EVERYONE', 'disabledComments': False, 'disabledDuet': False,
      'disabledStitch': False, 'isBrandedContent': False, 'isYourBrand': False, 'isAiGenerated': False,
      'isDraft': False, 'autoAddMusic': False}


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={'blotato-api-key': KEY, 'Content-Type': 'application/json', 'accept': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return json.loads(resp.read() or b'{}')
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path}: {e.code} {e.read()[:400].decode('utf-8', 'replace')}")


def upload(p):
    up = req('POST', '/media/uploads', {'filename': 'video.mp4'})
    r = urllib.request.Request(up['presignedUrl'], data=p.read_bytes(), method='PUT', headers={'Content-Type': 'video/mp4'})
    with urllib.request.urlopen(r, timeout=1800) as resp:
        if resp.status >= 300: raise RuntimeError(f'загрузка {p}: {resp.status}')
    return up['publicUrl']


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True)


def schedules():
    items, cur = [], None
    while True:
        r = req('GET', '/schedules?limit=50' + (f'&cursor={cur}' if cur else ''))
        items += r.get('items', []); cur = r.get('cursor')
        if not cur: return items


def when(it):
    try:
        return datetime.datetime.fromisoformat(str(it.get('scheduledAt') or it.get('scheduledTime')).replace('Z', '+00:00'))
    except Exception:
        return None


cfg = json.load(open(sys.argv[1], encoding='utf-8'))
dry = '--dry' in sys.argv
res = []
sched = None
for it in cfg['items']:
    name = it['folder']; r = {'folder': name}
    D = pathlib.Path('k') / name; D.mkdir(parents=True, exist_ok=True)
    remote = f"montazh:Брокер/Посты/Карусели/{name}"
    try:
        sh('rclone', 'copy', remote, str(D), '--include', '[0-9][0-9].jpg', '--include', 'spec.json',
           '--include', 'karusel.json', '--include', '_отправлено.json', '--include', 'karusel_slajdy.json')
        p = subprocess.run(['python3', str(ROOT / 'scripts/karusel/slajdshou.py'), str(D), str(D / 'reel.mp4')],
                           capture_output=True, text=True)
        r['sborka'] = (p.stdout + p.stderr).strip()[-300:]
        v = D / 'reel.mp4'
        if not v.exists(): raise RuntimeError('reel.mp4 не собрался: ' + r['sborka'])
        vol = sh('ffmpeg', '-hide_banner', '-i', str(v), '-af', 'volumedetect', '-f', 'null', '-').stderr
        r['zvuk'] = ' '.join(l.split('] ')[-1] for l in vol.splitlines() if 'mean_volume' in l or 'max_volume' in l)
        dur = float(sh('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(v)).stdout or 0)
        r['dlit'] = round(dur, 1)
        n = int(dur * 30)
        sel = '+'.join(f'eq(n\\,{k})' for k in (15, n // 3, 2 * n // 3, n - 40, n - 3))
        sh('ffmpeg', '-loglevel', 'error', '-y', '-i', str(v), '-vf', f"select='{sel}',scale=216:384,tile=5x1",
           '-frames:v', '1', '-update', '1', str(OUT / f'{name}.jpg'))
        sh('rclone', 'copyto', str(v), f'{remote}/reel.mp4')
        sh('rclone', 'copyto', str(D / '_музыка.txt'), f'{remote}/_музыка.txt')
        if dry:
            r['dry'] = True; res.append(r); continue
        url = upload(v)
        posts = {}
        for net, tgt in (('instagram', {'targetType': 'instagram', 'mediaType': 'reel'}), ('tiktok', TT)):
            body = {'post': {'accountId': ACC[net], 'content': {'text': it['text'], 'mediaUrls': [url], 'platform': net},
                             'target': tgt}, 'scheduledTime': it['at']}
            try:
                x = req('POST', '/posts', body)
                posts[net] = {'id': x.get('postSubmissionId'), 'account': ACC[net], 'target': tgt}
            except Exception as ex:
                posts[net] = {'error': str(ex)[:300]}
        r['blotato'] = posts
        (D / '_рилс.json').write_text(json.dumps({'at': it['at'], 'text': it['text'], 'video': 'reel.mp4', 'posts': posts},
                                                ensure_ascii=False, indent=1), encoding='utf-8')
        sh('rclone', 'copyto', str(D / '_рилс.json'), f'{remote}/_рилс.json')
        if it.get('youtube_update'):
            kc = json.loads((D / 'karusel.json').read_text(encoding='utf-8-sig'))
            k_at = datetime.datetime.fromisoformat(kc['at'])
            if sched is None: sched = schedules()
            hit = []
            for s in sched:
                d = s.get('draft') or {}
                if (d.get('target') or {}).get('targetType') != 'youtube': continue
                w = when(s)
                if w and abs(w - k_at) <= datetime.timedelta(minutes=3):
                    nd = json.loads(json.dumps(d)); nd.setdefault('content', {})['mediaUrls'] = [url]
                    req('PATCH', f"/schedules/{s['id']}", {'patch': {'draft': nd}}); hit.append(s['id'])
            r['youtube_zamena'] = hit or 'НЕ НАЙДЕН в расписании Blotato'
            if hit: sh('rclone', 'copyto', str(v), f'{remote}/shorts.mp4')
        at = datetime.datetime.fromisoformat(it['at'])
        job = {'platform': 'fb', 'kind': 'arenda', 'mode': 'live', 'folder': f'../Посты/Карусели/{name}',
               'video': 'reel.mp4', 'cover_file': '01.jpg', 'date': f'{at:%Y-%m-%d}', 'time': f'{at:%H:%M}',
               'text': it['text'], 'groups': it.get('groups', [])}
        jn = f'{at:%Y-%m-%d_%H%M}_fb_РИЛС {name}.json'
        (OUT / jn).write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding='utf-8')
        cp = sh('rclone', 'copyto', str(OUT / jn), f'montazh:Брокер/К публикации/_задания/{jn}')
        r['fb_zadanie'] = jn if cp.returncode == 0 else 'ОШИБКА ' + cp.stderr[-200:]
    except Exception as ex:
        r['OSHIBKA'] = str(ex)[:400]
    res.append(r)
    print(json.dumps(r, ensure_ascii=False))
(OUT / 'итог.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
