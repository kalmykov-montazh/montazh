# Постановка роликов в Blotato из облака (решение Евгения 07.11 и 11.11.2026).
# Instagram, TikTok, YouTube, Threads. Facebook НЕ трогает (только робот на компьютере).
# Логику берёт из компьютерного Общее/Робот/blotato.py (schedule(): тексты, обложки, плейлисты, TikTok с обложкой).
# Кто ставит — решает рубильник «_задания/_blotato_облако_вкл.txt» (пишет Claude):
#   есть рубильник И компьютер подтвердил («_blotato_облако_принял.txt» с тем же словом, старше 5 минут) → ставит облако;
#   иначе облако ничего не ставит. Откат — удалить рубильник, компьютер сразу ставит сам.
# Облако НИКОГДА не пишет _blotato.json компьютера. Своё пишет в «_blotato_облако.json»,
# компьютер оттуда забирает записи к себе (_adopt_cloud) и дальше проверяет и архивирует как обычно.
# X, Bluesky, LinkedIn остаются на компьютере: они берут уже загруженное видео из _blotato.json.
import json, sys, os, subprocess, pathlib, datetime, importlib, copy, time

Q = 'montazh:Брокер/К публикации/_задания'
PUBR = 'montazh:Брокер/К публикации'
W = pathlib.Path('work').resolve()

def rc(*a, check=True):
    return subprocess.run(['rclone', *a], capture_output=True, text=True, check=check).stdout

def rc_json(path, default):
    try:
        t = rc('cat', path, check=False)
        return json.loads(t.lstrip('﻿')) if t.strip() else default
    except Exception:
        return default

def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ''          # «проверка» — только показать, что поставил бы
    sw = rc('cat', f'{Q}/_blotato_облако_вкл.txt', check=False).strip()
    if not sw:
        print('рубильник выключен — ставит компьютер'); return
    ack_ls = rc('lsjson', f'{Q}/_blotato_облако_принял.txt', check=False)
    ack = rc('cat', f'{Q}/_blotato_облако_принял.txt', check=False).strip()
    if ack != sw:
        print('компьютер ещё не подтвердил рубильник — жду'); return
    try:
        mt = datetime.datetime.fromisoformat(json.loads(ack_ls)[0]['ModTime'].replace('Z', '+00:00')[:26] + '+00:00')
        if datetime.datetime.now(datetime.timezone.utc) - mt < datetime.timedelta(minutes=5):
            print('подтверждение свежее (<5 мин) — жду, пока Диск досинхронизирует'); return
    except Exception as ex:
        print('время подтверждения не прочитал:', ex)

    R = W / 'Общее' / 'Робот'; R.mkdir(parents=True, exist_ok=True)
    for f in ('blotato.py', 'common.py', 'telegram_ключ.txt.txt'):
        rc('copyto', f'montazh:Общее/Робот/{f}', str(R / f), check=False)
    (R / 'blotato_ключ.txt').write_text(open('key.txt', encoding='utf-8-sig').read().strip(), encoding='utf-8')
    QL = W / 'Брокер' / 'К публикации' / '_задания'; QL.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(R))
    common = importlib.import_module('common')
    b = importlib.import_module('blotato')

    plan = rc_json(f'{Q}/_план.json', {})
    pc = rc_json(f'{Q}/_blotato.json', {})
    cloud = rc_json(f'{Q}/_blotato_облако.json', {})
    (QL / '_план.json').write_text(json.dumps(plan, ensure_ascii=False), encoding='utf-8')

    today = datetime.date.today().isoformat()
    todo = [n for n, v in plan.items() if v.get('platform', 'fb') == 'fb' and v.get('date', '') >= today
            and n not in pc and n not in cloud]
    print('к постановке:', todo or 'ничего')
    if not todo or only == 'проверка':
        return
    for n in todo:                                            # только нужное: готовое видео, упаковка, обложка
        d = W / 'Брокер' / 'К публикации' / n
        rc('copy', f'{PUBR}/{n}', str(d), '--include', '!!!*.mp4', '--include', 'упаковка.txt',
           '--include', 'обложка.jpg', check=False)

    logs = []
    def log(m):
        print('журнал:', m); logs.append(f"{datetime.datetime.now():%Y-%m-%d %H:%M} {m}")
        if m.startswith(('ОШИБКА', 'ПРОПУСК', 'СБОЙ')):
            common.tg('Робот-публикатор (облако): ' + m)
    common.log = log; b.log = log

    s = copy.deepcopy(pc)
    for n, e in cloud.items():
        s.setdefault(n, e)
    skip = set(pc) | set(cloud)                               # чужие записи облако не трогает и не пишет

    def save(st):
        out = rc_json(f'{Q}/_blotato_облако.json', {})
        for n, e in st.items():
            if n.startswith('_') or n in skip or not isinstance(e, dict):
                continue
            e['_облако'] = True
            if logs: e['_журнал'] = logs[-5:]
            out[n] = e
        p = W / 'oblako.json'; p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
        rc('copyto', str(p), f'{Q}/_blotato_облако.json')
    b._save = save
    b.schedule(open('key.txt', encoding='utf-8-sig').read().strip(), s)
    print('готово, в журнале:', *logs, sep='\n  ')

if __name__ == '__main__':
    main()
