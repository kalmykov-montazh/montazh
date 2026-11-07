# Blotato: Instagram, Threads, TikTok, YouTube (решение Евгения 22.10.2026). Facebook остаётся на роботе (fb.py).
# Берёт ролики, которые planner.py уже поставил в Facebook (_план.json), и ставит их в Blotato на 10 минут позже FB.
# Если это время уже прошло — через 20–30 минут. Ролики с прошедшей датой не трогает (они уже выложены).
# Ключ API — файл blotato_ключ.txt рядом со скриптом. Учёт — «_задания\_blotato.json», чтобы не ставить дважды.
# Без браузера, лимит Claude не тратит. Ошибки — в журнал и в Telegram (как у робота FB).
# X (Twitter) добавлен 22.10.2026: не все ролики, а 1–3 в день по плану наращивания (X_PLAN), только до 2:20,
# короткий текст без ссылок. Ошибки X не мешают переносу папки в «опубликованные».
# LinkedIn добавлен 23.10.2026: прогрев — вт, чт, сб по 1 ролику (вечерний), без путешествий (ПАЛЬМА/ПУТЕШ),
# текст — упаковка целиком без ссылок. LinkedIn тоже не влияет на перенос папки.
# Bluesky добавлен 23.10.2026: новый аккаунт, наращивание как у X (BS_PLAN), видео до 3:00, текст до 300 знаков без ссылок.
# Проверка исправлена 23.10.2026: после переноса времени старый id отвечает «in-progress» вечно — теперь check() ищет пост
# в списке GET /v2/posts (сеть + видео), «не ясно» пишет в журнал раз в час, через 2 часа — журнал + Telegram.
# TikTok (23.10.2026): API TikTok не берёт картинку-обложку, только кадр видео. Основное решение — автомонтаж вшивает
# обложку первым кадром. ВРЕМЕННО, для роликов, смонтированных до этого: если первый кадр не похож на обложка.jpg,
# скрипт через ffmpeg делает копию с обложкой первым кадром (1/30 с) только для TikTok. Нет ffmpeg — уходит обычное видео.
# Текстовые посты (24.10.2026): задания из «Посты!\Соцсети\*.json» → Threads, X, Bluesky, Instagram (с картинкой), LinkedIn.
# С 23.10.2026 опубликованные папки — по месяцам: «!!!ШОРТЫ ОПУБЛИКОВАННЫЕ\Октябрь 2026», список роликов — один, в корне.
import json, re, os, struct, time, random, datetime, shutil, subprocess, tempfile, glob, urllib.request, urllib.error, urllib.parse
from common import HERE, PUB, QUEUE, ROOT, log, read_pack

API = 'https://backend.blotato.com/v2'
KEYS = [HERE / 'blotato_ключ.txt', HERE / 'blotato_ключ.txt.txt']
STATE = QUEUE / '_blotato.json'
LOCK = QUEUE / '_blotato.lock'
FBPLAN = QUEUE / '_план.json'
MOVE = QUEUE / '_blotato_перенос.json'      # {"папка": "2026-10-22 19:30"} — перенести время в 4 сетях
DONE_DIR = ROOT / 'Брокер' / 'Опубликованные' / 'Шортсы'  # вышло везде — папка уезжает сюда
PLATFORMS = ['youtube', 'instagram', 'tiktok', 'threads']
DELAY_MIN = 10
YT_SPAIN = '54490'                # «С нуля в Испании»; крипто-канал 54914 ведёт crypto_yt.py (25.10.2026)                    # через сколько минут после Facebook

# X (Twitter): с какой даты, и сколько роликов в день до какой даты включительно (решение Евгения 22.10.2026)
X_START = '2026-10-23'
# 26.10.2026: 1 в день до 4.11, неделя по 2, две недели по 3, с 26.11 — все 4
X_PLAN = [('2026-11-04', 1), ('2026-11-11', 2), ('2026-11-25', 3), ('9999-12-31', 4)]
X_MAX_SEC = 140                   # видео в X — не длиннее 2:20
X_MAX_TEXT = 280

# LinkedIn (личный профиль): с какой даты, в какие дни недели (0=пн … 5=сб), сколько роликов в такой день
LI_START = '2026-10-23'
LI_DAYS = {1, 3, 5}                # вторник, четверг, суббота — только до LI_DAILY
LI_PER_DAY = 1
# 26.10.2026: до 8.11 — вт/чт/сб по 1; с 9.11 — каждый день по 1; с 23.11 — каждый день по 2
LI_DAILY = '2026-11-09'
LI_TWO = '2026-11-23'
# в LinkedIn только деловые темы: недвижимость, аренда, налоги, деньги, документы, работа
LI_TOPIC = re.compile(r'недвиж|аренд|квартир|жиль|ипотек|налог|залог|арендат|хозя|собственник|покуп|прода|сдач|сдать|сдаю|окупас|'
                      r'риэлт|агентств|нотари|договор|контракт|автоном|autónomo|irpf|ibi|itp|plusval|бизнес|зарплат|работ|'
                      r'внж|пмж|документ|штраф|закон|пенси|выплат|\bнедв\b|\bск\b|\bбиз\b', re.I)
LI_SKIP = ('ПАЛЬМА', 'ПУТЕШ')     # ролики про путешествия в LinkedIn не ставим
LI_MAX_TEXT = 3000

# Bluesky: новый аккаунт (23.10.2026) — 1 ролик в день две недели, потом 2, потом 3
BS_START = '2026-10-24'
# 26.10.2026: 1 в день до 6.11, неделя по 2, две недели по 3, с 28.11 — все 4
BS_PLAN = [('2026-11-06', 1), ('2026-11-13', 2), ('2026-11-27', 3), ('9999-12-31', 4)]
BS_MAX_SEC = 180                  # видео в Bluesky — не длиннее 3:00
BS_MAX_TEXT = 300

# Плейлисты YouTube (новая структура из 10 плейлистов, решение Евгения 25.10.2026;
# файл проекта «YouTube — плейлисты и автораскладка шортсов»). Один плейлист на шортс, по id.
PL = {
    'rent':   'PLmG0Z0zkAWLwU3v8reBkiRdjnH8qHWpAq',  # Аренда и недвижимость в Испании
    'vnzh':   'PLLpbvRw71C5k',                       # ВНЖ, временная защита и документы в Испании
    'auto':   'PLmG0Z0zkAWLzmm9HIJ2kkdDgvIwK1tfh2',  # Машины, ПДД и штрафы в Испании
    'money':  'PLmG0Z0zkAWLxx4cP0WvC8xi0_WFgcB11q',  # Деньги в Испании: налоги, пенсия, работа
    'life':   'PLmG0Z0zkAWLzY3ODXfC6Saa2CoCZ4XwxE',  # Жизнь в Испании: цены, быт, адаптация
    'vlc':    'PLmG0Z0zkAWLwsAe8qpWYaV-1dRsQeJ1V3',  # Валенсия: районы, город и праздники
    'travel': 'PLEL0Wb3EBHw8',                       # Путешествия без переплат!
    'path':   'PLmG0Z0zkAWLwBClBzRVxdvlwf1H0u2vqH',  # Мой путь: с нуля в третий раз
    'obj':    'PLmG0Z0zkAWLylDNlBRwcudBVTJpsLOPRF',  # Квартиры в Валенсии: аренда и продажа
}
LABELS = [
    (('ПАЛЬМА', 'ПУТЕШ'), 'travel'),
    (('НЕДВ', 'СК'), 'rent'),
    (('ВНЖ',), 'vnzh'),
    (('АВТО',), 'auto'),
    (('БИЗ',), 'money'),
    (('ПУТЬ',), 'path'),
    (('ЖИЗНЬ',), 'life'),
]
# для ЖИЗНЬ и роликов без метки — уточнение по словам в имени папки (первое совпадение)
WORDS = [
    (('защит', 'внж', 'пмж', 'арраиго', 'гражданств', 'nie', 'tie', 'прописк', 'empadron', 'документ'), 'vnzh'),
    (('штраф', 'пдд', 'маяч', 'номер', 'машин', 'авто', 'парковк', 'права'), 'auto'),
    (('налог', 'пенси', 'стаж', 'imv', 'пособ', 'выплат', 'банк', 'autonomo', 'автоном', 'зарплат', 'работ'), 'money'),
    (('аренд', 'квартир', 'жиль', 'окупас', 'залог', 'ипотек', 'недвиж'), 'rent'),
    (('валенси', 'район', 'fallas', 'праздник', 'пляж'), 'vlc'),
    (('соцсет', 'подписчик', 'блогер', 'youtube', 'тикток', 'instagram'), 'path'),
    (('отел', 'билет', 'багаж', 'букинг', 'путешеств'), 'travel'),
]

def _key():
    for k in KEYS:
        if k.exists():
            return k.read_text(encoding='utf-8-sig').strip()
    return None

def _req(method, path, body=None, key=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={'blotato-api-key': key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return json.loads(resp.read() or b'{}')
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path}: {e.code} {e.read()[:300].decode('utf-8', 'replace')}")

def _upload(path, key):
    up = _req('POST', '/media/uploads', {'filename': 'video.mp4' if path.suffix.lower() == '.mp4' else 'cover.jpg'}, key)
    ctype = 'video/mp4' if path.suffix.lower() == '.mp4' else 'image/jpeg'
    r = urllib.request.Request(up['presignedUrl'], data=path.read_bytes(), method='PUT', headers={'Content-Type': ctype})
    with urllib.request.urlopen(r, timeout=1800) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"загрузка {path.name}: {resp.status}")
    return up['publicUrl']

def _load(p, default):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default

def _save(s):
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding='utf-8')

def _accounts(key, s):
    if s.get('_accounts') and s['_accounts'].get('_v') == 4:
        return s['_accounts']
    items = _req('GET', '/users/me/accounts', key=key).get('items', [])
    acc = {a['platform']: a['id'] for a in items if a['platform'] in PLATFORMS}
    for a in items:                                  # X в Blotato может называться twitter или x
        if str(a.get('platform', '')).lower() in ('twitter', 'x'):
            acc['twitter'] = a['id']
        if str(a.get('platform', '')).lower() == 'linkedin':
            acc['linkedin'] = a['id']
        if str(a.get('platform', '')).lower() == 'bluesky':
            acc['bluesky'] = a['id']
    if 'youtube' in acc:
        acc['youtube'] = YT_SPAIN                     # два YouTube в Blotato — испанские ролики только на свой канал
    acc['_v'] = 4
    if 'youtube' in acc:
        pl = _req('GET', f"/users/me/accounts/{acc['youtube']}/subaccounts", key=key).get('items', [])
        acc['_playlists'] = {p['name']: p['id'] for p in pl}
    s['_accounts'] = acc
    return acc

def _playlists(folder, acc):
    """Плейлист по метке папки + второй по словам в имени, если тема другая (до 2, решение Евгения 25.10.2026).
    Без метки — по словам; по умолчанию «Жизнь в Испании»"""
    up, low = folder.upper().split(), folder.lower()
    keys = []
    for tags, k in LABELS:
        if any(t in up for t in tags):
            keys.append(k); break
    for words, k in WORDS:
        if any(w in low for w in words) and k not in keys:
            if keys == ['life']:
                keys = [k]          # ЖИЗНЬ + явная тема → тематический плейлист вместо общего
            else:
                keys.append(k)
            break
    if not keys:
        keys = ['life']
    return [PL[k] for k in keys[:2]]

def _yt_title(title):
    """Название YouTube + « #shorts», если влезает в 100 знаков (решение Евгения 22.10.2026)"""
    title = title.strip()[:100]
    if '#shorts' not in title.lower() and len(title) + 8 <= 100:
        title += ' #shorts'
    return title

def _target(platform, title, cover_url, acc, folder):
    if platform == 'youtube':
        t = {'targetType': 'youtube', 'title': _yt_title(title), 'privacyStatus': 'public',
             'shouldNotifySubscribers': True, 'isMadeForKids': False, 'containsSyntheticMedia': False,
             'playlistIds': _playlists(folder, acc)}
        if cover_url: t['thumbnailUrl'] = cover_url
        return t
    if platform == 'instagram':
        t = {'targetType': 'instagram', 'mediaType': 'reel', 'shareToFeed': True}
        if cover_url: t['coverImageUrl'] = cover_url
        return t
    if platform == 'tiktok':
        return {'targetType': 'tiktok', 'privacyLevel': 'PUBLIC_TO_EVERYONE', 'disabledComments': False,
                'disabledDuet': False, 'disabledStitch': False, 'isBrandedContent': False,
                'isYourBrand': False, 'isAiGenerated': False, 'isDraft': False, 'videoCoverTimestamp': 0}
    return {'targetType': 'threads', 'replyControl': 'everyone'}

def _ffmpeg():
    """ffmpeg: из PATH или из папки winget (Планировщик может не видеть новый PATH до перезагрузки)."""
    f = shutil.which('ffmpeg')
    if f:
        return f
    la = os.environ.get('LOCALAPPDATA', '')
    for pat in (os.path.join(la, 'Microsoft', 'WinGet', 'Links', 'ffmpeg.exe'),
                os.path.join(la, 'Microsoft', 'WinGet', 'Packages', '*FFmpeg*', '*', 'bin', 'ffmpeg.exe'),
                r'C:\ffmpeg\bin\ffmpeg.exe', r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'):
        hit = glob.glob(pat)
        if hit:
            return hit[0]
    return None

def _tiktok_video(video, cover):
    """Копия ролика для TikTok: обложка первым кадром (1/30 с). Не вышло — None (уйдёт обычное видео)."""
    ff = _ffmpeg()
    if not ff:
        today = datetime.date.today().isoformat()
        flag = QUEUE / '_нет_ffmpeg.txt'
        if not flag.exists() or flag.read_text(encoding='utf-8').strip() != today:
            flag.write_text(today, encoding='utf-8')
            log("BLOTATO TikTok: ffmpeg не найден — ролики уходят без вшитой обложки")
        return None
    if not cover.exists():
        return None
    flags = 0x08000000 if os.name == 'nt' else 0              # без чёрного окна
    try:                                                        # монтаж уже вшил обложку первым кадром — копия не нужна
        r = subprocess.run([ff, '-v', 'info', '-i', str(video), '-i', str(cover), '-filter_complex',
                            '[0:v]trim=end_frame=1,setpts=PTS-STARTPTS[a];[1:v][a]scale2ref[c][m];[m][c]ssim',
                            '-frames:v', '1', '-f', 'null', '-'], capture_output=True, timeout=120, creationflags=flags)
        m = re.search(r'All:([0-9.]+)', (r.stderr or b'').decode('utf-8', 'replace'))
        if m and float(m.group(1)) >= 0.9:
            return None
    except Exception:
        pass
    out = os.path.join(tempfile.gettempdir(), 'blotato_tiktok.mp4')
    fc = ("[0:v][2:v]scale2ref[c][m];"
          "[c]setsar=1,fps=30,format=yuv420p,trim=end_frame=1,setpts=PTS-STARTPTS[c1];"
          "[m]setsar=1,fps=30,format=yuv420p[m1];"
          "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[s];"
          "[2:a]aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo[a];"
          "[c1][s][m1][a]concat=n=2:v=1:a=1[v][aa]")
    cmd = [ff, '-v', 'error', '-y', '-loop', '1', '-framerate', '30', '-t', '0.0334', '-i', str(cover),
           '-f', 'lavfi', '-t', '0.0334', '-i', 'anullsrc=r=48000:cl=stereo', '-i', str(video),
           '-filter_complex', fc, '-map', '[v]', '-map', '[aa]', '-c:v', 'libx264', '-preset', 'veryfast',
           '-crf', '19', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=1800, creationflags=flags)
        if r.returncode != 0 or not os.path.exists(out) or os.path.getsize(out) < 100000:
            log(f"BLOTATO TikTok: обложку вшить не вышло ({(r.stderr or b'').decode('utf-8', 'replace')[-200:]}) — уходит обычное видео")
            return None
        from pathlib import Path
        return Path(out)
    except Exception as ex:
        log(f"BLOTATO TikTok: обложку вшить не вышло ({str(ex)[:150]}) — уходит обычное видео")
        return None

def _when(fb_date, fb_time, now, name=None):
    # 07.11.2026 (решение Евгения): не ровно через 10 мин после FB, а через 5–40 мин — у каждого ролика своё
    delay = random.Random(f"blotato-{name}").randint(5, 40) if name and fb_date >= '2026-11-08' else DELAY_MIN
    at = datetime.datetime.fromisoformat(f"{fb_date} {fb_time}") + datetime.timedelta(minutes=delay)
    if at < now + datetime.timedelta(minutes=15):
        at = now + datetime.timedelta(minutes=random.randint(20, 30))
    return at

def schedule(key, s):
    fb = _load(FBPLAN, {})
    now = datetime.datetime.now()
    today = now.date().isoformat()
    for name, v in sorted(fb.items(), key=lambda kv: (kv[1].get('date', ''), kv[1].get('time', ''))):
        if v.get('platform', 'fb') != 'fb' or v.get('date', '') < today or name in s:
            continue
        folder = PUB / name
        video = next((f for f in folder.glob('*.mp4') if f.name.startswith('!!!')), None) if folder.exists() else None
        if not video:
            continue
        acc = _accounts(key, s)
        e = s[name] = {'fb': f"{v['date']} {v['time']}", 'status': 'загрузка', 'posts': {}}
        _save(s)                                   # отметка до загрузки — второй запуск не задвоит
        text = read_pack(folder)
        title = text.splitlines()[0].strip() if text else re.sub(r'^\d+\s+', '', name)
        vurl = _upload(video, key)
        cover = folder / 'обложка.jpg'
        curl = _upload(cover, key) if cover.exists() else None
        at = _when(v['date'], v['time'], datetime.datetime.now(), name)
        e['at'] = f"{at:%Y-%m-%d %H:%M}"
        e['video'] = vurl
        _save(s)
        tturl = vurl
        if 'tiktok' in acc:
            ttv = _tiktok_video(video, cover)
            if ttv:
                try:
                    tturl = e['video_tt'] = _upload(ttv, key)
                except Exception as ex:
                    log(f"BLOTATO TikTok: копия с обложкой не загрузилась ({str(ex)[:150]}) — уходит обычное видео")
                try: ttv.unlink()
                except Exception: pass
        for p in PLATFORMS:
            if p not in acc:
                e['posts'][p] = {'status': 'нет аккаунта'}; continue
            ptext = read_pack(folder, raw=True) if p == 'youtube' else text   # YouTube — упаковка как есть, со строкой про полное видео (решение 25.10.2026)
            if p == 'threads':
                ptext = _threads_clean(ptext)
            if p == 'threads' and len(ptext) > 500:            # у Threads лимит 500 знаков
                ptext = ptext[:497].rsplit(' ', 1)[0] + '…'
            body = {'post': {'accountId': acc[p],
                             'content': {'text': ptext, 'mediaUrls': [tturl if p == 'tiktok' else vurl], 'platform': p},
                             'target': _target(p, title, curl, acc, name)},
                    'scheduledTime': at.astimezone().isoformat(timespec='seconds')}
            try:
                r = _req('POST', '/posts', body, key)
                e['posts'][p] = {'id': r.get('postSubmissionId'), 'status': 'запланирован'}
            except Exception as ex:
                e['posts'][p] = {'status': 'ошибка', 'error': str(ex)[:300]}
                log(f"ОШИБКА blotato {p} — {name}: {str(ex)[:200]}")
            _save(s)
            time.sleep(2)
        e['status'] = 'запланирован'
        _save(s)
        ok = [p for p, x in e['posts'].items() if x['status'] == 'запланирован']
        log(f"BLOTATO {e['at']} — {name}: {', '.join(ok) or 'ничего'}")

def _duration(path):
    """Длина mp4 в секундах из заголовка (mvhd), без ffmpeg. Не смог прочитать — None."""
    try:
        size = os.path.getsize(path)
        with open(path, 'rb') as f:
            pos = 0
            while pos + 8 <= size:
                f.seek(pos)
                sz, typ = struct.unpack('>I4s', f.read(8))
                hdr = 8
                if sz == 1:
                    sz = struct.unpack('>Q', f.read(8))[0]; hdr = 16
                elif sz == 0:
                    sz = size - pos
                if sz < hdr:
                    return None
                if typ == b'moov':
                    data = f.read(min(sz - hdr, 64 * 1024 * 1024))
                    i = data.find(b'mvhd')
                    if i < 0:
                        return None
                    v = data[i + 4]
                    if v == 1:
                        ts, dur = struct.unpack('>IQ', data[i + 24:i + 36])
                    else:
                        ts, dur = struct.unpack('>II', data[i + 16:i + 24])
                    return dur / ts if ts else None
                pos += sz
    except Exception:
        return None
    return None

def _x_per_day(date, start=None, plan=None):
    start, plan = start or X_START, plan or X_PLAN
    if date < start:
        return 0
    for until, n in plan:
        if date <= until:
            return n
    return 0

def _x_text(pack, folder, limit=None):
    """Первая строка упаковки + 1–2 хэштега, без ссылок, до 280 знаков (Bluesky — 300)."""
    limit = limit or X_MAX_TEXT
    lines = [l.strip() for l in (pack or '').splitlines() if l.strip()]
    title = lines[0] if lines else re.sub(r'^\d+\s+', '', folder)
    title = re.sub(r'https?://\S+|www\.\S+|t\.me/\S+', '', title)
    title = re.sub(r'#\w+', '', title).strip()
    tags = [t for t in re.findall(r'#\w+', pack or '') if t.lower() != '#shorts']
    seen = []
    for t in tags:
        if t.lower() not in [x.lower() for x in seen]:
            seen.append(t)
    tail = ' '.join(seen[:2])
    room = limit - (len(tail) + 2 if tail else 0)
    if len(title) > room:
        title = title[:room - 1].rsplit(' ', 1)[0] + '…'
    return f"{title}\n\n{tail}" if tail else title

def schedule_x(key, s):
    _ramp(key, s, 'twitter', '_x', 'X', X_START, X_PLAN, X_MAX_SEC, X_MAX_TEXT)

def schedule_bs(key, s):
    _ramp(key, s, 'bluesky', '_bs', 'Bluesky', BS_START, BS_PLAN, BS_MAX_SEC, BS_MAX_TEXT)

def _ramp(key, s, plat, skey, label, start, plan, max_sec, max_text):
    """Каждый день выбирает ролики для X/Bluesky: сначала вечерний, потом обеденный, потом утренний; только короткие."""
    fb = _load(FBPLAN, {})
    acc = s.get('_accounts') or {}
    if plat not in acc:
        if any(v.get('date', '') >= start for v in fb.values()):
            acc = _accounts(key, s)
        if plat not in acc:
            return
    now = datetime.datetime.now()
    xs = s.setdefault(skey, {})
    days = {}
    for name, v in fb.items():
        if v.get('platform', 'fb') == 'fb' and v.get('date'):
            days.setdefault(v['date'], []).append((v.get('time', ''), name))
    for date, items in sorted(days.items()):
        n = _x_per_day(date, start, plan)
        if not n or date in xs or date < now.date().isoformat():
            continue
        items.sort()
        first = datetime.datetime.fromisoformat(f"{date} {items[0][0]}")
        # решаем, когда день уже разложен (3 ролика) или до первого ролика меньше 3 часов
        if len(items) < 4 and now < first - datetime.timedelta(hours=3):   # 4 ролика в день с 27.10.2026
            continue
        entries = [(t, nm) for t, nm in items if s.get(nm, {}).get('at') and s[nm].get('video')]
        if not entries or (len(entries) < len(items) and now < first - datetime.timedelta(hours=3)):
            continue                                   # кто-то ещё не загружен в Blotato — ждём
        picked, skipped = [], []
        for t, nm in reversed(entries):                # вечер → обед → утро
            if len(picked) >= n:
                break
            video = next((f for f in (PUB / nm).glob('*.mp4') if f.name.startswith('!!!')), None) \
                if (PUB / nm).exists() else None
            d = _duration(video) if video else None
            if d is None or d > max_sec:
                skipped.append(f"{nm} ({'?' if d is None else int(d)} с)")
                continue
            picked.append(nm)
        xs[date] = picked
        _save(s)
        if skipped:
            log(f"{label} {date}: пропущены (длиннее {max_sec // 60}:{max_sec % 60:02d} или не прочитал длину): {', '.join(skipped)}")
        if not picked:
            log(f"{label} {date}: подходящих роликов нет, в {label} сегодня ничего")
            continue
        for nm in picked:
            e = s[nm]
            if e.get('moved') or plat in e.get('posts', {}):
                continue
            at = datetime.datetime.fromisoformat(e['at'])
            if at < datetime.datetime.now() + datetime.timedelta(minutes=10):
                at = datetime.datetime.now() + datetime.timedelta(minutes=random.randint(20, 30))
            text = _x_text(read_pack(PUB / nm), nm, max_text)
            body = {'post': {'accountId': acc[plat],
                             'content': {'text': text, 'mediaUrls': [e['video']], 'platform': plat},
                             'target': {'targetType': plat}},
                    'scheduledTime': at.astimezone().isoformat(timespec='seconds')}
            try:
                r = _req('POST', '/posts', body, key)
                e['posts'][plat] = {'id': r.get('postSubmissionId'), 'status': 'запланирован'}
                if e.get('status') == 'проверено':
                    e['status'] = 'запланирован'
                log(f"BLOTATO {label} {at:%Y-%m-%d %H:%M} — {nm}")
            except Exception as ex:
                e['posts'][plat] = {'status': 'ошибка', 'error': str(ex)[:300]}
                log(f"ОШИБКА blotato {label} — {nm}: {str(ex)[:200]}")
            _save(s)
            time.sleep(2)

# Threads (разбор 27.10.2026): хештеги и строки про ссылки/видео/личку режут охват — убираем ТОЛЬКО для Threads.
_TH_DROP = re.compile(r'(Полное видео|Монтаж делал|в шапке профиля|ссылка в шапке|Пишите в личку|youtu\.be|https?://|www\.|t\.me/)', re.I)
def _threads_clean(text):
    out = []
    for line in (text or '').splitlines():
        s = line.strip()
        if _TH_DROP.search(s):
            continue
        words = s.split()
        if '#' in s and words and sum(w.startswith('#') for w in words) >= len(words) - 1:
            continue                                   # строка хештегов (бывает первый без «#»)
        s = re.sub(r'(\s*#[\w\-]+)+\s*$', '', s)        # хвост из хештегов в конце строки
        s = re.sub(r'#(?=\w)', '', s).strip()            # хештег внутри фразы — оставляем слово
        out.append(s)
    txt = '\n'.join(out)
    txt = re.sub(r'(\n\s*⠀?\s*){3,}', '\n\n', txt)
    txt = re.sub(r'(\n[\s⠀]*)+$', '', txt).strip()
    return txt or (text or '').strip()

def _no_links(text):
    return re.sub(r'[ \t]*(https?://\S+|www\.\S+|t\.me/\S+)', '', text or '').strip()

def schedule_li(key, s):
    """LinkedIn: вт, чт, сб — 1 ролик (вечер → обед → утро), путешествия пропускаем."""
    fb = _load(FBPLAN, {})
    acc = s.get('_accounts') or {}
    if 'linkedin' not in acc:
        acc = _accounts(key, s)
        if 'linkedin' not in acc:
            return
    now = datetime.datetime.now()
    ls = s.setdefault('_li', {})
    days = {}
    for name, v in fb.items():
        if v.get('platform', 'fb') == 'fb' and v.get('date'):
            days.setdefault(v['date'], []).append((v.get('time', ''), name))
    for date, items in sorted(days.items()):
        if date < LI_START or date in ls or date < now.date().isoformat():
            continue
        if date < LI_DAILY and datetime.date.fromisoformat(date).weekday() not in LI_DAYS:
            continue
        per_day = 2 if date >= LI_TWO else LI_PER_DAY
        items.sort()
        first = datetime.datetime.fromisoformat(f"{date} {items[0][0]}")
        if len(items) < 4 and now < first - datetime.timedelta(hours=3):   # 4 ролика в день с 27.10.2026
            continue
        entries = [(t, nm) for t, nm in items if s.get(nm, {}).get('at') and s[nm].get('video')]
        if not entries or (len(entries) < len(items) and now < first - datetime.timedelta(hours=3)):
            continue
        picked = []
        for t, nm in reversed(entries):
            if len(picked) >= per_day:
                break
            if any(w in nm.upper().split() for w in LI_SKIP):
                continue
            try: head = (read_pack(PUB / nm) or '')[:400]
            except Exception: head = ''
            if not LI_TOPIC.search(nm + ' ' + head):
                continue                               # жизненные темы в LinkedIn не ставим
            picked.append(nm)
        ls[date] = picked
        _save(s)
        if not picked:
            log(f"LinkedIn {date}: деловых роликов нет (недвижимость, аренда, налоги, документы), в LinkedIn ничего")
            continue
        for nm in picked:
            e = s[nm]
            if e.get('moved') or 'linkedin' in e.get('posts', {}):
                continue
            at = datetime.datetime.fromisoformat(e['at'])
            if at < datetime.datetime.now() + datetime.timedelta(minutes=10):
                at = datetime.datetime.now() + datetime.timedelta(minutes=random.randint(20, 30))
            text = _no_links(read_pack(PUB / nm)) or re.sub(r'^\d+\s+', '', nm)
            if len(text) > LI_MAX_TEXT:
                text = text[:LI_MAX_TEXT - 1].rsplit(' ', 1)[0] + '…'
            body = {'post': {'accountId': acc['linkedin'],
                             'content': {'text': text, 'mediaUrls': [e['video']], 'platform': 'linkedin'},
                             'target': {'targetType': 'linkedin'}},
                    'scheduledTime': at.astimezone().isoformat(timespec='seconds')}
            try:
                r = _req('POST', '/posts', body, key)
                e['posts']['linkedin'] = {'id': r.get('postSubmissionId'), 'status': 'запланирован'}
                if e.get('status') == 'проверено':
                    e['status'] = 'запланирован'
                log(f"BLOTATO LinkedIn {at:%Y-%m-%d %H:%M} — {nm}")
            except Exception as ex:
                e['posts']['linkedin'] = {'status': 'ошибка', 'error': str(ex)[:300]}
                log(f"ОШИБКА blotato LinkedIn — {nm}: {str(ex)[:200]}")
            _save(s)
            time.sleep(2)

CHECK_LOG_EVERY = 60               # минут: «ещё не ясно» пишем в журнал не чаще раза в час на ролик
CHECK_ALERT_AFTER = 120           # минут после выхода: всё ещё не ясно — журнал + Telegram (один раз)

def _plat(name):
    name = str(name or '').lower()
    return 'twitter' if name in ('x', 'twitter') else name

def _list_posts(key, at):
    """Все посты Blotato за сутки вокруг времени выхода (GET /v2/posts) — запасной путь, когда старый id молчит."""
    since = (at - datetime.timedelta(days=1)).astimezone().isoformat(timespec='seconds')
    until = (at + datetime.timedelta(days=1)).astimezone().isoformat(timespec='seconds')
    q = urllib.parse.urlencode({'since': since, 'until': until, 'limit': 250})
    items, cursor = [], None
    for _ in range(10):
        r = _req('GET', '/posts?' + q + (f'&cursor={urllib.parse.quote(str(cursor))}' if cursor else ''), key=key)
        items += r.get('items', [])
        cursor = r.get('cursor')
        if not cursor:
            break
    return items

def _find(items, p, e, text):
    """Ищем пост ролика в списке: та же сеть и то же видео (или тот же текст)."""
    for it in items:
        if _plat(it.get('platform') or (it.get('account') or {}).get('platform')) != p:
            continue
        if any(v and v in (it.get('mediaUrls') or []) for v in (e.get('video'), e.get('video_tt'))):
            return it
    head = (text or '').strip()[:60]
    for it in items:
        if _plat(it.get('platform') or (it.get('account') or {}).get('platform')) == p and head \
                and (it.get('text') or '').strip()[:60] == head:
            return it
    return None

def check(key, s):
    """После времени выхода спрашиваем у Blotato, вышло ли.
    Сначала по id (GET /posts/{id}); если ответа нет или статус не «вышел/ошибка» — ищем в списке постов
    (после переноса времени старый id отвечает «in-progress» вечно). Не ясно — журнал раз в час,
    через 2 часа после выхода — журнал + Telegram. Ошибка публикации — журнал + Telegram сразу."""
    now = datetime.datetime.now()
    for name, e in s.items():
        if name.startswith('_') or not isinstance(e, dict) or not e.get('at') or e.get('status') == 'проверено':
            continue
        at = datetime.datetime.fromisoformat(e['at'])
        if now < at + datetime.timedelta(minutes=15):
            continue
        done, unclear, listed = True, [], None
        for p, x in e.get('posts', {}).items():
            if x.get('status') != 'запланирован' or not x.get('id'):
                continue
            st, why = None, ''
            try:
                r = _req('GET', f"/posts/{x['id']}", key=key)
                st = r.get('status')
                why = f"по id: {st or json.dumps(r, ensure_ascii=False)[:120]}"
            except Exception as ex:
                r, why = {}, f"по id: {str(ex)[:120]}"
            if st == 'published':
                x['status'] = 'вышел'; x['url'] = r.get('publicUrl')
                continue
            if st == 'failed':
                x['status'] = 'ошибка'; x['error'] = (r.get('errorMessage') or '')[:300]
                log(f"ОШИБКА blotato {p} не вышел — {name}: {x['error'][:200]}")
                continue
            # запасной путь: список постов
            try:
                if listed is None:
                    listed = _list_posts(key, at)
                it = _find(listed, p, e, read_pack(PUB / name))
            except Exception as ex:
                it = None; why += f"; список: {str(ex)[:120]}"
            if it:
                state = it.get('state') or {}
                t = state.get('type')
                if t == 'published':
                    x['status'] = 'вышел'; x['url'] = state.get('postUrl') or it.get('postUrl')
                    if it.get('id') and it['id'] != x['id']:
                        x['id_old'], x['id'] = x['id'], it['id']
                    continue
                if t == 'failed':
                    x['status'] = 'ошибка'; x['error'] = (state.get('errorMessage') or '')[:300]
                    log(f"ОШИБКА blotato {p} не вышел — {name}: {x['error'][:200]}")
                    continue
                why += f"; в списке: {t or '?'}"
            elif listed is not None:
                why += "; в списке не найден"
            done = False
            unclear.append(f"{p} ({why})")
        if done:
            e['status'] = 'проверено'
            log(f"BLOTATO проверка — {name}: " + ', '.join(f"{p} {x['status']}" for p, x in e['posts'].items()))
        elif unclear:
            mins = int((now - at).total_seconds() // 60)
            last = e.get('check_log')
            if mins >= CHECK_ALERT_AFTER and not e.get('check_alert'):
                e['check_alert'] = True; e['check_log'] = f"{now:%Y-%m-%d %H:%M}"
                log(f"ОШИБКА blotato проверка — {name}: через {mins // 60} ч {mins % 60} мин после выхода "
                    f"статус не ясен: {'; '.join(unclear)[:600]}")
            elif not last or now - datetime.datetime.fromisoformat(last) >= datetime.timedelta(minutes=CHECK_LOG_EVERY):
                e['check_log'] = f"{now:%Y-%m-%d %H:%M}"
                log(f"BLOTATO проверка — {name}: ещё не ясно ({mins} мин после выхода): {'; '.join(unclear)[:600]}")
        _save(s)

def move(key, s):
    """Перенос времени: файл _blotato_перенос.json {"папка": "ГГГГ-ММ-ДД ЧЧ:ММ"}. Выполнил — файл удаляю."""
    want = _load(MOVE, None)
    if not want:
        return
    items, cursor = [], None
    while True:
        r = _req('GET', '/schedules?limit=50' + (f'&cursor={cursor}' if cursor else ''), key=key)
        items += r.get('items', [])
        cursor = r.get('cursor')
        if not cursor:
            break
    left = {}
    for name, when in want.items():
        e = s.get(name)
        if not e or e.get('status') == 'загрузка':
            left[name] = when; continue
        text = read_pack(PUB / name)
        at = datetime.datetime.fromisoformat(when)
        n = 0
        for it in items:
            c = (it.get('draft') or {}).get('content') or {}
            same = any(v and v in (c.get('mediaUrls') or []) for v in (e.get('video'), e.get('video_tt'))) or \
                   (text and (c.get('text') or '').strip() == text.strip())
            if same:
                patch = {'scheduledTime': at.astimezone().isoformat(timespec='seconds')}
                tg = (it.get('draft') or {}).get('target') or {}
                if tg.get('targetType') == 'youtube' and tg.get('title') and '#shorts' not in tg['title'].lower():
                    d = json.loads(json.dumps(it['draft'])); d['target']['title'] = _yt_title(tg['title'])
                    patch['draft'] = d
                _req('PATCH', f"/schedules/{it['id']}", {'patch': patch}, key)
                n += 1
        if n:
            e['at'] = f"{at:%Y-%m-%d %H:%M}"
            e['status'] = 'запланирован'
            log(f"BLOTATO перенос {name} → {e['at']} ({n} сети)")
        else:
            log(f"ОШИБКА blotato перенос {name}: в расписании Blotato не найден")
    _save(s)
    if left:
        MOVE.write_text(json.dumps(left, ensure_ascii=False), encoding='utf-8')
    else:
        MOVE.unlink(missing_ok=True)

MONTHS = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь',
          'Октябрь', 'Ноябрь', 'Декабрь']

def _month_dir(date_str):
    """«!!!ШОРТЫ ОПУБЛИКОВАННЫЕ\Октябрь 2026» — по дате выхода (решение Евгения 23.10.2026)."""
    try: d = datetime.date.fromisoformat(date_str[:10])
    except Exception: d = datetime.date.today()
    return DONE_DIR / f"{MONTHS[d.month - 1]} {d.year}"

def _tidy_done():
    """Папки роликов, лежащие прямо в «!!!ШОРТЫ ОПУБЛИКОВАННЫЕ», раскладываю по месяцам (дата — из списка роликов)."""
    if not DONE_DIR.exists():
        return
    dates = {}
    lst = DONE_DIR / '_список роликов.txt'
    if lst.exists():
        for line in lst.read_text(encoding='utf-8-sig').splitlines():
            parts = [x.strip() for x in line.split('|')]
            if len(parts) >= 2:
                dates[parts[1]] = parts[0]
    for d in DONE_DIR.iterdir():
        if not d.is_dir() or d.name.startswith('_') or any(d.name.startswith(m + ' ') for m in MONTHS):
            continue
        date = dates.get(d.name) or datetime.date.fromtimestamp(d.stat().st_mtime).isoformat()
        dst_dir = _month_dir(date)
        try:
            dst_dir.mkdir(parents=True, exist_ok=True)
            if not (dst_dir / d.name).exists():
                shutil.move(str(d), str(dst_dir / d.name))
        except Exception as ex:
            log(f"раскладка по месяцам {d.name}: {str(ex)[:150]}")

def archive(s):
    """Вышло в Facebook и во всех 4 сетях — папку в «!!!ШОРТЫ ОПУБЛИКОВАННЫЕ»."""
    fb = _load(FBPLAN, {})
    for name, e in s.items():
        if name.startswith('_') or e.get('status') != 'проверено' or e.get('moved'):
            continue
        if fb.get(name, {}).get('status') != 'готово':
            continue
        if any(x.get('status') != 'вышел' for p, x in e.get('posts', {}).items() if p not in ('twitter', 'linkedin', 'bluesky')):
            continue
        src = PUB / name
        if src.exists():
            try:
                mdir = _month_dir(e.get('at', ''))
                mdir.mkdir(parents=True, exist_ok=True)
                dst = mdir / re.sub(r'^\d+\s+', '', name)
                if dst.exists():
                    dst = mdir / f"{dst.name} {datetime.date.today():%d.%m}"
                title = (read_pack(src).splitlines() or [''])[0].strip()
                shutil.move(str(src), str(dst))
                log(f"ОПУБЛИКОВАНО везде — {name} → «{DONE_DIR.name}\\{mdir.name}»")
                links = ' '.join(f"{p}: {x['url']}" for p, x in e.get('posts', {}).items() if x.get('url'))
                with open(DONE_DIR / '_список роликов.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{e.get('at', '')[:10]} | {dst.name} | {title} | {links}\n")
            except Exception as ex:
                log(f"перенос папки {name}: {str(ex)[:150]}"); continue
        e['moved'] = True
        _save(s)

# ---------------- Текстовые посты (24.10.2026) ----------------
# Папка «Посты!\Соцсети»: задание = .json {"name": "...", "image": "карточка.jpg" (необязательно, рядом с заданием),
#   "texts": {"threads": "...", "twitter": "...", "bluesky": "...", "instagram": "...", "linkedin": "..."},
#   "at": "ГГГГ-ММ-ДД ЧЧ:ММ" (необязательно — иначе сразу)}.
# Отправляет в каждую сеть из texts, учёт — «_blotato.json» → «_text». До 3 попыток на сеть.
# Всё отправлено (или попытки кончились) — задание и картинка уезжают в «Соцсети\отправлено».
# Через 5+ минут проверяет выход; итог — в журнал и в Telegram (со ссылками).
TEXT_DIR = ROOT / 'Брокер' / 'Посты' / 'Соцсети'
TEXT_LIMITS = {'threads': 500, 'twitter': 280, 'bluesky': 300, 'instagram': 2200, 'linkedin': 3000}
TEXT_TRIES = 3

def _text_target(p):
    if p == 'threads':
        return {'targetType': 'threads', 'replyControl': 'everyone'}
    return {'targetType': p}

def schedule_text(key, s):
    if not TEXT_DIR.exists():
        return
    tasks = sorted(f for f in TEXT_DIR.glob('*.json') if not f.name.startswith('_'))
    if not tasks:
        return
    acc = _accounts(key, s)
    ts = s.setdefault('_text', {})
    now = datetime.datetime.now()
    for f in tasks:
        try:
            j = json.loads(f.read_text(encoding='utf-8-sig'))
        except Exception as ex:
            log(f"ОШИБКА текст-пост {f.name}: не читается ({str(ex)[:120]})"); f.rename(f.with_suffix('.bad')); continue
        if j.get('at') and datetime.datetime.fromisoformat(j['at']) > now:
            continue
        e = ts.setdefault(f.stem, {'posts': {}, 'sent': f"{now:%Y-%m-%d %H:%M}"})
        img_url = e.get('image_url')
        img = TEXT_DIR / j['image'] if j.get('image') else None
        for p, text in (j.get('texts') or {}).items():
            p = _plat(p)
            x = e['posts'].setdefault(p, {'tries': 0})
            if x.get('id') or x['tries'] >= TEXT_TRIES:
                continue
            if p not in acc:
                x['tries'] = TEXT_TRIES; x['status'] = 'нет аккаунта'; continue
            text = (text or '').strip()
            if p == 'threads':
                text = _threads_clean(text)
            lim = TEXT_LIMITS.get(p, 500)
            if len(text) > lim:
                text = text[:lim - 1].rsplit(' ', 1)[0] + '…'
            media = []
            if img and img.exists() and p in ('instagram', 'threads', 'twitter', 'bluesky', 'linkedin') \
                    and (p == 'instagram' or j.get('image_all')):
                if not img_url:
                    try:
                        img_url = e['image_url'] = _upload(img, key)
                    except Exception as ex:
                        x['tries'] += 1; x['status'] = 'ошибка'; x['error'] = f"картинка: {str(ex)[:250]}"
                        log(f"ОШИБКА текст-пост {p} — {f.stem}: картинка не загрузилась {str(ex)[:150]}")
                        continue
                media = [img_url]
            if p == 'instagram' and not media:
                x['tries'] = TEXT_TRIES; x['status'] = 'ошибка'; x['error'] = 'Instagram без картинки не принимает'
                log(f"ОШИБКА текст-пост instagram — {f.stem}: нет картинки"); continue
            at = datetime.datetime.now() + datetime.timedelta(minutes=2)
            body = {'post': {'accountId': acc[p], 'content': {'text': text, 'mediaUrls': media, 'platform': p},
                             'target': _text_target(p)},
                    'scheduledTime': at.astimezone().isoformat(timespec='seconds')}
            x['tries'] += 1
            try:
                r = _req('POST', '/posts', body, key)
                x.update(id=r.get('postSubmissionId'), status='отправлен', at=f"{at:%Y-%m-%d %H:%M}")
                x.pop('error', None)
                log(f"BLOTATO текст {p} — {f.stem}: отправлен")
            except Exception as ex:
                x['status'] = 'ошибка'; x['error'] = str(ex)[:300]
                log(f"ОШИБКА текст-пост {p} — {f.stem} (попытка {x['tries']} из {TEXT_TRIES}): {str(ex)[:200]}")
            _save(s)
            time.sleep(2)
        _save(s)
        if all(x.get('id') or x.get('tries', 0) >= TEXT_TRIES for x in e['posts'].values()):
            dst = TEXT_DIR / 'отправлено'
            dst.mkdir(exist_ok=True)
            try:
                shutil.move(str(f), str(dst / f.name))
                if img and img.exists() and not any(
                        (TEXT_DIR / g.name).exists() and g != f and json.loads(g.read_text(encoding='utf-8-sig')).get('image') == j['image']
                        for g in TEXT_DIR.glob('*.json')):
                    shutil.move(str(img), str(dst / img.name))
            except Exception as ex:
                log(f"текст-пост перенос {f.name}: {str(ex)[:150]}")

def check_text(key, s):
    from common import tg
    now = datetime.datetime.now()
    for name, e in (s.get('_text') or {}).items():
        if e.get('status') == 'проверено':
            continue
        waiting = False
        for p, x in e.get('posts', {}).items():
            if x.get('status') != 'отправлен' or not x.get('id'):
                continue
            if now < datetime.datetime.fromisoformat(x['at']) + datetime.timedelta(minutes=3):
                waiting = True; continue
            try:
                r = _req('GET', f"/posts/{x['id']}", key=key)
            except Exception as ex:
                r = {'status': '?', 'errorMessage': str(ex)[:150]}
            st = r.get('status')
            if st == 'published':
                x['status'] = 'вышел'; x['url'] = r.get('publicUrl')
            elif st == 'failed':
                x['status'] = 'ошибка'; x['error'] = (r.get('errorMessage') or '')[:300]
                log(f"ОШИБКА текст-пост {p} не вышел — {name}: {x['error'][:200]}")
            elif now - datetime.datetime.fromisoformat(x['at']) > datetime.timedelta(hours=2):
                x['status'] = 'не ясно'
                log(f"ОШИБКА текст-пост {p} — {name}: через 2 часа статус не ясен ({st})")
            else:
                waiting = True
        if not waiting and all(x.get('status') != 'отправлен' for x in e.get('posts', {}).values()):
            e['status'] = 'проверено'
            res = ', '.join(f"{p} {x.get('status')}" + (f" {x['url']}" if x.get('url') else '') +
                            (f" ({x.get('error', '')[:120]})" if x.get('status') == 'ошибка' else '')
                            for p, x in e['posts'].items())
            log(f"BLOTATO текст проверка — {name}: {res}")
            tg(f"Текстовый пост «{name}»: {res}")
        _save(s)

def run():
    key = _key()
    if not key:
        return
    if LOCK.exists() and time.time() - LOCK.stat().st_mtime < 2 * 3600:
        return
    LOCK.write_text('1')
    try:
        s = _load(STATE, {})
        try: schedule(key, s)
        except Exception as ex: log(f"ОШИБКА blotato постановка: {str(ex)[:200]}")
        try: schedule_x(key, s)
        except Exception as ex: log(f"ОШИБКА blotato X: {str(ex)[:200]}")
        try: schedule_bs(key, s)
        except Exception as ex: log(f"ОШИБКА blotato Bluesky: {str(ex)[:200]}")
        try: schedule_li(key, s)
        except Exception as ex: log(f"ОШИБКА blotato LinkedIn: {str(ex)[:200]}")
        try: schedule_text(key, s)
        except Exception as ex: log(f"ОШИБКА blotato текст-посты: {str(ex)[:200]}")
        try: check_text(key, s)
        except Exception as ex: log(f"blotato проверка текст-постов: {str(ex)[:150]}")
        try: move(key, s)
        except Exception as ex: log(f"ОШИБКА blotato перенос: {str(ex)[:200]}")
        try: check(key, s)
        except Exception as ex: log(f"blotato проверка: {str(ex)[:150]}")
        try: archive(s)
        except Exception as ex: log(f"blotato архив: {str(ex)[:150]}")
        try: _tidy_done()
        except Exception as ex: log(f"blotato раскладка по месяцам: {str(ex)[:150]}")
    finally:
        LOCK.unlink(missing_ok=True)
