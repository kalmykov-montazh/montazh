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

import numpy as np

def pcm(f):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", f, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"])
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def quiet(a, lo, hi, prefer):
    """самая тихая точка (окно 40 мс) между lo и hi; при равной тишине — ближе к prefer"""
    lo, hi = max(0.0, lo), max(lo + 0.05, hi)
    best, bt = None, prefer
    t = lo
    while t <= hi:
        i0, i1 = int((t - 0.02) * 16000), int((t + 0.02) * 16000)
        seg = a[max(0, i0):max(1, i1)]
        r = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 1.0
        r += abs(t - prefer) * 0.002
        if best is None or r < best: best, bt = r, t
        t += 0.01
    return bt

# соседние куски одного ролика (кончается слово i, следующий начинается с i+1) — один кусок, без стыка
parts, prev = [], None
for p in item["parts"]:
    W = json.load(open(f"{IN}/{p['key']}/osnova_words.json"))
    i0 = find_seq(W, p["from"], float(p.get("after", 0)))
    i1 = find_seq(W, p["to"], W[i0]["s"], end=True)
    if prev and prev["key"] == p["key"] and prev["i1"] + 1 == i0:
        prev["i1"] = i1; continue
    prev = {"key": p["key"], "i0": i0, "i1": i1}; parts.append(prev)

words, faces, segs, off = [], [], [], 0.0
for n, p in enumerate(parts):
    d = f"{IN}/{p['key']}"
    W = json.load(open(f"{d}/osnova_words.json")); i0, i1 = p["i0"], p["i1"]
    D = dur(f"{d}/osnova.mp4"); A = pcm(f"{d}/osnova.mp4")
    s0 = W[i0]["s"]; pe = W[i0 - 1]["e"] if i0 > 0 else max(0.0, s0 - 0.4)
    # первый кусок ролика-основы: основа и так начинается с первого слова — берём с самого начала
    t0 = 0.0 if i0 == 0 else quiet(A, max(pe, s0 - 0.35), s0 - 0.02, s0 - 0.08)
    e1 = W[i1]["e"]; ns = W[i1 + 1]["s"] if i1 + 1 < len(W) else min(D, e1 + 0.5)
    t1 = quiet(A, e1 - 0.06, min(ns, e1 + 0.45), e1 + 0.1)
    t1 = min(t1, D)
    L = t1 - t0
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-i", f"{d}/osnova.mp4", "-t", f"{L:.3f}",
                    "-vf", "fps=30,format=yuv420p", "-af", f"aresample=48000,afade=t=in:d=0.02,afade=t=out:st={max(0, L - 0.03):.3f}:d=0.03",
                    "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-c:a", "pcm_s16le", f"{OUT}/seg{n}.mkv"], check=True)
    L = dur(f"{OUT}/seg{n}.mkv")
    for w in W[i0:i1 + 1]:
        words.append({**w, "s": round(max(0, w["s"] - t0) + off, 3), "e": round(min(L, w["e"] - t0) + off, 3)})
    if os.path.exists(f"{d}/face.json"): faces.append(json.load(open(f"{d}/face.json")))
    print(f"кусок {n}: {p['key']} {t0:.2f}–{t1:.2f} ({L:.2f} с) «{W[i0]['w']} … {W[i1]['w']}»")
    segs.append(f"{OUT}/seg{n}.mkv"); off += L

# правка распознавания для субтитров: {"неверно": "верно"}, ключ может быть из нескольких слов (сливаются в одно)
FIX = item.get("fix") or {}
def _n(x): return re.sub(r"[^\wё%]", "", x.lower())
for k_, v_ in sorted(FIX.items(), key=lambda kv: -len(kv[0].split())):
    ks = [_n(x) for x in k_.split()]
    i = 0
    while i + len(ks) <= len(words):
        if [_n(words[i + j]["w"]) for j in range(len(ks))] == ks:
            tail = re.sub(r"^.*?([.,!?:;»]*)$", r"\1", words[i + len(ks) - 1]["w"])
            words[i] = {**words[i], "w": v_ + (tail if not re.search(r"[.,!?:;»]$", v_) else ""), "e": words[i + len(ks) - 1]["e"]}
            del words[i + 1:i + len(ks)]
        i += 1

words = [w for w in words if re.sub(r"[^\wё%]", "", w["w"])]

lst = f"{OUT}/list.txt"
open(lst, "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in segs))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-crf", "13",
                "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"{OUT}/osnova.mp4"], check=True)
json.dump(words, open(f"{OUT}/osnova_words.json", "w"), ensure_ascii=False)
print("ТЕКСТ:", " ".join(w["w"] for w in words))
# голова выше всех — по ней место для плашек (чтобы плашки ни в одном куске не легли на голову)
if faces:
    f = min(faces, key=lambda x: x["EYE"] - 0.72 * x["HN"])
    json.dump(f, open(f"{OUT}/face.json", "w"))
print(f"итого {off:.1f} с, {len(words)} слов")
