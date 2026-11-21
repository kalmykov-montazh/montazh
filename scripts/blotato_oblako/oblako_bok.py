# X, Bluesky, LinkedIn из облака (решение Евгения 21.11.2026: «чтобы не зависело от моего компьютера»).
# Логика та же, что на компьютере: schedule_x / schedule_bs / schedule_li из Общее/Робот/blotato.py (план наращивания,
# длина видео, деловые темы для LinkedIn, только сегодня + завтра).
# Кто ставит — рубильник «_задания/_blotato_облако_бок_вкл.txt»:
#   есть рубильник И компьютер подтвердил («_blotato_облако_бок_принял.txt» с тем же словом, старше 5 минут) → ставит облако;
#   иначе облако ничего не ставит. Откат — удалить рубильник, компьютер сразу ставит сам.
# Облако НИКОГДА не пишет _blotato.json компьютера. Своё пишет в «_blotato_облако_бок.json»:
#   {"_x": {дата: [папки]}, "_bs": {...}, "_li": {...}, "posts": {папка: {twitter|bluesky|linkedin: {...}}}}
# Компьютер (_adopt_side) забирает оттуда к себе и дальше проверяет и архивирует как обычно.
# Режим «проверка» — без рубильника и без постановки: только показать, что поставил бы.
import json, sys, subprocess, pathlib, datetime, importlib, copy

Q = 'montazh:Брокер/К публикации/_задания'
PUBR = 'montazh:Брокер/К публикации'
W = pathlib.Path('work_bok').resolve()
SIDE = ('twitter', 'bluesky', 'linkedin')
DAYK = ('_x', '_bs', '_li')

def rc(*a, check=True):
    return subprocess.run(['rclone', *a], capture_output=True, text=True, check=check).stdout

def rc_json(path, default):
    try:
        t = rc('cat', path, check=False)
        return json.loads(t.lstrip('﻿')) if t.strip() else default
    except Exception:
        return default

def gate():
    sw = rc('cat', f'{Q}/_blotato_облако_бок_вкл.txt', check=False).strip()
    if not sw:
        print('рубильник X/Bluesky/LinkedIn выключен — ставит компьютер'); return False
    ack = rc('cat', f'{Q}/_blotato_облако_бок_принял.txt', check=False).strip()
    if ack != sw:
        print('компьютер ещё не подтвердил рубильник X/Bluesky/LinkedIn — жду'); return False
    try:
        ls = rc('lsjson', f'{Q}/_blotato_облако_бок_принял.txt', check=False)
        mt = datetime.datetime.fromisoformat(json.loads(ls)[0]['ModTime'][:19] + '+00:00')
        if datetime.datetime.now(datetime.timezone.utc) - mt < datetime.timedelta(minutes=5):
            print('подтверждение свежее (<5 мин) — жду'); return False
    except Exception as ex:
        print('время подтверждения не прочитал:', ex)
    return True

def main():
    dry = (sys.argv[1] if len(sys.argv) > 1 else '') == 'проверка'
    if not dry and not gate():
        return

    R = W / 'Общее' / 'Робот'; R.mkdir(parents=True, exist_ok=True)
    for f in ('blotato.py', 'common.py', 'telegram_ключ.txt.txt'):
        rc('copyto', f'montazh:Общее/Робот/{f}', str(R / f), check=False)
    key = open('key.txt', encoding='utf-8-sig').read().strip()
    (R / 'blotato_ключ.txt').write_text(key, encoding='utf-8')
    QL = W / 'Брокер' / 'К публикации' / '_задания'; QL.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(R))
    common = importlib.import_module('common')
    b = importlib.import_module('blotato')

    plan = rc_json(f'{Q}/_план.json', {})
    pc = rc_json(f'{Q}/_blotato.json', {})
    cloud = rc_json(f'{Q}/_blotato_облако.json', {})
    side = rc_json(f'{Q}/_blotato_облако_бок.json', {})
    (QL / '_план.json').write_text(json.dumps(plan, ensure_ascii=False), encoding='utf-8')

    # состояние = компьютер + записи облака (основные 4 сети) + уже поставленное облаком в X/Bluesky/LinkedIn
    s = copy.deepcopy(pc)
    for n, e in cloud.items():
        if isinstance(e, dict) and n not in s:
            e = copy.deepcopy(e); e.pop('_журнал', None); s[n] = e
    for k in DAYK:
        for d, picked in (side.get(k) or {}).items():
            s.setdefault(k, {}).setdefault(d, picked)
    for n, posts in (side.get('posts') or {}).items():
        e = s.get(n)
        if isinstance(e, dict):
            for p, x in posts.items():
                cur = e.setdefault('posts', {}).get(p)
                if not cur or (b._full(cur) and not b._full(x)):
                    e['posts'][p] = x

    # нужные файлы: упаковка — для текста, видео — только для дней, где X/Bluesky ещё не выбраны (длина ролика)
    today = datetime.date.today()
    last = b._side_limit()
    for n, v in plan.items():
        d = v.get('date', '')
        if v.get('platform', 'fb') != 'fb' or not (today.isoformat() <= d <= last):
            continue
        dst = W / 'Брокер' / 'К публикации' / n
        inc = ['--include', 'упаковка.txt']
        if d not in (s.get('_x') or {}) or d not in (s.get('_bs') or {}):
            inc += ['--include', '!!!*.mp4']
        rc('copy', f'{PUBR}/{n}', str(dst), *inc, check=False)

    logs = []
    def log(m):
        print('журнал:', m); logs.append(f"{datetime.datetime.now():%Y-%m-%d %H:%M} {m}")
        if not dry and m.startswith(('ОШИБКА', 'ПРОПУСК', 'СБОЙ')):
            common.tg('Робот-публикатор (облако, X/Bluesky/LinkedIn): ' + m)
    common.log = log; b.log = log

    def save(st):
        if dry:
            return
        out = rc_json(f'{Q}/_blotato_облако_бок.json', {})
        for k in DAYK:
            for d, picked in (st.get(k) or {}).items():
                if d not in (pc.get(k) or {}):
                    out.setdefault(k, {})[d] = picked
        for n, e in st.items():
            if n.startswith('_') or not isinstance(e, dict):
                continue
            mine = (pc.get(n) or {}).get('posts') or {}
            for p in SIDE:
                x = (e.get('posts') or {}).get(p)
                if x and x != mine.get(p):
                    out.setdefault('posts', {}).setdefault(n, {})[p] = x
        if logs:
            out['_журнал'] = (out.get('_журнал') or [])[-30:] + logs[-5:]
        p = W / 'bok.json'; p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
        rc('copyto', str(p), f'{Q}/_blotato_облако_бок.json')
    b._save = save

    if dry:
        real = b._req
        def fake(method, path, body=None, key=None):
            if method == 'POST':
                c = body['post']['content']
                print(f"ПОСТАВИЛ БЫ {c['platform']} {body['scheduledTime']}: {c['text'][:80]!r}")
                return {'postSubmissionId': 'проверка'}
            return real(method, path, body, key)
        b._req = fake
        b.time.sleep = lambda *_: None

    for f in (b.schedule_x, b.schedule_bs, b.schedule_li):
        try:
            f(key, s)
        except Exception as ex:
            log(f"ОШИБКА облако {f.__name__}: {str(ex)[:200]}")
    print('готово' + (' (проверка, ничего не поставлено)' if dry else ''), *logs, sep='\n  ')

if __name__ == '__main__':
    main()
