# Публикатор для 5 соцсетей. Берёт задания из «К публикации!\_задания\*.json».
# Задание: {"platform":"fb","folder":"08 Час вместо одного звонка","date":"2026-10-15","time":"09:00"}
# Готово -> .done, ошибка -> .error + .png (скрин) + .error.txt. Всё пишется в журнал.txt.
# Запуск: Планировщик Windows каждые 10 минут (publish.vbs). «py publish.py login» — вход в соцсети.
import sys, json, time, random, traceback, os
from common import QUEUE, PUB, PROFILE, log, pause
import fb
import planner
import textposts

PLATFORMS = {'fb': fb.publish}   # текстовые посты ('fbtext') — textposts.publish   # дальше добавим: 'ig', 'th', 'tt', 'yt'
MAX_PER_RUN = 3
LOCK = QUEUE / '_идёт.lock'

def launch(pw):
    return pw.chromium.launch_persistent_context(
        str(PROFILE), channel='chrome', headless=False, locale='ru-RU',
        viewport={'width': 1400, 'height': 900}, args=['--start-minimized'])

def run_jobs():
    QUEUE.mkdir(parents=True, exist_ok=True)
    try: planner.cleanup()
    except Exception as e: log(f"очистка: ошибка {str(e)[:150]}")
    try: planner.plan()
    except Exception as e: log(f"раскладка: ошибка {str(e)[:150]}")
    try: textposts.plan()
    except Exception as e: log(f"раскладка текстов: ошибка {str(e)[:150]}")
    jobs = []
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
        elif j.get('date', '') > time.strftime('%Y-%m-%d'):
            continue                                       # ролик на завтра: ставим только после полуночи, в его день (FB плохо выбирает дату)
        jobs.append(f)
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
                            import datetime
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
