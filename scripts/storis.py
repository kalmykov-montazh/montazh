#!/usr/bin/env python3
"""Сторис: куски сырого с разной скоростью + одна надпись на весь ролик (21.10.2026).
python storis.py raw.mp4 '[[19.5,28.5,4],[28.5,61,1]]' 'Строка 1|Строка 2|Строка 3' 230 final.mp4"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

RAW, SEGS, LINES, Y, OUT = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3].split('|'), int(sys.argv[4]), sys.argv[5]
D = os.path.dirname(os.path.abspath(__file__))
F = lambda n, s: ImageFont.truetype(f'{D}/../fonts/montserrat-{n}.ttf', s)
W, H = 1080, 1920

trc = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=color_transfer',
                      '-of', 'csv=p=0', RAW], capture_output=True, text=True).stdout.strip()
# тот же перевод HDR в обычную картинку, что в montage.py (сверено 04.10.2026)
TM = ('zscale=t=linear:npl=250,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=2,'
      'zscale=t=bt709:m=bt709:r=tv,format=yuv420p,eq=contrast=1.06:saturation=1.15,') if trc in ('arib-std-b67', 'smpte2084') else ''

# надпись
im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
y = Y
if LINES and LINES[0].strip():
    f = F(900, 68); t = LINES[0].strip(); b = d.textbbox((0, 0), t, font=f)
    tw, th = b[2] - b[0], b[3] - b[1]; px, py = 38, 26
    x0 = (W - tw) // 2 - px
    d.rounded_rectangle([x0, y, x0 + tw + 2 * px, y + th + 2 * py], 26, fill=(255, 255, 255, 250))
    d.text(((W - tw) // 2 - b[0], y + py - b[1]), t, font=f, fill=(18, 18, 22))
    y += th + 2 * py + 18
if len(LINES) > 1 and LINES[1].strip():
    f = F(800, 42); t = LINES[1].strip(); b = d.textbbox((0, 0), t, font=f)
    tw, th = b[2] - b[0], b[3] - b[1]; px, py = 26, 14
    x0 = (W - tw) // 2 - px
    d.rounded_rectangle([x0, y, x0 + tw + 2 * px, y + th + 2 * py], (th + 2 * py) // 2, fill=(225, 30, 40, 245))
    d.text(((W - tw) // 2 - b[0], y + py - b[1]), t, font=f, fill=(255, 255, 255))
    y += th + 2 * py + 16
if len(LINES) > 2 and LINES[2].strip():
    f = F(800, 44); t = LINES[2].strip(); b = d.textbbox((0, 0), t, font=f)
    tw = b[2] - b[0]
    d.text(((W - tw) // 2 - b[0], y - b[1]), t, font=f, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0, 200))
im.save('text.png')

n = len(SEGS)
fc = [f'[0:v]{TM}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps=30,split={n}' + ''.join(f'[s{i}]' for i in range(n)),
      f'[0:a]asplit={n}' + ''.join(f'[r{i}]' for i in range(n))]
for i, (s, e, sp) in enumerate(SEGS):
    fc.append(f'[s{i}]trim={s}:{e},setpts=(PTS-STARTPTS)/{sp}[v{i}]')
    at = []
    k = float(sp)
    while k > 2.0: at.append('atempo=2.0'); k /= 2.0
    if abs(k - 1) > 1e-3: at.append(f'atempo={k:.4f}')
    vol = ',volume=0.6' if float(sp) > 1 else ''
    fc.append(f'[r{i}]atrim={s}:{e},asetpts=PTS-STARTPTS' + ''.join(',' + a for a in at) + f'{vol}[a{i}]')
fc.append(''.join(f'[v{i}][a{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=1[cv][ca]')
fc.append('[1:v]format=rgba,fade=in:st=0:d=0.4:alpha=1[tx]')
fc.append('[cv][tx]overlay=0:0:shortest=1,format=yuv420p[ov]')
cmd = ['ffmpeg', '-v', 'error', '-y', '-i', RAW, '-loop', '1', '-framerate', '30', '-i', 'text.png',
       '-filter_complex', ';'.join(fc), '-map', '[ov]', '-map', '[ca]',
       '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
       '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
       '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT]
subprocess.run(cmd, check=True)
print('сторис', OUT, 'цвет', trc or 'sdr', 'кусков', n)
