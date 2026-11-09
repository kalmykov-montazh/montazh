# Склейка нового шортса из кусков готовых основ (решение Евгения 09.11.2026: банк кусков → конструктор шортов).
# Основа (osnova.mp4 + osnova_words.json) уже ускорена 1.2, без пауз и кряхтения, кадрирована — режем её по словам,
# стыкуем и отдаём дальше в обычный HF-монтаж (build_auto + рендер + субтитры «микс»).
# Запуск: python hf/skleika.py <item.json> <папка с основами: in/<ключ>/> <выход>
# item: {"parts": [{"key": "...", "from": "первые слова", "to": "последние слова"}, ...]}
import json, os, re, subprocess, sys

item = json.load(open(sys.argv[1])); IN, OUT = sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

def norm(s): return re.sub(r"[^\wё%]", "", s.lower().replace("ё", "е"))

def find_seq(W, phrase, after=0.0, end=False):
    ph = [norm(x) for x in phrase.split() if norm(x)]
    lw = [norm(w["w"]) for w in W]
    for i in range(len(lw)):
        if W[i]["s"] + 0.01 < after: continue
        if all(i + k < len(lw) and (lw[i + k] == ph[k] or (len(ph[k]) > 3 and lw[i + k].startswith(ph[k][:max(3, len(ph[k]) - 2)]))) for k in range(len(ph))):
            return i + len(ph) - 1 if end else i
    raise SystemExit(f"не нашёл «{phrase}» после {after:.2f} с")

def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())

words, faces, segs, off = [], [], [], 0.0
for n, p in enumerate(item["parts"]):
    d = f"{IN}/{p['key']}"
    W = json.load(open(f"{d}/osnova_words.json"))
    i0 = find_seq(W, p["from"], float(p.get("after", 0)))
    i1 = find_seq(W, p["to"], W[i0]["s"], end=True)
    D = dur(f"{d}/osnova.mp4")
    t0 = W[i0]["s"] - 0.07
    if i0 > 0: t0 = max(t0, W[i0 - 1]["e"] + 0.03)
    t0 = max(0.0, t0)
    t1 = W[i1]["e"] + 0.16
    if i1 + 1 < len(W): t1 = min(t1, W[i1 + 1]["s"] - 0.03)
    t1 = min(t1, D)
    seg = f"{OUT}/seg{n}.mp4"
    L = t1 - t0
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-i", f"{d}/osnova.mp4", "-t", f"{L:.3f}",
                    "-vf", "fps=30,format=yuv420p", "-af", f"aresample=48000,afade=t=in:d=0.03,afade=t=out:st={max(0, L - 0.05):.3f}:d=0.05",
                    "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-c:a", "pcm_s16le", f"{OUT}/seg{n}.mkv"], check=True)
    L = dur(f"{OUT}/seg{n}.mkv")
    for w in W[i0:i1 + 1]:
        words.append({**w, "s": round(w["s"] - t0 + off, 3), "e": round(w["e"] - t0 + off, 3)})
    if os.path.exists(f"{d}/face.json"): faces.append(json.load(open(f"{d}/face.json")))
    print(f"кусок {n}: {p['key']} {t0:.2f}–{t1:.2f} ({L:.2f} с) «{W[i0]['w']} … {W[i1]['w']}»")
    segs.append(f"{OUT}/seg{n}.mkv"); off += L

lst = f"{OUT}/list.txt"
open(lst, "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in segs))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-crf", "13",
                "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"{OUT}/osnova.mp4"], check=True)
json.dump(words, open(f"{OUT}/osnova_words.json", "w"), ensure_ascii=False)
# голова выше всех — по ней место для плашек (чтобы плашки ни в одном куске не легли на голову)
if faces:
    f = min(faces, key=lambda x: x["EYE"] - 0.72 * x["HN"])
    json.dump(f, open(f"{OUT}/face.json", "w"))
print(f"итого {off:.1f} с, {len(words)} слов")
