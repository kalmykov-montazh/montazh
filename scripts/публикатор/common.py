# Общее для всех соцсетей: пути, журнал и «человеческое» поведение (паузы, мышь, печать по буквам)
import os, time, random, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent                      # G:\Мой диск\Монтаж!
PUB = ROOT / 'К публикации!'
QUEUE = PUB / '_задания'
LOG = QUEUE / 'журнал.txt'
PROFILE = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'publisher-chrome'

TG_CHAT = 8341379322                           # Евгений в @kalmykov_assistant_bot
TG_KEYS = [HERE / 'telegram_ключ.txt', HERE / 'telegram_ключ.txt.txt']  # токен бота (кладёт Евгений сам)

def tg(text):
    """Сообщение Евгению в Telegram. Без ключа или без сети — молча пропускаем."""
    try:
        import json, urllib.request
        token = next(k for k in TG_KEYS if k.exists()).read_text(encoding='utf-8-sig').strip()
        body = json.dumps({"chat_id": TG_CHAT, "text": text[:3500]}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage",
                                     data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20)
    except Exception:
        pass

def log(msg):
    QUEUE.mkdir(parents=True, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M} {msg}\n")
    if msg.startswith(('ОШИБКА', 'ПРОПУСК', 'СБОЙ', 'повтор не поставлен')):
        tg("Робот-публикатор: " + msg)

def pause(a=2.0, b=5.0):
    time.sleep(random.uniform(a, b))

def read_pack(folder: Path):
    p = folder / 'упаковка.txt'
    return p.read_text(encoding='utf-8-sig').rstrip() if p.exists() else ''

def human_click(page, loc):
    """Подвести мышь к элементу кривой траекторией, чуть подождать, кликнуть не в центр."""
    loc.scroll_into_view_if_needed()
    pause(0.4, 1.2)
    box = loc.bounding_box()
    if box:
        x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
        y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
        page.mouse.move(x + random.uniform(-80, 80), y + random.uniform(-60, 60), steps=random.randint(8, 15))
        pause(0.2, 0.6)
        page.mouse.move(x, y, steps=random.randint(10, 20))
        pause(0.2, 0.7)
        page.mouse.click(x, y, delay=random.randint(60, 160))
    else:
        loc.click(delay=random.randint(60, 160))
    pause(1.5, 3.5)

def human_type(page, text):
    """Печать по буквам с разной скоростью, иногда короткие «задумки». Перенос строки — Shift+Enter."""
    for ch in text:
        if ch == '\n':
            page.keyboard.press('Shift+Enter')
            time.sleep(random.uniform(0.3, 0.9))
            continue
        if ord(ch) > 0xFFFF or ch in '⠀':          # эмодзи и невидимый пробел печатаем вставкой
            page.keyboard.insert_text(ch)
        else:
            page.keyboard.type(ch)
        time.sleep(random.uniform(0.05, 0.18))
        if ch in ' .,!?' and random.random() < 0.12:
            time.sleep(random.uniform(0.6, 1.8))

def warm_up(page):
    """Перед публикацией — как человек: открыть ленту и немного полистать."""
    page.goto('https://www.facebook.com/', wait_until='domcontentloaded')
    pause(5, 9)
    for _ in range(random.randint(2, 5)):
        page.mouse.wheel(0, random.randint(300, 900))
        pause(2, 6)
    page.mouse.wheel(0, -2000)
    pause(2, 4)
