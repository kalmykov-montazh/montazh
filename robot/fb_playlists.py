# Автораскладка новых рилсов Facebook (личный профиль) по плейлистам. Решение Евгения 25.10.2026.
# Раз в 3 часа (9:00–23:30) открывает «Панель автора», берёт последние 20 публикаций,
# каждый рилс без плейлиста кладёт в плейлист по теме (правила ниже, по названию и хэштегам).
# Один рилс — один плейлист (правило Facebook). Ручную раскладку Евгения не трогает.
# Учёт: «_задания\_плейлисты.json». Сбой — в журнал и раз в сутки в Telegram.
import json, re, time, datetime
from common import QUEUE, PROFILE, log, tg

PAGE_ID = '689263940944921'
ACTOR = '61576419612412'
STATE = QUEUE / '_плейлисты.json'
LOCK = QUEUE / '_идёт.lock'
EVERY_H = 3

# id плейлистов (созданы и переименованы 25.10.2026)
PL = {
    'ВНЖ':        '908302442331879',    # ВНЖ, ПМЖ и временная защита
    'АРЕНДА':     '1329844881880415',   # Аренда в Испании: права жильца
    'СОБСТВ':     '2132250374174135',   # Сдать и управлять: собственникам
    'ОКУПАС':     '1765554794891898',   # Окупасы: как защитить жильё
    'ПОКУПКА':    '1120846786863500',   # Покупка и продажа недвижимости
    'СЕРГЕЙ':     '1773889650583539',   # Интервью с Сергеем: управление недвижимостью
    'ПЕНСИЯ':     '1101989575852507',   # Пенсия, стаж и пособия
    'АВТО':       '1621086179167179',   # Авто и ПДД: штрафы, номера, права
    'ДЕНЬГИ':     '973791308347039',    # Налоги, банки и деньги
    'РАБОТА':     '28506746565694691',  # Работа в Испании
    'ЖИЗНЬ':      '1620610559158281',   # Жизнь в Испании и Валенсии: быт, районы, цены
    'ПЕРЕЕЗД':    '788257853883408',    # Переезд в Испанию
    'ПУТЬ':       '1711962863221662',   # Мой путь: год в Испании, язык, блог
    'ПУТЕШ':      '2473709366374960',   # Путешествия без переплат
    'ОБЪЕКТЫ':    '1341305691393701',   # Мои объекты: аренда и продажа
}

# Порядок важен: первое совпадение решает. Если ролик ни к чему не подошёл — «Жизнь в Испании».
RULES = [
    ('СЕРГЕЙ',  r'\bэпизод|сергеем|сергей и кристин'),
    ('ОБЪЕКТЫ', r'^(🏠|🏡)|\d[\d .]*\s?€\s?/\s?(мес|сутк)|€/мес|в сутки|^(аренда|продажа) \||сда[её]тся|прода[её]тся|\d\s?спальн'),
    ('ПУТЕШ',   r'отел|букинг|booking|перел[её]т|билет|лоукост|багаж|турагентств|горящ|всё включено|отпуск'),
    ('ОКУПАС',  r'окупас|захват|инкиокупас|вторжени'),
    ('ПЕНСИ',   r'пенси|стаж|\bimv\b|\bимв\b|доплат|пособи|гарантированн\w* доход'),
    ('ВНЖ',     r'внж|пмж|временн\w* защит|защиту продл|арраиго|arraigo|резиденц|extranjer|\bnie\b|\btie\b|гражданств|легализац|воинск|отсрочк|резерв\+|несудимост'),
    ('АВТО',    r'машин|авто(?!ном)|номерах?\b|пдд|за рул[её]м|водител|права? (в испании|украин)|дтп|авари|европротокол|парков|эвакуат|растамож|гбо|itv|v-16|треугольн|штраф без остановки'),
    ('РАБОТА',  r'работ[аеуы]? (в испании|в валенсии)|вакан|завод|трудоустр|професси|таксист|работу'),
    ('ДЕНЬГИ',  r'налог|декларац|modelo|\birpf\b|банк|bbva|наличн|зарплат|доход|бекхэм|крипт|autónomo|автономо|\bsl\b|чаев|мошенник|деньг'),
    ('АРЕНДА',  r'арендатор|жил[её]ц|жильц|снять|сним|залог|депозит|fianza|съ[её]мн|не сда[юё]т|договор аренды|аренд\w* без договор|на 11 месяц|выселен|мораторий|ловушк\w* аренд|аренда в испании'),
    ('СОБСТВ',  r'сдава|сдаю|сдать|посуточ|туристическ\w* (аренд|лиценз)|\bvut\b|airbnb|управлен|собственник|по комнатам'),
    ('ПОКУПКА', r'купить|покупк|купил|продаж|прода(ть|л)|nota simple|задат|новостройк|недвижимост|ипотек|флиппинг|инвест|пусту|пустых|первой линии|квартир\w* дешевле'),
    ('ПЕРЕЕЗД', r'переезд|переех|до переезда|empadronamiento|прописк|первые шаги|после переезда'),
    ('ПУТЬ',    r'подписчик|tiktok|instagram|youtube|блог|соцсет|стрим|видео|caritas|каритас|испанск\w* (язык|курс)|учу испанский|год в испании|с нуля|потерял всё|мой путь'),
]

RULES.insert(2, ('СЕРГЕЙ', r'#управлениенедвижимостью|#сагунто|#домвиспании|#инвестициивнедвижимость|#ремонтвиспании'))

# Метка в имени папки решает сразу («2 ВНЖ Статус и время», «1 СК Купить под сдачу»)
LABELS = [('ПАЛЬМА', 'ПУТЕШ'), ('ПУТЕШ', 'ПУТЕШ'), ('ВНЖ', 'ВНЖ'), ('АВТО', 'АВТО'), ('ПУТЬ', 'ПУТЬ'),
          ('РАБОТА', 'РАБОТА'), ('СК', 'СЕРГЕЙ'), ('ОБЪЕКТ', 'ОБЪЕКТЫ')]

def pick(title, folder=''):
    words = re.sub(r'^\s*\d+\s+(\d+\s+)?', '', folder or '').upper().split()
    for lab, key in LABELS:
        if words and words[0] == lab:
            return key
    t = (title or '').lower()
    rules = RULES
    if words and words[0] == 'НЕДВ':                     # недвижимость: выбираем только среди её плейлистов
        rules = [r for r in RULES if r[0] in ('СЕРГЕЙ', 'ОБЪЕКТЫ', 'ОКУПАС', 'АРЕНДА', 'СОБСТВ', 'ПОКУПКА')]
        rules = rules + [('АРЕНДА', r'аренд')] + [('ПОКУПКА', r'.')]
    for key, rx in rules:
        if re.search(rx, t):
            return 'ПЕНСИЯ' if key == 'ПЕНСИ' else key
    return 'ЖИЗНЬ'

def _norm(s):
    return re.sub(r'\W+', ' ', (s or '').splitlines()[0] if s else '').strip().lower()[:60]

def _from_file(folder):
    """Файл «плейлист.txt» в папке ролика (кладёт Claude при упаковке): ключ из PL или название плейлиста."""
    p = folder / 'плейлист.txt'
    if not p.exists():
        return None
    v = p.read_text(encoding='utf-8-sig').strip().upper()
    for k in PL:
        if v.startswith(k):
            return k
    names = {'ВНЖ': 'ВНЖ, ПМЖ', 'АРЕНДА': 'АРЕНДА В ИСПАНИИ', 'СОБСТВ': 'СДАТЬ И УПРАВЛЯТЬ', 'ОКУПАС': 'ОКУПАСЫ',
             'ПОКУПКА': 'ПОКУПКА И ПРОДАЖА', 'СЕРГЕЙ': 'ИНТЕРВЬЮ С СЕРГЕЕМ', 'ПЕНСИЯ': 'ПЕНСИЯ', 'АВТО': 'АВТО И ПДД',
             'ДЕНЬГИ': 'НАЛОГИ, БАНКИ', 'РАБОТА': 'РАБОТА', 'ЖИЗНЬ': 'ЖИЗНЬ В ИСПАНИИ', 'ПЕРЕЕЗД': 'ПЕРЕЕЗД',
             'ПУТЬ': 'МОЙ ПУТЬ', 'ПУТЕШ': 'ПУТЕШЕСТВИЯ', 'ОБЪЕКТЫ': 'МОИ ОБЪЕКТЫ'}
    for k, n in names.items():
        if v.startswith(n):
            return k
    return None

def remember(folder):
    """Вызывается из publish.py сразу после того, как ролик встал в Facebook.
    Запоминает плейлист по первой строке упаковки — когда ролик выйдет, run() положит его туда."""
    try:
        from common import read_pack
        text = read_pack(folder)
        key = _from_file(folder) or pick(folder.name + '\n' + text, folder.name)
        s = _state()
        s.setdefault('wait', {})[_norm(text)] = key
        s['wait'] = dict(list(s['wait'].items())[-60:])
        _save(s)
        log(f"плейлист FB: запомнил {key} — {folder.name}")
    except Exception as e:
        log(f"плейлист FB: не запомнил {folder.name}: {str(e)[:120]}")

# GraphQL-запросы «Панели автора» (doc_id сняты 25.10.2026; если Facebook их поменяет — придёт сбой)
Q_LIST = ('ProdashCometV2AddToPlaylistDialogPaginationQuery', '28403664409243547')
Q_ADD = ('ProdashCometAddToPlaylistMutation', '27570916245903032')

JS = r"""async ([name, doc, vars, actor]) => {
  const b = new URLSearchParams({av: actor, __user: actor, __a: '1', fb_dtsg: require('DTSGInitialData').token,
    fb_api_caller_class: 'RelayModern', fb_api_req_friendly_name: name, variables: JSON.stringify(vars),
    server_timestamps: 'true', doc_id: doc});
  const r = await fetch('/api/graphql/', {method: 'POST', body: b, credentials: 'include'});
  return (await r.text()).split('\n')[0];
}"""

class RateLimit(Exception):
    pass

def _gql(page, q, vars):
    j = json.loads(page.evaluate(JS, [q[0], q[1], vars, ACTOR]))
    if 'data' not in j:                                   # Facebook ответил ошибкой вместо данных
        errs = j.get('errors') or [{}]
        msg = '; '.join(f"{e.get('message', '?')} ({e.get('code', '')})" for e in errs)
        if any(e.get('code') == 1675004 or 'rate limit' in str(e.get('message', '')).lower() for e in errs):
            raise RateLimit(msg)
        raise RuntimeError('Facebook: ' + (msg if errs != [{}] else str(j)[:150]))
    return j

def _state():
    try: return json.loads(STATE.read_text(encoding='utf-8'))
    except Exception: return {'last': 0, 'done': {}, 'err_day': ''}

def _save(s):
    s['done'] = dict(list(s['done'].items())[-600:])
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding='utf-8')

def due():
    s = _state()
    h = datetime.datetime.now().hour
    return 9 <= h <= 23 and time.time() - s.get('last', 0) > EVERY_H * 3600

def run(page):
    """page — открытая страница Chrome робота (Facebook уже залогинен)."""
    s = _state()
    s['last'] = time.time(); _save(s)
    try:
        page.goto('https://www.facebook.com/professional_dashboard/content/playlists', wait_until='domcontentloaded')
        time.sleep(8)
        j = _gql(page, Q_LIST, {'after': None, 'first': 20, 'keyword': None, 'id': PAGE_ID})
        edges = j['data']['node']['prodash_content_library']['edges']
        put = 0
        for e in edges:
            n = e['node']
            if ':VK:' in n.get('id', ''):                 # копии в группах — не трогаем
                continue
            v = (n.get('story') or {}).get('video') or {}
            vid = v.get('id')
            if not vid or v.get('creator_playlist') or vid in s['done']:
                continue
            if v.get('unpublished_content_type') not in (None, 'PUBLISHED'):
                continue                                  # отложенные ещё не вышли — дойдём после выхода
            title = (n.get('title') or '').strip()
            key = s.get('wait', {}).pop(_norm(title), None) or pick(title)
            r = _gql(page, Q_ADD, {'video_ids': [vid], 'videolist_id': PL[key], 'connections': []})
            ok = bool(((r.get('data') or {}).get('xfb_add_videos_to_videolist') or {}).get('edges'))
            s['done'][vid] = f"{key} {'ok' if ok else 'нет'} {datetime.datetime.now():%d.%m %H:%M}"
            log(f"плейлист FB: {key if ok else 'НЕ ВСТАЛ ' + key} — {title.splitlines()[0][:70] if title else vid}")
            put += 1
            time.sleep(6)
        _save(s)
    except RateLimit as e:                                # временный лимит запросов — не сбой, повтор через час
        s['last'] = time.time() - (EVERY_H - 1) * 3600; _save(s)
        log(f"плейлист FB: Facebook просит паузу ({str(e)[:80]}), повторю через час")
    except Exception as e:
        log(f"плейлист FB: сбой {str(e)[:150]}")
        today = time.strftime('%Y-%m-%d')
        if s.get('err_day') != today:
            s['err_day'] = today; _save(s)
            tg(f"Робот-публикатор: не смог разложить новые рилсы FB по плейлистам ({str(e)[:150]}). Скажи Claude")

def maybe_run():
    """Вызывается из publish.py после основных заданий. Отдельный короткий запуск Chrome робота."""
    if not due():
        return
    if LOCK.exists() and time.time() - LOCK.stat().st_mtime < 3 * 3600:
        return                                            # робот сейчас публикует — в следующий раз
    import os
    LOCK.write_text(str(os.getpid()))
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                str(PROFILE), channel='chrome', headless=False, locale='ru-RU',
                viewport={'width': 1400, 'height': 900},
                args=['--start-minimized', '--disable-blink-features=AutomationControlled'],
                ignore_default_args=['--enable-automation'])
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.set_default_timeout(60000)
            run(page)
            ctx.close()
    finally:
        LOCK.unlink(missing_ok=True)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':          # py fb_playlists.py test "название" — проверить правило
        print(pick(' '.join(sys.argv[2:])))
    else:
        s = _state(); s['last'] = 0; _save(s)
        maybe_run()
