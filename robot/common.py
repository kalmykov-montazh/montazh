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

# 18.11.2026: СЛУЖЕБНЫЙ БЛОК УПАКОВКИ. 17.11 «Звонят из банка и просят код» ушёл во все сети с хвостом
# «Обложка:» + 5 вариантов заголовков «(топ)», «— стоит на обложке». Всё от строки «Обложка:» (и похожих
# заголовков служебных блоков) до конца — служебное, в подписи не уходит НИКОГДА, ни в одну сеть, YouTube тоже.
# Плюс отдельные служебные строки и снятые призывы («подберу варианты» — подбором Евгений не занимается, 09.11).
_SERVICE_HEAD = _re.compile(r'^\s*(обложк[аи]|варианты\s+(обложк|заголов)\w*|заголовк[иа]\s+(для\s+)?обложк\w*|плейлист|для\s+claude|служебн\w*)\s*[:—-]', _re.I)
_SERVICE_LINE = _re.compile(r'\((топ|top)\)|стоит\s+на\s+обложке|на\s+обложк[еу]\s*:|подбер[уё]\w*\s+вариант|подбираю\s+вариант|!{3}', _re.I)
# 18.11.2026: метка папки «!!! БИЗ» в названии (18.10 ушла в подпись) — убираем из первой строки
_BANG_HEAD = _re.compile(r'^\s*!{2,}\s*(?:[А-ЯЁA-Z]{2,8}\b\s*)?')

def strip_service(text):
    """Убирает служебный блок упаковки (от «Обложка:» до конца) и служебные строки. Для всех сетей."""
    src = (text or '').splitlines()
    out = []
    for i, l in enumerate(src):
        if i and _SERVICE_HEAD.match(l):
            break
        if i and _SERVICE_LINE.search(l):
            continue
        if not i:
            l = _BANG_HEAD.sub('', l)
        out.append(l)
    while out and out[-1].strip() in ('', '\u2800'):
        out.pop()
    return '\n'.join(out)

def caption_problems(text):
    """Последняя проверка перед публикацией: служебные слова в подписи. Пустой список — можно."""
    bad = []
    for l in (text or '').splitlines():
        if _SERVICE_HEAD.match(l) or _SERVICE_LINE.search(l):
            bad.append(l.strip()[:60])
    return bad

def clean_pack(text):
    """Убирает из упаковки служебный блок и строки со ссылками и отсылками «ссылка в шапке / полное видео на YouTube»."""
    src = strip_service(text).splitlines()
    lines = src[:1] + [l for l in src[1:] if not _BAN.search(l)]   # название (1-я строка) не трогаем
    out = []
    for l in lines:                      # не оставлять две строки-разделителя ⠀ подряд
        if l.strip() == '⠀' and out and out[-1].strip() == '⠀':
            continue
        out.append(l)
    return '\n'.join(out).strip()

def read_pack(folder: Path, raw=False):
    """raw=True — упаковка со ссылками (только для YouTube), но без служебного блока; иначе ещё и без строк про ссылки."""
    p = folder / 'упаковка.txt'
    if not p.exists():
        return ''
    t = p.read_text(encoding='utf-8-sig').rstrip()
    t = strip_service(t).strip() if raw else clean_pack(t)
    return ensure_search(t, folder)

# 18.11.2026 (решение Евгения, ОБЯЗАТЕЛЬНО): ПЕРВАЯ СТРОКА ОПИСАНИЯ — ПОИСКОВАЯ ФРАЗА, как её набирают люди
# («штраф за мусор в Валенсии», «вернуть товар в Испании»). Поиск в TikTok упал до 2,6% просмотров.
# Если Claude при упаковке фразу поставил — не трогаем. Нет — робот ставит сам: по словам названия,
# потом по «плейлист.txt», потом «жизнь в Испании». Во все сети (и YouTube). Название (1-я строка) не меняется.
_SEARCH_HAS = _re.compile(r'\bв\s+(испании|валенсии|аликанте|мадриде|барселоне)\b', _re.I)
_SEARCH_MAP = [
    (r'мусор', 'штраф за мусор в Валенсии'),
    (r'штраф', 'штраф в Испании'),
    (r'(украинск\w*\s+прав|обмен\w*\s+прав|поменять\s+прав|водительск)', 'поменять украинские права в Испании'),
    (r'растамож', 'растаможка авто в Испании'),
    (r'(украинск\w*\s+номер|машин|авто\b|dgt)', 'машина в Испании'),
    (r'\b(nie|tie)\b', 'NIE и TIE в Испании'),
    (r'(арраиго|гражданств|пмж)', 'ВНЖ и гражданство в Испании'),
    (r'(внж|временн\w*\s+защит|продлен\w*\s+защит)', 'ВНЖ в Испании'),
    (r'(пропис|падрон)', 'прописка в Испании'),
    (r'ипотек', 'ипотека в Испании'),
    (r'(купить|покупк|продать|продаж)\w*.{0,20}(квартир|жиль|дом)', 'купить квартиру в Испании'),
    (r'окупас', 'окупасы в Испании'),
    (r'(аренд|снять\s+квартир|залог|жилец|хозяин\w*\s+квартир|арендатор)', 'аренда квартиры в Испании'),
    (r'пенси', 'пенсия в Испании'),
    (r'(\bimv\b|пособи|доплат|выплат)', 'пособия в Испании'),
    (r'(налог|резидент|декларац|hacienda)', 'налоги в Испании'),
    (r'(мошен|развод\w*\s+по\s+телефон)', 'мошенники в Испании'),
    (r'(банк|счёт\s+в|счет\s+в|наличн|bizum)', 'банк в Испании'),
    (r'(автономо|autónomo)', 'автономо в Испании'),
    (r'(работ|зарплат|увол|безработ)', 'работа в Испании'),
    (r'(медиц|врач|sip|аптек|рецепт|больниц)', 'медицина в Испании'),
    (r'(школ|детский\s+сад)', 'школа в Испании'),
    (r'(вернуть\s+товар|возврат\w*\s+(товар|покуп))', 'вернуть товар в Испании'),
    (r'гаранти', 'гарантия в Испании'),
    (r'(\bчек\b|чека\b)', 'чек в Испании'),
    (r'(задат|предоплат)', 'задаток в Испании'),
    (r'(ресторан|\bбар\b|кафе)', 'ресторан в Испании'),
    (r'(супермаркет|mercadona|меркадон|ценник|lidl|consum)', 'цены в магазинах Испании'),
    (r'(поезд|электричк|renfe|проездн|автобус)', 'транспорт в Испании'),
    (r'(переезд|переехать|эмиграц)', 'переезд в Испанию'),
    (r'валенси', 'жизнь в Валенсии'),
]
_SEARCH_PL = {
    'ВНЖ': 'ВНЖ в Испании', 'ВНЖАРР': 'ВНЖ и гражданство в Испании', 'АРЕНДА': 'аренда квартиры в Испании',
    'СОБСТВ': 'сдать квартиру в Испании', 'ИНВЕСТ': 'купить квартиру в Испании', 'ОКУПАС': 'окупасы в Испании',
    'ПОКУПКА': 'купить квартиру в Испании', 'СЕРГЕЙ': 'сдать квартиру в Испании', 'ПЕНСИЯ': 'пенсия в Испании',
    'IMV': 'пособия в Испании', 'АВТО': 'машина в Испании', 'ШТРАФЫ': 'штраф в Испании', 'ДЕНЬГИ': 'налоги в Испании',
    'БАНКИ': 'банк в Испании', 'АВТОНОМО': 'автономо в Испании', 'РАБОТА': 'работа в Испании',
    'ЖИЗНЬ': 'жизнь в Испании', 'ВАЛЕНСИЯ': 'жизнь в Валенсии', 'ШКОЛА': 'школа в Испании',
    'ПЕРЕЕЗД': 'переезд в Испанию', 'АДАПТ': 'жизнь в Испании', 'ГОРОД': 'где жить в Испании',
    'ПУТЬ': 'переезд в Испанию', 'ЯЗЫК': 'испанский язык', 'ПУТЕШ': 'дешёвые отели', 'ОБЪЕКТЫ': 'квартиры в Валенсии',
}

def search_phrase(title, folder=None):
    """Поисковая фраза по названию ролика, иначе по плейлисту, иначе общая."""
    low = (title or '').lower()
    for pat, ph in _SEARCH_MAP:
        if _re.search(pat, low):
            return ph
    try:
        key = (Path(folder) / 'плейлист.txt').read_text(encoding='utf-8-sig').strip().split()[0].upper()
        if key in _SEARCH_PL:
            return _SEARCH_PL[key]
    except Exception:
        pass
    return 'жизнь в Испании'

def ensure_search(text, folder=None):
    """Первая строка описания (после названия и ⠀) — поисковая фраза. Есть — не трогаем, нет — вставляем."""
    lines = (text or '').splitlines()
    if len(lines) < 2:
        return text
    i = 1
    while i < len(lines) and lines[i].strip() in ('', '⠀'):
        i += 1
    if i >= len(lines):
        return text
    first = lines[i].strip()
    if first.startswith('#') or (_SEARCH_HAS.search(first) and len(first) <= 70):
        return text
    ph = search_phrase(lines[0], folder)
    return '\n'.join(lines[:i] + [ph] + lines[i:])

# 18.11.2026: ПОДПИСЬ FACEBOOK КОРОТКАЯ. Facebook советует 100–200 знаков (максимум 400) и не больше
# 3 хэштегов. 17.11 лонг «Одна страна, два климата» вышел с подписью ~1300 знаков и таймкодами.
# Таймкоды — только YouTube. Для Facebook: без таймкодов и служебного, длинное — до первого абзаца.
FB_MAX = 400
FB_TAGS = 3
_TIMECODE = _re.compile(r'^\s*\(?\d{1,2}:\d{2}(:\d{2})?\)?\s')

def fb_short(text):
    lines = [l for l in strip_service(text).splitlines() if not _TIMECODE.match(l)]
    tags = []
    body = []
    for l in lines:
        w = l.split()
        if w and all(x.startswith('#') for x in w):
            tags += [x for x in w if x.lower() not in [t.lower() for t in tags]]
        else:
            body.append(l.rstrip())
    while body and body[-1].strip() in ('', '\u2800'):
        body.pop()
    t = _re.sub(r'\n{3,}', '\n\n', '\n'.join(body)).strip()
    tail = ' '.join(tags[:FB_TAGS])
    sep = '\n\u2800\n' if '\u2800' in t else '\n\n'
    room = FB_MAX - len(tail) - len(sep)
    if len(t) > room:
        paras = [p.strip() for p in _re.split(r'\n\s*\n|\n\u2800\n', t) if p.strip().strip('\u2800')]
        keep = ''
        for p in paras:
            nxt = (keep + '\n\n' + p) if keep else p
            if len(nxt) <= room:
                keep = nxt; continue
            left = room - len(keep) - (2 if keep else 0)
            if left > 80:                              # не влез абзац — берём из него целые предложения
                cut = p[:left]
                m = max(cut.rfind('. '), cut.rfind('? '), cut.rfind('! '), cut.rfind('.\n'))
                part = cut[:m + 1] if m > 40 else ''
                if part:
                    keep = (keep + '\n\n' + part) if keep else part
            break
        if not keep:
            keep = t[:room - 1].rsplit(' ', 1)[0] + '…'
        t = keep
        sep = '\n\n'
    return (t + (sep + tail if tail else '')).strip()

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

# ЗАЩИТА ОТ ПУСТОЙ УПАКОВКИ (10.11.2026, решение Евгения): 9.11 «73 12 Мусор мимо контейнера» ушёл в Blotato
# с пустым описанием — в папке была только заглушка «упаковка — сцены.txt». Теперь без нормальной
# «упаковка.txt» (меньше 3 строк с текстом) ролик не ставим ни в Facebook, ни в Blotato.
PACK_MIN_LINES = 3
PACK_WARN = QUEUE / '_нет_упаковки.json'        # {папка: дата последней тревоги} — тревога раз в сутки

def pack_problem(folder: Path):
    """None — упаковка в порядке, иначе причина словами."""
    p = folder / 'упаковка.txt'
    if not p.exists():
        alt = [f.name for f in folder.glob('упаковка*.txt')]
        return 'нет «упаковка.txt»' + (f" (есть только {', '.join('«' + a + '»' for a in alt)})" if alt else '')
    try: lines = [l for l in p.read_text(encoding='utf-8-sig').splitlines() if l.strip().strip('\u2800').strip()]
    except Exception as e: return f'«упаковка.txt» не читается: {str(e)[:80]}'
    if len(lines) < PACK_MIN_LINES:
        return f'в «упаковка.txt» {len(lines)} строк(и) с текстом, нужно хотя бы {PACK_MIN_LINES}'
    return None

def pack_guard(folder: Path):
    """True — можно ставить. False — нельзя; пишу в журнал и в Telegram (не чаще раза в сутки на папку)."""
    why = pack_problem(folder)
    import json
    try: warned = json.loads(PACK_WARN.read_text(encoding='utf-8'))
    except Exception: warned = {}
    if not why:
        if folder.name in warned:
            warned.pop(folder.name)
            try: PACK_WARN.write_text(json.dumps(warned, ensure_ascii=False, indent=1), encoding='utf-8')
            except Exception: pass
        return True
    today = datetime.date.today().isoformat()
    if warned.get(folder.name) != today:
        warned[folder.name] = today
        try: PACK_WARN.write_text(json.dumps(warned, ensure_ascii=False, indent=1), encoding='utf-8')
        except Exception: pass
        log(f"ОШИБКА нет упаковки — {folder.name}: {why}. Ролик не ставлю; появится нормальная «упаковка.txt» — встанет сам")  # ОШИБКА → log сам шлёт в Telegram
    return False


def sync_playwright_engine():
    """11.11.2026: движок браузера для робота — Patchright (та же Playwright, но без следов управления
    браузером, которые видит страница). Нет пакета — ставит сам (pip, не чаще раза в сутки).
    Не встал или лежит файл «_без_patchright.txt» рядом с роботом — обычная Playwright, как раньше."""
    if not (HERE / '_без_patchright.txt').exists():
        try:
            from patchright.sync_api import sync_playwright
            return sync_playwright, 'patchright'
        except ImportError:
            mark = HERE / '_patchright_установка.txt'
            if not mark.exists() or time.time() - mark.stat().st_mtime > 24 * 3600:
                import subprocess, sys
                mark.write_text(time.strftime('%Y-%m-%d %H:%M'), encoding='utf-8')
                log('движок: ставлю Patchright (pip install patchright)')
                try:
                    r = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'patchright'],
                                       timeout=600, capture_output=True, text=True)
                    if r.returncode:
                        log(f'движок: Patchright не встал ({(r.stderr or r.stdout)[-200:].strip()})')
                except Exception as e:
                    log(f'движок: Patchright не встал ({e})')
                try:
                    from patchright.sync_api import sync_playwright
                    log('движок: Patchright установлен')
                    return sync_playwright, 'patchright'
                except ImportError:
                    pass
    from playwright.sync_api import sync_playwright
    return sync_playwright, 'playwright'


# ---------- 14.11.2026 (решение Евгения): В ТЕКСТЕ FACEBOOK ССЫЛОК НЕТ — ссылка первым комментарием ----------
# Особенно объявления (аренда, продажа: пост, карусель, рилс): строку с Telegram-каналом заменяем на
# «Больше объектов в моём Телеграм-канале, ссылка в первом комментарии», остальные ссылки вырезаем.
# Что вырезали — в «_задания/_первый_комментарий.json»: оттуда комментарий ставит задача (Claude в браузере).
import re as _re
FB_TG_LINE = 'Больше объектов в моём Телеграм-канале, ссылка в первом комментарии'
FB_TG_COMMENT = 'Больше объектов в Валенсии в моём Телеграм-канале: https://t.me/kalmykov_realty'
_URL = _re.compile(r'(https?://\S+|www\.\S+|t\.me/\S+|wa\.me/\S+)', _re.I)


def fb_clean(text):
    """Возвращает (текст без ссылок, [вырезанные ссылки])."""
    if not text:
        return text, []
    out, cut = [], []
    for line in text.split('\n'):
        links = _URL.findall(line)
        if not links:
            out.append(line); continue
        cut += links
        if any('t.me/kalmykov_realty' in l.lower() for l in links):
            if FB_TG_LINE not in out:
                out.append(FB_TG_LINE)
            continue
        rest = _URL.sub('', line).rstrip(' :—-–👉📲📱').rstrip()
        if rest.strip():
            out.append(rest)
    t = '\n'.join(out)
    t = _re.sub(r'\n{3,}', '\n\n', t).strip()
    return t, cut


def fb_note_comment(key, links, where):
    """Запомнить: под публикацией (первая строка key) нужен первый комментарий с этими ссылками."""
    try:
        import json
        p = QUEUE / '_первый_комментарий.json'
        d = json.loads(p.read_text(encoding='utf-8')) if p.exists() else []
        txt = FB_TG_COMMENT if any('kalmykov_realty' in l for l in links) else ''
        other = [l for l in links if 'kalmykov_realty' not in l]
        if other:
            txt = (txt + '\n' if txt else '') + '\n'.join(other)
        d.append({'когда': f"{datetime.datetime.now():%Y-%m-%d %H:%M}", 'где': where,
                  'первая строка': (key or '')[:80], 'комментарий': txt, 'поставлен': False})
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
        log(f"ССЫЛКИ из текста FB убраны ({where}) — нужен первый комментарий: {(key or '')[:40]}")
    except Exception as e:
        log(f"fb_note_comment: {e}")
