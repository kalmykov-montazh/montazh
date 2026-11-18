# Истории (сторис) в Facebook — делает сам робот (решение Евгения 18.11.2026: «истории на робота, чтобы не тратить лимит Claude»).
# После каждой вышедшей новости, сильного дневного поста и ночного длинного:
#   1) берёт только что вышедший текст из «Посты\Опубликовано» (шапка = первая строка),
#   2) подбирает фото города из «Посты\Фото» (то же «фото по смыслу», что и для постов; фото отдыхает 60 дней),
#   3) рисует картинку 1080×1920 (фото на весь кадр, метка рубрики, заголовок, «подробно у меня в профиле»),
#   4) ставит её в историю личного профиля и кладёт копию в «Посты\Сторис\Опубликованные».
# Плюс картинки, которые Claude положил вручную в «Посты\Сторис\Очередь» (раз в день, по одной за запуск).
# Журнал выхода — «_задания\_истории.json». Ошибка — строка «ОШИБКА история …» (уходит Евгению в Telegram).
import json, re, time, random, datetime, shutil
from pathlib import Path
from common import QUEUE, log, pause, human_click

import textposts as tp

STORIES = tp.POSTS / 'Сторис'
ST_QUEUE, ST_DONE = STORIES / 'Очередь', STORIES / 'Опубликованные'
ST_PHOTOS = STORIES / '_сторис_фото.json'      # {фото: дата} — фото в историях отдыхает 60 дней
STATE = QUEUE / '_истории.json'                # {ключ: "ГГГГ-ММ-ДД ЧЧ:ММ"} — что уже вышло
TMP = Path(__file__).resolve().parent / '_tmp_фото'
W, H = 1080, 1920
REST_DAYS = 60

FONTS_B = [r'C:\Windows\Fonts\segoeuib.ttf', r'C:\Windows\Fonts\arialbd.ttf',
           '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
FONTS_M = [r'C:\Windows\Fonts\segoeuisb.ttf', r'C:\Windows\Fonts\arial.ttf',
           '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']

LABELS = [  # метка рубрики по словам шапки и @фото-тема
    ('ИПОТЕКА', ('ипотек', 'euribor', 'евробор', 'банк')),
    ('АРЕНДА', ('аренд', 'съём', 'жилец', 'арендатор', 'залог', 'окупас')),
    ('ЖИЛЬЁ', ('жиль', 'квартир', 'недвижим')),
    ('ВНЖ', ('внж', 'nie', 'tie', 'миграц', 'легализац', 'гражданств')),
    ('УКРАИНЦЫ', ('украин', 'защит')),
    ('ТРАНСПОРТ', ('поезд', 'электрич', 'renfe', 'автобус', 'метро', 'забастов', 'дорог', 'машин', 'авто', 'бензин')),
    ('КОШЕЛЁК', ('цен', 'зарплат', 'пенси', 'налог', 'евро', '€', 'минималк', 'пособи', 'деньг', 'подорож')),
]
SUBS = ['Подробно — у меня в профиле', 'Все цифры и что делать — у меня в профиле',
        'Разобрал по полочкам — пост у меня в профиле']

def _j(path, default):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return default

def _jw(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')

def _font(cands, size):
    from PIL import ImageFont
    for f in cands:
        try: return ImageFont.truetype(f, size)
        except Exception: pass
    return ImageFont.load_default()

def _wrap(d, text, font, maxw):
    words, lines, cur = text.split(' '), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    lines.append(cur)
    # висячие короткие слова («и», «в», «за») не оставляем в конце строки
    for i in range(len(lines) - 1):
        parts = lines[i].split(' ')
        if len(parts) > 1 and len(parts[-1]) <= 2 and \
                d.textlength(parts[-1] + ' ' + lines[i + 1], font=font) <= maxw:
            lines[i] = ' '.join(parts[:-1]); lines[i + 1] = parts[-1] + ' ' + lines[i + 1]
    return lines

def draw(src, label, head, sub, out):
    from PIL import Image, ImageOps, ImageDraw
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((l, t, l + W, t + H))
    g = Image.new('L', (1, H))
    for y in range(H):
        a = 0
        if y > H * 0.38: a = int(min(235, (y - H * 0.38) / (H * 0.42) * 235))
        if y < 260: a = max(a, int((260 - y) / 260 * 150))
        g.putpixel((0, y), a)
    im = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), im, g.resize((W, H)))
    d = ImageDraw.Draw(im)
    size = 84
    while True:                                   # заголовок не больше 5 строк — иначе шрифт меньше
        fh = _font(FONTS_B, size); hl = _wrap(d, head, fh, W - 140)
        if len(hl) <= 5 or size <= 60: break
        size -= 6
    fl, fs = _font(FONTS_B, 40), _font(FONTS_M, 44)
    sl = _wrap(d, sub, fs, W - 140)
    lh = int(size * 1.19)
    y = H - 150 - len(sl) * 60 - 40 - len(hl) * lh - 100
    tw = d.textlength(label, font=fl)
    d.rounded_rectangle((70, y, 70 + tw + 48, y + 70), radius=35, fill=(232, 48, 48))
    d.text((94, y + 12), label, font=fl, fill='white'); y += 110
    for line in hl: d.text((70, y), line, font=fh, fill='white'); y += lh
    y += 30; d.rectangle((70, y, 190, y + 8), fill=(255, 196, 0)); y += 40
    for line in sl: d.text((70, y), line, font=fs, fill=(235, 235, 235)); y += 60
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=90)
    return out

def _clean_head(head):
    head = re.sub(r'^[^\wА-Яа-яЁё]+', '', head.strip())                  # мигалка и эмодзи в начале
    head = re.sub(r'^\d{1,2}\s+[а-я]+\s*:\s*', '', head, flags=re.I)        # «18 ноября: »
    head = re.sub(r'[\U0001F000-\U0001FFFF\u2600-\u27BF]', '', head).strip()
    head = head.rstrip('.').strip()
    return head[:1].upper() + head[1:] if head else head

def _label(meta, head, text):
    low = (meta.get('фото-тема', '') + ' ' + head + ' ' + text[:400]).lower()
    for lab, keys in LABELS:
        if any(k in low for k in keys): return lab
    return 'ИСПАНИЯ'

def _story_photo(meta, text):
    """Фото по смыслу (как у постов), но не то, что было в историях за 60 дней, и не из «использованные»."""
    used = _j(ST_PHOTOS, {})
    now = datetime.date.today()
    fresh = {k for k, v in used.items() if (now - datetime.date.fromisoformat(v)).days < REST_DAYS}
    tags = tp._photo_tags()
    wanted, _ = tp._wanted_tags(meta, text)
    pool = []
    for f in tp.PHOTO.iterdir():
        if not f.is_file() or f.suffix.lower() not in tp.PHOTO_EXT or f.name in fresh:
            continue
        t = set(tags.get(f.name, []))
        if not t or tp.SKIP_TAG in t or 'дети' in t or 'я' in t or (t & tp.SENSITIVE and not (tp.SENSITIVE & set(wanted))):
            continue
        pool.append((tp._score(wanted, t), random.random(), f))
    if not pool:
        return None
    pool.sort(reverse=True)
    best = pool[0][0]
    top = [p for p in pool if p[0] >= best - 0.01][:6]           # среди лучших — случайное, чтобы не одно и то же
    return random.choice(top)[2]

def _post(page, img):
    """Ставит картинку в историю личного профиля. True — вышла."""
    page.goto('https://www.facebook.com/stories/create', wait_until='domcontentloaded')
    pause(5, 8)
    if 'i_user' in str(page.context.cookies('https://www.facebook.com')):
        raise RuntimeError('Facebook открыт от Страницы, а не от личного профиля')
    inp = page.locator('input[type="file"][accept*="image"]').first
    inp.set_input_files(str(img))
    pause(6, 9)
    btn = page.get_by_text('Поделиться в истории', exact=False).last
    if not btn.count():
        btn = page.get_by_role('button', name=re.compile('Поделиться', re.I)).last
    human_click(page, btn)
    pause(10, 14)                                  # не уходить со страницы, пока история грузится
    return True

def _publish_one(page, key, img):
    state = _j(STATE, {})
    if key in state:
        return False
    tp._window(page, 'normal')                     # не грузить из свёрнутого окна
    try:
        _post(page, img)
    finally:
        tp._window(page, 'minimized')
    state[key] = f'{datetime.datetime.now():%Y-%m-%d %H:%M}'
    _jw(STATE, state)
    try:
        ST_DONE.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(img), str(ST_DONE / img.name))
    except Exception: pass
    return True

def after_text(page, j):
    """Вызывается из publish.py сразу после вышедшего текста (новость, сильный пост, ночной длинный)."""
    files = sorted(f for f in tp.DONE.glob('*.txt') if f.name[:10] == f'{datetime.date.today():%Y-%m-%d}'
                   or f.name[:10] == f'{datetime.date.today() - datetime.timedelta(days=1):%Y-%m-%d}')
    if not files:
        log('история: не нашёл вышедший текст в «Опубликовано» — пропуск'); return
    src = files[-1]
    if time.time() - src.stat().st_mtime > 6 * 3600 and src.name[:10] != f'{datetime.date.today():%Y-%m-%d}':
        log('история: свежего текста нет — пропуск'); return
    key = 'текст ' + src.name
    if key in _j(STATE, {}):
        return
    meta, text = tp._parse(src)
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return
    head = _clean_head(lines[0])
    if len(head) > 120:                            # длинный пост без шапки — первая фраза
        head = re.split(r'(?<=[.!?…])\s', head)[0][:120].rstrip('.')
    label = _label(meta, head, text)
    photo = _story_photo(meta, text)
    if not photo:
        log('ОШИБКА история: нет свободного размеченного фото в «Посты\\Фото» — история не вышла'); return
    sub = random.choice(SUBS)
    img = TMP / f'{datetime.datetime.now():%d.%m %H%M} история {re.sub(r"[^\w ]", "", head)[:40]}.jpg'
    draw(photo, label, head, sub, img)
    pause(60, 120)                                 # не сразу после поста — как человек
    if _publish_one(page, key, img):
        used = _j(ST_PHOTOS, {}); used[photo.name] = f'{datetime.date.today():%Y-%m-%d}'; _jw(ST_PHOTOS, used)
        log(f'ГОТОВО история: «{head[:60]}» ({label}, фото {photo.name})')
    _queue(page)

def _queue(page):
    """Картинки, которые положили вручную в «Сторис\\Очередь»: одна за раз, не больше 2 в день."""
    if not ST_QUEUE.exists():
        return
    state = _j(STATE, {})
    today = f'{datetime.date.today():%Y-%m-%d}'
    if sum(1 for k, v in state.items() if k.startswith('очередь ') and v.startswith(today)) >= 2:
        return
    for f in sorted(ST_QUEUE.iterdir()):
        if f.suffix.lower() in ('.jpg', '.jpeg', '.png') and ('очередь ' + f.name) not in state:
            pause(60, 120)
            if _publish_one(page, 'очередь ' + f.name, f):
                log(f'ГОТОВО история из очереди: {f.name}')
            return
