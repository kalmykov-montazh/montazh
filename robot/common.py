# Общее для всех соцсетей: пути, журнал и «человеческое» поведение (паузы, мышь, печать по буквам)
import os, time, random, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent                      # G:\Мой диск\Монтаж!
PUB = ROOT / 'Брокер' / 'К публикации'
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

# Строки, за которые Meta режет охват и ставит ограничения (решение Евгения 25.10.2026):
# любые упоминания «ссылка в шапке», «полное видео на YouTube», «монтаж в приложении» и сами ссылки.
import re as _re
_BAN = _re.compile(r'(шапк[еиу]\s+профил|полное\s+видео|монтаж\s+делал|ссылк\w*[^\n]{0,30}\s+в\s+(шапке|описании|профиле)|https?://|www\.|t\.me/|youtu\.be)', _re.I)

def clean_pack(text):
    """Убирает из упаковки строки со ссылками и отсылками «ссылка в шапке / полное видео на YouTube»."""
    src = (text or '').splitlines()
    lines = src[:1] + [l for l in src[1:] if not _BAN.search(l)]   # название (1-я строка) не трогаем
    out = []
    for l in lines:                      # не оставлять две строки-разделителя ⠀ подряд
        if l.strip() == '⠀' and out and out[-1].strip() == '⠀':
            continue
        out.append(l)
    return '\n'.join(out).strip()

def read_pack(folder: Path, raw=False):
    """raw=True — упаковка как есть (только для YouTube), иначе без строк про ссылки."""
    p = folder / 'упаковка.txt'
    if not p.exists():
        return ''
    t = p.read_text(encoding='utf-8-sig').rstrip()
    return t if raw else clean_pack(t)

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

def warm_up(page, short=False, profile=False):
    """Перед публикацией — как человек: открыть ленту и немного полистать.
    07.11.2026: short — пара прокруток; иначе 1–3 минуты; profile — ещё заглянуть в свой профиль."""
    page.goto('https://www.facebook.com/', wait_until='domcontentloaded')
    pause(3, 6) if short else pause(5, 9)
    n = random.randint(1, 3) if short else random.randint(5, 14)
    for _ in range(n):
        try:
            page.mouse.move(random.randint(300, 1100), random.randint(200, 750), steps=random.randint(6, 18))
        except Exception:
            pass
        page.mouse.wheel(0, random.randint(250, 900))
        pause(1.5, 5) if short else pause(3, 12)
    if profile:
        try:
            page.goto('https://www.facebook.com/me', wait_until='domcontentloaded')
            pause(5, 10)
            for _ in range(random.randint(1, 4)):
                page.mouse.wheel(0, random.randint(300, 800)); pause(2, 6)
        except Exception:
            pass
    page.mouse.wheel(0, -2000)
    pause(2, 4)
