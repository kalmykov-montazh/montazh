"""Проверка начала ролика (первые 3–5 секунд) — по «ДНК хитов» 10.11.2026.

Запуск: python scripts/proverka_nachala.py words.json [novyj.json] [video.mp4]
  words.json — слова ролика [{"w","s","e"}] (osnova_words.json / words.json)
  novyj.json — настройки ролика (надпись в начале и обложка), необязательно
  video.mp4  — готовый ролик, для проверки «срезан первый слог», необязательно
Печатает JSON: {"ok": bool, "warns": [...], "first": "первые слова"}.
Код выхода всегда 0 — проверка не останавливает монтаж, только пишет замечания.
"""
import json, re, subprocess, sys

BAD_START = {'также', 'и', 'там', 'вот', 'ну', 'так', 'следующая', 'следующий', 'следующее', 'ещё', 'еще',
             'кстати', 'дальше', 'потом', 'начинаю', 'продолжаем', 'поэтому', 'то', 'короче', 'значит',
             'остальные'}
# «А вы знали», «А вы замечали», «А кто докажет» — у хитов, поэтому «а» плохо только без вопроса к зрителю
OK_AFTER_A = {'вы', 'кто', 'что', 'если', 'знаете', 'вам', 'вас', 'ваш', 'ваша'}
SELF_STORY = ['мы приехали', 'я приехал', 'моё первое', 'мое первое', 'когда мы', 'в прошлом году',
              'я начал', 'мы пошли', 'мы подавались', 'у меня в']
DEFIN = ['то есть', 'это называется', 'называется']
HOOK = re.compile(r'\d|\bвы\b|\bвам\b|\bвас\b|\bваш|испани|валенси|валенц|мадрид|барселон|штраф|евро|налог|закон|'
                  r'внж|пенси|аренд|квартир|банк|тысяч|сотн|процент|полиц|документ|\bтie\b|\btie\b|'
                  r'один|одна|два|две|три|трет|пять|десят|двадцат|сто\b|половин|машин|топлив|работ|детей|ребён|ребен|школ', re.I)
TOPIC = re.compile(r'букинг|букинх|отел|авиабилет|билет|стрим|подписчик|instagram|facebook|youtube|ютуб|блог|лонг', re.I)
NUMW = re.compile(r'\d|тысяч|процент|половин|вдвое|\bдва\b|\bтри\b|пять|десят|сто\b', re.I)


def load_words(p):
    d = json.load(open(p, encoding='utf-8'))
    out = []
    for x in d:
        if isinstance(x, dict):
            w = x.get('w') or x.get('word') or x.get('text') or ''
            s = x.get('s', x.get('start', 0))
        else:
            s, w = x[0], x[1]
        w = str(w).strip()
        if w:
            out.append((float(s), w))
    return out


def clean(w):
    return re.sub(r'[^\wё-]', '', w.lower())


def cut_syllable(video, t0):
    """Громкость первых 40 мс речи против следующих 200 мс: старт сразу на полной громкости — слог, скорее всего, срезан."""
    def rms(a, d):
        r = subprocess.run(['ffmpeg', '-hide_banner', '-ss', f'{a:.3f}', '-t', f'{d:.3f}', '-i', video,
                            '-af', 'astats=metadata=0:reset=0', '-f', 'null', '-'], capture_output=True, text=True).stderr
        m = re.findall(r'RMS level dB:\s*(-?[\d.]+|-inf)', r)
        v = [float(x) for x in m if x != '-inf']
        return max(v) if v else -99.0
    a, b = rms(max(0, t0), 0.04), rms(max(0, t0) + 0.04, 0.2)
    return a > -28 and a > b - 4, a, b


def main():
    words = load_words(sys.argv[1])
    nov = json.load(open(sys.argv[2], encoding='utf-8')) if len(sys.argv) > 2 and sys.argv[2].endswith('.json') else {}
    video = next((a for a in sys.argv[2:] if a.endswith('.mp4')), None)
    warns = []
    if not words:
        print(json.dumps({'ok': False, 'warns': ['нет слов — проверить распознавание'], 'first': ''}, ensure_ascii=False))
        return
    t0 = words[0][0]
    w8 = [clean(w) for _, w in words[:8]]
    first = ' '.join(w for s, w in words if s < 5.0)
    head = ' '.join(w8)

    if t0 > 0.3:
        warns.append(f'пауза до первого слова {t0:.2f} с — срезать до 0,3')
    if w8[0] in BAD_START or (w8[0] == 'а' and (len(w8) < 2 or w8[1] not in OK_AFTER_A)):
        warns.append(f'начало с середины мысли («{" ".join(w for _, w in words[:3])}») — старт с первой законченной фразы или переходник-хук')
    if any(head.startswith(p) or f' {p}' in ' '.join(w8[:5]) for p in SELF_STORY):
        warns.append('начало — хронология о себе; хиты начинаются с ситуации зрителя')
    if any(p in ' '.join(w8[:5]) for p in DEFIN):
        warns.append('начало с определения («это…, то есть…») — сначала удар: цифра, угроза, парадокс')
    if not HOOK.search(head):
        warns.append('в первых 8 словах нет ни цифры, ни «вы», ни Испании, ни денег/штрафа — фраза может не зацепить')

    if TOPIC.search(first):
        warns.append('тема с потолком в TikTok (билеты, отели, блог, соцсети: 50–59% при любой фразе) — не в основную сетку')

    # надпись в начале и обложка: следствие или вопрос, а не ярлык темы
    texts = []
    t = nov.get('title') or {}
    texts += [t.get('stamp', '')] + list(t.get('cards', []) or [])
    c = nov.get('cover') or {}
    cover = ' '.join([c.get('top', ''), c.get('bot', '')]).replace('|', ' ').strip()
    if cover:
        n = len(cover.split())
        if n <= 2 and '?' not in cover and not re.search(r'\d', cover):
            warns.append(f'обложка-ярлык «{cover}» — нужна следствие или вопрос («СТРАХОВАЯ ТЯНЕТ С ВЫПЛАТОЙ?»)')

    # срезанный первый слог: первое слово не похоже на русское слово («Раховая» вместо «Страховая»)
    try:
        import pymorphy3
        mw = clean(words[0][1])
        ma = pymorphy3.MorphAnalyzer()
        ab = 'абвгдеёжзийклмнопрстуфхцчшщыэюя'
        def chopped(x):
            if ma.word_is_known(x):
                return False
            return any(ma.word_is_known(a + x) for a in ab) or any(ma.word_is_known(a + b + x) for a in ab for b in ab)
        if re.fullmatch(r'[а-яё]{3,}', mw) and chopped(mw):
            warns.append(f'первое слово «{words[0][1]}» не похоже на слово — возможно, срезан первый слог; послушать первую секунду')
    except ImportError:
        pass

    print(json.dumps({'ok': not warns, 'warns': warns, 'first': first}, ensure_ascii=False))


if __name__ == '__main__':
    main()
