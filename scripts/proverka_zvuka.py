# Проверка готового ролика на слух второй программой (Евгений 04.11.2026, ролик «Соцслужбы и мелочи»):
# whisper при монтаже «съедает» повторённые фразы — дубль оставался в звуке, а субтитров на нём не было
# («ударился ребёнок… ударился ребёнок», «ссорьтесь потише… ссорьтесь потише»).
# Здесь звук готового ролика слушает GigaAM v2 (русская модель Сбера, sherpa-onnx) независимо от субтитров и ищет:
#   ПОВТОР      — одна и та же фраза из 2+ слов подряд два раза в пределах нескольких секунд
#   БЕЗ ТИТРОВ  — речь, на которой нет субтитров (если передан words_out.json)
#   НАЧАЛО      — первое слово обрезано: голос уже громкий в первом кадре звука
# Запуск: python3 proverka_zvuka.py ролик.mp4 [words_out.json] [папка модели]
# Код выхода 1 — есть находки (ролик слушать и чинить), 0 — чисто.
import sys, os, re, json, subprocess, wave
import numpy as np

MODEL = sys.argv[3] if len(sys.argv) > 3 else os.environ.get('GIGAAM', 'gigaam')
SR = 16000

def load(video):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def recognizer():
    import sherpa_onnx
    d = MODEL
    return sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=f'{d}/encoder.int8.onnx', decoder=f'{d}/decoder.onnx', joiner=f'{d}/joiner.onnx',
        tokens=f'{d}/tokens.txt', model_type='nemo_transducer')

def words_of(r, a):
    # куски по ~6 с, режем в самом тихом месте последних 1,5 с; слова собираем из букв с таймингами
    out = []; pos = 0; n = len(a)
    while pos < n:
        end = min(n, pos + 6 * SR)
        if end < n:
            lo = end - int(1.5 * SR); fr = 400
            en = [np.abs(a[i:i + fr]).mean() for i in range(lo, end - fr, fr)]
            end = lo + int(np.argmin(en)) * fr + fr // 2
        s = r.create_stream(); s.accept_waveform(SR, a[pos:end]); r.decode_stream(s)
        cur = None
        for ch, t in zip(s.result.tokens, s.result.timestamps):
            t = pos / SR + t
            if ch.strip() == '':
                if cur: out.append(cur); cur = None
                continue
            if cur is None: cur = {'w': '', 's': t, 'e': t}
            cur['w'] += ch; cur['e'] = t + 0.04
        if cur: out.append(cur)
        pos = end
    return out

NUMW = re.compile(r'^(ноль|один|одна|одно|два|две|три|четыр|пят|шест|сем|восем|девят|десят|одиннадцат|двенадцат|двадцат|тридцат|сорок|пятьдесят|шестьдесят|семьдесят|восемьдесят|девяност|сто|двест|трист|четырест|пятьсот|шестьсот|семьсот|восемьсот|девятьсот|тысяч|миллион|евро|цент|процент|год|градус|раз|первого|второго|тре|четверт|пято|шесто|седьмо|восьмо|девято|половин)')
FILLER = {'и', 'а', 'да', 'ну', 'вот', 'это', 'э', 'то', 'так'}
def is_num(w): return bool(NUMW.match(w))

def norm(w):
    return re.sub(r'[^\w]', '', w.lower().replace('ё', 'е'))

def main():
    video = sys.argv[1]
    wo = json.load(open(sys.argv[2], encoding='utf-8')) if len(sys.argv) > 2 and sys.argv[2] and os.path.exists(sys.argv[2]) else None
    a = load(video); r = recognizer(); ws = words_of(r, a)
    bad = []
    print('СЛЫШНО:', ' '.join(w['w'] for w in ws))

    # 1. повторы: одинаковые 2–4 слова подряд, второй раз начинается не позже 5 с после первого
    toks = [norm(w['w']) for w in ws]
    seen = set()
    for n in (4, 3, 2):
        for i in range(len(toks) - n):
            g = toks[i:i + n]
            if any(len(x) < 2 for x in g) or sum(len(x) for x in g) < 8: continue
            if sum(is_num(x) for x in g) >= len(g) - 1: continue   # «тысяча сто… тысяча сто семьдесят», «пять евро… тридцать пять евро» — числа, не дубль
            # дубль — второй раз сразу следом, между ними максимум одно «и/а/да/ну/вот» (риторика «через месяц выселю, через месяц…» — не дубль)
            for j in range(i + n, min(len(toks) - n + 1, i + n + 2)):
                if j > i + n and toks[i + n] not in FILLER: continue
                if toks[j:j + n] == g and ws[j]['s'] - ws[i]['s'] < 5 and (i, j) not in seen:
                    # «нужны, нужны» и подобное — одно слово, сюда не попадает (n ≥ 2)
                    seen.update((i + k, j + k) for k in range(n))
                    ctx = ' '.join(w['w'] for w in ws[max(0, i - 3):j + n + 3])
                    bad.append(f"ПОВТОР {ws[i]['s']:.1f} с и {ws[j]['s']:.1f} с: «{' '.join(w['w'] for w in ws[i:i + n])}» … {ctx}")

    # 2. речь без субтитров (дубль, который whisper не записал)
    if wo:
        cov = [(w['s'] - 0.35, w['e'] + (0.9 if re.search(r'[A-Za-z]', w['w']) else 0.35)) for w in wo]
        run = []
        def flush():
            if len(run) >= 2 and run[-1]['e'] - run[0]['s'] > 0.4:
                bad.append(f"БЕЗ ТИТРОВ {run[0]['s']:.1f}–{run[-1]['e']:.1f} с: «{' '.join(w['w'] for w in run)}»")
        for w in ws:
            m = (w['s'] + w['e']) / 2
            if any(x <= m <= y for x, y in cov):
                flush(); run = []
            else:
                run.append(w)
        flush()

    # 3. начало: голос не должен начинаться в первые 0,08 с звука (обложка идёт 0,15 с — её не считаем)
    fr = int(0.02 * SR)
    rms = np.array([np.sqrt((a[i:i + fr] ** 2).mean() + 1e-12) for i in range(0, min(len(a), 3 * SR) - fr, fr)])
    if len(rms):
        db = 20 * np.log10(rms + 1e-9); peak = np.percentile(db, 95)
        on = next((k for k, v in enumerate(db) if v > peak - 18), None)
        if on is not None:
            print(f'Голос с {on * 0.02:.2f} с (пик {peak:.0f} дБ)')
            if on * 0.02 < 0.02:   # 05.11.2026: ролик начинается прямо со слова (запас 0,05 с), тревога — только голос с первого кадра
                bad.append(f'НАЧАЛО: голос громкий уже с {on * 0.02:.2f} с — первое слово, скорее всего, обрезано')
    if wo and ws:
        f1, g1 = norm(wo[0]['w']), norm(ws[0]['w'])
        if f1 and g1 and f1 != g1 and not f1.endswith(g1) and not g1.endswith(f1):
            print(f'Первое слово: в субтитрах «{wo[0]["w"]}», слышно «{ws[0]["w"]}»')

    for b in bad: print(b)
    if not bad: print('ЧИСТО')
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
