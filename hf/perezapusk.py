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


import math, re
WH = "hf/pustaya/snd/whoosh.wav"
def ease_back(x):
    c1 = 1.70158; c3 = c1 + 1; x = min(max(x, 0), 1)
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def ease_out(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def speech(wav):
    """Интервалы речи по тишине (для раскладки слов субтитров)."""
    e = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "silencedetect=noise=-38dB:d=0.12", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    D = dur(wav); ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", e)]
    se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", e)]
    sil = list(zip(ss, se + [D] * (len(ss) - len(se))))
    out = []; cur = 0.0
    for a, b in sil:
        if a - cur > 0.05: out.append((cur, a))
        cur = b
    if D - cur > 0.05: out.append((cur, D))
    return out or [(0, D)]

def word_times(text, wav):
    text = re.sub(r"(\d) (\d{3})", "\\1\u00a0\\2", text); text = re.sub(r"\s+—", "\u00a0—", text)
    words = text.split(" "); wts = [len(re.sub(r"\W", "", x)) + 1.5 for x in words]
    iv = speech(wav); tot = sum(b - a for a, b in iv); W = sum(wts)
    def at(frac):  # доля речи -> время
        need = frac * tot
        for a, b in iv:
            if need <= b - a: return a + need
            need -= b - a
        return iv[-1][1]
    res = []; acc = 0
    for x, wt in zip(words, wts):
        res.append((x, at(acc / W), at((acc + wt) / W))); acc += wt
    return res

def groups(wt):
    g = []; cur = []
    for x in wt:
        cur.append(x)
        if len(cur) == 3 or len(" ".join(y[0] for y in cur)) > 16 or re.search(r"[.,?!—:]$", x[0]):
            g.append(cur); cur = []
    if cur: g.append(cur)
    return g

def hook_card(it, w, D):
    """Хук с движением (правка Евгения 10.11.2026 18:22): надписи влетают по одной, 3 картинки влетают и улетают
    со звуком «вжик», медленный наезд, субтитры по словам с подсветкой."""
    lines = [(it["l1"], "y"), (it["l2"], "y")] + ([(it["l3"], "w")] if it.get("l3") else [])
    bg = Image.new("RGB", (W, H)); d = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=(int(22 - 8 * k), int(36 - 12 * k), int(74 - 26 * k)))
    # плашки надписей — отдельными картинками
    tiles = []; y = 130
    for i, (txt, col) in enumerate(lines):
        sz = 96 if i == 0 else 86
        while True:
            f = ImageFont.truetype(F9, sz); tw = d.textlength(txt, font=f)
            if tw <= W - 140 or sz < 48: break
            sz -= 4
        bh = sz + 30; tl = Image.new("RGBA", (int(tw + 44), bh), (255, 210, 63, 255) if col == "y" else (255, 255, 255, 255))
        ImageDraw.Draw(tl).text((tl.width / 2, bh / 2 + 2), txt, font=f, fill=(12, 12, 12), anchor="mm")
        tiles.append((tl, y)); y += bh + 14
    top = max(y + 50, 520); bot = 1440; BW, BH = 980, min(700, bot - top)
    imgs = [it["img"]] + it.get("imgs", [])
    pics = []
    for k, name in enumerate(imgs):
        src = f"{w}/img{k}.jpg"
        if k: sh("rclone", "copyto", f"montazh:Брокер/Вставки/Предметы_ov/{name}", src)
        else: src = f"{w}/img.jpg"
        im = Image.open(src).convert("RGB"); r = max(BW * 1.12 / im.width, BH * 1.12 / im.height)
        pics.append(im.resize((int(im.width * r) + 2, int(im.height * r) + 2)))
    n = len(pics); seg = D / n; ch = [k * seg for k in range(n)]
    mask = Image.new("L", (BW, BH), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, BW - 1, BH - 1], radius=34, fill=255)
    sh_ = Image.new("RGBA", (BW + 60, BH + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh_).rounded_rectangle([30, 40, BW + 30, BH + 40], radius=40, fill=(0, 0, 0, 110))
    from PIL import ImageFilter
    sh_ = sh_.filter(ImageFilter.GaussianBlur(14))
    gr = groups(word_times(it["text"], f"{w}/hook.wav"))
    fs = ImageFont.truetype(F9, 72); cy = (top + bot) // 2 + 0
    N = int(D * 30) + 1
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                          "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", f"{w}/av.mp4"], stdin=subprocess.PIPE)
    for i in range(N):
        t = i / 30; fr = bg.copy()
        for j, (tl, ty) in enumerate(tiles):  # надписи влетают по одной
            x = ease_back((t - 0.08 - j * 0.16) / 0.3)
            if x <= 0: continue
            s = (0.55 + 0.45 * x) * (1 + 0.012 * math.sin(t * 5 + j))
            im2 = tl.resize((max(1, int(tl.width * s)), max(1, int(tl.height * s))))
            fr.paste(im2, (int(W / 2 - im2.width / 2), int(ty + tl.height / 2 - im2.height / 2)), im2)
        k = min(n - 1, int(t / seg)); lt = t - ch[k]
        im = pics[k]; z = 1 + 0.10 * (lt / seg)  # наезд
        cw, chh = BW * 1.12 / z / 1.0, BH * 1.12 / z
        cw = min(cw, im.width); chh = min(chh, im.height)
        dx = (im.width - cw) / 2 + (8 if k % 2 else -8) * (lt / seg) * 3
        c = im.crop((int(dx), int((im.height - chh) / 2), int(dx + cw), int((im.height - chh) / 2 + chh))).resize((BW, BH))
        ent = ease_back(lt / 0.28); off = 0
        side = 1 if k % 2 == 0 else -1
        x0 = (W - BW) / 2 + side * (1 - ent) * 1100
        if k < n - 1 and seg - lt < 0.16: x0 -= side * ease_out(1 - (seg - lt) / 0.16) * 1100  # улетает
        rot = (1 - min(ent, 1)) * 8 * side
        card_ = Image.new("RGBA", (BW, BH)); card_.paste(c, (0, 0)); card_.putalpha(mask)
        if abs(rot) > 0.2: card_ = card_.rotate(rot, resample=Image.BICUBIC, expand=True)
        fr.paste(sh_, (int(x0 - 30), int(cy - BH / 2 - 30)), sh_)
        fr.paste(card_, (int(x0 + BW / 2 - card_.width / 2), int(cy - card_.height / 2)), card_)
        # субтитры по словам
        g = next((g for g in gr if g[0][1] - 0.05 <= t < g[-1][2] + 0.25), None)
        if g is None:
            g = max((g for g in gr if g[0][1] <= t), key=lambda g: g[0][1], default=gr[0])
        txt = [x[0].upper() for x in g]; d2 = ImageDraw.Draw(fr)
        pop = ease_back((t - g[0][1] + 0.05) / 0.18); sz = int(72 * (0.8 + 0.2 * min(pop, 1.1)))
        f2 = ImageFont.truetype(F9, sz); sp = d2.textlength(" ", font=f2)
        ws = [d2.textlength(x, font=f2) for x in txt]
        while sum(ws) + sp * (len(ws) - 1) > W - 80 and sz > 40:
            sz -= 4; f2 = ImageFont.truetype(F9, sz); sp = d2.textlength(" ", font=f2); ws = [d2.textlength(x, font=f2) for x in txt]
        x = (W - (sum(ws) + sp * (len(ws) - 1))) / 2; yy = 1600
        for (wd, a, b), tx, ww in zip(g, txt, ws):
            col = (255, 210, 63) if a <= t else (255, 255, 255)
            d2.text((x, yy), tx, font=f2, fill=col, stroke_width=7, stroke_fill=(0, 0, 0), anchor="lm"); x += ww + sp
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    # звук: голос + «вжик» на каждой картинке и на первой надписи
    ins = ["-i", f"{w}/hook.wav"]; fl = []; times = [0.05] + ch[1:]
    for j, tt in enumerate(times):
        ins += ["-i", WH]; fl.append(f"[{j+2}:a]volume=0.45,adelay={int(tt*1000)}|{int(tt*1000)}[w{j}]")
    mix = "".join(f"[w{j}]" for j in range(len(times)))
    fl.append(f"[1:a]apad[v0];[v0]{mix}amix=inputs={len(times)+1}:normalize=0:duration=first,atrim=0:{D:.3f}[a]")
    sh("ffmpeg", "-v", "error", "-y", "-i", f"{w}/av.mp4", *ins, "-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]",
       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", f"{D:.3f}", f"{w}/a.mp4")

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
    hook_card(it, w, D)
    VF = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p"
    if it.get("segs"):  # несколько кусков старого ролика (вырезать устаревшее), границы — в тишину
        sil = speech(f"{w}/old.mp4")
        def snap(x, start):
            best = x
            for (a, b), (c, _) in zip(sil, sil[1:] + [(dur(f"{w}/old.mp4"), 0)]):
                if b - 0.45 <= x <= c + 0.45 and c - b > 0.05:  # пауза между речью b..c рядом с x
                    best = (c - 0.06) if start else (b + 0.08); break
            return best
        parts = []
        for k, (a, b) in enumerate(it["segs"]):
            a2, b2 = (a, b) if it.get("exact") else (snap(a, True), snap(b, False))
            sh("ffmpeg", "-v", "error", "-y", "-ss", f"{a2:.3f}", "-to", f"{b2:.3f}", "-i", f"{w}/old.mp4", "-vf", VF,
               "-af", "aresample=48000,afade=t=in:d=0.02", "-ac", "2", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
               "-c:a", "aac", "-b:a", "192k", f"{w}/s{k}.mp4")
            parts.append(f"{w}/s{k}.mp4"); print(f"  кусок {a2:.2f}–{b2:.2f}")
        n_ = len(parts); ins_ = sum([["-i", x] for x in parts], [])
        sh("ffmpeg", "-v", "error", "-y", *ins_, "-filter_complex", "".join(f"[{k}:v][{k}:a]" for k in range(n_)) + f"concat=n={n_}:v=1:a=1[v][a]",
           "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", f"{w}/b.mp4")
        it["cut"] = it["segs"][0][0]
    else:
        sh("ffmpeg", "-v", "error", "-y", "-ss", f"{it['cut']}", "-i", f"{w}/old.mp4", "-vf", VF,
           "-af", "aresample=48000,afade=t=in:d=0.03", "-ac", "2", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
           "-c:a", "aac", "-b:a", "192k", f"{w}/b.mp4")
    name = f"{n} {it['name']}"
    out = f"{w}/!!! {name} — перезапуск.mp4"
    sh("ffmpeg", "-v", "error", "-y", "-i", f"{w}/a.mp4", "-i", f"{w}/b.mp4", "-filter_complex",
       "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "17",
       "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)
    sh("ffmpeg", "-v", "error", "-y", "-ss", "0.2", "-i", out, "-frames:v", "1", "-q:v", "2", f"{w}/обложка.jpg")
    dest = "montazh:" + it["dest"] if it.get("dest") else f"montazh:Брокер/На проверке/Перезапуск провалов/{name}"
    sh("rclone", "copyto", out, f"{dest}/!!! {name} — перезапуск.mp4")
    sh("rclone", "copyto", f"{w}/обложка.jpg", f"{dest}/обложка.jpg")
    up = os.path.dirname(it["old"]) + "/упаковка.txt"
    subprocess.run(["rclone", "copyto", f"montazh:{up}", f"{dest}/упаковка.txt"])
    os.makedirs("pr", exist_ok=True)
    sh("ffmpeg", "-v", "error", "-y", "-i", out, "-t", f"{D + 6:.1f}", "-vf", "fps=2,scale=180:-2,tile=8x2", "-frames:v", "1", f"pr/{n}.jpg")
    sh("ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, D - 2.5):.2f}", "-i", out, "-t", "5", "-vn", "-ac", "1", "-ar", "16000", f"pr/{n}_styk.wav")
    print(f"{name}: хук {D:.1f} с, старый с {it['cut']} с, итого {dur(out):.1f} с")
