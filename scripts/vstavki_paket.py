# Пакет вставок-картинок по плану (04.11.2026): python3 vstavki_paket.py plan.json
# plan.json: {"<имя ролика>": {"key": "<папка в работа/>", "cover": {"img":..., ...} | null,
#              "ins": [["<слова-якорь>", "<картинка>", {доп: stamp, w, frame}], ...]}}
# Для каждого ролика: качает «!!!», обложку, words_out.json, ищет якорь в тексте готового ролика,
# собирает вставки через vstavki.py, кладёт ролик и обложку обратно, лист проверки — в pics/<имя>.jpg
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import vstavki

B = "montazh:Брокер"
IMG = "imgs"   # все картинки сюда (Предметы + Предметы_ov), имя файла = имя картинки
norm = lambda s: re.sub(r'[^\wа-я0-9%]', '', s.lower().replace('ё', 'е'))

def rc(*a): subprocess.run(["rclone", *a], check=True, stdin=subprocess.DEVNULL)

def resolve(words, dur, ins):
    toks = [norm(w['w']) for w in words]; res = []; pos = 0
    for ph, img, opt in ins:
        pt = [p for p in (norm(x) for x in ph.split()) if p]; hit = None
        for i in range(pos, len(toks)):
            if all(i + j < len(toks) and toks[i + j].startswith(pt[j]) for j in range(len(pt))): hit = i; break
        if hit is None: print("  НЕТ ЯКОРЯ", ph); continue
        res.append([max(0.5, words[hit]['s']), img, opt]); pos = hit + 1
    out = []
    for k, (t0, img, opt) in enumerate(res):
        nxt = res[k + 1][0] - 0.3 if k + 1 < len(res) else dur - 0.2
        e = {"img": img, "t0": round(t0, 2), "t1": round(min(t0 + 2.6, nxt), 2), "slot": "br" if k % 2 == 0 else "bl",
             "ang": 6 if k % 2 == 0 else -6, "w": 470, "frame": True}
        e.update(opt); out.append(e)
    if out and out[-1]["t1"] >= dur - 0.5: out[-1]["t1"] = 99
    return out

def main():
    plan = json.load(open(sys.argv[1]))
    os.makedirs("pics", exist_ok=True)
    for name, p in plan.items():
        print("==", name, flush=True)
        d = f"v/{name}"; os.makedirs(d, exist_ok=True)
        try:
            rc("copy", f"{B}/На проверке/{name}", d, "--include", f"!!! {name}.mp4", "--include", "обложка.jpg")
            rc("copyto", f"{B}/работа/{p['key']}/words_out.json", f"{d}/words.json")
            words = json.load(open(f"{d}/words.json"))
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{d}/!!! {name}.mp4"], capture_output=True, text=True).stdout)
            spec = {"cover": p.get("cover"), "inserts": resolve(words, dur, p["ins"])}
            if spec["cover"]: spec["cover"] = {"slot": "br", "ang": 7, "w": 470, "frame": True, **spec["cover"]}
            print("  ", [(e["t0"], e["img"]) for e in spec["inserts"]], flush=True)
            out, cov, nc = vstavki.run(spec, d, IMG)
            rc("copyto", out, f"{B}/На проверке/{name}/!!! {name}.mp4")
            rc("copyto", cov, f"{B}/На проверке/{name}/обложка.jpg")
            # лист проверки: обложка + середина каждой вставки
            ts = [0.05] + [min(e["t0"] + 1.0, dur - 0.1) for e in spec["inserts"]]
            fr = []
            for i, t in enumerate(ts):
                f = f"{d}/k{i}.png"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", out, "-frames:v", "1", "-vf", "scale=270:480", f], check=True)
                fr.append(f)
            subprocess.run(["ffmpeg", "-v", "error", "-y", *sum([["-i", f] for f in fr], []), "-filter_complex",
                            "".join(f"[{i}:v]" for i in range(len(fr))) + f"hstack=inputs={len(fr)}" if len(fr) > 1 else "null", f"pics/{name}.jpg"], check=True)
            print("  готово", flush=True)
        except Exception as e:
            print("  ОШИБКА", e, flush=True)
        subprocess.run(["rm", "-rf", d, f"/tmp/vst/{name}"])

if __name__ == "__main__":
    main()
