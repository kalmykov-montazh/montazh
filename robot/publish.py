# Публикатор для 5 соцсетей. Берёт задания из «К публикации!\_задания\*.json».
# Задание: {"platform":"fb","folder":"08 Час вместо одного звонка","date":"2026-10-15","time":"09:00"}
# Готово -> .done, ошибка -> .error + .png (скрин) + .error.txt. Всё пишется в журнал.txt.
# Запуск: Планировщик Windows каждые 10 минут (publish.vbs). «py publish.py login» — вход в соцсети.
import sys, json, time, random, traceback, os, datetime
from common import QUEUE, PUB, PROFILE, log, pause
import fb
import planner
import textposts
import blotato
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Крипто', 'скрипты'))
import crypto_yt                                       # шортсы «Всё о крипте» (25.10.2026)
import fb_playlists                                    # новые рилсы FB — сами в плейлист по теме (25.10.2026)

PLATFORMS = {'fb': fb.publish}   # текстовые посты ('fbtext') — textposts.publish   # дальше добавим: 'ig', 'th', 'tt', 'yt'
MAX_PER_RUN = 3
FB_AHEAD = 4   # на сколько дней вперёд ставить ролики в Facebook (29.10.2026: было «только в день выхода»; растим до 7)
LOCK = QUEUE / '_идёт.lock'
LIVE_EARLY = 12   # «сразу»-ролик берём за 12 мин: загрузка и обработка видео в FB ~5–10 мин, выходит около своей минуты

def launch(pw):
    return pw.chromium.launch_persistent_context(
        str(PROFILE), channel='chrome', headless=False, locale='ru-RU',
        viewport={'width': 1400, 'height': 900}, args=['--start-minimized'])

PULSE = QUEUE / '_пульс.txt'

def pulse():
    """Отметка каждого запуска. Перерыв больше 40 минут — в журнал и в Telegram (25.10.2026:
    в ночь перевода часов Планировщик Windows пропустил целый час, ролики лежали без раскладки)."""
    now = time.time()
    try:
        last = float(PULSE.read_text(encoding='utf-8').split()[0])
    except Exception:
        last = None
    try: PULSE.write_text(f"{now} {time.strftime('%Y-%m-%d %H:%M')}", encoding='utf-8')
    except Exception: pass
    if last and now - last > 40 * 60:
        log(f"ПРОПУСК запусков: робот не запускался {int((now - last) // 60)} мин "
            f"(с {time.strftime('%d.%m %H:%M', time.localtime(last))}) — проверь компьютер и Планировщик")

def run_jobs():
    QUEUE.mkdir(parents=True, exist_ok=True)
    try: pulse()
    except Exception: pass
    try: planner.cleanup()
    except Exception as e: log(f"очистка: ошибка {str(e)[:150]}")
    try: planner.plan()
    except Exception as e: log(f"раскладка: ошибка {str(e)[:150]}")
    try: textposts.plan()
    except Exception as e: log(f"раскладка текстов: ошибка {str(e)[:150]}")
    try: blotato.run()                                  # Instagram, Threads, TikTok, YouTube — через Blotato
    except Exception as e: log(f"blotato: ошибка {str(e)[:150]}")
    try: crypto_yt.run()                                # YouTube «Всё о крипте» — 1 шортс в день в 18:00
    except Exception as e: log(f"крипто: ошибка {str(e)[:150]}")
    jobs, live, live_soon = [], [], []
    for f in sorted(f for f in QUEUE.glob('*.json') if not f.name.startswith('_')):
        try: j = json.loads(f.read_text(encoding='utf-8-sig'))
        except Exception: continue
        if j.get('platform') == 'fbtext':
            d = textposts.due(j)
            if d is None:
                continue                                   # ещё не время
            if d is False:                                 # компьютер был выключен — слот пропускаем
                f.rename(f.with_suffix('.done'))
                textposts.mark(j, 'пропущен (опоздание)')
                log(f"ПРОПУСК текст {j['kind']} {j['at']} — сильно опоздали")
                continue
        elif j.get('mode') == 'live':                      # тест 04.11.2026: публикуем сразу, в свою минуту
            at = datetime.datetime.fromisoformat(f"{j['date']} {j['time'].zfill(5)}")
            if datetime.datetime.now() < at - datetime.timedelta(minutes=LIVE_EARLY):
                live_soon.append(at)
                continue                                   # ещё рано
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
    if not jobs:
        return
    if LOCK.exists() and time.time() - LOCK.stat().st_mtime < 3 * 3600:
        return
    LOCK.write_text(str(os.getpid()))
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as pw:
            ctx = launch(pw)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.set_default_timeout(60000)
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
            ctx.close()
    finally:
        LOCK.unlink(missing_ok=True)

def login():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(str(PROFILE), channel='chrome', headless=False, locale='ru-RU')
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
            run_jobs()
        except Exception as e:
            log(f"СБОЙ запуска: {str(e).splitlines()[0][:200] if str(e) else type(e).__name__}")
            (QUEUE / '_сбой.txt').write_text(traceback.format_exc(), encoding='utf-8')
        try:
            fb_playlists.maybe_run()                         # раз в 3 часа: вышедшие рилсы без плейлиста — в плейлист
        except Exception as e:
            log(f"плейлист FB: ошибка {str(e)[:150]}")
