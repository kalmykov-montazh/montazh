# Часы робота-публикатора (25.10.2026). Планировщик Windows пропускал запуски каждые 10 минут,
# поэтому теперь отсчёт ведёт этот скрипт: каждые 10 минут (в ЧЧ:х4) запускает publish.py и ждёт его.
# Планировщик только следит, чтобы этот цикл был жив (при входе в Windows и каждые 10 минут).
# Второй экземпляр цикла сам закрывается (именованный мьютекс), двойных запусков publish.py нет.
import ctypes, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MUTEX = 'Local\\KalmykovPublikatorLoop'

h = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX)
if ctypes.windll.kernel32.GetLastError() == 183:      # ERROR_ALREADY_EXISTS — цикл уже работает
    sys.exit(0)

QUEUE = HERE.parent.parent / 'Брокер' / 'К публикации' / '_задания'
HB = QUEUE / '_цикл.txt'

def note(s):
    try: HB.write_text(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {s}", encoding='utf-8')
    except Exception: pass

def next_slot():
    now = time.time()
    t = time.localtime(now)
    add = (4 - t.tm_min % 10) % 10 or 10                # следующие ЧЧ:х4 (если сейчас х4 — через 10 минут)
    return now - t.tm_sec + add * 60

while True:
    note('запуск publish.py')
    try:
        p = subprocess.Popen([sys.executable, str(HERE / 'publish.py')], cwd=str(HERE))
        try: p.wait(timeout=2 * 3600)
        except subprocess.TimeoutExpired:
            p.kill(); note('publish.py шёл дольше 2 часов — остановлен')
    except Exception as e:
        note(f'не смог запустить publish.py: {e}')
    target = next_slot()
    note(f"жду до {time.strftime('%H:%M', time.localtime(target))}")
    while time.time() < target:                          # короткими шагами — не сбивается после сна и перевода часов
        time.sleep(min(30, max(1, target - time.time())))
