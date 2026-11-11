# 11.11.2026 (Евгений 21:37: «давай пропишем в монтаж и это»): «МИР ЗА СПИНОЙ» прямо в монтаже.
# Меняет фон за спиной на 1–3 отрезках ролика по полю "mir" в novyj/<ключ>.json. Сам Евгений остаётся живым кадром.
#
#   python3 hf/mir.py <osnova.mp4> <novyj.json> <osnova_words.json> <face.json> <out.mp4>
#
# "mir": [{"at": "фраза начала", "to": "фраза, где фон возвращается" | "dur": 3.5,
#          "src": "ves:<путь на Диске к видео или фото>" | "montazh:<путь в Монтаж!>",
#          "from": 2.0   (секунда, с которой брать видео-фон, необязательно)}]
# Правила (пробы 11.11): только целые чёткие кадры фона, без растяжения; фото — с медленным наездом;
# человек чуть подстраивается по цвету к фону (30%), мягкие края маски; синее кресло срезается маской по человеку.
# Маска человека — rembg u2net_human_seg (ставится сам). Звук не трогается, длина не меняется.
import os, sys, json, re, subprocess, shutil, tempfile
import numpy as np
from PIL import Image, ImageFilter

OSN, SPEC, WORDS, FACE, OUT = sys.argv[1:6]
spec = json.load(open(SPEC))
MIR = spec.get("mir") or []
if not MIR:
    shutil.copy(OSN, OUT); print("мир: поле mir пустое — без изменений"); sys.exit(0)
words = json.load(open(WORDS))


def norm(s): return re.sub(r"[^\wё%]", "", str(s).lower().replace("ё", "е"))


def find(phrase, after=0.0):
    ph = [norm(x) for x in str(phrase).split() if norm(x)]
    lw, ls, le = [], [], []
    for w in words:
        for x in str(w["w"]).split():
            lw.append(norm(x)); ls.append(w["s"]); le.append(w.get("e", w["s"] + 0.3))
    for i in range(len(lw)):
        if ls[i] + 0.01 < after: continue
        if ph and all(i + k < len(lw) and lw[i + k].startswith(ph[k][:max(3, len(ph[k]) - 2)]) for k in range(len(ph))):
            return ls[i], le[min(i + len(ph) - 1, len(le) - 1)]
    return None


def probe(f, what):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", what, "-of", "csv=p=0", f],
                          capture_output=True, text=True).stdout.strip().split(",")[0]


fr = probe(OSN, "stream=r_frame_rate"); num, den = (fr.split("/") + ["1"])[:2]; FPS = float(num) / float(den or 1)
DUR = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", OSN],
                           capture_output=True, text=True).stdout.strip())
try:
    from rembg import remove, new_session
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "rembg", "onnxruntime"], check=True)
    from rembg import remove, new_session
SESS = new_session("u2net_human_seg")

T = tempfile.mkdtemp(prefix="mir_")
segs = []
for k, m in enumerate(MIR):
    a = find(m.get("at", ""))
    if not a: print(f"мир: фраза «{m.get('at')}» не найдена — пропуск"); continue
    t0 = max(0.0, a[0] - 0.05)
    if m.get("to"):
        b = find(m["to"], after=a[1])
        t1 = b[0] if b else t0 + float(m.get("dur", 3.5))
    else:
        t1 = t0 + float(m.get("dur", 3.5))
    t1 = min(t1, DUR - 0.1, t0 + 6.0)
    if t1 - t0 < 1.0: print("мир: отрезок короче секунды — пропуск"); continue
    if any(not (t1 <= s0 or t0 >= s1) for s0, s1, _ in segs): print("мир: отрезки пересекаются — пропуск"); continue
    src = m["src"]; ext = os.path.splitext(src)[1].lower() or ".mp4"
    loc = f"{T}/bg{k}{ext}"
    if src.startswith(("ves:", "montazh:")):
        r = subprocess.run(["rclone", "copyto", src, loc])
        if r.returncode or not os.path.exists(loc): print("мир: фон не скачался —", src); continue
    elif os.path.exists(src): shutil.copy(src, loc)
    else: print("мир: нет фона —", src); continue
    segs.append((t0, t1, (loc, float(m.get("from", 0)))))
    print(f"мир: {t0:.1f}–{t1:.1f} с ← {os.path.basename(src)}")

if not segs:
    shutil.copy(OSN, OUT); print("мир: ни одного отрезка — без изменений"); sys.exit(0)

W, H = 1080, 1920
filt = []
inputs = ["-i", OSN]
for k, (t0, t1, (bg, frm)) in enumerate(segs):
    n = int(round((t1 - t0) * FPS))
    d = f"{T}/s{k}"; os.makedirs(f"{d}/p", exist_ok=True); os.makedirs(f"{d}/b", exist_ok=True); os.makedirs(f"{d}/o", exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-i", OSN, "-frames:v", str(n), "-vf", f"scale={W}:{H}", f"{d}/p/%05d.png"], check=True)
    isimg = os.path.splitext(bg)[1].lower() in (".jpg", ".jpeg", ".png", ".webp", ".heic")
    if isimg:
        # фото: целиком по высоте кадра, медленный наезд 1.00 → 1.08, без растяжения
        z = f"zoompan=z='1+0.08*on/{max(n,1)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS:.3f}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", bg, "-vf",
                        f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},{z}", "-frames:v", str(n), f"{d}/b/%05d.png"], check=True)
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{frm:.2f}", "-i", bg, "-vf",
                        f"fps={FPS:.3f},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-frames:v", str(n), f"{d}/b/%05d.png"], check=True)
    pf = sorted(os.listdir(f"{d}/p")); bf = sorted(os.listdir(f"{d}/b"))
    if not bf: print("мир: фон пустой — пропуск отрезка"); continue
    prev = None
    for i, f in enumerate(pf):
        P = Image.open(f"{d}/p/{f}").convert("RGB"); B = Image.open(f"{d}/b/{bf[min(i, len(bf) - 1)]}").convert("RGB")
        if i % 2 == 0 or prev is None:   # маска раз в 2 кадра — экономия времени, движение головы плавное
            prev = remove(P.resize((540, 960)), session=SESS, only_mask=True).resize((W, H)).filter(ImageFilter.GaussianBlur(2))
        M = prev
        pa = np.asarray(P).astype(np.float32); ba = np.asarray(B).astype(np.float32); ma = np.asarray(M).astype(np.float32)[..., None] / 255.0
        # синее кресло за спиной вырезаем из маски по цвету (правило пробы 11.11)
        # 12.11.2026: только тёмно-насыщенный синий кресла (R низкий, G меньше половины B) —
        # старое правило вырезало голубые и серо-голубые рубашки, фон «съедал» плечи
        blue = (pa[..., 2] > 70) & (pa[..., 0] < 70) & (pa[..., 1] < pa[..., 2] * 0.5)
        if blue.any():
            bm_ = Image.fromarray((blue * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2))
            ma = ma * (1 - np.asarray(bm_).astype(np.float32)[..., None] / 255.0)
        # свет под фон: человек на 30% к среднему цвету фона, яркость ближе на 18%
        msk = ma[..., 0] > 0.5
        if msk.any():
            pm = pa[msk].mean(0); bm = ba.mean((0, 1))
            pa = np.clip(pa + (bm - pm) * 0.30 + (bm.mean() - pm.mean()) * 0.18 * 0.3, 0, 255)
        # мягкая тень за человеком
        sh = np.asarray(M.filter(ImageFilter.GaussianBlur(18))).astype(np.float32)[..., None] / 255.0
        ba = ba * (1 - 0.25 * sh)
        o = pa * ma + ba * (1 - ma)
        Image.fromarray(o.astype(np.uint8)).save(f"{d}/o/{f}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", f"{FPS:.3f}", "-i", f"{d}/o/%05d.png", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", f"{d}/seg.mp4"], check=True)
    inputs += ["-itsoffset", f"{t0:.3f}", "-i", f"{d}/seg.mp4"]

# склейка: отрезки накладываются поверх основы точно на своё время, остальное и звук — без изменений
chain = "[0:v]"
for k, (t0, t1, _) in enumerate(segs):
    lab = f"[v{k}]"
    filt.append(f"{chain}[{k+1}:v]overlay=enable='between(t,{t0:.3f},{t1:.3f})':eof_action=pass{lab}")
    chain = lab
r = subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(filt), "-map", chain, "-map", "0:a?",
                    "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy", OUT])
if r.returncode: sys.exit(r.returncode)
print(f"мир: готово, отрезков {len(segs)}")
