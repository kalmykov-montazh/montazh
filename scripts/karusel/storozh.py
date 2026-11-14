# Сторож каруселей (07.11.2026): каждые 20 минут смотрит карусели, вышедшие за последние 48 часов.
# Рилсы из той же папки — по _рилс.json (с 07.11.2026), та же логика.
# Если какая-то сеть в Blotato упала (failed) — сам перевыкладывает её сразу (karusel.py retry), до 2 раз.
# Пишет Евгению в Telegram (@kalmykov_assistant_bot): что упало, что перевыложил, что так и не вышло.
import json, subprocess, sys, pathlib, datetime, urllib.request, urllib.error, urllib.parse

ROOT = 'montazh:Брокер/Посты/Карусели'
API = 'https://backend.blotato.com/v2'
KEY = open('key.txt', encoding='utf-8-sig').read().strip()
TG_CHAT = 8341379322
NAMES = {'instagram': 'Instagram', 'tiktok': 'TikTok', 'threads': 'Threads', 'youtube': 'YouTube'}

def rc(*a, check=True):
    return subprocess.run(['rclone', *a], capture_output=True, text=True, check=check).stdout

def tg(text):
    try:
        tok = pathlib.Path('tg.txt').read_text(encoding='utf-8-sig').strip()
        body = json.dumps({'chat_id': TG_CHAT, 'text': text[:3500]}).encode()
        urllib.request.urlopen(urllib.request.Request(f'https://api.telegram.org/bot{tok}/sendMessage', data=body,
                               headers={'Content-Type': 'application/json'}), timeout=30)
    except Exception as e:
        print('telegram не ушёл:', e)

def status(pid):
    r = urllib.request.Request(f'{API}/posts/{pid}', headers={'blotato-api-key': KEY})
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return json.loads(resp.read() or b'{}')
    except Exception as e:
        return {'status': 'не ясно', 'errorMessage': str(e)[:200]}

def post(body):
    r = urllib.request.Request(f'{API}/posts', data=json.dumps(body).encode(), method='POST',
                               headers={'blotato-api-key': KEY, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read() or b'{}')

def _head(t):
    t = (t or '').replace('⠀', ' ').strip()
    return t.splitlines()[0].strip()[:40].lower() if t else ''

def alive(p, text, at, dead=()):
    """14.11.2026 (защита от дублей): есть ли в Blotato пост этой сети с тем же началом текста, который НЕ упал
    (вышел, в работе, запланирован). Бывает, когда прошлый запрос завис уже после того, как Blotato пост принял.
    Возвращает пост, None — нет живого, 'неясно' — список не получен (тогда не перевыкладываем в этот заход)."""
    head = _head(text)
    if len(head) < 12:
        return None
    since = (at - datetime.timedelta(days=1)).isoformat(timespec='seconds')
    until = (max(at, now) + datetime.timedelta(days=1)).isoformat(timespec='seconds')
    q = urllib.parse.urlencode({'since': since, 'until': until, 'limit': 250})
    items, cur = [], None
    try:
        for _ in range(10):
            r = urllib.request.Request(f'{API}/posts?{q}' + (f'&cursor={urllib.parse.quote(str(cur))}' if cur else ''),
                                       headers={'blotato-api-key': KEY})
            with urllib.request.urlopen(r, timeout=60) as resp:
                d = json.loads(resp.read() or b'{}')
            items += d.get('items', []); cur = d.get('cursor')
            if not cur:
                break
    except Exception as e:
        print('список постов не получен:', str(e)[:150]); return 'неясно'
    for it in items:
        pl = str(it.get('platform') or (it.get('account') or {}).get('platform') or '').lower()
        if pl != p or it.get('id') in dead:
            continue
        if _head(it.get('text')) == head and (it.get('state') or {}).get('type') != 'failed':
            return it
    return None

def reels(name, F):
    # _рилс.json: {"at": "...", "text": "...", "video": "shorts.mp4",
    #  "posts": {"instagram": {"id": "...", "account": "80093", "target": {...}}, ...}}
    try:
        cfg = json.loads(rc('cat', f'{F}/_рилс.json').lstrip('\ufeff'))
    except Exception:
        return
    at = datetime.datetime.fromisoformat(cfg['at'])
    if not (datetime.timedelta(0) < now - at < datetime.timedelta(hours=48)):
        return
    changed = False; vurl = None
    for p, x in cfg['posts'].items():
        if x.get('status') in ('published', 'сдался'):
            continue
        if x.get('id'):
            r = status(x['id']); x['status'] = r.get('status'); x['url'] = r.get('publicUrl'); x['error'] = r.get('errorMessage'); changed = True
        print(name, 'рилс', p, x.get('status'), (x.get('error') or '')[:150])
        if x.get('status') not in ('failed', 'ошибка', 'неясно'):
            continue
        live = alive(p, cfg['text'], at, {x.get('id')})      # 14.11.2026: не задвоить
        if live == 'неясно':
            continue
        if live:
            x['id'] = live.get('id'); x['status'] = (live.get('state') or {}).get('type') or 'есть'; changed = True
            print(name, 'рилс', p, 'уже есть живой пост', x['id'], '— не перевыкладываю'); continue
        if x.get('повторов', 0) >= 2:
            tg(f'Рилс «{name}»: {NAMES.get(p, p)} так и не вышел после 2 повторов. Ошибка: {(x.get("error") or "")[:300]}')
            x['status'] = 'сдался'; continue
        try:
            if not vurl:
                rc('copyto', f'{F}/{cfg.get("video", "shorts.mp4")}', 'v.mp4')
                up = json.loads(urllib.request.urlopen(urllib.request.Request(f'{API}/media/uploads',
                    data=json.dumps({'filename': 'video.mp4'}).encode(), method='POST',
                    headers={'blotato-api-key': KEY, 'Content-Type': 'application/json'}), timeout=120).read())
                urllib.request.urlopen(urllib.request.Request(up['presignedUrl'], data=open('v.mp4', 'rb').read(),
                    method='PUT', headers={'Content-Type': 'video/mp4'}), timeout=1800)
                vurl = up['publicUrl']
            r = post({'post': {'accountId': x['account'], 'content': {'text': cfg['text'], 'mediaUrls': [vurl], 'platform': p},
                               'target': x['target']}})
            x['id'] = r.get('postSubmissionId'); x['status'] = 'отправлен заново'
            tg(f'Рилс «{name}»: упал {NAMES.get(p, p)} — перевыложил сам, проверю через 20 минут')
        except urllib.error.HTTPError as e:                 # отказ Blotato — поста нет
            x['status'] = 'ошибка'; x['error'] = str(e)[:300]
        except Exception as e:                              # 14.11.2026: завис — пост мог создаться, проверим в следующий заход
            x['id'] = None; x['status'] = 'неясно'; x['error'] = str(e)[:300]
        x['повторов'] = x.get('повторов', 0) + 1
    if changed:
        pathlib.Path('rl.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding='utf-8')
        rc('copyto', 'rl.json', f'{F}/_рилс.json', check=False)

now = datetime.datetime.now(datetime.timezone.utc)
for name in [x.rstrip('/') for x in rc('lsf', '--dirs-only', ROOT, check=False).splitlines()]:
    F = f'{ROOT}/{name}'
    reels(name, F)
    try:
        cfg = json.loads(rc('cat', f'{F}/karusel.json').lstrip('﻿'))
        res = json.loads(rc('cat', f'{F}/_отправлено.json'))
    except Exception:
        continue
    at = datetime.datetime.fromisoformat(cfg['at'])
    if not (datetime.timedelta(0) < now - at < datetime.timedelta(hours=48)):
        continue
    try:
        rep = json.loads(rc('cat', f'{F}/_повторы.json', check=False) or '{}')
    except Exception:
        rep = {}
    failed = []
    for p, x in res.items():
        if x.get('status') == 'published':
            continue
        if x.get('id'):
            r = status(x['id'])
            x['status'] = r.get('status'); x['url'] = r.get('publicUrl'); x['error'] = r.get('errorMessage')
        print(name, p, x.get('status'), (x.get('error') or '')[:150])
        if x.get('status') in ('failed', 'ошибка', 'неясно'):
            live = alive(p, (cfg.get('texts') or {}).get(p), at, {x.get('id')})   # 14.11.2026: не задвоить
            if live == 'неясно':
                continue
            if live:
                x['id'] = live.get('id'); x['status'] = (live.get('state') or {}).get('type') or 'есть'
                print(name, p, 'уже есть живой пост', x['id'], '— не перевыкладываю'); continue
            failed.append(p)
    if not failed:
        pathlib.Path('r.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
        rc('copyto', 'r.json', f'{F}/_отправлено.json', check=False)
        continue
    give_up = [p for p in failed if rep.get(p, 0) >= 2]
    todo = [p for p in failed if rep.get(p, 0) < 2]
    for p in give_up:
        if not rep.get(p + '_сказал'):
            tg(f'Карусель «{name}»: {NAMES.get(p, p)} так и не вышел после 2 повторов. Ошибка: {(res[p].get("error") or "")[:300]}')
            rep[p + '_сказал'] = 1
    if todo:
        rc('copy', F, 'k', '--exclude', '_превью*')
        pathlib.Path('k/_отправлено.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
        out = subprocess.run([sys.executable, 'scripts/karusel/karusel.py', 'k', 'retry', ','.join(todo)], capture_output=True, text=True)
        print(out.stdout, out.stderr[-500:])
        rc('copyto', 'k/_отправлено.json', f'{F}/_отправлено.json', check=False)
        for p in todo:
            rep[p] = rep.get(p, 0) + 1
        tg(f'Карусель «{name}»: упал {", ".join(NAMES.get(p, p) for p in todo)} — перевыложил сам, проверю через 20 минут')
        subprocess.run(['rm', '-rf', 'k'])
    pathlib.Path('rep.json').write_text(json.dumps(rep, ensure_ascii=False), encoding='utf-8')
    rc('copyto', 'rep.json', f'{F}/_повторы.json', check=False)

# Ролики (07.11.2026)
try:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import storozh_video
    storozh_video.main(tg)
except Exception as ex:
    print('сторож роликов:', str(ex)[:300])
