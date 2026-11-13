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


# ---------- сборка ----------
def main():
    folder = sys.argv[1]
    outp = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else os.path.join(folder, "shorts.mp4")
    trek = None
    if "--trek" in sys.argv: trek = int(sys.argv[sys.argv.index("--trek") + 1])
    files = sorted(p for p in glob.glob(os.path.join(folder, "[0-9][0-9].jpg")))
    if not files: sys.exit("нет 01.jpg, 02.jpg …")
    n = len(files)
    dur = durations(folder, n)
    slides = [Image.open(p).convert("RGB").resize((SW, SH)) for p in files]
    bgs = [make_bg(s) for s in slides]
    bands = [site_band(i == n - 1) for i in range(n)]
    starts = np.cumsum([0] + dur[:-1])
    total = float(sum(dur))
    nf = int(round(total * FPS))

    def single(i, t):
        k = min(1, max(0, (t - starts[i]) / (dur[i] + XF)))
        return frame_of(slides[i], bgs[i], bands[i], k, i % 2 == 0)

    if trek is None: trek = int(hashlib.md5(os.path.basename(os.path.abspath(folder)).encode()).hexdigest(), 16) % len(TREKI)
    wav = outp + ".wav"
    write_wav(wav, music(total, trek))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", outp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    first0 = frame_of(slides[0], bgs[0], bands[0], 0, True)
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
        fh.write(f"трек {trek + 1} из {len(TREKI)} (свой, синтез), длина {total:.1f} с, слайдов {n}\n")
    print(f"готово: {outp}  {total:.1f} с, слайдов {n}, музыка — трек {trek + 1}")


if __name__ == "__main__":
    main()
