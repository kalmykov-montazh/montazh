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
#  6) лёгкая фоновая музыка, СВОЯ (синтез, без чужих треков и Content ID): мягкий пэд + пианино-переборы,
#     без бита и электроники; 6 мелодий-вариантов, вариант по названию папки (или --trek N), громкость фоновая,
#     вход 0,5 с, выход 1,5 с, конец музыки = конец видео. Какой трек — пишется в _музыка.txt.
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
TREKI = [  # (тоника Гц, лад, темп уд/мин, рисунок)
    (261.63, [0, 7, 9, 5], 78, "arp"),   # C: I–V–vi–IV
    (293.66, [0, 5, 9, 7], 72, "arp"),   # D: I–IV–vi–V
    (246.94, [9, 5, 0, 7], 80, "bro"),   # B♭-ish: vi–IV–I–V
    (220.00, [0, 9, 5, 7], 70, "arp"),   # A: I–vi–IV–V
    (329.63, [0, 7, 5, 5], 84, "bro"),   # E: I–V–IV–IV
    (277.18, [5, 0, 7, 9], 76, "arp"),   # C♯: IV–I–V–vi
]


def chord(root_semi, minor):
    return [root_semi, root_semi + (3 if minor else 4), root_semi + 7]


def note(freq, dur, amp, kind="piano"):
    t = np.arange(int(dur * SR)) / SR
    if kind == "piano":
        env = np.exp(-t * 3.2) * (1 - np.exp(-t * 200))
        w = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) * np.exp(-t * 5) + 0.12 * np.sin(6 * np.pi * freq * t) * np.exp(-t * 8)
    else:  # мягкий пэд
        a = min(0.8, dur / 3)
        env = np.minimum(1, t / a) * np.minimum(1, (dur - t) / a)
        w = sum(np.sin(2 * np.pi * freq * (1 + dt) * t) for dt in (-0.003, 0, 0.003)) / 3
    return amp * env * w


def music(total, idx):
    tonic, prog, bpm, pat = TREKI[idx % len(TREKI)]
    beat = 60 / bpm
    bar = beat * 4
    out = np.zeros(int((total + 3) * SR))
    f = lambda s: tonic * 2 ** (s / 12)
    t0, b = 0.0, 0
    while t0 < total + 1:
        r = prog[b % 4]
        ch = chord(r, r in (9, 2, 4))
        i0 = int(t0 * SR)
        pad = sum(note(f(s - 12), bar + 0.6, 0.06, "pad") for s in ch)
        out[i0:i0 + len(pad)] += pad[:len(out) - i0]
        bass = note(f(r - 24), bar, 0.10)
        out[i0:i0 + len(bass)] += bass[:len(out) - i0]
        seq = [ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[1], ch[0] + 12, ch[2]] if pat == "arp" else [ch[0], ch[2], ch[1] + 12, ch[2]] * 2
        for j, s in enumerate(seq):
            tt = t0 + j * beat / 2
            n = note(f(s), 1.6, 0.07 if j % 2 else 0.09)
            k = int(tt * SR)
            if k < len(out): out[k:k + len(n)] += n[:len(out) - k]
        t0 += bar; b += 1
    # «зал»: несколько затухающих отражений
    rev = out.copy()
    for dly, g in ((0.11, 0.25), (0.23, 0.16), (0.37, 0.10)):
        k = int(dly * SR); rev[k:] += g * out[:-k]
    out = rev[:int(total * SR)]
    n = len(out); t = np.arange(n) / SR
    out *= np.minimum(1, t / 0.5) * np.minimum(1, (total - t) / 1.5)
    out = out / (np.max(np.abs(out)) + 1e-9) * 10 ** (-11 / 20)   # пик −11 dBFS, на слух фон
    st = np.stack([out, np.roll(out, int(0.012 * SR))], 1)       # лёгкая ширина
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
