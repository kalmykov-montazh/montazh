# Картинки-предметы поверх готового ролика + предмет на обложке (правило с 03.11.2026,
# проба «ЖИЗНЬ Пятисотка в банке»). Запуск: python3 vstavki.py spec.json <папка ролика> <папка картинок>
# spec: {"cover": {...} | null, "inserts": [{img,t0,t1,x,y,ang,w,mode,stamp,frame}]}
#   mode: right / left (вылет сбоку), up (всплытие снизу с проявлением — для тёмно-синих вставок)
#   frame: true — фото в белой рамке (фото, скрины), false — предмет как есть (купюра, карта)
#   t1 больше длины ролика — предмет остаётся до конца без ухода
import json, sys, os, subprocess, wave
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageOps
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "sceny"))
from snd import snd, SR

FONT = os.path.join(os.path.dirname(__file__), "..", "fonts", "montserrat-900.ttf")

def card(src, w, ang, stamp=None, frame=False):
    n = Image.open(src).convert("RGBA")
    n = n.resize((w, round(w * n.height / n.width)), Image.LANCZOS)
    if frame:  # белая рамка со скруглением
        b = max(8, w // 40)
        f = Image.new("RGBA", (n.width + 2 * b, n.height + 2 * b), (255, 255, 255, 255))
        f.alpha_composite(n, (b, b))
        m = Image.new("L", f.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, *f.size), radius=b * 2, fill=255)
        f.putalpha(m); n = f
    if stamp:
        fs = max(30, w // 10)
        fo = ImageFont.truetype(FONT, fs)
        L = Image.new("RGBA", (w, fs * 3), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        bb = d.textbbox((0, 0), stamp, font=fo); tw, th = bb[2] - bb[0], bb[3] - bb[1]
        x0 = (w - tw) // 2; yc = fs * 3 // 2
        d.rounded_rectangle((x0 - fs // 2, yc - th // 2 - fs // 3, x0 + tw + fs // 2, yc + th // 2 + fs // 3), fs // 4, outline=(206, 22, 32, 235), width=max(5, fs // 7))
        d.text((x0, yc - th // 2 - bb[1]), stamp, font=fo, fill=(206, 22, 32, 235))
        L = L.rotate(14, expand=True, resample=Image.BICUBIC)
        n.alpha_composite(L, ((n.width - L.width) // 2 + w // 12, (n.height - L.height) // 2))
    pad = 40
    c = Image.new("RGBA", (n.width + 2 * pad, n.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", n.size, (0, 0, 0, 120)); sh.putalpha(n.getchannel("A").point(lambda a: a * 120 // 255))
    c.alpha_composite(sh, (pad + 8, pad + 14)); c = c.filter(ImageFilter.GaussianBlur(10)); c.alpha_composite(n, (pad, pad))
    return c.rotate(ang, expand=True, resample=Image.BICUBIC)

def cover_frames(video):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-frames:v", "20", "-vf", "scale=54:96,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    d = np.frombuffer(out, np.uint8).reshape(-1, 96, 54).astype(int)
    for i in range(1, len(d)):
        if abs(d[i] - d[0]).mean() > 20: return i
    return 0

def run(spec, folder, imgdir):
    name = os.path.basename(folder.rstrip("/"))
    vid = os.path.join(folder, f"!!! {name}.mp4"); cov = os.path.join(folder, "обложка.jpg")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", vid], capture_output=True, text=True).stdout)
    work = os.path.join("/tmp/vst", name); os.makedirs(work, exist_ok=True)
    ins = spec.get("inserts", [])
    for k, e in enumerate(ins):
        card(os.path.join(imgdir, e["img"]), e.get("w", 450), e.get("ang", 0), e.get("stamp"), e.get("frame", False)).save(f"{work}/i{k}.png")
    if spec.get("cover"):
        c = spec["cover"]; cv = Image.open(cov).convert("RGBA")
        a = card(os.path.join(imgdir, c["img"]), c.get("w", 450), c.get("ang", 0), c.get("stamp"), c.get("frame", False))
        cv.alpha_composite(a, (c["x"], c["y"])); cv.convert("RGB").save(f"{work}/cover.jpg", quality=93)
    else:
        Image.open(cov).convert("RGB").save(f"{work}/cover.jpg", quality=93)
    a = np.zeros(int((dur + 2) * SR)); w = snd("whoosh")
    for e in ins:
        i = max(0, int((e["t0"] - 0.08) * SR)); a[i:i + len(w)] += w * 0.35
    a = (np.clip(a, -1, 1) * 32767).astype(np.int16)
    with wave.open(f"{work}/wh.wav", "wb") as f: f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(a.tobytes())
    inp = ["-i", vid, "-loop", "1", "-i", f"{work}/cover.jpg"]; fl = []; last = "[0:v]"
    for k, e in enumerate(ins):
        t0, t1, X, Y, m = e["t0"], e["t1"], e["x"], e["y"], e.get("mode", "right")
        inp += ["-loop", "1", "-t", str(dur + 1), "-i", f"{work}/i{k}.png"]; j = k + 2
        p = f"min(1,max(0,(t-{t0})/0.28))"; q = f"min(1,max(0,(t-({t1}-0.22))/0.22))"
        if m in ("right", "left"):
            s = 1 if m == "right" else -1
            x = f"{X}+{s}*700*pow(1-{p},3)+{s}*700*pow({q},2)"; y = f"{Y}"
            fl.append(f"[{j}:v]format=rgba[s{k}]")
        else:
            x = f"{X}"; y = f"{Y}+220*pow(1-{p},3)"
            fl.append(f"[{j}:v]format=rgba,fade=t=in:st={t0}:d=0.25:alpha=1,fade=t=out:st={t1 - 0.18}:d=0.18:alpha=1[s{k}]")
        fl.append(f"{last}[s{k}]overlay=x='{x}':y='{y}':enable='between(t,{t0},{t1})':eval=frame[v{k}]"); last = f"[v{k}]"
    nc = cover_frames(vid)
    fl.append("[1:v]scale=1080:1920,format=yuv420p[cv]")
    fl.append(f"{last}[cv]overlay=0:0:enable='lt(n,{nc})'[vout]" if nc else f"{last}null[vout]")
    fl.append(f"[0:a]aresample=48000[a0];[{len(ins) + 2}:a]aresample=48000[a1];[a0][a1]amix=inputs=2:normalize=0:duration=first[aout]")
    out = f"{work}/out.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-i", f"{work}/wh.wav", "-filter_complex", ";".join(fl), "-map", "[vout]", "-map", "[aout]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-t", str(dur), out], check=True)
    return out, f"{work}/cover.jpg", nc

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1])); print(run(spec, sys.argv[2], sys.argv[3]))
