# Сторис в Instagram (@kalmykov.rieltor.valencia, Blotato 80093) — для задачи «Instagram: сторис для Актуального».
# Запуск через blotato-api.yml (там уже есть api() и rclone с remote «montazh:»). Код запроса, например:
#   SRC = 'Брокер/Опубликованные/Шортсы/Октябрь 2026/3 ЖИЗНЬ Стаж для пенсии/!!! ЖИЗНЬ Стаж для пенсии.mp4'
#   DRY = True          # True — только подготовить и показать, False — выложить
#   exec(open('scripts/storis_ig.py', encoding='utf-8').read())
# Ограничение Meta для сторис: видео 3–60 с, до 100 МБ, подпись не поддерживается (text пустой).
# До 66 с — чуть ускоряем целиком; длиннее — режем на части по 59 с и выкладываем по очереди (как телефон).
import json, math, subprocess, time, urllib.request

ACC = '80093'
SRC = globals().get('SRC')
DRY = globals().get('DRY', True)
assert SRC, 'нужен SRC — путь к ролику внутри «Монтаж!»'


def sh(cmd):
    r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout)[-800:])
    return r.stdout


if subprocess.run('which ffmpeg', shell=True, capture_output=True).returncode:
    sh('sudo apt-get update -qq >/dev/null && sudo apt-get install -y -qq ffmpeg >/dev/null')
sh(['rclone', 'copyto', f'montazh:{SRC}', 'src.mp4'])
dur = float(sh(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', 'src.mp4']).strip())
VF = 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30'
parts = []
if dur <= 59.5:
    sh(['ffmpeg', '-v', 'error', '-y', '-i', 'src.mp4', '-vf', VF, '-c:v', 'libx264', '-crf', '23', '-preset', 'veryfast',
        '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', 'p1.mp4'])
    parts = ['p1.mp4']
elif dur <= 66:
    k = dur / 59.0
    sh(['ffmpeg', '-v', 'error', '-y', '-i', 'src.mp4', '-filter:v', f'setpts=PTS/{k},{VF}', '-filter:a', f'atempo={k}',
        '-c:v', 'libx264', '-crf', '23', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', 'p1.mp4'])
    parts = ['p1.mp4']
else:
    n = math.ceil(dur / 59.0)
    step = dur / n
    for i in range(n):
        out = f'p{i + 1}.mp4'
        sh(['ffmpeg', '-v', 'error', '-y', '-ss', f'{i * step:.2f}', '-t', f'{step:.2f}', '-i', 'src.mp4', '-vf', VF,
            '-c:v', 'libx264', '-crf', '23', '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out])
        parts.append(out)

info = []
for p in parts:
    d = float(sh(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).strip())
    mb = round(int(sh(['stat', '-c', '%s', p]).strip()) / 1e6, 1)
    info.append(f'{p}: {d:.1f} с, {mb} МБ')
print(f'Исходник {dur:.1f} с → частей {len(parts)}: ' + '; '.join(info))

if DRY:
    print('ПРОБА: ничего не выложено')
else:
    for p in parts:
        s, up = api('POST', '/media/uploads', {'filename': 'video.mp4'})
        r = urllib.request.Request(up['presignedUrl'], data=open(p, 'rb').read(), method='PUT', headers={'Content-Type': 'video/mp4'})
        urllib.request.urlopen(r, timeout=1800).read()
        s, res = api('POST', '/posts', {'post': {'accountId': ACC, 'content': {'text': '', 'mediaUrls': [up['publicUrl']], 'platform': 'instagram'},
                                                  'target': {'targetType': 'instagram', 'mediaType': 'story'}}})
        pid = res.get('postSubmissionId')
        st = None
        for _ in range(60):                       # ждём, пока выйдет, — чтобы части шли по порядку
            time.sleep(10)
            try:
                s, st = api('GET', f'/posts/{pid}')
            except Exception as e:
                st = {'status': f'ошибка опроса: {e}'}
            if (st or {}).get('status') in ('published', 'failed'):
                break
        print(f'{p}: id {pid}, статус {(st or {}).get("status")}, {(st or {}).get("publicUrl") or (st or {}).get("errorMessage") or ""}')
        if (st or {}).get('status') != 'published':
            print('СТОП: часть не вышла, следующие не выкладываю')
            break
