# 15.11.2026 (Евгений: «собери максимум до „На проверке“, публиковать ничего не нужно»):
# новые карусели из фото-архива «Брокер/Посты/Фото» + рилс к каждой — только сборка и выкладка на проверку.
#   python3 scripts/karusel/novye_pachka.py karuseli/novye_1511/pachka.json
# Для каждой: фото с Диска → (panel: вырезать табличку/витрину и положить на размытый фон сверху) →
# slajdy.py (крупный текст) → slajdshou.py (музыка, трек из "trek") →
# «Брокер/На проверке/Рилсы из каруселей/<name>/»: 01..NN.jpg, reel.mp4, spec.json, _текст.txt, _музыка.txt.
# Для проверки Claude: pics/<name>_слайды.jpg (все слайды) и pics/<name>_рилс.jpg (5 кадров).
import json, sys, os, subprocess, pathlib
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[2]
W, H = 1080, 1350
DST = 'montazh:Брокер/На проверке/Рилсы из каруселей'
PICS = pathlib.Path('pics'); PICS.mkdir(exist_ok=True)


def sh(*a):
    p = subprocess.run(a, capture_output=True, text=True)
    return (p.stdout + p.stderr).strip()


def panel(src, box, out):
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    w, h = im.size
    cr = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    bg = ImageOps.fit(im, (W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    sc = min(1000 / cr.width, 860 / cr.height)
    cr = cr.resize((int(cr.width * sc), int(cr.height * sc)), Image.LANCZOS)
    bg.paste(cr, ((W - cr.width) // 2, 60 + (860 - cr.height) // 2))
    bg.save(out, quality=94)


def sheet(files, out, tw=270):
    ims = [Image.open(f) for f in files]
    th = int(tw * ims[0].height / ims[0].width)
    cols = 5; rows = (len(ims) + cols - 1) // cols
    s = Image.new('RGB', (cols * tw, rows * th), 'white')
    for i, im in enumerate(ims):
        s.paste(im.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    s.save(out, quality=85)


cfg = json.load(open(sys.argv[1], encoding='utf-8'))
for k in cfg:
    name = k['name']; D = pathlib.Path('nk') / name; D.mkdir(parents=True, exist_ok=True)
    try:
        need = sorted({s['photo'] for s in k['slides']})
        (D / '_need.txt').write_text('\n'.join(need), encoding='utf-8')
        sh('rclone', 'copy', 'montazh:Брокер/Посты/Фото', str(D / 'src'), '--files-from', str(D / '_need.txt'))
        slides = []
        for i, s in enumerate(k['slides'], 1):
            s = dict(s); src = D / 'src' / s['photo']
            if not src.exists(): raise RuntimeError('нет фото ' + s['photo'])
            if s.get('panel'):
                p = D / 'src' / f'p_{i:02d}.jpg'; panel(src, s.pop('panel'), p); s['photo'] = 'src/' + p.name
            else:
                s['photo'] = 'src/' + s['photo']
            slides.append(s)
        spec = {'plashka': k.get('plashka', ''), 'slides': slides}
        (D / 'spec.json').write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding='utf-8')
        print(name, sh('python3', str(ROOT / 'scripts/karusel/slajdy.py'), str(D / 'spec.json'), str(D))[-200:])
        print(name, sh('python3', str(ROOT / 'scripts/karusel/slajdshou.py'), str(D), str(D / 'reel.mp4'),
                       '--trek', str(int(k.get('trek', 1)) - 1))[-300:])
        (D / '_текст.txt').write_text(k['text'], encoding='utf-8')
        nums = sorted(D.glob('[0-9][0-9].jpg'))
        sheet(nums, PICS / f'{name}_слайды.jpg')
        v = D / 'reel.mp4'
        dur = float(sh('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(v)) or 0)
        n = int(dur * 30)
        sel = '+'.join(f'eq(n\\,{x})' for x in (15, n // 3, 2 * n // 3, n - 40, n - 3))
        sh('ffmpeg', '-loglevel', 'error', '-y', '-i', str(v), '-vf', f"select='{sel}',scale=216:384,tile=5x1",
           '-frames:v', '1', '-update', '1', str(PICS / f'{name}_рилс.jpg'))
        vol = sh('ffmpeg', '-hide_banner', '-i', str(v), '-af', 'volumedetect', '-f', 'null', '-')
        vol = ' '.join(l.split('] ')[-1] for l in vol.splitlines() if 'mean_volume' in l)
        for f in nums + [v, D / 'spec.json', D / '_текст.txt', D / '_музыка.txt']:
            if f.exists(): sh('rclone', 'copyto', str(f), f'{DST}/{name}/{f.name}')
        print(f'ИТОГ {name}: слайдов {len(nums)}, рилс {dur:.1f} с, {vol}')
    except Exception as ex:
        print(f'ОШИБКА {name}: {ex}')
print(sh('rclone', 'lsf', '-R', DST))
