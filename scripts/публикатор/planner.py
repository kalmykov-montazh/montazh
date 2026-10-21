# Автораскладка и автоочистка (решение Евгения 15.10.2026).
# Раскладка: каждая папка в «К публикации!», у которой имя начинается с номера («1 03 Меньше года на защите»),
# ставится в Facebook на ближайший свободный слот 8:20 / 13:00 / 18:30. Порядок — по первому числу в имени.
# Папку без номера не трогаем. Папки НЕ переносим в «Опубликовано!» (Евгений переносит сам, пока остальные
# соцсети не на автопостинге). Что уже поставлено — помним в «_задания\_план.json», чтобы не ставить второй раз.
# Очистка: выполненное и старые ошибки — в «_задания\архив», архив и скриншоты шагов старше 14 дней удаляются.
import json, re, time, datetime, shutil
from common import PUB, QUEUE, log

SLOTS = ['08:20', '13:00', '18:30']
LEAD_MIN = 70                     # минимум минут до выхода: робот забирает задание до 10 мин + ставит ~10 мин + запас
PLAN = QUEUE / '_план.json'
ARCHIVE = QUEUE / 'архив'
NUM = re.compile(r'^\s*(\d+)\s+\S')

def _load():
    try:
        return json.loads(PLAN.read_text(encoding='utf-8'))
    except Exception:
        return {}

def _save(p):
    PLAN.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding='utf-8')

def _pending_folders():
    # любые задания (ждут, выполнены, с ошибкой, в архиве) — папку второй раз не ставим
    s = set()
    for d in (QUEUE, ARCHIVE):
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.name.startswith('_') or f.suffix not in ('.json', '.done', '.error'):
                continue
            try: s.add(json.loads(f.read_text(encoding='utf-8-sig'))['folder'])
            except Exception: pass
    return s

def plan():
    p = _load()
    busy = {(v['date'], v['time']) for v in p.values() if v.get('platform', 'fb') == 'fb'}
    skip = set(p) | _pending_folders()
    new = []
    for d in PUB.iterdir():
        if not d.is_dir() or d.name.startswith('_') or d.name in skip:
            continue
        m = NUM.match(d.name)
        if m and any(f.suffix.lower() == '.mp4' for f in d.iterdir()):
            new.append((int(m.group(1)), d.name))
    if not new:
        return
    new.sort()
    now = datetime.datetime.now()
    earliest = now + datetime.timedelta(minutes=LEAD_MIN)
    day = now.date()
    for _, name in new:
        while True:
            free = [t for t in SLOTS if (day.isoformat(), t) not in busy and
                    datetime.datetime.combine(day, datetime.time(*map(int, t.split(':')))) >= earliest]
            if free:
                t = free[0]; break
            day += datetime.timedelta(days=1)
        ds = day.isoformat()
        busy.add((ds, t))
        job = {'platform': 'fb', 'folder': name, 'date': ds, 'time': t}
        safe = re.sub(r'[^\w\- ]', '', name)[:40].strip()
        (QUEUE / f"{ds}_{t.replace(':', '')}_fb_{safe}.json").write_text(
            json.dumps(job, ensure_ascii=False), encoding='utf-8')
        p[name] = {'platform': 'fb', 'date': ds, 'time': t, 'status': 'задание', 'created': f"{now:%Y-%m-%d %H:%M}"}
        log(f"РАСКЛАДКА fb {ds} {t} — {name}")
    _save(p)

def mark(j, status, time_set=None):
    p = _load()
    e = p.setdefault(j['folder'], {'platform': j['platform'], 'date': j['date'], 'time': j['time']})
    e['status'] = status
    if time_set:
        e['time'] = time_set
    _save(p)

def cleanup():
    ARCHIVE.mkdir(exist_ok=True)
    now = time.time()
    day = 86400
    for f in QUEUE.iterdir():
        if not f.is_file() or f.name in ('журнал.txt', '_план.json', '_идёт.lock') or f.suffix == '.json':
            continue
        age = now - f.stat().st_mtime
        base = f.name.split('.')[0]
        done = (QUEUE / f'{base}.done').exists()
        # выполненное — сразу в архив; ошибки и скриншоты — через сутки
        if f.suffix == '.done' or done or age > day:
            try: shutil.move(str(f), str(ARCHIVE / f.name))
            except Exception: pass
    for folder in (ARCHIVE, QUEUE / 'шаги'):
        if folder.exists():
            for f in folder.iterdir():
                if f.is_file() and now - f.stat().st_mtime > 14 * day:
                    f.unlink(missing_ok=True)
    # журнал — последние 400 строк
    log_f = QUEUE / 'журнал.txt'
    if log_f.exists():
        lines = log_f.read_text(encoding='utf-8').splitlines()
        if len(lines) > 500:
            log_f.write_text('\n'.join(lines[-400:]) + '\n', encoding='utf-8')
    # план — забываем записи старше 30 дней, если папки уже нет
    p = _load()
    cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    keep = {k: v for k, v in p.items() if v.get('date', '9999') >= cutoff or (PUB / k).exists()}
    if keep != p:
        _save(keep)
