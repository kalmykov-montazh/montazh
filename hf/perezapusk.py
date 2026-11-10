# Перезапуск провалов (решение Евгения 10.11.2026, «Перезапуск 10 провалов — новые начала»):
# хук голосом поверх карточки на весь экран (тёмно-синий фон, надпись жёлтой и белой плашками, картинка-предмет
# с медленным наездом, подпись темы внизу) → старый готовый ролик с первой законченной фразы.
# Запуск (ves-bash, rclone remote montazh:): python3 hf/perezapusk.py hf/perezapusk/spisok.json [номера через запятую]
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

L = json.load(open(sys.argv[1])); ONLY = [x for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else []) if x]
F9 = "fonts/montserrat-900.ttf"; F8 = "fonts/montserrat-800.ttf"
W, H = 1080, 1920
def sh(*a): subprocess.run(a, check=True)
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())

def card(lines, caption, out):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):  # мягкий градиент тёмно-синего
        k = y / H; d.line([(0, y), (W, y)], fill=(int(22 - 8 * k), int(36 - 12 * k), int(74 - 26 * k)))
    y = 130
    for i, (txt, col) in enumerate(lines):
        sz = 96 if i == 0 else 86
        while True:
            f = ImageFont.truetype(F9, sz); tw = d.textlength(txt, font=f)
            if tw <= W - 140 or sz < 48: break
            sz -= 4
        bx0 = (W - tw) / 2 - 22; bh = sz + 30
        d.rectangle([bx0, y, bx0 + tw + 44, y + bh], fill=(255, 210, 63) if col == "y" else (255, 255, 255))
        d.text((W / 2, y + bh / 2 + 2), txt, font=f, fill=(12, 12, 12), anchor="mm")
        y += bh + 14
    if caption:
        f = ImageFont.truetype(F8, 46); d.text((W / 2, 1500), caption, font=f, fill=(235, 238, 245), anchor="mm")
    im.save(out)
    return y

os.makedirs("pz", exist_ok=True)
for it in L:
    n = it["n"]
    if ONLY and n not in ONLY: continue
    w = f"pz/{n}"; os.makedirs(w, exist_ok=True)
    sh("rclone", "copyto", f"montazh:Брокер/Хуки/{it['hook']}", f"{w}/hook.mp4")
    sh("rclone", "copyto", f"montazh:{it['old']}", f"{w}/old.mp4")
    sh("rclone", "copyto", f"montazh:Брокер/Вставки/Предметы_ov/{it['img']}", f"{w}/img.jpg")
    # голос хука: ×1.2, тишина по краям срезана, громкость −14
    sh("ffmpeg", "-v", "error", "-y", "-i", f"{w}/hook.mp4", "-vn", "-af",
       "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,areverse,atempo=1.2,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000",
       "-ac", "2", f"{w}/hook.wav")
    D = dur(f"{w}/hook.wav") + 0.3
    ytop = card([(it["l1"], "y"), (it["l2"], "y"), (it["l3"], "w")] if it.get("l3") else [(it["l1"], "y"), (it["l2"], "y")], it.get("cap", ""), f"{w}/bg.png")
    py = max(ytop + 70, 560); fr = int(D * 30) + 2
    im = Image.open(f"{w}/img.jpg").convert("RGB"); tw, th = 980, 660
    r = max(tw / im.width, th / im.height); im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1))
    l = (im.width - tw) // 2; t = (im.height - th) // 2; im.crop((l, t, l + tw, t + th)).save(f"{w}/pic.png")
    sh("ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", f"{w}/bg.png", "-i", f"{w}/pic.png", "-i", f"{w}/hook.wav",
       "-filter_complex",
       f"[1:v]scale=1960:1320,zoompan=z='min(1+0.0009*on,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s=980x660:fps=30[p];"
       f"[0:v][p]overlay=50:{py}:shortest=1,format=yuv420p,fade=t=in:st=0.12:d=0.01[v];[2:a]apad[a]",
       "-map", "[v]", "-map", "[a]", "-t", f"{D:.3f}", "-r", "30", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", f"{w}/a.mp4")
    sh("ffmpeg", "-v", "error", "-y", "-ss", f"{it['cut']}", "-i", f"{w}/old.mp4",
       "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
       "-af", "aresample=48000,afade=t=in:d=0.03", "-ac", "2", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
       "-c:a", "aac", "-b:a", "192k", f"{w}/b.mp4")
    name = f"{n} {it['name']}"
    out = f"{w}/!!! {name} — перезапуск.mp4"
    sh("ffmpeg", "-v", "error", "-y", "-i", f"{w}/a.mp4", "-i", f"{w}/b.mp4", "-filter_complex",
       "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "17",
       "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)
    sh("ffmpeg", "-v", "error", "-y", "-ss", "0.2", "-i", out, "-frames:v", "1", "-q:v", "2", f"{w}/обложка.jpg")
    dest = f"montazh:Брокер/На проверке/Перезапуск провалов/{name}"
    sh("rclone", "copyto", out, f"{dest}/!!! {name} — перезапуск.mp4")
    sh("rclone", "copyto", f"{w}/обложка.jpg", f"{dest}/обложка.jpg")
    up = os.path.dirname(it["old"]) + "/упаковка.txt"
    subprocess.run(["rclone", "copyto", f"montazh:{up}", f"{dest}/упаковка.txt"])
    os.makedirs("pr", exist_ok=True)
    sh("ffmpeg", "-v", "error", "-y", "-i", out, "-t", f"{D + 6:.1f}", "-vf", "fps=2,scale=180:-2,tile=8x2", "-frames:v", "1", f"pr/{n}.jpg")
    sh("ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, D - 2.5):.2f}", "-i", out, "-t", "5", "-vn", "-ac", "1", "-ar", "16000", f"pr/{n}_styk.wav")
    print(f"{name}: хук {D:.1f} с, старый с {it['cut']} с, итого {dur(out):.1f} с")
