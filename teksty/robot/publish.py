# Публикатор для 5 соцсетей. Берёт задания из «К публикации!\_задания\*.json».
# Задание: {"platform":"fb","folder":"08 Час вместо одного звонка","date":"2026-10-15","time":"09:00"}
# Готово -> .done, ошибка -> .error + .png (скрин) + .error.txt. Всё пишется в журнал.txt.
# Запуск: Планировщик Windows каждые 10 минут (publish.vbs). «py publish.py login» — вход в соцсети.
import sys, json, time, random, traceback, os, datetime
from pathlib import Path
from common import QUEUE, PUB, PROFILE, log, pause
import fb
import planner
import textposts
import blotato
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Крипто', 'скрипты'))
import crypto_yt                                       # шортсы «Всё о крипте» (25.10.2026)
import fb_playlists                                    # новые рилсы FB — сами в плейлист по теме (25.10.2026)
import reel_groups                                     # лучший рилс дня — в тематические группы (07.11.2026)
import claude_guard                                    # Claude закрыт (после своего обновления) — поднять (04.11.2026)

PLATFORMS = {'fb': fb.publish}   # текстовые посты ('fbtext') — textposts.publish   # дальше добавим: 'ig', 'th', 'tt', 'yt'
MAX_PER_RUN = 3
FB_AHEAD = 4   # на сколько дней вперёд ставить ролики в Facebook (29.10.2026: было «только в день выхода»; растим до 7)
LOCK = QUEUE / '_идёт.lock'
LIVE_EARLY = 15   # 07.11.2026: было 12; публикация теперь с «человеческими» паузами, бывает до 15 мин; «сразу»-ролик берём за 12 мин: загрузка и обработка видео в FB ~5–10 мин, выходит около своей минуты

def launch(pw):
    # 07.11.2026: без метки «браузером управляет программа» (navigator.webdriver, полоса автотеста)
    return pw.chromium.launch_persistent_context(
        str(PROFILE), channel='chrome', headless=False, locale='ru-RU', chromium_sandbox=True,
        no_viewport=True,          # 10.11.2026: без подмены размера страницы (размер окна = размер страницы, как у человека)
        args=['--start-minimized', '--window-size=1400,950', '--disable-blink-features=AutomationControlled'],
        ignore_default_args=['--enable-automation'])

PULSE = QUEUE / '_пульс.txt'
PULSE_END = QUEUE / '_пульс_конец.txt'   # 06.11.2026: время КОНЦА запуска (пишется в finally)
CYCLE = QUEUE / '_цикл.txt'

def _read_ts(path):
    try:
        return float(path.read_text(encoding='utf-8').split()[0])
    except Exception:
        return None

def pulse():
    """Отметка каждого запуска. Перерыв больше 40 минут — в журнал и в Telegram (25.10.2026:
    в ночь перевода часов Планировщик Windows пропустил целый час, ролики лежали без раскладки).
    06.11.2026: перерыв считаем от КОНЦА прошлого запуска, а не от начала. Часы робота (цикл.pyw) ждут,
    пока publish.py закончит, поэтому длинная раскладка роликов (00:04–00:40) давала ложный «ПРОПУСК 40 мин».
    Конец не записан (прошлый запуск упал или его убили часы через 2 часа) — смотрим «_цикл.txt»:
    там «запуск publish.py» и с прошлого старта меньше 2 часов — молчим."""
    now = time.time()
    last = _read_ts(PULSE)                       # начало прошлого запуска
    end = _read_ts(PULSE_END)                    # конец прошлого запуска
    try: PULSE.write_text(f"{now} {time.strftime('%Y-%m-%d %H:%M')}", encoding='utf-8')
    except Exception: pass
    if not last:
        return
    if end and end >= last - 5:                  # прошлый запуск дописал конец
        ref = end
    else:                                        # конец не записан: упал, убит или старый publish.py
        try: cyc = CYCLE.read_text(encoding='utf-8')
        except Exception: cyc = ''
        if 'запуск publish.py' in cyc and now - last < 2 * 3600 + 15 * 60:
            return                               # часы живы и ждали долгий запуск — это не пропуск
        ref = last
    if now - ref > 40 * 60:
        log(f"ПРОПУСК запусков: робот не запускался {int((now - ref) // 60)} мин "
            f"(с {time.strftime('%d.%m %H:%M', time.localtime(ref))}"
            f"{', конец прошлого запуска' if ref is end else ''}) — проверь компьютер и Планировщик")

def pulse_end():
    try: PULSE_END.write_text(f"{time.time()} {time.strftime('%Y-%m-%d %H:%M')}", encoding='utf-8')
    except Exception: pass

# 13.11.2026: «перенос к удалению». Список «Брокер\Посты\_служебное\_к_удалению.txt» — по одному полному пути
# в строке. Каждый файл ПЕРЕНОСИМ (не удаляем) в «Монтаж!\к удалению»; имя занято — добавляем дату и время.
# Перенесённые и ненайденные строки из списка убираем. Насовсем ничего не удаляется — папку чистит Евгений.
from common import ROOT as _ROOT
import shutil
TRASH_LIST = _ROOT / 'Брокер' / 'Посты' / '_служебное' / '_к_удалению.txt'
TRASH_DIR = _ROOT / 'к удалению'

def move_to_trash():
    if not TRASH_LIST.exists():
        return
    try:
        lines = TRASH_LIST.read_text(encoding='utf-8-sig').splitlines()
    except Exception as e:
        log(f"к удалению: не прочитал список ({str(e)[:120]})"); return
    paths = [l.strip().strip('"').strip() for l in lines if l.strip()]
    if not paths:
        return
    TRASH_DIR.mkdir(parents=True, exist_ok=True)
    base = _ROOT.parent                                  # G:\Мой диск — за его пределы ничего не трогаем
    moved, missing, keep = 0, [], []
    for s in paths:
        p = Path(s)
        try:
            rp = p.resolve()
        except Exception:
            rp = p
        if not (str(rp).lower().startswith(str(base).lower() + os.sep)) or rp == TRASH_DIR or TRASH_DIR in rp.parents \
                or rp == TRASH_LIST.resolve():
            missing.append(f"{s} (не трогаю: вне Моего диска или служебный)"); continue
        if not p.exists():
            missing.append(s); continue
        dest = TRASH_DIR / p.name
        if dest.exists():
            dest = TRASH_DIR / f"{p.stem} {time.strftime('%Y-%m-%d %H-%M-%S')}{p.suffix}"
            n = 2
            while dest.exists():
                dest = TRASH_DIR / f"{p.stem} {time.strftime('%Y-%m-%d %H-%M-%S')} ({n}){p.suffix}"; n += 1
        try:
            shutil.move(str(p), str(dest)); moved += 1
        except Exception as e:
            keep.append(s)                               # файл занят — оставляю в списке, попробую в следующий запуск
            log(f"к удалению: не смог перенести {p.name} ({str(e)[:100]}) — попробую позже")
    try:
        TRASH_LIST.write_text(''.join(k + '\n' for k in keep), encoding='utf-8')
    except Exception as e:
        log(f"к удалению: не смог обновить список ({str(e)[:120]})")
    log(f"к удалению: перенёс {moved}, не нашёл {len(missing)}" + (': ' + '; '.join(missing) if missing else ''))

# 13.11.2026: «входящие» от задач Claude по расписанию. Задачи не видят «Монтаж!», но умеют создавать файлы
# в Google Диске коннектором — кладут задание в «Мой диск\_задания_робота_от_Claude». Берём только лонги FB
# ("platform":"fb","kind":"long") и переносим в _задания. Остальное — .отклонено, ничего не публикуем.
INBOX = _ROOT.parent / '_задания_робота_от_Claude'

def take_inbox():
    if not INBOX.exists():
        return
    for f in sorted(INBOX.glob('*.json')):
        try:
            j = json.loads(f.read_text(encoding='utf-8-sig'))
            ok = j.get('platform') == 'fb' and j.get('kind') == 'long' and j.get('folder_abs') and j.get('date') and j.get('time')
        except Exception:
            ok = False
        if not ok:
            try: f.rename(f.with_suffix('.отклонено'))
            except Exception: pass
            log(f"входящие Claude: {f.name} отклонено — не задание лонга FB")
            continue
        dest = QUEUE / f.name
        if dest.exists():
            dest = QUEUE / f"{f.stem}_{time.strftime('%H%M%S')}.json"
        try:
            shutil.move(str(f), str(dest)); log(f"входящие Claude: взял {f.name} (лонг FB {j['date']} {j['time']})")
        except Exception as e:
            log(f"входящие Claude: не смог перенести {f.name} ({str(e)[:100]})")

def run_jobs():
    QUEUE.mkdir(parents=True, exist_ok=True)
    try: pulse()
    except Exception: pass
    try: take_inbox()                                   # 13.11.2026: задания лонгов от задач Claude через Google Диск
    except Exception as e: log(f"входящие Claude: ошибка {str(e)[:150]}")
    try: move_to_trash()                                # 13.11.2026: перенос к удалению
    except Exception as e: log(f"к удалению: ошибка {str(e)[:150]}")
    try: claude_guard.run()
    except Exception as e: log(f"сторож Claude: ошибка {str(e)[:150]}")
    try: planner.cleanup()
    except Exception as e: log(f"очистка: ошибка {str(e)[:150]}")
    try: planner.migrate_0811()                         # разово: всё с 08.11 — сразу, по новым окнам (07.11.2026)
    except Exception as e: log(f"ОШИБКА перехода 0811: {str(e)[:200]}")
    try: planner.plan()
    except Exception as e: log(f"раскладка: ошибка {str(e)[:150]}")
    try: textposts.plan()
    except Exception as e: log(f"раскладка текстов: ошибка {str(e)[:150]}")
    try: blotato.run()                                  # Instagram, Threads, TikTok, YouTube — через Blotato
    except Exception as e: log(f"blotato: ошибка {str(e)[:150]}")
    try: crypto_yt.run()                                # YouTube «Всё о крипте» — 1 шортс в день в 18:00
    except Exception as e: log(f"крипто: ошибка {str(e)[:150]}")
    jobs, live, live_soon = [], [], []
    late_n = 0                                         # 13.11.2026: счётчик опоздавших новостей для сдвига
    for f in sorted(f for f in QUEUE.glob('*.json') if not f.name.startswith('_')):
        try: j = json.loads(f.read_text(encoding='utf-8-sig'))
        except Exception: continue
        if j.get('platform') == 'fbtext':
            d = textposts.due(j)
            if d is None:
                continue                                   # ещё не время
            if d is False:                                 # компьютер был выключен — слот пропускаем
                # 13.11.2026 (решение Евгения, вариант А: ни один пост не терять): новость, которую проспали,
                # не выбрасываем, а ставим ещё раз через 20+ минут (несколько опоздавших — с шагом 70 минут), один раз
                # и только до 23:30 того же дня. Повтор — обычное задание, дальше всё как всегда
                try:
                    _now = datetime.datetime.now()
                    if j.get('kind') in textposts.NEWS_KINDS and not j.get('late_requeued') \
                            and textposts._next_text(j['kind']) and j.get('day') == f'{_now:%Y-%m-%d}':
                        _at = _now + datetime.timedelta(minutes=20 + 70 * late_n + random.randint(0, 10))
                        if _at.hour < 23 or (_at.hour == 23 and _at.minute <= 30):
                            late_n += 1
                            r = dict(j, at=f'{_at:%Y-%m-%d %H:%M}', late_requeued=True)
                            (QUEUE / f"{_at:%Y-%m-%d_%H%M}_fbtext_{j['kind']}_опоздание.json").write_text(
                                json.dumps(r, ensure_ascii=False), encoding='utf-8')
                            f.rename(f.with_suffix('.done'))
                            log(f"ПОВТОР текст {j['kind']} {j['at']} — опоздали, поставил на {_at:%H:%M}")
                            continue
                except Exception as e3:
                    log(f"повтор опоздавшего не поставлен: {str(e3)[:120]}")
                f.rename(f.with_suffix('.done'))
                textposts.mark(j, 'пропущен (опоздание)')
                log(f"ПРОПУСК текст {j['kind']} {j['at']} — сильно опоздали")
                continue
            if j.get('kind') == 'short' and j.get('day', '') >= textposts.NEWS_FROM.isoformat():   # 10.11.2026: коротыши с 11.11 не публикуем
                f.rename(f.with_suffix('.done'))
                textposts.mark(j, 'отменён (коротыши с 11.11 не выходят)')
                log(f"текст short {j['at']} не публикую: с 11.11 вместо коротыша утренняя новость")
                continue
            if j.get('kind') == 'photo' and j.get('day', '') >= textposts.NEWS4_FROM.isoformat():   # 11.11.2026: фото-посты с 12.11 не публикуем
                f.rename(f.with_suffix('.done'))
                textposts.mark(j, 'отменён (фото-посты с 12.11 не выходят)')
                log(f"текст photo {j['at']} не публикую: с 12.11 вместо фото-поста дневная новость")
                continue
            if j.get('kind') in textposts.NEWS_KINDS and not textposts._next_text(j['kind']):   # 11.11.2026: пустая папка — ПРОПУСК
                f.rename(f.with_suffix('.done'))
                textposts.mark(j, 'пропущен (нет текста)')
                log(f"ПРОПУСК текст {j['kind']} {j['at']} — в «{textposts.FOLDER_NAMES.get(j['kind'])}» пусто")
                continue
        elif j.get('mode') == 'live':                      # тест 04.11.2026: публикуем сразу, в свою минуту
            at = datetime.datetime.fromisoformat(f"{j['date']} {j['time'].zfill(5)}")
            if datetime.datetime.now() < at - datetime.timedelta(minutes=LIVE_EARLY):
                live_soon.append(at)
                continue                                   # ещё рано
            # 07.11.2026: старая отложка этого ролика ещё не удалена из FB — сначала удаление, иначе будет дубль
            dele = _load_delete()
            if j.get('folder') in dele:
                old = datetime.datetime.fromisoformat(dele[j['folder']]['old'])
                if datetime.datetime.now() >= old:         # отложка уже вышла сама — живую не публикуем
                    was = dele.pop(j['folder'])['old']
                    f.rename(f.with_suffix('.done'))
                    planner.mark(j, 'вышел отложкой', was[11:])
                    _save_delete(dele)
                    log(f"FB: живую не публикую — старая отложка уже вышла сама в {was} (дубля нет) — {j['folder']}")
                    continue
                continue                                   # ждём удаления отложки
            live.append(f)
            continue
        elif j.get('date', '') > (datetime.date.today() + datetime.timedelta(days=FB_AHEAD)).isoformat() \
                and not j.get('ahead'):                    # "ahead": true — разовая постановка заранее (тест 29.10.2026)
            continue                                       # ролик дальше FB_AHEAD дней — ждёт
        jobs.append(f)
    # «сразу»-ролик подошёл — в этом запуске только он (не ждёт, пока робот ставит отложку на другие дни);
    # «сразу»-ролик через час-полтора — берём не больше одного другого задания, чтобы не опоздать
    if live:
        jobs = live
    elif any(a - datetime.datetime.now() < datetime.timedelta(minutes=80) for a in live_soon):
        jobs = jobs[:1]
    dele = _load_delete()
    try: reel_due = reel_groups.due()
    except Exception: reel_due = False
    if live:                                       # живой ролик важнее — группы в следующий запуск
        reel_due = False
    if not jobs and not dele and not reel_due:
        return
    if LOCK.exists() and time.time() - LOCK.stat().st_mtime < 3 * 3600:
        return
    LOCK.write_text(str(os.getpid()))
    from common import sync_playwright_engine
    sync_playwright, engine = sync_playwright_engine()
    try:
        with sync_playwright() as pw:
            try:
                ctx = launch(pw)
            except Exception as e:
                if engine != 'patchright':
                    raise
                log(f'движок: Patchright не запустил Chrome ({str(e).splitlines()[0][:150]}) — запасной Playwright')
                from common import HERE as _RH
                (_RH / '_без_patchright.txt').write_text('авто: не запустился ' + time.strftime('%Y-%m-%d %H:%M'), encoding='utf-8')
                raise
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.set_default_timeout(60000)
            if dele:                                      # 07.11.2026: сначала убрать старые отложки FB
                _delete_scheduled(page, dele)
            batch = jobs[:MAX_PER_RUN]
            for i, job in enumerate(batch):
                for _ in range(3):                    # Facebook после прошлого ролика ещё сам перебрасывает страницу
                    try:
                        page.goto('about:blank'); break
                    except Exception:
                        time.sleep(15)
                try:
                    j = json.loads(job.read_text(encoding='utf-8-sig'))
                    if j['platform'] == 'fbtext':
                        try:
                            textposts.publish(page, j)
                        except textposts.DryRun:
                            job.rename(job.with_suffix('.done')); continue
                        job.rename(job.with_suffix('.done'))
                        textposts.mark(j, 'готово')
                        log(f"ГОТОВО текст {j['kind']} {j['at']}")
                    elif j.get('kind') in ('arenda', 'long'):   # 10.11.2026: рилс-объявление аренды; 13.11.2026: лонг в ленту FB
                        # "long": видео и обложка лежат в своей папке лонга — "folder_abs" (полный путь), "video", "cover_file", "text"
                        what = 'лонг' if j.get('kind') == 'long' else 'рилс аренды'
                        fld = Path(j['folder_abs']) if j.get('folder_abs') else PUB / j['folder']
                        if j.get('cover_url') and j.get('cover_file') and not (fld / j['cover_file']).exists():
                            try:                               # 13.11.2026: обложка с YouTube — робот скачивает сам
                                import urllib.request
                                cp = fld / j['cover_file']; cp.parent.mkdir(parents=True, exist_ok=True)
                                req = urllib.request.Request(j['cover_url'], headers={'User-Agent': 'Mozilla/5.0'})
                                cp.write_bytes(urllib.request.urlopen(req, timeout=30).read())
                                log(f"обложка скачана: {cp.name} ({cp.stat().st_size // 1024} КБ)")
                            except Exception as e:
                                log(f"обложка не скачалась ({str(e)[:100]}) — ставлю без неё")
                        try:
                            fb.publish(page, j, fld)
                        except fb.DryRun:
                            job.rename(job.with_suffix('.done')); log(f"ПРОВЕРКА {what} закончена — {j['folder']}"); continue
                        job.rename(job.with_suffix('.done'))   # в _план.json не пишем: Blotato его второй раз не выложит
                        log(f"ГОТОВО {what} {j['date']} {j.get('time_set', j['time'])}, групп {len(j.get('groups_done', []))} — {j['folder']}")
                    else:
                        PLATFORMS[j['platform']](page, j, PUB / j['folder'])
                        job.rename(job.with_suffix('.done'))
                        planner.mark(j, 'готово', j.get('time_set', j['time']))
                        if j['platform'] == 'fb':
                            fb_playlists.remember(PUB / j['folder'])
                        log(f"ГОТОВО {j['platform']} {j['date']} {j.get('time_set', j['time'])} — {j['folder']}")
                except Exception as e:
                    try: page.screenshot(path=str(job.with_suffix('.png')))
                    except Exception: pass
                    job.with_suffix('.error.txt').write_text(traceback.format_exc(), encoding='utf-8')
                    job.rename(job.with_suffix('.error'))
                    try:
                        if j.get('platform') == 'fbtext': textposts.mark(j, 'ошибка')
                        else: planner.mark(j, 'ошибка')
                    except Exception: pass
                    log(f"ОШИБКА {job.name}: {str(e).splitlines()[0][:200]}")
                    # текст не ушёл (остался в очереди) — сам ставлю повтор через 20–30 минут, до 2 раз
                    try:
                        if j.get('platform') == 'fbtext' and not j.get('dry') and j.get('retry', 0) < 2 \
                                and textposts._next_text(j['kind']) and 'нет текста' not in str(e) \
                                and 'опубликован' not in str(e) and '130 знаков' not in str(e):
                            at = datetime.datetime.now() + datetime.timedelta(minutes=random.randint(20, 30))
                            r = dict(j, at=f'{at:%Y-%m-%d %H:%M}', retry=j.get('retry', 0) + 1)
                            (QUEUE / f"{at:%Y-%m-%d_%H%M}_fbtext_{j['kind']}_повтор{r['retry']}.json").write_text(
                                json.dumps(r, ensure_ascii=False), encoding='utf-8')
                            log(f"ПОВТОР текст {j['kind']} поставлен на {at:%H:%M} (повтор {r['retry']} из 2)")
                    except Exception as e2:
                        log(f"повтор не поставлен: {str(e2)[:120]}")
                if i < len(batch) - 1:
                    time.sleep(random.uniform(180, 480))     # 3–8 минут между публикациями
            if reel_due:
                try:
                    if batch: time.sleep(random.uniform(120, 300))
                    textposts._window(page, 'normal')     # 10.11.2026: не делиться из свёрнутого (скрытого) окна
                    try: reel_groups.run(page)
                    finally: textposts._window(page, 'minimized')
                except Exception as e:
                    log(f"РИЛС В ГРУППЫ: сбой {str(e).splitlines()[0][:150]}")
            ctx.close()
    finally:
        LOCK.unlink(missing_ok=True)

def _load_delete():
    try: return json.loads(planner.DELETE_FB.read_text(encoding='utf-8'))
    except Exception: return {}

def _save_delete(d):
    planner.DELETE_FB.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')

def _delete_scheduled(page, dele):
    """Переход 07.11.2026: удаляем из «Запланированных» FB отложки роликов, которые теперь выходят сразу.
    3 неудачи подряд — сообщение в Telegram (удалить вручную); живая публикация этого ролика ждёт,
    а если отложка всё-таки вышла сама — живую не делаем (см. run_jobs)."""
    for name in list(dele):
        e = dele[name]
        if datetime.datetime.now() >= datetime.datetime.fromisoformat(e['old']):
            continue                                       # время отложки уже прошло — она вышла
        try:
            ok = fb.delete_scheduled(page, e['key'])
        except Exception as ex:
            ok = False
            log(f"FB удаление отложки: сбой {str(ex).splitlines()[0][:150]} — {name}")
        if ok:
            dele.pop(name)
            log(f"FB отложка удалена (теперь выйдет сразу) — {name}")
        else:
            e['tries'] = e.get('tries', 0) + 1
            if e['tries'] == 3:
                log(f"ОШИБКА: не могу удалить отложку FB «{e['key']}» (стоит на {e['old']}) — удалить вручную: "
                    f"Библиотека контента → Запланированные → «…» → «Удалить публикацию». Иначе выйдет отложкой, дубля не будет")
        _save_delete(dele)
        pause(4, 9)

def login():
    from common import sync_playwright_engine
    sync_playwright, _ = sync_playwright_engine()
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(str(PROFILE), channel='chrome', headless=False, locale='ru-RU', chromium_sandbox=True, no_viewport=True)
        urls = ['https://www.facebook.com/', 'https://www.instagram.com/', 'https://www.threads.net/',
                'https://www.tiktok.com/login', 'https://studio.youtube.com/']
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(urls[0])
        for u in urls[1:]:
            ctx.new_page().goto(u)
        try:
            while ctx.pages:
                time.sleep(2)
        except Exception:
            pass

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'login':
        login()
    else:
        try:
            try:
                run_jobs()
            except Exception as e:
                log(f"СБОЙ запуска: {str(e).splitlines()[0][:200] if str(e) else type(e).__name__}")
                (QUEUE / '_сбой.txt').write_text(traceback.format_exc(), encoding='utf-8')
            try:
                fb_playlists.maybe_run()                     # раз в 3 часа: вышедшие рилсы без плейлиста — в плейлист
            except Exception as e:
                log(f"плейлист FB: ошибка {str(e)[:150]}")
        finally:
            pulse_end()                                      # 06.11.2026: конец запуска — даже при ошибке
