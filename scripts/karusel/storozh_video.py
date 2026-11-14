# Сторож роликов Blotato (07.11.2026, решение Евгения): перевыкладка упавших сетей — ТОЛЬКО здесь, в облаке.
# Компьютер (Общее/Робот/blotato.py) ролики в Blotato ставит и проверяет, но сам НЕ перевыкладывает.
# Читаем «_задания/_blotato.json» (только чтение, его пишет компьютер). Свои перевыкладки пишем в
# «_задания/_blotato_повторы.json»: {"папка": {"instagram": {"id": "...", "n": 1, "at": "...", "status": "..."}}}.
# Компьютер оттуда подхватывает новый id и дальше проверяет его сам (чтобы папка уехала в опубликованные).
# Сети: youtube, instagram, tiktok, threads. До 2 повторов на сеть. Окно — 48 часов после выхода.
import json, sys, subprocess, pathlib, datetime, importlib, urllib.request

Q = 'montazh:Брокер/К публикации/_задания'
PUBR = 'montazh:Брокер/К публикации'
MAIN = ['youtube', 'instagram', 'tiktok', 'threads']
NAMES = {'instagram': 'Instagram', 'tiktok': 'TikTok', 'threads': 'Threads', 'youtube': 'YouTube'}
W = pathlib.Path('work').resolve()

def rc(*a, check=True):
    return subprocess.run(['rclone', *a], capture_output=True, text=True, check=check).stdout

def main(tg):
    (W / 'Общее' / 'Робот').mkdir(parents=True, exist_ok=True)
    for f in ('blotato.py', 'common.py'):
        rc('copyto', f'montazh:Общее/Робот/{f}', str(W / 'Общее' / 'Робот' / f))
    sys.path.insert(0, str(W / 'Общее' / 'Робот'))
    common = importlib.import_module('common')
    common.log = lambda m: print('журнал:', m)          # журнал компьютера не трогаем
    b = importlib.import_module('blotato')
    b.log = common.log
    key = open('key.txt', encoding='utf-8-sig').read().strip()
    s = json.loads(rc('cat', f'{Q}/_blotato.json'))
    try:
        rep = json.loads(rc('cat', f'{Q}/_blotato_повторы.json', check=False) or '{}')
    except Exception:
        rep = {}
    acc = s.get('_accounts') or {}
    now = datetime.datetime.now(datetime.timezone.utc)
    from zoneinfo import ZoneInfo; tz = ZoneInfo('Europe/Madrid')   # время в _blotato.json — местное, валенсийское
    changed = False
    for name, e in s.items():
        if name.startswith('_') or not isinstance(e, dict) or not e.get('at'):
            continue
        at = datetime.datetime.fromisoformat(e['at']).replace(tzinfo=tz)
        if not (datetime.timedelta(minutes=15) < now - at < datetime.timedelta(hours=48)):
            continue
        for p in MAIN:
            x = (e.get('posts') or {}).get(p) or {}
            if x.get('status') == 'вышел' or not (x.get('id') or rep.get(name, {}).get(p)):
                continue
            r = rep.setdefault(name, {}).get(p)
            if r and r.get('status') in ('published', 'сдался'):
                continue
            pid = r['id'] if r and r.get('id') else x.get('id')
            try:
                st = b._req('GET', f'/posts/{pid}', key=key)
            except Exception as ex:
                print(name, p, 'не ясно', str(ex)[:120]); continue
            status, err = st.get('status'), (st.get('errorMessage') or '')[:300]
            print(name, p, status, err[:150])
            if r is not None and r.get('status') != status:
                r['status'] = status; changed = True
            if status != 'failed':
                continue
            n = (r or {}).get('n', 0)
            if n >= 2:
                if r and r.get('status') != 'сдался':
                    r['status'] = 'сдался'; changed = True
                    tg(f'Ролик «{name}»: {NAMES[p]} так и не вышел после 2 повторов. Ошибка: {err}')
                continue
            live = alive(b, key, name, e, p, at, now, {pid, x.get('id')})   # 14.11.2026: защита от дубля
            if live:
                st2 = (live.get('state') or {}).get('type') or 'есть'
                print(name, p, 'в Blotato уже есть живой пост', live.get('id'), st2, '— не перевыкладываю')
                rep[name][p] = {'id': live.get('id'), 'n': n, 'at': f'{now:%Y-%m-%d %H:%M}', 'status': st2}
                changed = True; continue
            if __import__('os').environ.get('DRY'):
                print('DRY: перевыложил бы', name, p); continue
            new = repost(b, key, acc, name, e, p)
            if new == 'неясно':                            # запрос завис: пост мог создаться — повтор только после проверки
                rep[name][p] = {'id': None, 'n': n + 1, 'at': f'{now:%Y-%m-%d %H:%M}', 'status': 'неясно'}
                changed = True; continue
            rep[name][p] = {'id': new, 'n': n + 1, 'at': f'{now:%Y-%m-%d %H:%M}', 'status': 'отправлен' if new else 'ошибка'}
            changed = True
            if new:
                tg(f'Ролик «{name}»: {NAMES[p]} упал ({err[:120]}) — перевыложил сам, проверю через 20 минут')
    rep = {k: v for k, v in rep.items() if v}
    if changed:
        pathlib.Path('rep_v.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
        rc('copyto', 'rep_v.json', f'{Q}/_blotato_повторы.json')

def alive(b, key, name, e, p, at, now, dead):
    """14.11.2026 (дубль «72 Мадрид зимой»): перед перевыкладкой ищем в Blotato пост этой же сети с тем же видео
    или тем же началом текста, который НЕ упал (вышел, в работе, запланирован). Такой пост мог появиться, если прошлая
    перевыкладка зависла после того, как Blotato её принял. Нашли — не перевыкладываем, берём его id."""
    folder = W / 'Брокер' / 'К публикации' / name
    folder.mkdir(parents=True, exist_ok=True)
    rc('copyto', f'{PUBR}/{name}/упаковка.txt', str(folder / 'упаковка.txt'), check=False)
    text = b.read_pack(folder, raw=True) if p == 'youtube' else b.read_pack(folder)
    if p == 'threads':
        text = b._threads_clean(text)
    head = (text or '').strip()[:60]
    vids = {v for v in (e.get('video'), e.get('video_tt')) if v}
    items = {}
    for t in {at.astimezone(), now.astimezone()}:
        try:
            for it in b._list_posts(key, t):
                items[it.get('id')] = it
        except Exception as ex:
            print(name, p, 'список постов не получен:', str(ex)[:150])
            return {'id': None, 'state': {'type': 'неясно'}}   # не видим список — не рискуем, повтор в следующий заход
    for it in items.values():
        if b._plat(it.get('platform') or (it.get('account') or {}).get('platform')) != p or it.get('id') in dead:
            continue
        same = bool(vids & set(it.get('mediaUrls') or [])) or (len(head) >= 12 and (it.get('text') or '').strip()[:60] == head)
        if same and (it.get('state') or {}).get('type') != 'failed':
            return it
    return None

def repost(b, key, acc, name, e, p):
    folder = W / 'Брокер' / 'К публикации' / name
    folder.mkdir(parents=True, exist_ok=True)
    for f in ('упаковка.txt', 'обложка.jpg'):
        rc('copyto', f'{PUBR}/{name}/{f}', str(folder / f), check=False)
    text = b.read_pack(folder)
    title = text.splitlines()[0].strip() if text else name
    ptext = b.read_pack(folder, raw=True) if p == 'youtube' else text
    if p == 'threads':
        ptext = b._threads_clean(ptext)
        if len(ptext) > 500:
            ptext = ptext[:497].rsplit(' ', 1)[0] + '…'
    cover = folder / 'обложка.jpg'
    curl = None
    if cover.exists() and p in ('youtube', 'instagram'):
        try: curl = b._upload(cover, key)
        except Exception as ex: print('обложка не загрузилась', ex)
    vurl = (e.get('video_tt') if p == 'tiktok' else None) or e.get('video')
    body = lambda u: {'post': {'accountId': acc[p], 'content': {'text': ptext, 'mediaUrls': [u], 'platform': p},
                               'target': b._target(p, title, curl, acc, name)}}
    # 14.11.2026: Blotato ответил ошибкой (RuntimeError из _req) — пост точно не создан, можно пробовать дальше.
    # Любой другой сбой (таймаут, обрыв) — пост мог создаться: возвращаем «неясно», без второй попытки.
    try:
        return b._req('POST', '/posts', body(vurl), key).get('postSubmissionId')
    except RuntimeError as ex:
        print(name, p, 'со старым видео не вышло:', str(ex)[:200])
    except Exception as ex:
        print(name, p, 'запрос завис, пост мог создаться:', str(ex)[:200]); return 'неясно'
    try:                                                   # видео заново с Диска
        vids = [l for l in rc('lsf', f'{PUBR}/{name}').splitlines() if l.startswith('!!!') and l.endswith('.mp4')]
        rc('copyto', f'{PUBR}/{name}/{vids[0]}', str(folder / 'v.mp4'))
        u = b._upload(folder / 'v.mp4', key)
    except Exception as ex:
        print(name, p, 'видео заново не загрузилось:', str(ex)[:200]); return None
    try:
        return b._req('POST', '/posts', body(u), key).get('postSubmissionId')
    except RuntimeError as ex:
        print(name, p, 'перевыкладка не удалась:', str(ex)[:200]); return None
    except Exception as ex:
        print(name, p, 'запрос завис, пост мог создаться:', str(ex)[:200]); return 'неясно'
