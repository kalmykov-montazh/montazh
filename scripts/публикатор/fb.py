# Facebook, личный профиль: отложенный Reels (видео + обложка + текст + время)
import datetime, re
from common import pause, read_pack, human_click, human_type, warm_up, log

MONTHS = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']

def publish(page, j, folder):
    video = _find_video(folder)
    cover = folder / 'обложка.jpg'
    text = j.get('text') or read_pack(folder)
    warm_up(page)
    page.goto('https://www.facebook.com/reels/create', wait_until='domcontentloaded')
    pause(5, 9)
    _upload_video(page, video)
    page.get_by_text('можно публиковать').first.wait_for(timeout=20 * 60 * 1000)
    pause(4, 8)
    for _ in range(2):
        human_click(page, page.get_by_role('button', name='Далее').last)
        pause(3, 6)
    if cover.exists() and j.get('cover', True):
        try:
            _set_cover(page, cover)
        except Exception as e:
            log(f"обложка не поставилась ({folder.name}): {str(e).splitlines()[0][:150]}")
            try: page.screenshot(path=str(folder.parent / '_задания' / f'обложка {folder.name}.png'))
            except Exception: pass
            if not _close_cover_dialog(page):
                for _ in range(2):
                    c = page.get_by_text('Отмена', exact=True)
                    if c.count(): human_click(page, c.last); pause(2, 3)
                    if not _cover_open(page): break
    _type_text(page, text)
    human_click(page, page.get_by_text('Настройки планирования', exact=True).first)
    _set_date(page, j['date'])
    j['time_set'] = _set_time(page, j['time'])
    _debug(page, f"перед планированием {folder.name[:30]}")
    human_click(page, page.get_by_role('button', name='Запланировать на будущее').last)
    pause(2, 4)
    human_click(page, page.get_by_role('button', name='Запланировать', exact=True).last)
    pause(15, 25)
    _debug(page, f"после планирования {folder.name[:30]}")
    _verify(page, text.split('\n')[0][:40], j['time_set'])

def _upload_video(page, video):
    """Видео в окно «Создание видео Reels». Сначала прямо в поле файла (надёжно),
    если его нет — через клик по «Добавить видео»."""
    inp = page.locator('[role="dialog"] input[type="file"]')
    if not inp.count():
        inp = page.locator('input[type="file"][accept*="video"]')
    if not inp.count():
        inp = page.locator('input[type="file"]')
    if inp.count():
        inp.first.set_input_files(str(video))
        pause(1, 3)
        return
    for target in (page.get_by_text('Добавить видео', exact=True).first,
                   page.get_by_text('или перетащить сюда').first):
        try:
            with page.expect_file_chooser(timeout=20000) as fc:
                human_click(page, target)
            fc.value.set_files(str(video)); pause(1, 3); return
        except Exception:
            pause(2, 4)
    raise RuntimeError('не получилось загрузить видео в окно Reels')

def _text_box(page):
    """Поле описания именно в окне создания ролика (не комментарий фонового рилса)."""
    box = page.locator('[role="dialog"] [contenteditable="true"][role="textbox"]')
    if not box.count():
        raise RuntimeError('не вижу поле описания в окне Reels')
    return box.last

def _type_text(page, text):
    key = text.strip().split('\n')[0][:20]
    for attempt in range(2):
        if _cover_open(page):                      # окно миниатюры перекрывает поле — сначала закрыть
            _close_cover_dialog(page)
        box = _text_box(page)
        human_click(page, box)
        pause(0.5, 1)
        if attempt and box.inner_text().strip():   # стираем только внутри поля описания
            box.press('Control+A'); box.press('Delete'); pause(1, 2)
        human_type(page, text)
        pause(3, 6)
        if key in _text_box(page).inner_text():
            return
        log(f"текст не встал в поле описания, попытка {attempt + 1}")
    _debug(page, 'текст')
    raise RuntimeError('текст не встал в поле описания — ролик не ставлю')

def _find_video(folder):
    # готовый ролик — .mp4 с «!!!» в начале имени; .mp4 без «!!!» — сырой, его не трогаем
    ready = sorted(f for f in folder.glob('*.mp4') if f.name.startswith('!!!'))
    if ready:
        return ready[0]
    if (folder / 'видео.mp4').exists():
        return folder / 'видео.mp4'
    raise RuntimeError(f'в папке {folder.name} нет готового ролика (.mp4 с «!!!» в начале)')

def _set_cover(page, cover):
    human_click(page, page.get_by_text('Редактировать', exact=True).first)
    pause(2, 4)
    # кнопка «Загрузить» (а не надпись «Загрузить свою миниатюру»)
    btn = page.get_by_role('button', name='Загрузить', exact=True)
    if not btn.count():
        btn = page.get_by_text('Загрузить', exact=True)
    with page.expect_file_chooser(timeout=15000) as fc:
        human_click(page, btn.last)
    fc.value.set_files(str(cover))
    pause(6, 10)
    if not _close_cover_dialog(page):
        raise RuntimeError('окно миниатюры не закрылось после «Сохранить»')

def _cover_open(page):
    t = page.get_by_text('Редактирование миниатюры', exact=True)
    try:
        return t.count() > 0 and t.first.is_visible()
    except Exception:
        return False

def _close_cover_dialog(page):
    """Жмёт «Сохранить» именно в окне «Редактирование миниатюры» и ждёт, пока оно закроется."""
    for _ in range(4):
        if not _cover_open(page):
            return True
        dlg = page.locator('[role="dialog"]').filter(has_text='Редактирование миниатюры').last
        b = dlg.get_by_text('Сохранить', exact=True) if dlg.count() else page.get_by_text('Сохранить', exact=True)
        if not b.count():
            b = page.get_by_role('button', name='Сохранить')
        try:
            human_click(page, b.last)
        except Exception:
            pass
        pause(3, 6)
    return not _cover_open(page)

def _set_date(page, date):
    d = datetime.date.fromisoformat(date)
    if d == datetime.date.today():
        return
    human_click(page, page.get_by_text('Дата', exact=True).first)
    pause(1, 2)
    month = MONTHS[d.month-1]
    labels = [f"{d.day} {month} {d.year}", f"{d.day} {month}"]
    for _ in range(3):
        for label in labels:
            cell = page.locator(f'[aria-label*="{label}"]')
            if cell.count():
                human_click(page, cell.first); pause(1, 2); return
        nxt = page.locator('[aria-label*="ледующий месяц"]')
        if nxt.count():
            human_click(page, nxt.first); pause(1, 2)
    _debug(page, 'дата')
    cell = page.locator('[role="gridcell"], td').filter(has_text=re.compile(rf'^\s*{d.day}\s*$'))
    if cell.count():
        human_click(page, cell.first); pause(1, 2); return
    raise RuntimeError(f'не смог выбрать дату {d.day} {month} в календаре Facebook (скрин «дата» в «шаги»)')

def _set_time(page, hhmm):
    """Ставит нужное время; если Facebook его уже не даёт — ближайшее доступное после него.
    Сначала пробует выпадающий список, если его нет — вводит время в поле вручную."""
    def options():
        o = page.get_by_role('option')
        if not o.count():
            o = page.get_by_text(re.compile(r'^\d{1,2}:\d{2}$'))
        t = [x.strip() for x in o.all_inner_texts()]
        return o, [x for x in t if re.fullmatch(r'\d{1,2}:\d{2}', x)]
    # 1) клик по полю «Время» (по самому полю, не только по надписи)
    field = page.locator('[role="combobox"], input').filter(has_text=re.compile(r'\d{1,2}:\d{2}'))
    targets = [page.get_by_text('Время', exact=True).first]
    inp = page.locator('input[value*=":"]')
    if inp.count():
        targets.append(inp.last)
    opts, times = None, []
    for t in targets:
        try:
            human_click(page, t)
        except Exception:
            continue
        pause(1, 2)
        opts, times = options()
        if times:
            break
    if times:
        key = lambda t: tuple(map(int, t.split(':')))
        later = [t for t in times if key(t) >= key(hhmm)]
        pick = min(later, key=key) if later else min(times, key=key)
        if pick != hhmm:
            log(f"время {hhmm} уже недоступно, ставлю ближайшее: {pick}")
        human_click(page, opts.nth(times.index(pick)) if len(times) == opts.count() else page.get_by_text(pick, exact=True).last)
        return pick
    # 2) списка нет — вводим время в поле
    _debug(page, 'время')
    if not inp.count():
        raise RuntimeError('не вижу ни списка, ни поля времени в «Настройках планирования»')
    human_click(page, inp.last)
    page.keyboard.press('Control+A'); pause(0.3, 0.8)
    human_type(page, hhmm)
    pause(1, 2)
    page.keyboard.press('Enter'); pause(1, 2)
    got = inp.last.input_value().strip()
    if got != hhmm:
        log(f"время: ввёл {hhmm}, в поле {got}")
        if not re.fullmatch(r'\d{1,2}:\d{2}', got):
            raise RuntimeError(f'время не встало (в поле «{got}»)')
    return got

def _debug(page, name):
    """Скрин и разметка окна для разбора, в «_задания\\шаги»."""
    try:
        from common import QUEUE
        d = QUEUE / 'шаги'; d.mkdir(exist_ok=True)
        stamp = datetime.datetime.now().strftime('%m%d_%H%M')
        page.screenshot(path=str(d / f'{stamp} {name}.png'))
        dlg = page.locator('[role="dialog"]').last
        html = dlg.inner_html() if dlg.count() else page.content()
        (d / f'{stamp} {name}.html').write_text(html[:300000], encoding='utf-8')
    except Exception:
        pass

def _verify(page, first_line, hhmm=None):
    url = 'https://www.facebook.com/professional_dashboard/content/content_library/?filter=SCHEDULED'
    for _ in range(3):                            # после «Запланировать» Facebook сам перебрасывает страницу
        try:
            page.goto(url, wait_until='domcontentloaded'); break
        except Exception:
            pause(10, 15)
    key = first_line.strip()[:25]
    for attempt in range(4):                      # Facebook показывает новый ролик не сразу
        pause(8, 12)
        body = page.inner_text('body')
        if key in body:
            if hhmm:
                near = body[body.find(key): body.find(key) + 400]
                if f'в {hhmm}' not in near and f'в {hhmm.lstrip("0")}' not in near:
                    m = re.search(r'в (\d{1,2}:\d{2})', near)
                    raise RuntimeError(f'ролик запланирован, но не на {hhmm}, а на {m.group(1) if m else "?"} — поправить время вручную')
            return
        pause(30, 60)
        page.reload(wait_until='domcontentloaded')
    raise RuntimeError('не нашёл ролик в «Запланированных» — проверить вручную')
