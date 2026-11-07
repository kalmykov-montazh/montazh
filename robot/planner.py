# Автораскладка и автоочистка (решение Евгения 15.10.2026).
# Раскладка: каждая папка в «К публикации!», у которой имя начинается с номера («1 03 Меньше года на защите»),
# ставится в Facebook на ближайший свободный слот (с 27.10.2026 — 8:15 / 10:45 / 13:30 / 16:30). Порядок — по первому числу в имени.
# Папку без номера не трогаем. Папки НЕ переносим в «Опубликовано!» (Евгений переносит сам, пока остальные
# соцсети не на автопостинге). Что уже поставлено — помним в «_задания\_план.json», чтобы не ставить второй раз.
# Очистка: выполненное и старые ошибки — в «_задания\архив», архив и скриншоты шагов старше 14 дней удаляются.
import json, re, time, datetime, shutil
from common import PUB, QUEUE, log

# 4 ролика в день с 27.10.2026 (решение Евгения 26.10.2026): 8:15 / 10:45 / 13:30 / 16:30.
# До 27.10 — старые 3 слота, чтобы 26.10 не трогать.
SLOTS = ['08:15', '10:45', '13:30', '16:30']
OLD_SLOTS = ['08:20', '13:00', '18:30']
SLOTS_FROM = datetime.date(2026, 10, 27)

# ТЕСТ 04.11.2026 (решение Евгения): с 07.11 по 20.11 время выхода каждый день плавает на 10–25 мин от слота,
# а в НЕЧЁТНЫЕ дни робот публикует рилс сразу кнопкой «Опубликовать» в нужную минуту (mode = live),
# в чётные — как раньше, через «Запланировать» (отложка). Сравниваем медианы. Разбор — файл проекта
# «Автопостинг и охваты — разбор 04.11.2026». Дни до 07.11 уже разложены — их не трогаем.
TEST_FROM = datetime.date(2026, 11, 7)
TEST_TO = datetime.date(2026, 11, 20)

def _slots(day):
    base = SLOTS if day >= SLOTS_FROM else OLD_SLOTS
    if day < TEST_FROM:
        return base
    import random
    out = []
    for i, t in enumerate(base):
        off = random.Random(f"{day.isoformat()}-{i}").choice([-25, -20, -15, -10, 10, 15, 20, 25])
        dt = datetime.datetime.combine(day, datetime.time(*map(int, t.split(':')))) + datetime.timedelta(minutes=off)
        out.append(f"{dt:%H:%M}")
    return out

def _mode(day):
    return 'live' if TEST_FROM <= day <= TEST_TO and day.day % 2 == 1 else 'schedule'

def _slot_index(day, hhmm):
    """К какому базовому слоту относится время (слоты разнесены на 2,5+ часа, сдвиг до 25 мин — не перепутать)."""
    base = SLOTS if day >= SLOTS_FROM else OLD_SLOTS
    m = lambda t: int(t[:2]) * 60 + int(t[3:5])
    return min(range(len(base)), key=lambda i: abs(m(base[i]) - m(hhmm)))
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

# Пауза перед раскладкой (28.10.2026): 02:44 робот схватил папку «03 Без документов не сдадут» в ту же минуту,
# как Евгений её вставил, — а он тут же переименовал её в «1 03 …», и задания FB/Blotato упали (файла по старому пути нет).
# Теперь новую папку робот сначала только запоминает (имя + размер роликов) в «_задания\_увидел.json»
# и ставит её не раньше чем через SETTLE_MIN минут, если за это время имя и размер не менялись.
# Переименовали или ролик ещё докачивается — отсчёт начинается заново.
SETTLE_MIN = 5
RETRY_MAX = 3   # всего попыток поставить ролик (первая + 2 повтора), дальше — ждём Евгения/Claude
# ПАУЗА «ПАЛЬМА» (решение Евгения 04.11.2026): ролики, в имени которых есть «ПАЛЬМА», не публикуем
# до его особого распоряжения. Робот такие папки не ставит, даже если они попали в «К публикации».
# Снять паузу — только по слову Евгения: PALMA_PAUSE = False.
PALMA_PAUSE = True
SEEN = QUEUE / '_увидел.json'

def _load_seen():
    try:
        return json.loads(SEEN.read_text(encoding='utf-8'))
    except Exception:
        return {}

def _save_seen(s):
    try:
        if s != _load_seen():
            SEEN.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding='utf-8')
    except Exception:
        pass

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
    # слот с ошибкой (ролик не встал) считаем свободным — иначе утро пропадает (22.10.2026)
    busy = {(v['date'], _slot_index(datetime.date.fromisoformat(v['date']), v['time'].zfill(5))) for v in p.values()
            if v.get('platform', 'fb') == 'fb' and v.get('status') != 'ошибка' and v.get('date') and v.get('time')}
    # ПОВТОР ПОСЛЕ ОШИБКИ (06.11.2026): раньше папка с ошибкой навсегда оставалась в плане и в .error
    # и больше не ставилась (10.11 так пропали «Испанцы живут с мамой» и «Срок для вашей машины»).
    # Теперь такую папку ставим заново, до RETRY_MAX попыток всего; сначала на её прежнее время, если оно ещё впереди.
    retry = {k for k, v in p.items() if v.get('platform', 'fb') == 'fb' and v.get('status') == 'ошибка'
             and v.get('попыток', 1) < RETRY_MAX}
    skip = (set(p) | _pending_folders()) - retry
    seen, seen_new = _load_seen(), {}
    new = []
    for d in PUB.iterdir():
        if not d.is_dir() or d.name.startswith('_') or d.name in skip:
            continue
        if PALMA_PAUSE and 'ПАЛЬМА' in d.name.upper():
            if d.name not in seen:
                log(f"ПАУЗА ПАЛЬМА: не ставлю — {d.name}")
            seen_new[d.name] = seen.get(d.name) or [time.time(), 0]
            continue
        m = NUM.match(d.name)
        if m and any(f.suffix.lower() == '.mp4' for f in d.iterdir()):
            sizes = sum(f.stat().st_size for f in d.iterdir() if f.suffix.lower() == '.mp4')
            s = seen.get(d.name)
            if not s or s[1] != sizes:
                seen_new[d.name] = [time.time(), sizes]
                log(f"ВИЖУ новую папку, жду {SETTLE_MIN} мин без изменений — {d.name}")
                continue
            seen_new[d.name] = s
            if time.time() - s[0] < SETTLE_MIN * 60:
                continue
            new.append((int(m.group(1)), d.name))
    _save_seen(seen_new)
    if not new:
        return
    new.sort()
    now = datetime.datetime.now()
    earliest = now + datetime.timedelta(minutes=LEAD_MIN)
    day = now.date()
    for _, name in new:
        day = now.date()
        prev = p.get(name) if name in retry else None
        if prev:
            try:
                pd = datetime.date.fromisoformat(prev['date']); pt = prev['time'].zfill(5)
                key = (prev['date'], _slot_index(pd, pt))
                if key not in busy and datetime.datetime.combine(pd, datetime.time(*map(int, pt.split(':')))) >= earliest:
                    day, si, t = pd, key[1], pt
                    _place(p, busy, name, day, si, t, now, prev)
                    continue
            except Exception:
                pass
        while True:
            free = [(i, t) for i, t in enumerate(_slots(day)) if (day.isoformat(), i) not in busy and
                    datetime.datetime.combine(day, datetime.time(*map(int, t.split(':')))) >= earliest]
            if free:
                si, t = free[0]; break
            day += datetime.timedelta(days=1)
        _place(p, busy, name, day, si, t, now, prev)
    _save(p)

def _place(p, busy, name, day, si, t, now, prev=None):
    ds = day.isoformat()
    busy.add((ds, si))
    mode = _mode(day)
    job = {'platform': 'fb', 'folder': name, 'date': ds, 'time': t, 'mode': mode}
    safe = re.sub(r'[^\w\- ]', '', name)[:40].strip()
    (QUEUE / f"{ds}_{t.replace(':', '')}_fb_{safe}.json").write_text(
        json.dumps(job, ensure_ascii=False), encoding='utf-8')
    tries = (prev.get('попыток', 1) + 1) if prev else 1
    p[name] = {'platform': 'fb', 'date': ds, 'time': t, 'mode': mode, 'status': 'задание',
               'created': f"{now:%Y-%m-%d %H:%M}", 'попыток': tries}
    log(f"РАСКЛАДКА fb {ds} {t} ({'сразу' if mode == 'live' else 'отложка'}){' ПОВТОР ' + str(tries) if prev else ''} — {name}")

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
        if not f.is_file() or f.name in ('журнал.txt', '_план.json', '_идёт.lock', '_пульс.txt', '_пульс_конец.txt', '_blotato.json', '_blotato.lock') or f.suffix == '.json':
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
