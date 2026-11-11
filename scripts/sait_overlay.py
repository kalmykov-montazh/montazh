#!/usr/bin/env python3
# 11.11.2026, решение Евгения: окошко сайта (пункт 13 главной версии монтажа) — в уже готовые ролики из «Готовых»,
# которые робот ещё не расставил. Ролик НЕ пересобирается: окошко накладывается поверх готового видео,
# всё остальное (монтаж, плашки, субтитры, обложка, звук) остаётся как было.
# Вид — как .sait в hf/auto.css: белая карточка, жёлтая полоса слева, слева скрин блока сайта (верх скрина),
# справа серая строка «kalmykov-realty · сайт», жирный текст и жёлтая плашка «Ссылка в шапке профиля».
# Въезжает сверху за 0,5 с с отскоком, держится, уходит вверх с затуханием за 0,32 с; «вжик» и «дзынь».
# Запуск: python3 scripts/sait_overlay.py in.mp4 out.mp4 <скрин из hf/sait_skriny> "<текст. Ссылка в шапке профиля>"
#         <секунда> [top px, по умолчанию 200] [высота карточки, по умолчанию 300] [длительность, 3.6]
import sys, os, subprocess, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

B = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(B)
inp, out, img, text, t0 = sys.argv[1:6]
t0 = float(t0)
TOP = int(sys.argv[6]) if len(sys.argv) > 6 else 200
HC = int(sys.argv[7]) if len(sys.argv) > 7 else 300
SD = float(sys.argv[8]) if len(sys.argv) > 8 else 3.6
F900 = f"{R}/hf/pustaya2/fonts/montserrat-900.ttf"
F800 = f"{R}/hf/pustaya2/fonts/montserrat-800.ttf"
SND = f"{R}/hf/pustaya2/snd"

txt = text.strip().rstrip(".").replace(" €", "\u00a0€").replace(" %", "\u00a0%")  # число и € не разрываются по строкам
main, pill = (txt.rsplit(". ", 1) + [""])[:2] if ". " in txt else (txt, "Ссылка в шапке профиля")

W = 1080 - 2 * 44
PAD = 40                      # запас под тень
card = Image.new("RGBA", (W + 2 * PAD, HC + 2 * PAD), (0, 0, 0, 0))
# тень
sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle((PAD, PAD + 18, PAD + W, PAD + HC + 18), 30, fill=(0, 0, 0, 140))
card = Image.alpha_composite(card, sh.filter(ImageFilter.GaussianBlur(22)))
d = ImageDraw.Draw(card)
# жёлтая полоса слева + белая карточка
d.rounded_rectangle((PAD, PAD, PAD + W, PAD + HC), 30, fill=(255, 210, 63, 255))
d.rounded_rectangle((PAD + 12, PAD, PAD + W, PAD + HC), 26, fill=(255, 255, 255, 255))
# скрин блока сайта (верх скрина), скруглённый
ih = HC - 28; iw = int(ih * 0.92)
sc = Image.open(f"{R}/hf/sait_skriny/{img}").convert("RGBA")
k = iw / sc.width
sc = sc.resize((iw, max(ih, int(sc.height * k))), Image.LANCZOS).crop((0, 0, iw, ih))
m = Image.new("L", (iw, ih), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, iw - 1, ih - 1), 18, fill=255)
ix, iy = PAD + 12 + 14, PAD + 14
d.rounded_rectangle((ix - 2, iy - 2, ix + iw + 1, iy + ih + 1), 19, fill=(230, 230, 230, 255))
card.paste(sc, (ix, iy), m)
# текст справа
tx = ix + iw + 26; tw = PAD + W - 26 - tx
def wrap(s, font, width):
    words, lines, cur = s.split(" "), [], ""
    for w_ in words:
        c = (cur + " " + w_).strip()
        if d.textlength(c, font=font) <= width: cur = c
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines
fs = 46 if len(main) <= 34 else (40 if len(main) <= 50 else 34)
while True:
    fb = ImageFont.truetype(F900, fs); lines = wrap(main, fb, tw)
    if len(lines) <= 3 or fs <= 28: break
    fs -= 2
fu = ImageFont.truetype(F800, 26); fp = ImageFont.truetype(F900, 32)
lh = int(fs * 1.08)
pw = int(d.textlength(pill, font=fp)) + 36; ph = 32 + 18
block = 26 + 12 + lh * len(lines) + 12 + ph
y = PAD + (HC - block) // 2
d.text((tx, y), "kalmykov-realty · сайт", font=fu, fill=(138, 138, 138, 255)); y += 26 + 12
for ln in lines:
    d.text((tx, y), ln, font=fb, fill=(17, 17, 17, 255)); y += lh
y += 12
d.rounded_rectangle((tx, y, tx + pw, y + ph), 12, fill=(255, 210, 63, 255))
d.text((tx + 18, y + 9), pill, font=fp, fill=(0, 0, 0, 255))
cp = os.path.splitext(out)[0] + "_sait.png"
card.save(cp)

# движение: въезд сверху за 0,5 с с отскоком (back.out), уход вверх на 160 px с затуханием за 0,32 с
ta, te = t0 - 0.08, t0 + SD
X = 44 - PAD; Y = TOP - PAD
s = 1.5
yin = f"({Y}+(-320)*(1-((({s}+1)*pow(min(1,(t-{ta})/0.5)-1,3))+{s}*pow(min(1,(t-{ta})/0.5)-1,2)+1)))"
yout = f"({Y}-160*((t-{te - 0.32})/0.32))"
yexp = f"if(lt(t,{te - 0.32}),{yin},{yout})"
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", inp],
                           capture_output=True, text=True).stdout.strip())
if te > dur - 0.2:
    sys.exit(f"окошко выходит за конец ролика ({te:.1f} > {dur:.1f})")
fc = (f"[1:v]format=rgba,fade=t=in:st={ta:.3f}:d=0.25:alpha=1,fade=t=out:st={te - 0.32:.3f}:d=0.32:alpha=1[c];"
      f"[0:v][c]overlay=x={X}:y='{yexp}':enable='between(t,{ta:.3f},{te:.3f})':eval=frame[v];"
      f"[2:a]adelay={int(max(0, t0 - 0.12) * 1000)}|{int(max(0, t0 - 0.12) * 1000)},volume=0.25[w];"
      f"[3:a]adelay={int((t0 + 0.45) * 1000)}|{int((t0 + 0.45) * 1000)},volume=0.2[g];"
      f"[0:a][w][g]amix=inputs=3:duration=first:normalize=0[a]")
cmd = ["ffmpeg", "-v", "error", "-y", "-i", inp, "-loop", "1", "-t", f"{dur:.3f}", "-i", cp,
       "-i", f"{SND}/whoosh.wav", "-i", f"{SND}/ding.wav", "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
       "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
       "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print(f"ok: окошко {img} в {t0:.1f}–{te:.1f} с, верх {TOP}px, «{main}» / «{pill}»")
