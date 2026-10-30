# Карусель (фото-публикация) через Blotato: Instagram, TikTok, Threads + видео-слайдшоу в YouTube Shorts.
# Папка карусели: 01.jpg, 02.jpg ... (по порядку), необязательно shorts.mp4, karusel.json:
# {"at": "ГГГГ-ММ-ДДTЧЧ:ММ:СС+01:00", "seti": ["instagram","tiktok","threads","youtube"],
#  "texts": {"instagram": "...", "tiktok": "...", "threads": "...", "youtube": "..."}, "youtube_title": "..."}
import json, sys, pathlib, urllib.request, urllib.error

API = 'https://backend.blotato.com/v2'
ACC = {'instagram': '80093', 'threads': '10321', 'tiktok': '65164', 'youtube': '54490'}
KEY = open('key.txt', encoding='utf-8-sig').read().strip()
D = pathlib.Path(sys.argv[1])

def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={'blotato-api-key': KEY, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return json.loads(resp.read() or b'{}')
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path}: {e.code} {e.read()[:400].decode('utf-8', 'replace')}")

def upload(p):
    mp4 = p.suffix.lower() == '.mp4'
    up = req('POST', '/media/uploads', {'filename': p.name if not mp4 else 'video.mp4'})
    r = urllib.request.Request(up['presignedUrl'], data=p.read_bytes(), method='PUT',
                               headers={'Content-Type': 'video/mp4' if mp4 else 'image/jpeg'})
    with urllib.request.urlopen(r, timeout=1800) as resp:
        if resp.status >= 300:
            raise RuntimeError(f'загрузка {p.name}: {resp.status}')
    return up['publicUrl']

def target(p, cfg):
    if p == 'instagram':
        return {'targetType': 'instagram'}
    if p == 'tiktok':
        return {'targetType': 'tiktok', 'privacyLevel': 'PUBLIC_TO_EVERYONE', 'disabledComments': False,
                'disabledDuet': False, 'disabledStitch': False, 'isBrandedContent': False,
                'isYourBrand': False, 'isAiGenerated': False, 'isDraft': False, 'autoAddMusic': True}
    if p == 'threads':
        return {'targetType': 'threads', 'replyControl': 'everyone'}
    if p == 'youtube':
        return {'targetType': 'youtube', 'title': cfg.get('youtube_title', '')[:100], 'privacyStatus': 'public',
                'shouldNotifySubscribers': True, 'isMadeForKids': False, 'containsSyntheticMedia': False}

cfg = json.loads((D / 'karusel.json').read_text(encoding='utf-8-sig'))
res_p = D / '_отправлено.json'
res = json.loads(res_p.read_text(encoding='utf-8')) if res_p.exists() else {}
mode = sys.argv[2] if len(sys.argv) > 2 else 'post'

if mode == 'status':
    for p, x in res.items():
        if x.get('id'):
            try:
                r = req('GET', f"/posts/{x['id']}")
                x['status'] = r.get('status'); x['url'] = r.get('publicUrl'); x['error'] = r.get('errorMessage')
            except Exception as ex:
                x['status'] = 'не ясно'; x['error'] = str(ex)[:300]
        print(p, x.get('status'), x.get('url') or '', (x.get('error') or '')[:300])
else:
    pics = sorted(f for f in D.iterdir() if f.suffix.lower() in ('.jpg', '.jpeg', '.png') and f.stem[:2].isdigit())
    urls = [upload(f) for f in pics]
    print('фото загружено:', len(urls))
    vid = D / 'shorts.mp4'
    vurl = upload(vid) if vid.exists() and 'youtube' in cfg.get('seti', []) else None
    for p in cfg.get('seti', []):
        if res.get(p, {}).get('id'):
            print(p, 'уже отправлен', res[p]['id']); continue
        media = [vurl] if p == 'youtube' else urls
        if p == 'youtube' and not vurl:
            print('youtube: нет shorts.mp4'); continue
        if p == 'threads':
            media = urls[:1]                      # Blotato: в Threads только одна картинка или видео (ошибка 30.10.2026)
        text = cfg['texts'][p]
        if p == 'instagram':                      # Instagram через Blotato: не больше 5 хэштегов
            import re
            tags = re.findall(r'#\S+', text)
            for t in tags[5:]:
                text = text.replace(' ' + t, '').replace(t, '')
        body = {'post': {'accountId': ACC[p], 'content': {'text': text.strip(), 'mediaUrls': media, 'platform': p},
                         'target': target(p, cfg)}, 'scheduledTime': cfg['at']}
        try:
            r = req('POST', '/posts', body)
            res[p] = {'id': r.get('postSubmissionId'), 'status': 'запланирован', 'at': cfg['at']}
            print(p, 'запланирован', res[p]['id'])
        except Exception as ex:
            res[p] = {'status': 'ошибка', 'error': str(ex)[:400]}
            print(p, 'ОШИБКА', str(ex)[:400])
res_p.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
