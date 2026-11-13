#!/usr/bin/env python3
# 11.11.2026, решение Евгения: окошко сайта (пункт 13 главной версии монтажа) — в уже готовые ролики из «Готовых»,
# которые робот ещё не расставил. Ролик НЕ пересобирается: окошко накладывается поверх готового видео,
# всё остальное (монтаж, плашки, субтитры, обложка, звук) остаётся как было.
# Вид — как .sait в hf/auto.css: белая карточка, жёлтая полоса слева, слева скрин блока сайта (верх скрина),
# справа серая строка «kalmykov-realty · сайт», жирный текст и жёлтая плашка «Ссылка в шапке профиля».
# Въезжает сверху за 0,5 с с отскоком, держится, уходит вверх с затуханием за 0,32 с; «вжик» и «дзынь».
# 13.11.2026 — ВАРИАНТ «Б» (решение Евгения): чёрная карточка, золотая рамка, значок KG + kalmykovgroup.com золотом,
# белый текст, жёлтая плашка; скрин целиком (не обрезается). 4 с. Переменная KG=1 — ещё и значок KG в правом верхнем
# углу на весь ролик (KG_X, KG_Y, KG_S — место и размер; KG_LEFT=1 — левый угол).
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
SD = float(sys.argv[8]) if len(sys.argv) > 8 else 4.0
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
GOLD = (201, 162, 75, 255)
d.rounded_rectangle((PAD, PAD, PAD + W, PAD + HC), 30, fill=GOLD)
d.rounded_rectangle((PAD + 4, PAD + 4, PAD + W - 4, PAD + HC - 4), 27, fill=(13, 15, 22, 255))
# скрин блока сайта целиком на светлой подложке
ih = HC - 32; iw = int(ih * 1.15)
sc = Image.open(f"{R}/hf/sait_skriny/{img}").convert("RGBA")
sc.thumbnail((iw - 8, ih - 8), Image.LANCZOS)
ix, iy = PAD + 16, PAD + 16
d.rounded_rectangle((ix, iy, ix + iw, iy + ih), 18, fill=(238, 241, 246, 255))
card.paste(sc, (ix + (iw - sc.width) // 2, iy + (ih - sc.height) // 2), sc)
# текст справа
tx = ix + iw + 24; tw = PAD + W - 24 - tx
def wrap(s, font, width):
    words, lines, cur = s.split(" "), [], ""
    for w_ in words:
        c = (cur + " " + w_).strip()
        if d.textlength(c, font=font) <= width: cur = c
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines
fs = 42 if len(main) <= 34 else (38 if len(main) <= 50 else 32)
if HC < 250: fs = min(fs, 32)
while True:
    fb = ImageFont.truetype(F900, fs); lines = wrap(main, fb, tw)
    if len(lines) <= 3 or fs <= 26: break
    fs -= 2
fu = ImageFont.truetype(F900, 34 if HC >= 250 else 28); fp = ImageFont.truetype(F900, 30 if HC >= 250 else 26)
lh = int(fs * 1.08); ks = 48 if HC >= 250 else 38
pw = int(d.textlength(pill, font=fp)) + 32; ph = fp.size + 18
block = ks + 12 + lh * len(lines) + 12 + ph
y = PAD + (HC - block) // 2
kg = Image.open(f"{R}/hf/kg.png").convert("RGBA").resize((ks, ks), Image.LANCZOS)
card.paste(kg, (tx, y), kg)
d.text((tx + ks + 12, y + (ks - fu.size) // 2 - 2), "kalmykovgroup.com", font=fu, fill=GOLD); y += ks + 12
for ln in lines:
    d.text((tx, y), ln, font=fb, fill=(255, 255, 255, 255)); y += lh
y += 12
d.rounded_rectangle((tx, y, tx + pw, y + ph), 12, fill=(255, 210, 63, 255))
d.text((tx + 16, y + 8), pill, font=fp, fill=(0, 0, 0, 255))
cp = os.path.splitext(out)[0] + "_sait.png"
card.save(cp)

# движение: въезд сверху за 0,5 с с отскоком (back.out), уход вверх на 160 px с затуханием за 0,32 с
ta, te = t0 - 0.08, t0 + SD
X = 44 - PAD; Y = TOP - PAD
s = 1.5
DY = 320 if TOP > 900 else -320   # 14.11.2026: окошко внизу въезжает снизу
yin = f"({Y}+({DY})*(1-((({s}+1)*pow(min(1,(t-{ta})/0.5)-1,3))+{s}*pow(min(1,(t-{ta})/0.5)-1,2)+1)))"
yout = f"({Y}+({DY // 2})*((t-{te - 0.32})/0.32))"
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
extra = []
if os.environ.get("KG") == "1":
    ksz = int(os.environ.get("KG_S", "84")); ky = int(os.environ.get("KG_Y", "150"))
    kx = int(os.environ.get("KG_X", "30" if os.environ.get("KG_LEFT") == "1" else str(1080 - 30 - ksz)))
    kgp = os.path.splitext(out)[0] + "_kg.png"
    kgi = Image.open(f"{R}/hf/kg.png").convert("RGBA").resize((ksz, ksz), Image.LANCZOS)
    a = kgi.getchannel("A").point(lambda v: int(v * 0.9)); kgi.putalpha(a); kgi.save(kgp)
    fc = fc.replace("[v];", "[v0];[4:v]format=rgba[kg];[v0][kg]overlay=x=%d:y=%d:enable='gte(t,0.6)*not(between(t,%.3f,%.3f))'[v];" % (kx, ky, ta, te), 1)
    extra = ["-i", kgp]
cmd = ["ffmpeg", "-v", "error", "-y", "-i", inp, "-loop", "1", "-t", f"{dur:.3f}", "-i", cp,
       "-i", f"{SND}/whoosh.wav", "-i", f"{SND}/ding.wav"] + extra + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
       "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
       "-movflags", "+faststart", out]
cmd = [c for c in cmd]
subprocess.run(cmd, check=True)
print(f"ok: окошко {img} в {t0:.1f}–{te:.1f} с, верх {TOP}px, «{main}» / «{pill}»")
