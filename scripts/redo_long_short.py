#!/usr/bin/env python3
"""Лёгкая переделка шортса из горизонтального лонга (слайд + камера, «ШОРТС ВНЖ после защиты»), 22.10.2026.
python3 redo_long_short.py in.mp4 обложка.jpg out.mp4 "Полное видео на YouTube" "ссылка в шапке профиля"
- отрезает последнюю 1,0 с — приклеенное «Всё, пошёл работать» (build.py клеил его ровно 1,0 с);
- старый призыв в верхней полосе закрывается фоном полосы, вместо него белая карточка нового стиля;
- обложка первым кадром на 0,15 с (TikTok через автопубликатор берёт кадр с 0 с)."""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, COVER, OUT, TEXT, LABEL = sys.argv[1:6]
END_SEC = float(os.environ.get('END_SEC', '1.0'))
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts') + '/'
TMP = os.path.dirname(os.path.abspath(OUT))

def probe(*a): return subprocess.run(['ffprobe', '-v', 'error', *a, '-of', 'csv=p=0', SRC], capture_output=True, text=True).stdout.strip()
dur = float(probe('-show_entries', 'format=duration'))
fps = probe('-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate')
total = dur - END_SEC

def shadow_wrap(img, rad=14, off=(0, 8), alpha=90):
    pad = rad * 2 + max(abs(off[0]), abs(off[1]))
    big = Image.new('RGBA', (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new('RGBA', img.size, (0, 0, 0, 255)); sh.putalpha(a)
    big.paste(sh, (pad + off[0], pad + off[1]), sh)
    big = big.filter(ImageFilter.GaussianBlur(rad)); big.alpha_composite(img, (pad, pad))
    return big

# белая карточка как в overlay.py (призыв нового стиля): метка на красной плашке, текст чёрный
f = ImageFont.truetype(F + 'montserrat-900.ttf', 54); lf = ImageFont.truetype(F + 'montserrat-900.ttf', 22)
lw = int(lf.getlength(LABEL.upper())) + 26
cw = int(max(f.getlength(TEXT), lw + 4) + 56); ch = 58 + 40 + 44
im = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.rounded_rectangle([0, 0, cw - 1, ch - 1], 26, fill=(255, 255, 255, 250))
d.rounded_rectangle([(cw - lw) // 2, 22, (cw + lw) // 2, 54], 16, fill=(150, 30, 40))
d.text((cw // 2, 38), LABEL.upper(), font=lf, fill='white', anchor='mm')
d.text((cw // 2, 22 + 42 + 29), TEXT, font=f, fill=(18, 18, 22), anchor='mm')
card = shadow_wrap(im); card.save(f'{TMP}/cta_card.png')
cx, cy = (1080 - card.width) // 2, 150 - card.height // 2
Image.open(COVER).convert('RGB').resize((1080, 1920), Image.LANCZOS).save(f'{TMP}/cover_full.png')

t0 = total - 4.0   # старый призыв висел последние 5 с вместе с «пошёл работать», после обрезки — последние 4 с
vf = (f"[0:v]trim=0:{total:.3f},setpts=PTS-STARTPTS,"
      f"drawbox=x=0:y=0:w=1080:h=300:color=0x0E1A2A:t=fill:enable='gte(t,{t0 - 0.1:.3f})'[v];"
      f"[1:v]format=rgba,fade=t=in:st={t0:.3f}:d=0.15:alpha=1[c];"
      f"[v][c]overlay={cx}:{max(0, cy)}:enable='gte(t,{t0:.3f})'[v2];"
      f"[v2][2:v]overlay=0:0:enable='lt(t,0.15)',format=yuv420p[vo];"
      f"[0:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={total - 0.03:.3f}:d=0.03[ao]")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-loop', '1', '-framerate', fps, '-t', f'{total:.3f}', '-i', f'{TMP}/cta_card.png',
                '-loop', '1', '-framerate', fps, '-t', '0.5', '-i', f'{TMP}/cover_full.png',
                '-filter_complex', vf, '-map', '[vo]', '-map', '[ao]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-profile:v', 'high',
                '-maxrate', '25M', '-bufsize', '50M', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', OUT], check=True)
print('ok', OUT, f'{dur:.2f} -> {total:.2f} с')
