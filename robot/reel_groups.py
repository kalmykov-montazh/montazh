# Лучший рилс дня — в тематические группы (решение Евгения 07.11.2026).
# Раз в день (окно 19:00–22:00, своё время каждый день) робот смотрит последние рилсы профиля,
# берёт тот, что набрал больше всех за сутки (вчерашние, не сегодняшние), и расшаривает его
# в REEL_GROUPS групп: только испанские и эмиграционные (как для новостей), проверенные первыми.
# Группа берётся не чаще раза в 3 дня — общий учёт с текстовыми постами (реестр групп textposts).
# Риэлторские/барахолки («не для постов»), юмор, чужие города — не берём.
# DRY = True — проверка: доходит до последней кнопки в 1 группе, делает скрин в «шаги», ничего не публикует.
# Разовый запуск проверки сейчас: файл «_задания\_рилсы_в_группы_проверка» (робот удалит сам).
import json, re, random, datetime, time
from common import QUEUE, log, pause, human_click, human_type
import textposts

DRY = True
REEL_GROUPS = 4
PROFILE_REELS = 'https://www.facebook.com/kalmykov.rieltor.valencia/reels/'
STATE = QUEUE / '_рилсы_в_группы.json'
FORCE = QUEUE / '_рилсы_в_группы_проверка'
STATUS_ORDER = {'проверенная': 0, 'средняя': 1, 'тест': 2}

def _load():
    try: return json.loads(STATE.read_text(encoding='utf-8'))
    except Exception: return {'done': {}}

def _save(s):
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding='utf-8')

def _start_time(day):
    m = random.Random(f"reelgroups-{day}").randint(19 * 60, 21 * 60 + 50)
    return datetime.datetime.combine(day, datetime.time(m // 60, m % 60))

def due():
    if FORCE.exists():
        return True
    now = datetime.datetime.now()
    s = _load()
    return s.get('last_day') != now.date().isoformat() and now >= _start_time(now.date())

def _views(t):
    t = (t or '').replace('\xa0', ' ').strip().lower()
    m = re.search(r'([\d]+(?:[.,]\d+)?)\s*(тыс|млн)?', t)
    if not m:
        return None
    v = float(m.group(1).replace(',', '.'))
    return int(v * (1000 if m.group(2) == 'тыс' else 1_000_000 if m.group(2) == 'млн' else 1))

JS_TILES = r"""() => {
  const out = [], seen = new Set();
  for (const a of document.querySelectorAll('a[href*="/reel/"]')) {
    const m = a.href.match(/\/reel\/(\d+)/); if (!m || seen.has(m[1])) continue;
    seen.add(m[1]); out.push({id: m[1], text: (a.innerText || '').trim()});
  }
  return out;
}"""

def _pick_reel(page, s):
    page.goto(PROFILE_REELS, wait_until='domcontentloaded'); pause(8, 12)
    page.mouse.wheel(0, random.randint(300, 600)); pause(3, 5)
    tiles = page.evaluate(JS_TILES)
    # 0–2 — сегодняшние (вышли меньше суток назад), смотрим следующие 6: вчерашние
    cands = []
    for t in tiles[3:9]:
        v = _views(t['text'])
        if v is not None and t['id'] not in s.get('done', {}):
            cands.append((v, t['id']))
    log(f"РИЛС В ГРУППЫ: кандидаты {', '.join(f'{i}:{v}' for v, i in cands) or 'нет'}")
    return max(cands) if cands else None

def _groups(day):
    reg = textposts._jload(textposts.GROUPS, {})
    names = [n for n, g in reg.items() if g.get('статус') in STATUS_ORDER]
    picked = textposts.choose_groups(names, 'новости', day)   # только испанские/эмиграционные, с перерывом 3 дня
    picked.sort(key=lambda n: STATUS_ORDER.get(reg[n].get('статус'), 9))
    return picked[:REEL_GROUPS]

def _share_one(page, reel_id, group, dry):
    page.goto(f'https://www.facebook.com/reel/{reel_id}', wait_until='domcontentloaded'); pause(6, 10)
    # 07.11: первая кнопка «Поделиться» на странице скрытая — берём только видимую
    btn = page.locator('[aria-label="Поделиться"][role="button"]:visible')
    if not btn.count():
        btn = page.locator('[aria-label*="оделиться"]:visible')
    if not btn.count():
        textposts_debug(page, 'рилс нет кнопки поделиться')
        raise RuntimeError('не вижу кнопку «Поделиться» у рилса')
    human_click(page, btn.last); pause(2, 4)
    grp = page.locator('[role="dialog"]').last.get_by_text('Группа', exact=True)
    if not grp.count():
        textposts_debug(page, 'рилс нет пункта группа')
        raise RuntimeError('в окне «Поделиться» нет пункта «Группа»')
    human_click(page, grp.last); pause(2, 4)
    box = page.locator('[role="dialog"] input:visible')
    if not box.count():
        textposts_debug(page, 'рилс нет поиска групп')
        raise RuntimeError('нет поля поиска групп')
    human_click(page, box.first)
    human_type(page, group[:30]); pause(3, 5)
    row = page.locator('[role="dialog"]').last.get_by_text(group[:40], exact=False)
    if not row.count():
        textposts_debug(page, f'рилс группа не найдена {group[:20]}')
        page.keyboard.press('Escape'); pause(1, 2); page.keyboard.press('Escape')
        raise RuntimeError(f'группа не нашлась в поиске: {group}')
    human_click(page, row.first); pause(3, 5)
    textposts_debug(page, f'рилс в группу перед кнопкой {group[:20]}')
    if dry:
        page.keyboard.press('Escape'); pause(1, 2); page.keyboard.press('Escape')
        return False
    dlg = page.locator('[role="dialog"]').last
    for name in ('Опубликовать', 'Поделиться', 'Отправить'):
        b = dlg.get_by_role('button', name=name, exact=True)
        if b.count():
            human_click(page, b.last); pause(6, 10)
            return True
    raise RuntimeError('не вижу кнопку «Опубликовать» в окне группы — не опубликовано')

def textposts_debug(page, name):
    try:
        import fb
        fb._debug(page, name)
    except Exception:
        pass

def run(page):
    forced = FORCE.exists()
    s = _load()
    day = datetime.date.today().isoformat()
    s['last_day'] = day
    _save(s)
    if forced:
        FORCE.unlink(missing_ok=True)
    best = _pick_reel(page, s)
    if not best:
        log("РИЛС В ГРУППЫ: подходящего рилса нет — сегодня пропуск")
        return
    views, reel_id = best
    groups = _groups(day)
    if not groups:
        log("РИЛС В ГРУППЫ: свободных групп нет (у всех перерыв) — пропуск")
        return
    dry = DRY or forced
    if dry:
        groups = groups[:1]
    done, reached = [], []
    for g in groups:
        try:
            if _share_one(page, reel_id, g, dry):
                done.append(g)
            elif dry:
                reached.append(g)
        except Exception as e:
            log(f"РИЛС В ГРУППЫ: {g} — {str(e).splitlines()[0][:150]}")
        pause(60, 200) if not dry else pause(3, 6)
    if dry:
        if reached:
            log(f"ПРОВЕРКА рилс в группы (без публикации): рилс {reel_id} ({views} просм.) → дошёл до кнопки в «{reached[0]}», скрин в «шаги»")
        else:
            log(f"ПРОВЕРКА рилс в группы: НЕ дошёл до кнопки (рилс {reel_id}), скрин в «шаги»")
        return
    textposts._record(done, day, 'reel', f'рилс {reel_id}')
    s.setdefault('done', {})[reel_id] = {'день': day, 'просмотры': views, 'группы': done}
    _save(s)
    log(f"РИЛС В ГРУППЫ: {reel_id} ({views} просм.) → {len(done)} групп: {'; '.join(done)}")
