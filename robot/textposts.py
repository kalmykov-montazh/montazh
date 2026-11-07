# Текстовые посты Facebook: 1 коротыш (цветной фон) утром + 1 короткий пост с фото днём + 1 длинный (с фото) ночью, сразу в 9 групп.
# С 25.10.2026: второй коротыш заменён постом с фото (папка «Фото-посты»); после выхода коротыш и фото-пост
# копируются заданием в «Посты!\Соцсети» (Threads; коротыш ещё в X и Bluesky). Новости («000 …») копирует новостная задача сама.
# Решения Евгения 15.10.2026 — файл проекта «Публикатор — коротыши и длинные посты (решения)».
#
# Папки: «Монтаж!\Посты!\Коротыши», «Длинные», «Фото», «Опубликовано», служебное — «Посты!\_служебное».
# Файл поста — .txt. Необязательные первые строки:
#   @тема: испания | новости | общая | юмор   (иначе «общая»; файл «000 …» — всегда «новости»)
#   Тематика групп (решение Евгения 27.10.2026): у каждой группы «жанр» — испания / юмор / мудрость /
#   интересное / эмиграция. Новости и испанские темы НЕ идут в юмор; юмор — только в юмор и общие.
#   @фото: имя.jpg         (длинные и фото-посты; иначе фото подбирается по теме текста — см. «фото по смыслу»)
#   @фото-тема: еда, дом   (необязательно: подсказка темы фото, теги из «Фото\_темы фото.json»)
#   @threads+:             (31.10.2026, необязательно, в любом месте текста) всё после — только для Threads,
#                          вставляется перед последним абзацем; Facebook-текст держим 300–400 знаков
#   Фото в Facebook: вертикаль выше 4:5 режется по центру до 4:5 (копия в «Робот\_tmp_фото»), см. photo_4x5
# Публикуем СРАЗУ, не отложкой: в отложке Facebook выключает «Поделиться в группах».
import json, random, re, shutil, datetime, time
from pathlib import Path
from common import ROOT, QUEUE, log, pause, human_click, human_type, warm_up

POSTS = ROOT / 'Брокер' / 'Посты'
SHORT, LONG, PHOTO, DONE = POSTS / 'Коротыши', POSTS / 'Длинные', POSTS / 'Фото', POSTS / 'Опубликовано'
PHOTOPOST = POSTS / 'Фото-посты'          # короткие посты с фото (2–4 строки), слот днём
SOCIAL = POSTS / 'Соцсети'               # задания для Threads / X / Bluesky (их отправляет blotato.py)
FOLDERS = {'short': SHORT, 'long': LONG, 'photo': PHOTOPOST}
FOLDER_NAMES = {'short': 'Коротыши', 'long': 'Длинные', 'photo': 'Фото-посты'}
# куда копировать после выхода в Facebook (решение Евгения 25.10.2026)
CROSS = {'short': ['threads', 'twitter', 'bluesky'], 'photo': ['threads']}
USED_PHOTO = PHOTO / 'использованные'
SYS = POSTS / '_служебное'
GROUPS = SYS / 'группы.json'
DAYPLAN = SYS / 'план дней.json'

# фото-пост 14:50–15:40 с 26.10.2026 — ролики теперь 8:15/10:45/13:30/16:30
# окна времени: (вид, начало, конец) — время внутри окна каждый день случайное
WINDOWS = [('short', '09:10', '10:00'), ('photo', '14:50', '15:40'), ('long', '22:30', '25:30')]
LATE_MIN = 90                       # опоздали больше чем на 90 минут (компьютер был выключен) — пропускаем
COOLDOWN = {'испания': 3, 'общая': 1}   # через сколько дней группу можно взять снова
PROVEN, MEDIUM, TESTS = 5, 1, 3   # решение Евгения 25.10.2026: 5 сильных + 1 средняя + 3 на тест
# фоны-картинки из «Настройки фона» (Евгению нравятся не однотонные, а «небо/море»-подобные):
# по порядку в окне «Выбор фона»: 0–21 «Декоративные», 22–29 «Градиентные», дальше «Сплошные» — их не берём.
# Без сердечек и конфетти (16–19).
BG_PICK = list(range(0, 16)) + [20, 21] + list(range(22, 30))
PHOTO_EXT = ('.jpg', '.jpeg', '.png', '.webp')

def _jload(p, default):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default

def _jsave(p, data):
    SYS.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    tmp.replace(p)

# ---------- раскладка по дням ----------
def plan():
    """Создаёт задания на сегодня и завтра. Окно, которое уже прошло, не создаём."""
    for d in (SHORT, LONG, PHOTO, PHOTOPOST, DONE, SYS):
        d.mkdir(parents=True, exist_ok=True)
    days = _jload(DAYPLAN, {})
    now = datetime.datetime.now()
    for add in (0, 1):
        day = now.date() + datetime.timedelta(days=add)
        ds = day.isoformat()
        for i, (kind, a, b) in enumerate(WINDOWS):
            key = f'{ds} {i}'
            if key in days:
                continue
            start = datetime.datetime.combine(day, datetime.time(0)) + _td(a)
            end = datetime.datetime.combine(day, datetime.time(0)) + _td(b)
            if end < now:
                continue
            lo = max(start, now + datetime.timedelta(minutes=5))
            at = lo + datetime.timedelta(seconds=random.randint(0, max(0, int((end - lo).total_seconds()))))
            job = {'platform': 'fbtext', 'kind': kind, 'day': ds, 'slot': i, 'at': f'{at:%Y-%m-%d %H:%M}'}
            (QUEUE / f'{at:%Y-%m-%d_%H%M}_fbtext_{kind}.json').write_text(json.dumps(job, ensure_ascii=False), encoding='utf-8')
            days[key] = {'вид': kind, 'время': f'{at:%H:%M}', 'статус': 'задание'}
            log(f'РАСКЛАДКА текст {kind} {at:%Y-%m-%d %H:%M}')
    cutoff = (now.date() - datetime.timedelta(days=30)).isoformat()
    _jsave(DAYPLAN, {k: v for k, v in days.items() if k >= cutoff})

def _td(hhmm):
    h, m = map(int, hhmm.split(':'))
    return datetime.timedelta(hours=h, minutes=m)

def due(j):
    """None — ещё рано; True — пора; False — сильно опоздали, пропускаем."""
    at = datetime.datetime.strptime(j['at'], '%Y-%m-%d %H:%M')
    now = datetime.datetime.now()
    if now < at:
        return None
    return (now - at).total_seconds() <= LATE_MIN * 60

def mark(j, status):
    days = _jload(DAYPLAN, {})
    e = days.setdefault(f"{j['day']} {j['slot']}", {'вид': j['kind']})
    e['статус'] = status
    _jsave(DAYPLAN, days)

# ---------- тексты и фото ----------
def _next_text(kind):
    folder = FOLDERS.get(kind, LONG)
    files = sorted(f for f in folder.glob('*.txt') if not f.name.startswith('_'))
    return files[0] if files else None

def _parse(path):
    meta, lines = {}, path.read_text(encoding='utf-8-sig').splitlines()
    while lines and lines[0].startswith('@') and not _TH_PLUS.match(lines[0]):
        k, _, v = lines.pop(0)[1:].partition(':')
        meta[k.strip().lower()] = v.strip()
    # «@threads+:» (31.10.2026): всё после маркера — добавка ТОЛЬКО для Threads, в Facebook не уходит никогда
    for i, ln in enumerate(lines):
        m = _TH_PLUS.match(ln)
        if m:
            extra = '\n'.join([m.group(1)] + lines[i + 1:]).strip().replace('⠀', '')
            meta['threads+'] = re.sub(r'\n{3,}', '\n\n', extra)
            lines = lines[:i]
            break
    text = '\n'.join(lines).strip().replace('⠀', '')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return meta, text

_TH_PLUS = re.compile(r'^\s*@threads\+\s*:?(.*)$', re.I)

def threads_text(text, meta):
    """Текст для Threads: Facebook-текст + добавка «@threads+:» перед последним абзацем-концовкой."""
    extra = (meta or {}).get('threads+', '').strip()
    if not extra:
        return text
    paras = [p for p in re.split(r'\n\s*\n', text.strip()) if p.strip()]
    if len(paras) < 2:
        return text.strip() + '\n\n' + extra
    return '\n\n'.join(paras[:-1] + [extra, paras[-1]])

# ---------- фото под ленту Facebook 4:5 (31.10.2026) ----------
# Очки Ray-Ban снимают вертикаль 3:4, а лента Facebook показывает вертикаль максимум 4:5 — режем по центру по высоте.
# Оригинал не трогаем (после выхода он, как раньше, уезжает в «Фото\использованные»), грузим копию из «_tmp_фото».
TMP_PHOTO = Path(__file__).resolve().parent / '_tmp_фото'

def _pil():
    try:
        from PIL import Image, ImageOps
        return Image, ImageOps
    except ImportError:
        import subprocess, sys
        log('фото 4:5: нет Pillow — ставлю (pip install pillow)')
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'pillow'], timeout=300,
                       capture_output=True)
        from PIL import Image, ImageOps
        return Image, ImageOps

def photo_4x5(photo):
    """Вертикальное фото выше 4:5 → копия JPEG 4:5 (центр по высоте). Иначе или при сбое — оригинал."""
    if not photo:
        return photo
    try:
        Image, ImageOps = _pil()
        with Image.open(photo) as im:
            im = ImageOps.exif_transpose(im)
            w, h = im.size
            if h / w <= 1.25:
                return photo
            nh = round(w * 5 / 4)
            top = (h - nh) // 2
            im = im.crop((0, top, w, top + nh))
            if im.mode != 'RGB':
                im = im.convert('RGB')
            TMP_PHOTO.mkdir(exist_ok=True)
            out = TMP_PHOTO / (photo.stem + '_4x5.jpg')
            im.save(out, 'JPEG', quality=92)
        log(f"фото 4:5: {photo.name} {w}×{h} → {w}×{nh}")
        return out
    except Exception as e:
        log(f"фото 4:5: не обрезалось {photo.name} ({str(e)[:120]}) — гружу оригинал")
        return photo

# ---------- фото по смыслу поста (27.10.2026) ----------
# Разметка: «Посты\Фото\_темы фото.json» {имя.jpg: [теги]} — ведёт Claude (новые фото размечает при пополнении).
# Порядок: «@фото: имя.jpg» → «@фото-тема: пляж, еда» → темы по словам текста → нейтральный город/море.
# Палатки/протест/полиция/каннабис — ТОЛЬКО если сам пост про это (слова в тексте или @фото-тема).
PHOTO_TAGS = PHOTO / '_темы фото.json'
SENSITIVE = {'палатки', 'протест', 'полиция', 'каннабис'}
NEUTRAL = ('город', 'улица', 'море', 'закат', 'пальмы', 'архитектура')
KEYWORDS = {
    'пляж':  ['пляж', 'море', 'морск', 'отпуск', 'купа', 'загар', 'волн', 'побереж'],
    'отдых': ['отдых', 'отпуск', 'выходн', 'каникул', 'путешеств', 'поездк'],
    'закат': ['закат', 'рассвет', 'небо', 'звёзд', 'звезд', 'вечер'],
    'еда':   ['кухн', 'блюд', 'приготов', 'готовит', 'обед', 'ужин', 'завтрак', 'вкус', 'гречк', 'варень', 'конфет',
              'пельмен', 'хлеб', 'выпечк', 'паэль', 'тапас', 'продукт', 'борщ', 'еду ', 'еда', 'едим', 'заготовк'],
    'кафе':  ['кафе', 'ресторан', 'бар ', 'кофе', 'официант', 'счёт', 'чаевы'],
    'магазин': ['магазин', 'покупк', 'купить', 'купил', 'скидк', 'распродаж', 'касс', 'супермаркет', 'mercadona', 'мерсадон'],
    'цены':  ['цен', 'дорож', 'дешев', 'дёшев', 'евро', 'деньг', 'зарплат', 'экономи', 'бережлив', 'жадн'],
    'праздник': ['праздник', 'рожден', 'подар', 'фиест', 'фальяс', 'фаяс', 'традиц', 'концерт', 'песн',
                 'музык', 'танц', 'свадьб', 'конверт', 'юбиле', 'отмеча'],
    'рождество': ['рождеств', 'новый год', 'новогод', 'ёлк', 'елк'],
    'транспорт': ['машин', 'автомоб', 'авто ', 'автобус', 'водит', 'парков', 'такси', 'автобус', 'метро', 'транспорт', 'пробк'],
    'история': ['истори', 'старин', 'собор', 'церк', 'башн', 'музей', 'архитектур', 'век назад'],
    'работа': ['работ', 'ремонт', 'стройк', 'строит', 'бригад', 'начальник', 'коллег', 'офис'],
    'дети':  ['ребён', 'ребен', 'детей', 'дети', 'сын', 'дочь', 'дочк', 'школ', 'игрушк'],
    'здоровье': ['аптек', 'лекарств', 'врач', 'болез', 'здоров', 'таблет', 'больниц'],
    'дом':   [' дом ', ' дома ', ' дому ', 'домой', 'домашн', 'квартир', 'кухн', 'мама', 'мамин', 'родител', 'бабушк', 'семь'],
    'документы': ['документ', 'бумаг', 'налог', 'договор', 'аренд', 'банк', 'внж', 'nie', 'гестор'],
    'город': ['город', 'улиц', 'валенси', 'испани', 'испанц', 'прогул', 'сосед', 'район', 'эмиграц', 'переезд'],
    'люди':  ['люд', 'друз', 'друг', 'знаком', 'человек', 'разговор'],
    'цветы': ['цветы', 'цветов', 'цветок', 'букет'],
    'протест': ['протест', 'митинг', 'забастов', 'палатк', 'манифестац', 'демонстрац', 'беспоряд', 'акампад'],
    'полиция': ['полици', 'полицейск'],
}

def _photo_tags():
    try:
        return json.loads(PHOTO_TAGS.read_text(encoding='utf-8'))
    except Exception:
        return {}

GENERIC = {'люди': 0.3, 'город': 0.5, 'дом': 0.6, 'работа': 0.5, 'документы': 0.6, 'закат': 0.6}

def _wanted_tags(meta, text):
    if meta.get('фото-тема'):
        return {t.strip().lower(): 3.0 for t in re.split(r'[,;]', meta['фото-тема']) if t.strip()}, 'по @фото-тема'
    low = ' ' + re.sub(r'[^\w\s]', ' ', text.lower().replace('ё', 'е')) + ' '
    w = {}
    for tag, stems in KEYWORDS.items():
        n = sum(low.count(st.replace('ё', 'е')) for st in stems)
        if n:
            if tag in SENSITIVE and n < 2:   # палатки только если пост правда про протест (2+ слова)
                continue
            w[tag] = n * GENERIC.get(tag, 1.0) * (3 if tag in SENSITIVE else 1)
    w = {k: v for k, v in w.items() if v >= 1.0}   # одно случайное слово — не тема
    return w, 'по словам текста'

# Фото с «особым» сюжетом (еда, дети, праздник…) берём ТОЛЬКО если пост про это.
# 01.11.2026: к новости про телеканалы ушло фото теста в пакете (теги дом/еда/кухня),
# потому что слово «дом» в тексте дало тему «дом».
SPECIFIC = {'еда': 'еда', 'кухня': 'еда', 'кафе': 'кафе', 'кофе': 'кафе', 'дети': 'дети',
            'праздник': 'праздник', 'фиесты': 'праздник', 'парад': 'праздник', 'концерт': 'праздник',
            'традиции': 'праздник', 'рождество': 'рождество', 'украшения': 'рождество',
            'здоровье': 'здоровье', 'аптека': 'здоровье', 'цветы': 'цветы', 'документы': 'документы',
            'парикмахерская': 'парикмахерская', 'мусор': 'мусор', 'стройка': 'работа'}
MIN_SCORE = 2.0   # слабое совпадение — не тема, берём нейтральный город/море

def _score(wanted, tags):
    hit = sorted((v for k, v in wanted.items() if k in tags), reverse=True)
    sc = (hit[0] + 0.25 * sum(hit[1:])) if hit else 0.0
    foreign = {SPECIFIC[t] for t in tags if t in SPECIFIC and SPECIFIC[t] not in wanted}
    return sc - 3.0 * len(foreign)

def _pick_photo(meta, text=''):
    files = [f for f in PHOTO.iterdir() if f.is_file() and f.suffix.lower() in PHOTO_EXT]
    if meta.get('фото'):
        p = PHOTO / meta['фото']
        if p.exists():
            log(f"фото: {p.name} (указано в посте)")
            return p
        log(f"фото «{meta['фото']}» не найдено, подбираю по теме")
    if not files:
        return None
    tags = _photo_tags()
    untagged = [f.name for f in files if f.name not in tags]
    if untagged:
        log(f"фото без разметки ({len(untagged)} шт.) не беру — пусть Claude разметит в «_темы фото.json»")
    wanted, how = _wanted_tags(meta, text)
    allow_sens = bool(SENSITIVE & set(wanted))
    pool = []
    for f in files:
        t = set(tags.get(f.name, []))
        if not t or (t & SENSITIVE and not allow_sens):
            continue
        score = _score(wanted, t)
        pool.append((score, f, t))
    if not pool:
        log('нет размеченных подходящих фото — беру самое старое неразмеченное')
        rest = sorted((f for f in files if f.name in untagged), key=lambda f: (f.stat().st_mtime, f.name))
        return rest[0] if rest else None
    best = max(p[0] for p in pool)
    if best >= MIN_SCORE:
        cand = [p for p in pool if p[0] == best]
    else:  # тема не угадана — спокойный город/море, без людей в палатках
        cand = [p for p in pool if p[2] & set(NEUTRAL) and not (p[2] & set(SPECIFIC))] \
            or [p for p in pool if p[2] & set(NEUTRAL)] or pool
        how = 'тема не найдена, нейтральное'
    cand.sort(key=lambda p: (p[1].stat().st_mtime, p[1].name))
    f = cand[0][1]
    top = ', '.join(k for k, _ in sorted(wanted.items(), key=lambda x: -x[1])[:4]) or '—'
    log(f"фото: {f.name} [{', '.join(sorted(cand[0][2]))}] ← {how} ({top})")
    return f

# ---------- выбор групп ----------
def _days_since(g, today):
    if not g.get('посты'):
        return 999
    last = max(p['дата'] for p in g['посты'])
    return (today - datetime.date.fromisoformat(last)).days

# Какие жанры групп подходят теме поста (решение Евгения 27.10.2026: новости не в шутки).
# main — сколько групп своего типа, other — сколько другого; жанры — из каких групп «общего» типа можно брать.
TOPIC_RULES = {
    'новости': {'main': 'испания', 'quota': {'испания': 9, 'общая': 0}, 'genres': {'испания', 'эмиграция', 'интересное'}},
    'испания': {'main': 'испания', 'quota': {'испания': 5, 'общая': 4}, 'genres': {'испания', 'эмиграция', 'мудрость', 'интересное'}},
    'общая':   {'main': 'общая',   'quota': {'общая': 5, 'испания': 4}, 'genres': {'испания', 'эмиграция', 'мудрость', 'интересное', 'юмор'}},
    'юмор':    {'main': 'общая',   'quota': {'общая': 6, 'испания': 3}, 'genres': {'испания', 'юмор', 'интересное'}},
}
HUMOR_RE = (r'юмор|шут|смех|анекдот|сарказм|ирони|прикол|позитив|улыбн|улыбк|весел|забавн|21\+|18\+|\+18|\+21|24\+|'
            r'пизд|пи✓д|ёп|курим|психуш|лечебниц|палата|абракадабр|пофиг|эгоист|fails|чума|бабки гонят|бабы рулят|'
            r'пересмешник|гусъ|блатн|двіжух|несерь|одесс|ша!|кукушк|пропанд|бісить|абсурд|ржак|угар|мем')
WISDOM_RE = (r'мудр|мысл|цитат|афоризм|слова|душ|жизн|счаст|философ|хайям|синдром успеха|в точку|калейдоскоп|истори|'
             r'судьб|любов|чувств|предава|никогда|след в|крик|волк|тишин|кофе|огон|денёчк|женщин|детств|чердак|старост|'
             r'нам ведь|написано|бандит|эмоци|психолог|статус')
ABROAD_RE = r'герман|deutsch|литв|вільнюс|vilnius|бельги|австрали|мюнхен|ирланд|латинск|польш|чехи|израил|канад|сша|usa'

def genre_of(name, typ):
    """Жанр группы по названию; руками поставленный «жанр» в реестре не трогаем."""
    if typ == 'испания':
        return 'испания'
    if re.search(HUMOR_RE, name, re.I):
        return 'юмор'
    if re.search(ABROAD_RE, name, re.I):
        return 'эмиграция'
    if re.search(WISDOM_RE, name, re.I):
        return 'мудрость'
    return 'интересное'

def topic_of(meta, path):
    t = meta.get('тема', '').lower()
    if path is not None and path.name.startswith('000'):
        return 'новости'
    for k in ('новост', 'испан', 'юмор'):
        if t.startswith(k):
            return {'новост': 'новости', 'испан': 'испания', 'юмор': 'юмор'}[k]
    return 'общая'

def choose_groups(available, topic, day):
    """9 групп: 5 проверенных (сильных) + 1 средняя + 3 тестовые (решение 25.10.2026).
    Типы и квоты — по теме, см. TOPIC_RULES; жанр группы должен подходить теме (27.10.2026):
    новости — только испанские (+ эмиграция/интересное, если не хватило), никогда не юмор.
    Наборы за день не пересекаются; испанская группа — не чаще раза в 3 дня, общая — раз в день.
    Статусы «слабая», «вышла», «мёртвая», «не для постов» робот не берёт."""
    reg = _jload(GROUPS, {})
    available = list(dict.fromkeys(available))   # одинаковые названия — один раз
    for n in available:                      # новые группы, в которые вступил Евгений, — сразу в тест
        if n not in reg:
            typ = 'испания' if re.search(SPAIN_RE, n, re.I) else 'общая'
            reg[n] = {'тип': typ, 'жанр': genre_of(n, typ),
                      'статус': 'не для постов' if re.search(ADS_RE, n, re.I) else 'тест',
                      'посты': [], 'добавлена': day}
            log(f"новая группа в тест: {n} ({reg[n]['жанр']})")
    for n, g in reg.items():
        if 'жанр' not in g:
            g['жанр'] = genre_of(n, g.get('тип', 'общая'))
    _jsave(GROUPS, reg)
    today = datetime.date.fromisoformat(day)
    used_today = {n for n, g in reg.items() for p in g.get('посты', []) if p.get('день') == day}
    rule = TOPIC_RULES.get(topic, TOPIC_RULES['общая'])
    genres = rule['genres']
    main = rule['main']
    other = 'общая' if main == 'испания' else 'испания'
    quota = dict(rule['quota'])

    def pool(typ, status, relax, taken):
        out = [n for n in available if n in reg and n not in used_today and n not in taken
               and reg[n]['тип'] == typ and reg[n]['статус'] == status
               and reg[n].get('жанр', 'интересное') in genres
               and _days_since(reg[n], today) >= COOLDOWN.get(typ, 1) - relax]
        def key(n):
            g = reg[n]
            top = g.get('топ', 99) if typ == 'испания' else 99
            pref = 0 if (topic == 'юмор' and g.get('жанр') == 'юмор') else 1
            if status == 'тест':             # 06.11.2026: сначала повтор (1–2 поста, прошлый 7+ дней назад), потом новые
                np_ = len(g.get('посты', []))
                due = 0 if 1 <= np_ <= 2 and _days_since(g, today) >= 7 else (1 if np_ == 0 else 2)
                return (pref, due, np_, random.random())
            return (pref, top if main == 'испания' else 99, -_days_since(g, today), random.random())
        return sorted(out, key=key)

    def room(typ):
        return quota[typ] - sum(1 for n in picked if reg[n]['тип'] == typ)

    picked = []
    # 1) три тестовые: основной тип, другой, основной (если места нет — что найдётся)
    for typ in (main, other, main):
        if sum(1 for n in picked if reg[n]['статус'] == 'тест') >= TESTS:
            break
        for t2 in (typ, other if typ == main else main):
            if room(t2) <= 0:
                continue
            t = []
            for relax in (0, 1, 2):
                t = pool(t2, 'тест', relax, picked)[:1]
                if t:
                    break
            if t:
                picked += t
                break
    # 2) одна средняя: сначала основной тип
    for typ in (main, other):
        if room(typ) <= 0:
            continue
        m = []
        for relax in (0, 1, 2):
            m = pool(typ, 'средняя', relax, picked)[:MEDIUM]
            if m:
                break
        if m:
            picked += m
            break
    # 3) остальное — проверенные, по квотам типов
    for typ in (main, other):
        for relax in (0, 1, 2):
            need = room(typ)
            if need <= 0:
                break
            picked += pool(typ, 'проверенная', relax, picked)[:need]
            if relax == 1:
                log(f'«{typ}»: групп с перерывом не хватает, ослабляю перерыв')
    if len(picked) < 9:                      # одного типа не хватило — добираем чем есть (жанр всё равно по теме)
        for status in ('проверенная', 'средняя', 'тест'):
            for typ in (main, other):
                picked += pool(typ, status, 2, picked)[:9 - len(picked)]
    return picked[:9]

ADS_RE = r'недвиж|нерухом|inmob|property|apartament|alquil|аренд|оренд|квартир|комнат|работ|робот|ваканс|trabajo|объявлен|обьявлен|оголош|anunci|реклам|из рук в руки|купи|куплю|барахол|площадка|грузопер|перевез|перевоз|transporte|ремонт|reforma|строит|construc|услуги|послуги|страхов|бизнес|бізнес|доска'
SPAIN_RE = (r'испан|españ|spain|валенс|valenc|торрев|torrev|аликан|alican|барсел|barcel|мадрид|малаг|марбел|мурси|мурсі|тенериф|іспан|валенсі|sagunt|сагунт|кальпе|'
            r'costa|коста|жирон|girona|салоу|salou|таррагон|tarragon|астури|asturi|бенидорм|benidorm|гвардамар|guardamar|кастейон|castell|канар|canar|камбрілс|cambrils|реус|андалус|севиль|гранад|кадис|бильбао|сарагос|ибиц|майорк|mallorc')

def _record(groups, day, kind, title):
    reg = _jload(GROUPS, {})
    stamp = f'{datetime.datetime.now():%Y-%m-%d %H:%M}'
    for n in groups:
        reg.setdefault(n, {'тип': 'общая', 'жанр': 'интересное', 'статус': 'тест', 'посты': []})
        reg[n].setdefault('посты', []).append({'дата': stamp[:10], 'день': day, 'время': stamp[11:], 'вид': kind, 'пост': title[:40]})
    _jsave(GROUPS, reg)

# ---------- публикация ----------
JS_LOAD = """async () => {
  const dlg = [...document.querySelectorAll('[role=dialog]')].find(d => d.innerText.includes('Публикация в группах'));
  if (!dlg) return -1;
  let hist = [];
  for (let i = 0; i < 30; i++) {
    const all = dlg.querySelectorAll('input[type=checkbox]');
    if (all.length) all[all.length - 1].scrollIntoView({block: 'end'});
    await new Promise(r => setTimeout(r, 900 + Math.random() * 600));
    hist.push(dlg.querySelectorAll('input[type=checkbox]').length);
    if (i > 3 && hist[i] === hist[i - 3]) break;
  }
  const first = dlg.querySelector('input[type=checkbox]');
  if (first) first.scrollIntoView({block: 'center'});
  return hist[hist.length - 1];
}"""
JS_SCROLLER = """() => {
  const d = [...document.querySelectorAll('[role=dialog]')].find(d => d.innerText.includes('Публикация в группах'));
  const first = d.querySelector('input[type=checkbox]');
  let e = first, box = null;
  while (e && e !== d) {
    const st = getComputedStyle(e);
    if (e.scrollHeight > e.clientHeight + 20 && /(auto|scroll)/.test(st.overflowY)) { box = e; break; }
    e = e.parentElement;
  }
  const r = (box || d).getBoundingClientRect();
  return {x: r.x + r.width / 2, y: r.y + r.height / 2, found: !!box};
}"""
JS_ROWS = """(want) => {
  const dlg = [...document.querySelectorAll('[role=dialog]')].find(d => d.innerText.includes('Публикация в группах'));
  const rows = [...dlg.querySelectorAll('input[type=checkbox]')].map(b => {
    const row = b.closest('[role=button]') || b.parentElement.parentElement;
    const name = (row.innerText || '').split('\\n')[0].replace(/\\ufeff/g, '').trim();
    return {b, row, name};
  });
  if (want === null) return rows.map(r => r.name);
  const r = rows.find(r => r.name === want);
  if (!r) return null;
  r.row.scrollIntoView({block: 'center'});
  const box = r.row.getBoundingClientRect();
  return {x: box.x, y: box.y, w: box.width, h: box.height,
          checked: r.b.checked || r.b.getAttribute('aria-checked') === 'true'};
}"""

def _set_background(page, dlg):
    """Фон из полоски под текстом. Решение Евгения 02.11.2026: тёмно-синюю «иллюстрацию» с конфетти
    и тёмные/чёрные фоны не ставить. Сначала небо, море, пляж, природа; потом однотонные светлые
    и спокойные цвета; потом светлые градиенты. Все варианты из полоски пишем в журнал."""
    human_click(page, dlg.get_by_role('button', name='Показать параметры фона').first)
    pause(1, 2)
    labels = [x for x in dlg.locator('[role="button"][aria-label*="фон "]').evaluate_all(
        "els => els.map(e => e.getAttribute('aria-label'))") if x]
    log('фоны в полоске: ' + ' | '.join(labels))
    low = lambda x: x.lower()
    BAD = ('темно-син', 'тёмно-син', 'черн', 'чёрн', 'темно-сер', 'тёмно-сер', 'конфетти',
           'сердц', 'сердеч', 'шар', 'праздн', 'фиолет')
    NICE = ('неб', 'облак', 'мор', 'пляж', 'океан', 'закат', 'рассвет', 'горы', 'гор ', 'природ',
            'лес', 'цвет', 'лист', 'пальм', 'солнц', 'песок', 'вода', 'волн')
    ok = [x for x in labels if not any(b in low(x) for b in BAD)]
    nice = [x for x in ok if any(n in low(x) for n in NICE)]
    solid = [x for x in ok if low(x).startswith('сплошн') and x not in nice]
    grads = [x for x in ok if low(x).startswith('градиент') and x not in nice]
    pool = nice or solid or grads or ok
    if not pool:
        log('фон: подходящего нет, оставляю без фона')
        return 'без фона'
    label = random.choice(pool)
    human_click(page, dlg.locator(f'[role="button"][aria-label="{label}"]').first)
    pause(1, 2)
    return label

def _load_picker(page):
    """Окно «Публикация в группах» догружает группы только при настоящей прокрутке колесом."""
    pdlg = page.locator('[role="dialog"]').filter(has_text='Публикация в группах').last
    pdlg.wait_for(timeout=20000)
    count, same = 0, 0
    for _ in range(120):
        # колесо крутим, держа мышь над последней видимой строкой списка
        # мышь — в середину прокручиваемой области списка (не на строку за краем)
        r = page.evaluate(JS_SCROLLER)
        page.mouse.move(r['x'] + random.uniform(-40, 40), r['y'] + random.uniform(-10, 10), steps=random.randint(4, 9))
        page.mouse.wheel(0, random.randint(700, 1100))
        time.sleep(random.uniform(0.9, 1.6))
        n = page.evaluate("() => { const d=[...document.querySelectorAll('[role=dialog]')].find(d=>d.innerText.includes('Публикация в группах')); return d ? d.querySelectorAll('input[type=checkbox]').length : 0 }")
        same = same + 1 if n == count else 0
        count = n
        if same >= 4:
            break
    names = page.evaluate(JS_ROWS, None)
    log(f"в окне выбора групп: {len(names)} (область прокрутки найдена: {r.get('found')})")
    if len(names) <= 25:
        try:
            from common import QUEUE
            (QUEUE / 'шаги').mkdir(exist_ok=True)
            page.screenshot(path=str(QUEUE / 'шаги' / f'{datetime.datetime.now():%m%d_%H%M} группы.png'))
        except Exception:
            pass
    return names

def _window(page, state):
    """Окно робота запускается свёрнутым; свёрнутое окно Facebook не догружает список групп.
    На время публикации разворачиваем, потом сворачиваем обратно."""
    try:
        cdp = page.context.new_cdp_session(page)
        wid = cdp.send('Browser.getWindowForTarget')['windowId']
        cdp.send('Browser.setWindowBounds', {'windowId': wid, 'bounds': {'windowState': state}})
        if state == 'normal':
            page.bring_to_front()
        pause(1, 2)
    except Exception as e:
        log(f'окно: не смог сделать {state} ({str(e)[:80]})')

class DryRun(Exception):
    pass

def _discard(page):
    """Закрыть окно публикации и стереть черновик."""
    page.keyboard.press('Escape'); pause(1, 2)
    back = page.get_by_role('button', name='Назад')
    if back.count():
        human_click(page, back.last)
    box = page.locator('[role="dialog"] [role="textbox"]').last
    if box.count():
        human_click(page, box)
        page.keyboard.press('Control+A'); pause(0.3, 0.6)
        page.keyboard.press('Delete'); pause(1, 2)
    close = page.get_by_role('button', name='Закрыть диалог создания публикаций')
    if close.count():
        human_click(page, close.last)
    for name in ('Удалить', 'Выйти', 'Не сохранять'):
        b = page.get_by_role('button', name=name, exact=True)
        if b.count():
            human_click(page, b.last); break

def publish(page, j):
    kind = j['kind']
    path = _next_text(kind)
    if not path:
        raise RuntimeError(f"нет текста в «Посты!\\{FOLDER_NAMES.get(kind, 'Длинные')}» — слот пропущен")
    meta, text = _parse(path)
    topic = topic_of(meta, path)
    if kind == 'short' and len(text) > 130:
        raise RuntimeError(f'коротыш «{path.name}» длиннее 130 знаков ({len(text)}) — фон не включится')
    photo = _pick_photo(meta, text) if kind in ('long', 'photo') else None
    j['_meta'] = meta
    bg = ''

    _window(page, 'normal')
    try:
        # до 3 попыток: Facebook иногда не грузит окно «Создать публикацию» (16.10.2026 — серая заглушка).
        # Повторяем, только пока текст ещё в очереди, т.е. «Опубликовать» точно не нажимали.
        for attempt in range(1, 4):
            try:
                _publish(page, j, kind, path, text, topic, photo, bg)
                return
            except Exception as e:
                if not path.exists() or attempt == 3 or j.get('dry') or isinstance(e, DryRun):
                    raise
                log(f"сбой {kind} (попытка {attempt}): {str(e).splitlines()[0][:120]} — закрываю окно, обновляю страницу, пробую ещё раз")
                try: _discard(page)
                except Exception: pass
                try: page.reload(wait_until='domcontentloaded')
                except Exception: pass
                time.sleep(random.uniform(90, 180))
    finally:
        _window(page, 'minimized')

def _publish(page, j, kind, path, text, topic, photo, bg):
    warm_up(page)
    page.goto('https://www.facebook.com/me', wait_until='domcontentloaded')
    pause(5, 9)
    human_click(page, page.get_by_text('Что у вас нового?').first)
    # у Facebook два слоя с именем «Создание публикации», нужен тот, где есть поле текста
    dlg = page.locator('[role="dialog"]').filter(has=page.locator('[role="textbox"]')).last
    dlg.wait_for(timeout=60000)
    pause(2, 4)
    att = dlg.get_by_role('button', name='Удалить вложение из публикации')
    if att.count():
        human_click(page, att.first)
    human_click(page, dlg.get_by_role('textbox').first)
    human_type(page, text)
    pause(2, 4)
    up = photo
    if kind == 'short':
        bg = _set_background(page, dlg)
    elif photo:
        inp = dlg.locator('input[type=file]')
        if not inp.count():
            human_click(page, dlg.get_by_role('button', name='Фото/видео').first)
            inp = dlg.locator('input[type=file]')
        up = photo_4x5(photo)
        inp.first.set_input_files(str(up))
        pause(6, 10)
    else:
        log('длинный пост без фото: в «Посты!\\Фото» пусто')
    pause(2, 4)
    human_click(page, dlg.get_by_role('button', name='Далее', exact=True).first)
    pause(3, 5)

    human_click(page, page.get_by_text('Поделиться в группах', exact=True).last)
    pause(3, 5)
    available = _load_picker(page)
    if j.get('dry'):                         # проверка без публикации: только посмотреть, что видно
        reg = _jload(GROUPS, {})
        log(f"ПРОВЕРКА без публикации: групп в окне {len(available)}, из них в реестре {sum(1 for n in set(available) if n in reg)}, фон: {bg}")
        _discard(page)
        raise DryRun()
    groups = choose_groups(available, topic, j['day'])
    if kind == 'photo':                      # 07.11.2026: дневной фото-пост — 5 групп вместо 9 (место под рилс в группах)
        reg_ = _jload(GROUPS, {})
        order = {'проверенная': 0, 'средняя': 1, 'тест': 2}
        groups = sorted(groups, key=lambda n: order.get(reg_.get(n, {}).get('статус'), 9))[:5]
    picked = []
    for n in groups:
        r = page.evaluate(JS_ROWS, n)
        if not r:
            log(f'группа не нашлась в окне: {n}'); continue
        pause(0.5, 1.5)
        r = page.evaluate(JS_ROWS, n)
        if not r['checked']:
            x = r['x'] + r['w'] * random.uniform(0.3, 0.7)
            y = r['y'] + r['h'] * random.uniform(0.35, 0.65)
            page.mouse.move(x, y, steps=random.randint(10, 18))
            pause(0.2, 0.6)
            page.mouse.click(x, y, delay=random.randint(60, 150))
            pause(0.8, 2.0)
        if page.evaluate(JS_ROWS, n)['checked']:
            picked.append(n)
        else:
            log(f'не отметилась группа: {n}')
    human_click(page, page.get_by_role('button', name='Готово', exact=True).last)
    pause(2, 4)
    human_click(page, page.get_by_role('button', name='Опубликовать', exact=True).last)
    # сразу убираем текст из очереди, чтобы при любом сбое дальше он не ушёл второй раз
    title = text.split('\n')[0]
    stamp = f'{datetime.datetime.now():%Y-%m-%d %H%M}'
    shutil.move(str(path), str(DONE / f'{stamp} {path.name}'))
    if photo:
        USED_PHOTO.mkdir(exist_ok=True)
        shutil.move(str(photo), str(USED_PHOTO / photo.name))
        if up != photo:
            try: up.unlink()                   # временная копия 4:5 больше не нужна
            except Exception: pass
    _record(picked, j['day'], kind, title)
    _crosspost(kind, text, path, j.get('_meta', {}))
    pause(15, 25)
    extra = f' | фон: {bg}' if kind == 'short' else (f' | фото: {photo.name}' if photo else '')
    log(f"ТЕКСТ {kind} {topic} «{title[:50]}»{extra} → лента + {len(picked)} групп: {'; '.join(picked)}")
    _verify(page, title)

def _crosspost(kind, text, path, meta):
    """После выхода в Facebook — задание в «Соцсети» (Threads; коротыш ещё X и Bluesky). «@соцсети: нет» — не копировать."""
    try:
        nets = CROSS.get(kind)
        if not nets or meta.get('соцсети', '').lower().startswith('нет'):
            return
        SOCIAL.mkdir(parents=True, exist_ok=True)
        stamp = f'{datetime.datetime.now():%Y-%m-%d_%H%M}'
        task = {'name': f'{kind} {path.stem}',
                'texts': {n: (threads_text(text, meta) if n == 'threads' else text) for n in nets}}
        if kind == 'photo':                    # Facebook днём, а Threads вечером 18:10–19:50 (решение Евгения 27.10.2026)
            now = datetime.datetime.now()
            a = datetime.datetime.combine(now.date(), datetime.time(18, 10))
            lo = max(a, now + datetime.timedelta(minutes=5))
            hi = datetime.datetime.combine(now.date(), datetime.time(19, 50))
            at = lo + datetime.timedelta(seconds=random.randint(0, max(0, int((hi - lo).total_seconds()))))
            task['at'] = f'{at:%Y-%m-%d %H:%M}'
        (SOCIAL / f'{stamp} {kind} {path.stem[:40]}.json').write_text(
            json.dumps(task, ensure_ascii=False, indent=1), encoding='utf-8')
        log(f"СОЦСЕТИ: {kind} «{path.stem[:40]}» → {', '.join(nets)}")
    except Exception as e:
        log(f"соцсети: задание не создано ({str(e)[:120]})")

def _verify(page, title):
    key = title.strip()[:25]
    for _ in range(3):
        page.goto('https://www.facebook.com/me', wait_until='domcontentloaded')
        pause(8, 12)
        if key in page.inner_text('body'):
            return
        pause(20, 40)
    raise RuntimeError('пост опубликован, но в ленте профиля его не видно — проверить вручную (повторно НЕ публикую)')
