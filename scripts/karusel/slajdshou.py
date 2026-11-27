# 13.11.2026 (Евгений 23:38, «на все 100 согласен»): видео-рилс из слайдов карусели — shorts.mp4 1080×1920.
#   python3 scripts/karusel/slajdshou.py <папка карусели> [выход.mp4]
# Берёт 01.jpg, 02.jpg … (1080×1350) по порядку. Что делает:
#  1) слайд по центру, сверху и снизу — тот же слайд размытый и затемнённый (без чёрных полос);
#  2) медленный наезд на каждом слайде (1.00 → 1.06), направление чередуется; мягкая смена 0,4 с;
#  3) время слайда по объёму текста: первый 1,8 с (вопрос/цифра — держим 3-ю секунду), остальные 2–4 с.
#     Источник текста — spec.json (тот же, что для slajdy.py) или karusel_slajdy.json {"dur": [..]}; нет — 3 с;
#  4) в нижней полосе всегда маленький kalmykovgroup.com, на последнем слайде крупно на жёлтой плашке
#     («Сохраните, пригодится» пишем на самом последнем слайде в spec — не дублируем);
#  5) петля: в последние 0,35 с плавно возвращается первый слайд — видео без шва идёт по второму кругу;
#  6) фоновая музыка, СВОЯ (синтез, без чужих треков и Content ID): лёгкий ритмичный акустик-поп —
#     гитара с синкопой, мягкая бочка, хлопок, шейкер, бас, маримба; не дискотека;
#     6 мелодий-вариантов, вариант по названию папки (или --trek N), громкость средняя ~−17 dB,
#     вход 0,3 с, выход 1,5 с, конец музыки = конец видео. Какой трек — пишется в _музыка.txt.
#
# 16.11.2026 (Евгений 21:34): Facebook у рилса «Зима в Валенсии» — «качество контента: видео с неполным заполнением
# экрана», показ занижен. ТЕПЕРЬ рилс собирается ТОЛЬКО из полноэкранных слайдов 1080×1920 (папка reel/):
#  — есть reel/01.jpg … (1080×1920) — берём их;
#  — нет, но есть spec.json и фото к нему — сами рисуем reel/ (slajdy.py --reel) и берём;
#  — нет ни того ни другого (старые карусели, нарисованные вручную) — НЕ собираем, выходим с ошибкой.
#    Старый вид «слайд 4:5 по центру + размытые полосы» — только флагом --s-polosami (не для Facebook).
# Сайт: маленький kalmykovgroup.com под текстом (у=1500, слева), на последнем слайде — жёлтая плашка вверху (у≈520),
# в безопасной зоне Reels. Номеров «1/7» и «Листайте» в рилсе не бывает.
import os, sys, json, glob, subprocess, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H, FPS = 1080, 1920, 30
SW, SH = 1080, 1350
XF = 0.4          # смена слайдов
LOOP = 0.35       # возврат к первому в конце
SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = os.path.join(ROOT, "fonts", "montserrat-800.ttf")
SITE = "kalmykovgroup.com"
YEL = (255, 214, 0)


def F(s): return ImageFont.truetype(FONT, s)


# ---------- длительности ----------
def durations(folder, n):
    p = os.path.join(folder, "karusel_slajdy.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8")).get("dur")
        if d and len(d) == n: return [float(x) for x in d]
    p = os.path.join(folder, "spec.json")
    out = []
    if os.path.exists(p):
        sl = json.load(open(p, encoding="utf-8")).get("slides", [])
        if len(sl) == n:
            for i, s in enumerate(sl):
                chars = sum(len(str(s.get(k, ""))) for k in ("big", "title", "sub", "price"))
                out.append(1.8 if i == 0 else min(4.0, max(2.0, 1.6 + chars / 25)))
            out[-1] = max(out[-1], 3.0)
            return out
    return [1.8] + [3.0] * (n - 2) + [3.5] if n > 1 else [3.5]


# ---------- картинка ----------
def make_bg(img):
    b = img.resize((int(SW * H / SH), H)).crop(((int(SW * H / SH) - W) // 2, 0, (int(SW * H / SH) - W) // 2 + W, H))
    b = b.filter(ImageFilter.GaussianBlur(40))
    return ImageEnhance.Brightness(b).enhance(0.45)


def site_band(last):
    """Прозрачный слой с адресом сайта в нижней полосе."""
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    top = (H + SH) // 2
    if not last:
        f = F(40); t = SITE
        w = d.textbbox((0, 0), t, font=f)[2]
        d.text(((W - w) // 2, top + 105), t, font=f, fill=(255, 255, 255, 215))
    else:
        f = F(64); t = SITE
        w = d.textbbox((0, 0), t, font=f)[2]
        x, y = (W - w) // 2, top + 60
        d.rounded_rectangle((x - 30, y - 18, x + w + 30, y + 82), 22, fill=YEL + (255,))
        d.text((x, y), t, font=f, fill=(0, 0, 0, 255))
    return L


def site_band_full(last):
    """16.11: сайт для полноэкранного рилса — в безопасной зоне."""
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    if not last:
        d.text((60, 1500), SITE, font=F(38), fill=(255, 255, 255, 200))
    else:
        f = F(64); w = d.textbbox((0, 0), SITE, font=f)[2]; x, y = (W - w) // 2, 520
        d.rounded_rectangle((x - 30, y - 18, x + w + 30, y + 82), 22, fill=YEL + (255,))
        d.text((x, y), SITE, font=f, fill=(0, 0, 0, 255))
    return L


def frame_full(slide, band, k, direction):
    z = 1.0 + 0.04 * (k if direction else 1 - k)          # на весь экран наезд мягче, чтобы текст не уходил к краю
    sw, sh = int(W * z), int(H * z)
    s = slide.resize((sw, sh), Image.BILINEAR)
    s = s.crop(((sw - W) // 2, (sh - H) // 2, (sw - W) // 2 + W, (sh - H) // 2 + H)).convert("RGBA")
    s.alpha_composite(band)
    return s.convert("RGB")


def full_slides(folder):
    """Список путей полноэкранных слайдов или None."""
    rd = os.path.join(folder, "reel")
    fs = sorted(glob.glob(os.path.join(rd, "[0-9][0-9].jpg")))
    if fs and all(Image.open(p).size == (W, H) for p in fs): return fs
    sp = os.path.join(folder, "spec_reel.json")             # вырезки-панели под 9:16 (novye_pachka.py)
    if not os.path.exists(sp): sp = os.path.join(folder, "spec.json")
    if os.path.exists(sp):
        base = os.path.dirname(os.path.abspath(sp))
        sl = json.load(open(sp, encoding="utf-8")).get("slides", [])
        if sl and all(os.path.exists(os.path.join(base, x["photo"])) for x in sl):
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import slajdy
            slajdy.render(sp, rd, "916")
            return sorted(glob.glob(os.path.join(rd, "[0-9][0-9].jpg")))
        print("в spec.json есть фото, которых нет в папке:",
              [x["photo"] for x in sl if not os.path.exists(os.path.join(base, x["photo"]))][:5])
    return None


def frame_of(slide, bg, band, k, direction):
    """k — доля прошедшего времени слайда 0..1, медленный наезд."""
    z = 1.0 + 0.06 * (k if direction else 1 - k)
    sw, sh = int(SW * z), int(SH * z)
    s = slide.resize((sw, sh), Image.BILINEAR)
    s = s.crop(((sw - SW) // 2, (sh - SH) // 2, (sw - SW) // 2 + SW, (sh - SH) // 2 + SH))
    f = bg.copy()
    f.paste(s, (0, (H - SH) // 2))
    f = f.convert("RGBA"); f.alpha_composite(band)
    return f.convert("RGB")


# ---------- музыка ----------
# 13.11.2026 23:53 Евгений: первая версия «как Моцарт, заснуть можно». Теперь — лёгкий ритмичный акустик-поп:
# мягкая бочка, хлопок на 2 и 4, шейкер восьмыми, гитара-«строй» с синкопой, бас с прыжками, мелодия маримбой.
# Не дискотека: без электро-баса и «качалова», бочка мягкая. Громче: средняя ~−17 dB.
TREKI = [  # (тоника Гц, прогрессия в полутонах от тоники, темп)
    (196.00, [0, 7, 9, 5], 104),   # G: I–V–vi–IV
    (220.00, [0, 5, 9, 7], 100),   # A: I–IV–vi–V
    (174.61, [9, 5, 0, 7], 108),   # F: vi–IV–I–V
    (246.94, [0, 9, 5, 7], 98),    # B: I–vi–IV–V
    (207.65, [0, 7, 5, 7], 112),   # G#: I–V–IV–V
    (185.00, [5, 0, 7, 9], 102),   # F#: IV–I–V–vi
]
RNG = np.random.default_rng(7)


def chord(r):
    minor = r % 12 in (9, 2, 4)
    return [r, r + (3 if minor else 4), r + 7]


def pluck(freq, dur, amp, bright=0.5):
    """Гитарная струна (Карплус — Стронг)."""
    n = int(dur * SR); p = max(2, int(SR / freq))
    buf = RNG.uniform(-1, 1, p); out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * (0.996 if bright > 0.4 else 0.993)
    return amp * out


def marimba(freq, dur, amp):
    t = np.arange(int(dur * SR)) / SR
    return amp * np.exp(-t * 7) * (np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t * 20))


def kick(amp):
    t = np.arange(int(0.35 * SR)) / SR
    f = 50 + 70 * np.exp(-t * 30)
    return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def clap(amp):
    t = np.arange(int(0.18 * SR)) / SR
    nz = RNG.uniform(-1, 1, len(t))
    nz = nz - np.concatenate([[0], nz[:-1]]) * 0.7      # светлее
    return amp * nz * (np.exp(-t * 28) + 0.4 * np.exp(-np.maximum(0, t - 0.012) * 40) * (t > 0.012))


def shaker(amp):
    t = np.arange(int(0.07 * SR)) / SR
    nz = RNG.uniform(-1, 1, len(t)); nz = nz - np.concatenate([[0], nz[:-1]])
    return amp * nz * np.sin(np.pi * t / t[-1]) ** 2


def bass(freq, dur, amp):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, t / 0.01) * np.exp(-t * 2.5)
    return amp * env * (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t))


def add(out, x, at):
    k = int(at * SR)
    if 0 <= k < len(out): out[k:k + len(x)] += x[:len(out) - k]


def music(total, idx):
    tonic, prog, bpm = TREKI[idx % len(TREKI)]
    b = 60 / bpm; e = b / 2; bar = 4 * b
    f = lambda s: tonic * 2 ** (s / 12)
    L = int((total + 3) * SR)
    drums, gtr, low, mel = (np.zeros(L) for _ in range(4))
    K, C = kick(0.9), clap(0.35)
    shs = [shaker(0.10), shaker(0.06)]
    # мелодия: 2-тактовый мотив из ступеней аккорда, повторяется с вариацией
    motif = [(0, 2, 1.0), (1.5, 1, 0.5), (2, 0, 1.0), (3, 2, 0.5), (3.5, 1, 0.5)]
    t0, n = 0.0, 0
    intro = 2 * bar if total > 12 else bar           # первые такты без барабанов — лёгкий вход
    while t0 < total + bar:
        r = prog[n % 4]; ch = chord(r)
        # гитара: «строй» ↓ ↓ ↑ ↑ ↓ ↑ (1, 2, 2+, 3+, 4, 4+) — синкопа
        for pos, up in ((0, 0), (1, 0), (1.5, 1), (2.5, 1), (3, 0), (3.5, 1)):
            notes = ch + [ch[0] + 12] if not up else [ch[1] + 12, ch[2], ch[0] + 12]
            for j, s in enumerate(notes):
                add(gtr, pluck(f(s), 0.9, 0.11 if not up else 0.07), t0 + pos * b + j * 0.008)
        # бас: 1, 2+ (синкопа), 3, 4+ — к следующему
        nxt = prog[(n + 1) % 4]
        for pos, s, d in ((0, r, 0.7), (1.5, r, 0.4), (2, r + 7, 0.6), (3.5, nxt - 1 if nxt > r else r + 2, 0.3)):
            add(low, bass(f(s - 24), d * b * 2, 0.33), t0 + pos * b)
        # барабаны
        if t0 >= intro - 1e-6:
            for pos in (0, 2, 2.75):
                add(drums, K * (0.75 if pos == 2.75 else 1), t0 + pos * b)
            for pos in (1, 3): add(drums, C, t0 + pos * b)
            for k8 in range(8): add(drums, shs[k8 % 2], t0 + k8 * e)
        # мелодия — со 2-го такта, через такт
        if n % 2 == 1 or t0 >= intro:
            for pos, deg, d in motif if n % 2 == 0 else [(m[0], (m[1] + 1) % 3, m[2]) for m in motif]:
                add(mel, marimba(f(ch[deg] + 12), max(0.4, d * b * 1.5), 0.16), t0 + pos * b)
        t0 += bar; n += 1
    gtr = np.convolve(gtr, [0.6, 0.4], "same")
    mix = drums * 0.9 + gtr + low + mel
    rev = mix.copy()
    for dly, g in ((0.09, 0.18), (0.17, 0.11)):
        k = int(dly * SR); rev[k:] += g * (gtr + mel)[:-k]
    out = rev[:int(total * SR)]
    t = np.arange(len(out)) / SR
    out *= np.minimum(1, t / 0.3) * np.minimum(1, (total - t) / 1.5)
    out = np.tanh(out / (np.percentile(np.abs(out), 99.5) + 1e-9) * 0.9)   # мягкий лимитер — плотнее и громче
    out = out / (np.max(np.abs(out)) + 1e-9) * 10 ** (-3 / 20)
    st = np.stack([out, np.roll(out, int(0.010 * SR))], 1)
    return (st * 32767).astype(np.int16)


def write_wav(path, data):
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())


# ---------- 16.11.2026: музыка FreePD (CC0) вместо своего синтеза ----------
# Евгений 16.11: своя музыка «нудная» — ставим весёлые треки FreePD (CC0, общественное достояние,
# без указания автора). Сайт freepd.com закрыт, берём с зеркала archive.org. Не скачалось — свой синтез.
# 25.11.2026: «City Sunshine» убран — на YouTube пришла заявка Content ID (Kevin MacLeod), хотя трек CC0.
# Трек, на который пришла заявка, больше не ставим (стоп-список — файл проекта «YouTube — заявки на авторские права»).
# 27.11.2026: «And Just Like That» убран — заявка Content ID на шортс oGJNrwTPXzs (Believe Music, «文字是骨»), трек CC0.
FREEPD = ["upbeat/Funshine.mp3", "upbeat/Happy Whistling Ukulele.mp3",
          "upbeat/Ukulele Song.mp3", "upbeat/Inventing Flight.mp3"]


def freepd_audio(total, trek, out_wav, lufs=-16):
    """Готовит wav длиной total из трека FreePD (старт — где трек уже звучит в полную силу). True/False."""
    import urllib.parse, urllib.request, re, statistics, tempfile
    t = FREEPD[trek % len(FREEPD)]
    cache = os.path.join(tempfile.gettempdir(), "freepd_" + re.sub(r"\W", "_", t))
    try:
        if not os.path.exists(cache):
            u = "https://archive.org/download/freepd/" + urllib.parse.quote(t)
            with urllib.request.urlopen(u, timeout=120) as r, open(cache, "wb") as f: f.write(r.read())
        st = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", cache, "-af",
                             "asetnsamples=n=22050,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
                             "-f", "null", "-"], capture_output=True, text=True).stderr
        v = [float(x) if x != "-inf" else -120 for x in re.findall(r"RMS_level=(\S+)", st)]
        med = statistics.median(v) if v else -20
        off = next((k for k, x in enumerate(v) if x >= med - 2), 0) * 0.5
        fo = max(0, total - 1.5)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(off), "-i", cache, "-t", f"{total:.3f}",
                        "-af", f"afade=t=in:d=0.3,afade=t=out:st={fo:.3f}:d=1.5,loudnorm=I={lufs}:TP=-1.5:LRA=11",
                        "-ar", "48000", "-ac", "2", out_wav], check=True)
        return t
    except Exception as e:
        print("FreePD не вышло:", e)
        return False


# ---------- сборка ----------
def main():
    folder = sys.argv[1]
    outp = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else os.path.join(folder, "shorts.mp4")
    trek = None
    if "--trek" in sys.argv: trek = int(sys.argv[sys.argv.index("--trek") + 1])
    polosy = "--s-polosami" in sys.argv
    full = None if polosy else full_slides(folder)
    if full:
        files = full
    else:
        if not polosy:
            sys.exit("НЕ СОБРАН: нет полноэкранных слайдов reel/01.jpg… и нет spec.json с фото. Рилс с размытыми полосами "
                     "Facebook режет («неполное заполнение экрана», 16.11.2026). Сначала spec.json + фото → slajdy.py --reel")
        files = sorted(p for p in glob.glob(os.path.join(folder, "[0-9][0-9].jpg")))
    if not files: sys.exit("нет 01.jpg, 02.jpg …")
    n = len(files)
    dur = durations(folder, n)
    if full:
        slides = [Image.open(p).convert("RGB") for p in files]
        bgs = [None] * n
        bez = os.path.exists(os.path.join(folder, "reel", "_bez_plashki"))   # сайт уже на слайдах (шпаргалки)
        bands = [Image.new("RGBA", (W, H), (0, 0, 0, 0)) if bez else site_band_full(i == n - 1) for i in range(n)]
    else:
        slides = [Image.open(p).convert("RGB").resize((SW, SH)) for p in files]
        bgs = [make_bg(s) for s in slides]
        bands = [site_band(i == n - 1) for i in range(n)]
    fr = (lambda sl, b, bd, k, dr: frame_full(sl, bd, k, dr)) if full else frame_of
    starts = np.cumsum([0] + dur[:-1])
    total = float(sum(dur))
    nf = int(round(total * FPS))

    def single(i, t):
        k = min(1, max(0, (t - starts[i]) / (dur[i] + XF)))
        return fr(slides[i], bgs[i], bands[i], k, i % 2 == 0)

    if trek is None: trek = int(hashlib.md5(os.path.basename(os.path.abspath(folder)).encode()).hexdigest(), 16) % len(TREKI)
    wav = outp + ".wav"
    src = freepd_audio(total, trek, wav)
    if not src: write_wav(wav, music(total, trek))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", outp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    first0 = fr(slides[0], bgs[0], bands[0], 0, True)
    for fi in range(nf):
        t = fi / FPS
        i = int(np.searchsorted(starts, t, side="right") - 1)
        img = single(i, t)
        te = starts[i] + dur[i] - t                      # сколько осталось у слайда
        if i < n - 1 and te < XF:                        # мягкая смена на следующий
            img = Image.blend(img, single(i + 1, t), 1 - te / XF)
        if total - t < LOOP:                             # петля — к первому кадру
            img = Image.blend(img, first0, 1 - (total - t) / LOOP)
        p.stdin.write(img.tobytes())
    p.stdin.close(); p.wait()
    os.remove(wav)
    with open(os.path.join(os.path.dirname(outp) or ".", "_музыка.txt"), "w", encoding="utf-8") as fh:
        fh.write((f"FreePD {src} (CC0)" if src else f"трек {trek + 1} из {len(TREKI)} (свой, синтез)") + f", длина {total:.1f} с, слайдов {n}\n")
    print(f"готово: {outp}  {total:.1f} с, слайдов {n}, {'ВО ВЕСЬ ЭКРАН 9:16' if full else 'С ПОЛОСАМИ (старый вид)'}, музыка — трек {trek + 1}")


if __name__ == "__main__":
    main()
