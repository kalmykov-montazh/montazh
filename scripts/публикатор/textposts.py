# Текстовые посты Facebook: 2 коротыша (цветной фон) + 1 длинный (с фото) в день, сразу в 9 групп.
# Решения Евгения 15.10.2026 — файл проекта «Публикатор — коротыши и длинные посты (решения)».
#
# Папки: «Монтаж!\Посты!\Коротыши», «Длинные», «Фото», «Опубликовано», служебное — «Посты!\_служебное».
# Файл поста — .txt. Необязательные первые строки:
#   @тема: испания        (иначе «общая»)
#   @фото: имя.jpg         (только для длинных; иначе берётся следующее неиспользованное фото)
# Публикуем СРАЗУ, не отложкой: в отложке Facebook выключает «Поделиться в группах».
import json, random, re, shutil, datetime, time
from pathlib import Path
from common import ROOT, QUEUE, log, pause, human_click, human_type, warm_up

POSTS = ROOT / 'Посты!'
SHORT, LONG, PHOTO, DONE = POSTS / 'Коротыши', POSTS / 'Длинные', POSTS / 'Фото', POSTS / 'Опубликовано'
USED_PHOTO = PHOTO / 'использованные'
SYS = POSTS / '_служебное'
GROUPS = SYS / 'группы.json'
DAYPLAN = SYS / 'план дней.json'

# окна времени: (вид, начало, конец) — время внутри окна каждый день случайное
WINDOWS = [('short', '09:10', '10:00'), ('short', '14:00', '15:00'), ('long', '22:30', '25:30')]
LATE_MIN = 90                       # опоздали больше чем на 90 минут (компьютер был выключен) — пропускаем
COOLDOWN = {'испания': 3, 'общая': 1}   # через сколько дней группу можно взять снова
PROVEN, TESTS = 7, 2               # в каждом посте 7 проверенных групп + 2 на тест
# фоны-картинки из «Настройки фона» (Евгению нравятся не однотонные, а «небо/море»-подобные):
# по порядку в окне «Выбор фона»: 0–21 «Декоративные», 22–29 «Градиентные», дальше «Сплошные» — их не берём.
# Без сердечек и конфетти (16–19).
BG_PICK = list(range(0, 16)) + [20, 21] + list(range(22, 30))
PHOTO_EXT = ('.jpg', '.jpeg', '.png', '.webp')

def _jload(p, default):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default

def _jsave(p, data):
    SYS.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    tmp.replace(p)

# ---------- раскладка по дням ----------
def plan():
    """Создаёт задания на сегодня и завтра. Окно, которое уже прошло, не создаём."""
    for d in (SHORT, LONG, PHOTO, DONE, SYS):
        d.mkdir(parents=True, exist_ok=True)
    days = _jload(DAYPLAN, {})
    now = datetime.datetime.now()
    for add in (0, 1):
        day = now.date() + datetime.timedelta(days=add)
        ds = day.isoformat()
        for i, (kind, a, b) in enumerate(WINDOWS):
            key = f'{ds} {i}'
            if key in days:
                continue
            start = datetime.datetime.combine(day, datetime.time(0)) + _td(a)
            end = datetime.datetime.combine(day, datetime.time(0)) + _td(b)
            if end < now:
                continue
            lo = max(start, now + datetime.timedelta(minutes=5))
            at = lo + datetime.timedelta(seconds=random.randint(0, max(0, int((end - lo).total_seconds()))))
            job = {'platform': 'fbtext', 'kind': kind, 'day': ds, 'slot': i, 'at': f'{at:%Y-%m-%d %H:%M}'}
            (QUEUE / f'{at:%Y-%m-%d_%H%M}_fbtext_{kind}.json').write_text(json.dumps(job, ensure_ascii=False), encoding='utf-8')
            days[key] = {'вид': kind, 'время': f'{at:%H:%M}', 'статус': 'задание'}
            log(f'РАСКЛАДКА текст {kind} {at:%Y-%m-%d %H:%M}')
    cutoff = (now.date() - datetime.timedelta(days=30)).isoformat()
    _jsave(DAYPLAN, {k: v for k, v in days.items() if k >= cutoff})

def _td(hhmm):
    h, m = map(int, hhmm.split(':'))
    return datetime.timedelta(hours=h, minutes=m)

def due(j):
    """None — ещё рано; True — пора; False — сильно опоздали, пропускаем."""
    at = datetime.datetime.strptime(j['at'], '%Y-%m-%d %H:%M')
    now = datetime.datetime.now()
    if now < at:
        return None
    return (now - at).total_seconds() <= LATE_MIN * 60

def mark(j, status):
    days = _jload(DAYPLAN, {})
    e = days.setdefault(f"{j['day']} {j['slot']}", {'вид': j['kind']})
    e['статус'] = status
    _jsave(DAYPLAN, days)

# ---------- тексты и фото ----------
def _next_text(kind):
    folder = SHORT if kind == 'short' else LONG
    files = sorted(f for f in folder.glob('*.txt') if not f.name.startswith('_'))
    return files[0] if files else None

def _parse(path):
    meta, lines = {}, path.read_text(encoding='utf-8-sig').splitlines()
    while lines and lines[0].startswith('@'):
        k, _, v = lines.pop(0)[1:].partition(':')
        meta[k.strip().lower()] = v.strip()
    text = '\n'.join(lines).strip().replace('⠀', '')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return meta, text

def _pick_photo(meta):
    if meta.get('фото'):
        p = PHOTO / meta['фото']
        if p.exists():
            return p
        log(f"фото «{meta['фото']}» не найдено, беру следующее")
    files = sorted((f for f in PHOTO.iterdir() if f.is_file() and f.suffix.lower() in PHOTO_EXT),
                   key=lambda f: (f.stat().st_mtime, f.name))
    return files[0] if files else None

# ---------- выбор групп ----------
def _days_since(g, today):
    if not g.get('посты'):
        return 999
    last = max(p['дата'] for p in g['посты'])
    return (today - datetime.date.fromisoformat(last)).days

def choose_groups(available, topic, day):
    """9 групп: 7 проверенных + 2 тестовые. Тема «испания» — 5 испанских + 4 общих, «общая» — 5 общих + 4 испанских.
    Наборы за день не пересекаются; испанская группа — не чаще раза в 3 дня, общая — раз в день."""
    reg = _jload(GROUPS, {})
    available = list(dict.fromkeys(available))   # одинаковые названия — один раз
    for n in available:                      # новые группы, в которые вступил Евгений, — сразу в тест
        if n not in reg:
            reg[n] = {'тип': 'испания' if re.search(SPAIN_RE, n, re.I) else 'общая',
                      'статус': 'не для постов' if re.search(ADS_RE, n, re.I) else 'тест',
                      'посты': [], 'добавлена': day}
            log(f'новая группа в тест: {n}')
    _jsave(GROUPS, reg)
    today = datetime.date.fromisoformat(day)
    used_today = {n for n, g in reg.items() for p in g.get('посты', []) if p.get('день') == day}
    main = 'испания' if topic == 'испания' else 'общая'
    other = 'общая' if main == 'испания' else 'испания'
    quota = {main: 5, other: 4}

    def pool(typ, status, relax, taken):
        out = [n for n in available if n in reg and n not in used_today and n not in taken
               and reg[n]['тип'] == typ and reg[n]['статус'] == status
               and _days_since(reg[n], today) >= COOLDOWN.get(typ, 1) - relax]
        def key(n):
            g = reg[n]
            top = g.get('топ', 99) if typ == 'испания' else 99
            if status == 'тест':             # тестовые: сначала те, что ещё ни разу не пробовали
                return (len(g.get('посты', [])), random.random())
            return (top if topic == 'испания' else 99, -_days_since(g, today), random.random())
        return sorted(out, key=key)

    picked = []
    tests_left = TESTS
    for typ in (main, other):                # по одному тестовому на каждый тип, остальное — проверенные
        for relax in (0, 1, 2):
            have = [n for n in picked if reg[n]['тип'] == typ]
            need = quota[typ] - len(have)
            if need <= 0:
                break
            if tests_left and not any(reg[n]['статус'] == 'тест' for n in have):
                t = pool(typ, 'тест', relax, picked)[:1]
                picked += t; tests_left -= len(t); need -= len(t)
            picked += pool(typ, 'проверенная', relax, picked)[:need]
            if relax == 1:
                log(f'«{typ}»: групп с перерывом не хватает, ослабляю перерыв')
    if len(picked) < 9:                      # один тип кончился — добираем другим
        for typ in (main, other):
            for status in ('проверенная', 'тест'):
                picked += pool(typ, status, 2, picked)[:9 - len(picked)]
    return picked[:9]

ADS_RE = r'недвиж|нерухом|inmob|property|apartament|alquil|аренд|оренд|квартир|комнат|работ|робот|ваканс|trabajo|объявлен|обьявлен|оголош|anunci|реклам|из рук в руки|купи|куплю|барахол|площадка|грузопер|перевез|перевоз|transporte|ремонт|reforma|строит|construc|услуги|послуги|страхов|бизнес|бізнес|доска'
SPAIN_RE = r'испан|españ|spain|валенс|valenc|торрев|torrev|аликан|alican|барсел|barcel|мадрид|малаг|марбел|мурси|тенериф|іспан|валенсі|sagunt|сагунт|кальпе'

def _record(groups, day, kind, title):
    reg = _jload(GROUPS, {})
    stamp = f'{datetime.datetime.now():%Y-%m-%d %H:%M}'
    for n in groups:
        reg.setdefault(n, {'тип': 'общая', 'статус': 'тест', 'посты': []})
        reg[n].setdefault('посты', []).append({'дата': stamp[:10], 'день': day, 'время': stamp[11:], 'вид': kind, 'пост': title[:40]})
    _jsave(GROUPS, reg)

# ---------- публикация ----------
JS_LOAD = """async () => {
  const dlg = [...document.querySelectorAll('[role=dialog]')].find(d => d.innerText.includes('Публикация в группах'));
  if (!dlg) return -1;
  let hist = [];
  for (let i = 0; i < 30; i++) {
    const all = dlg.querySelectorAll('input[type=checkbox]');
    if (all.length) all[all.length - 1].scrollIntoView({block: 'end'});
    await new Promise(r => setTimeout(r, 900 + Math.random() * 600));
    hist.push(dlg.querySelectorAll('input[type=checkbox]').length);
    if (i > 3 && hist[i] === hist[i - 3]) break;
  }
  const first = dlg.querySelector('input[type=checkbox]');
  if (first) first.scrollIntoView({block: 'center'});
  return hist[hist.length - 1];
}"""
JS_SCROLLER = """() => {
  const d = [...document.querySelectorAll('[role=dialog]')].find(d => d.innerText.includes('Публикация в группах'));
  const first = d.querySelector('input[type=checkbox]');
  let e = first, box = null;
  while (e && e !== d) {
    const st = getComputedStyle(e);
    if (e.scrollHeight > e.clientHeight + 20 && /(auto|scroll)/.test(st.overflowY)) { box = e; break; }
    e = e.parentElement;
  }
  const r = (box || d).getBoundingClientRect();
  return {x: r.x + r.width / 2, y: r.y + r.height / 2, found: !!box};
}"""
JS_ROWS = """(want) => {
  const dlg = [...document.querySelectorAll('[role=dialog]')].find(d => d.innerText.includes('Публикация в группах'));
  const rows = [...dlg.querySelectorAll('input[type=checkbox]')].map(b => {
    const row = b.closest('[role=button]') || b.parentElement.parentElement;
    const name = (row.innerText || '').split('\\n')[0].replace(/\\ufeff/g, '').trim();
    return {b, row, name};
  });
  if (want === null) return rows.map(r => r.name);
  const r = rows.find(r => r.name === want);
  if (!r) return null;
  r.row.scrollIntoView({block: 'center'});
  const box = r.row.getBoundingClientRect();
  return {x: box.x, y: box.y, w: box.width, h: box.height,
          checked: r.b.checked || r.b.getAttribute('aria-checked') === 'true'};
}"""

def _set_background(page, dlg):
    """Фон из полоски под текстом (решение Евгения 15.10.2026): там Facebook иногда даёт пляж, небо и т.п.
    Сначала картинки/иллюстрации, потом градиенты; однотонные («Сплошной …») не берём."""
    human_click(page, dlg.get_by_role('button', name='Показать параметры фона').first)
    pause(1, 2)
    labels = [x for x in dlg.locator('[role="button"][aria-label*="фон "]').evaluate_all(
        "els => els.map(e => e.getAttribute('aria-label'))") if x]
    pics = [x for x in labels if 'изображение' in x or 'иллюстрац' in x.lower()]
    grads = [x for x in labels if x.startswith('Градиент') and x not in pics]
    pool = pics + pics + grads or grads or labels   # картинки вдвое чаще
    label = random.choice(pool)
    human_click(page, dlg.locator(f'[role="button"][aria-label="{label}"]').first)
    pause(1, 2)
    return label

def _load_picker(page):
    """Окно «Публикация в группах» догружает группы только при настоящей прокрутке колесом."""
    pdlg = page.locator('[role="dialog"]').filter(has_text='Публикация в группах').last
    pdlg.wait_for(timeout=20000)
    count, same = 0, 0
    for _ in range(120):
        # колесо крутим, держа мышь над последней видимой строкой списка
        # мышь — в середину прокручиваемой области списка (не на строку за краем)
        r = page.evaluate(JS_SCROLLER)
        page.mouse.move(r['x'] + random.uniform(-40, 40), r['y'] + random.uniform(-10, 10), steps=random.randint(4, 9))
        page.mouse.wheel(0, random.randint(700, 1100))
        time.sleep(random.uniform(0.9, 1.6))
        n = page.evaluate("() => { const d=[...document.querySelectorAll('[role=dialog]')].find(d=>d.innerText.includes('Публикация в группах')); return d ? d.querySelectorAll('input[type=checkbox]').length : 0 }")
        same = same + 1 if n == count else 0
        count = n
        if same >= 4:
            break
    names = page.evaluate(JS_ROWS, None)
    log(f"в окне выбора групп: {len(names)} (область прокрутки найдена: {r.get('found')})")
    if len(names) <= 25:
        try:
            from common import QUEUE
            (QUEUE / 'шаги').mkdir(exist_ok=True)
            page.screenshot(path=str(QUEUE / 'шаги' / f'{datetime.datetime.now():%m%d_%H%M} группы.png'))
        except Exception:
            pass
    return names

def _window(page, state):
    """Окно робота запускается свёрнутым; свёрнутое окно Facebook не догружает список групп.
    На время публикации разворачиваем, потом сворачиваем обратно."""
    try:
        cdp = page.context.new_cdp_session(page)
        wid = cdp.send('Browser.getWindowForTarget')['windowId']
        cdp.send('Browser.setWindowBounds', {'windowId': wid, 'bounds': {'windowState': state}})
        if state == 'normal':
            page.bring_to_front()
        pause(1, 2)
    except Exception as e:
        log(f'окно: не смог сделать {state} ({str(e)[:80]})')

class DryRun(Exception):
    pass

def _discard(page):
    """Закрыть окно публикации и стереть черновик."""
    page.keyboard.press('Escape'); pause(1, 2)
    back = page.get_by_role('button', name='Назад')
    if back.count():
        human_click(page, back.last)
    box = page.locator('[role="dialog"] [role="textbox"]').last
    if box.count():
        human_click(page, box)
        page.keyboard.press('Control+A'); pause(0.3, 0.6)
        page.keyboard.press('Delete'); pause(1, 2)
    close = page.get_by_role('button', name='Закрыть диалог создания публикаций')
    if close.count():
        human_click(page, close.last)
    for name in ('Удалить', 'Выйти', 'Не сохранять'):
        b = page.get_by_role('button', name=name, exact=True)
        if b.count():
            human_click(page, b.last); break

def publish(page, j):
    kind = j['kind']
    path = _next_text(kind)
    if not path:
        raise RuntimeError(f"нет текста в «Посты!\\{'Коротыши' if kind == 'short' else 'Длинные'}» — слот пропущен")
    meta, text = _parse(path)
    topic = 'испания' if meta.get('тема', '').lower().startswith('испан') else 'общая'
    if kind == 'short' and len(text) > 130:
        raise RuntimeError(f'коротыш «{path.name}» длиннее 130 знаков ({len(text)}) — фон не включится')
    photo = _pick_photo(meta) if kind == 'long' else None
    bg = ''

    _window(page, 'normal')
    try:
        # до 3 попыток: Facebook иногда не грузит окно «Создать публикацию» (16.10.2026 — серая заглушка).
        # Повторяем, только пока текст ещё в очереди, т.е. «Опубликовать» точно не нажимали.
        for attempt in range(1, 4):
            try:
                _publish(page, j, kind, path, text, topic, photo, bg)
                return
            except Exception as e:
                if not path.exists() or attempt == 3 or j.get('dry') or isinstance(e, DryRun):
                    raise
                log(f"сбой {kind} (попытка {attempt}): {str(e).splitlines()[0][:120]} — закрываю окно, обновляю страницу, пробую ещё раз")
                try: _discard(page)
                except Exception: pass
                try: page.reload(wait_until='domcontentloaded')
                except Exception: pass
                time.sleep(random.uniform(90, 180))
    finally:
        _window(page, 'minimized')

def _publish(page, j, kind, path, text, topic, photo, bg):
    warm_up(page)
    page.goto('https://www.facebook.com/me', wait_until='domcontentloaded')
    pause(5, 9)
    human_click(page, page.get_by_text('Что у вас нового?').first)
    # у Facebook два слоя с именем «Создание публикации», нужен тот, где есть поле текста
    dlg = page.locator('[role="dialog"]').filter(has=page.locator('[role="textbox"]')).last
    dlg.wait_for(timeout=60000)
    pause(2, 4)
    att = dlg.get_by_role('button', name='Удалить вложение из публикации')
    if att.count():
        human_click(page, att.first)
    human_click(page, dlg.get_by_role('textbox').first)
    human_type(page, text)
    pause(2, 4)
    if kind == 'short':
        bg = _set_background(page, dlg)
    elif photo:
        inp = dlg.locator('input[type=file]')
        if not inp.count():
            human_click(page, dlg.get_by_role('button', name='Фото/видео').first)
            inp = dlg.locator('input[type=file]')
        inp.first.set_input_files(str(photo))
        pause(6, 10)
    else:
        log('длинный пост без фото: в «Посты!\\Фото» пусто')
    pause(2, 4)
    human_click(page, dlg.get_by_role('button', name='Далее', exact=True).first)
    pause(3, 5)

    human_click(page, page.get_by_text('Поделиться в группах', exact=True).last)
    pause(3, 5)
    available = _load_picker(page)
    if j.get('dry'):                         # проверка без публикации: только посмотреть, что видно
        reg = _jload(GROUPS, {})
        log(f"ПРОВЕРКА без публикации: групп в окне {len(available)}, из них в реестре {sum(1 for n in set(available) if n in reg)}, фон: {bg}")
        _discard(page)
        raise DryRun()
    groups = choose_groups(available, topic, j['day'])
    picked = []
    for n in groups:
        r = page.evaluate(JS_ROWS, n)
        if not r:
            log(f'группа не нашлась в окне: {n}'); continue
        pause(0.5, 1.5)
        r = page.evaluate(JS_ROWS, n)
        if not r['checked']:
            x = r['x'] + r['w'] * random.uniform(0.3, 0.7)
            y = r['y'] + r['h'] * random.uniform(0.35, 0.65)
            page.mouse.move(x, y, steps=random.randint(10, 18))
            pause(0.2, 0.6)
            page.mouse.click(x, y, delay=random.randint(60, 150))
            pause(0.8, 2.0)
        if page.evaluate(JS_ROWS, n)['checked']:
            picked.append(n)
        else:
            log(f'не отметилась группа: {n}')
    human_click(page, page.get_by_role('button', name='Готово', exact=True).last)
    pause(2, 4)
    human_click(page, page.get_by_role('button', name='Опубликовать', exact=True).last)
    # сразу убираем текст из очереди, чтобы при любом сбое дальше он не ушёл второй раз
    title = text.split('\n')[0]
    stamp = f'{datetime.datetime.now():%Y-%m-%d %H%M}'
    shutil.move(str(path), str(DONE / f'{stamp} {path.name}'))
    if photo:
        USED_PHOTO.mkdir(exist_ok=True)
        shutil.move(str(photo), str(USED_PHOTO / photo.name))
    _record(picked, j['day'], kind, title)
    pause(15, 25)
    extra = f' | фон: {bg}' if kind == 'short' else (f' | фото: {photo.name}' if photo else '')
    log(f"ТЕКСТ {kind} {topic} «{title[:50]}»{extra} → лента + {len(picked)} групп: {'; '.join(picked)}")
    _verify(page, title)

def _verify(page, title):
    key = title.strip()[:25]
    for _ in range(3):
        page.goto('https://www.facebook.com/me', wait_until='domcontentloaded')
        pause(8, 12)
        if key in page.inner_text('body'):
            return
        pause(20, 40)
    raise RuntimeError('пост опубликован, но в ленте профиля его не видно — проверить вручную (повторно НЕ публикую)')
