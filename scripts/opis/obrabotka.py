# Опись архива Google Фото (с 08.11.2026, просьба Евгения): по каждому файлу
# дата, время, место (GPS → город), камера, длительность, ориентация, звук (моно/один канал),
# теги CLIP (что в кадре), эмбеддинг CLIP для поиска по смыслу, расшифровка речи (видео).
# Итог шарда — results.jsonl + миниатюры + emb.npy в рабочую папку на Диске.
# Ничего личного в лог не печатать: репозиторий публичный.
import json, os, subprocess, sys, time, hashlib, glob, traceback
import numpy as np
from PIL import Image, ImageOps
try:
    import pillow_heif; pillow_heif.register_heif_opener()
except Exception: pass

SHARD = int(os.environ["SHARD"]); OUT = os.environ.get("OUT", "out")
os.makedirs(f"{OUT}/thumbs", exist_ok=True)
man = [x for x in json.load(open("manifest.json")) if x["shard"] == SHARD]
done = set()
if os.path.exists(f"{OUT}/results.jsonl"):
    for l in open(f"{OUT}/results.jsonl", encoding="utf-8"):
        try: done.add(json.loads(l)["path"])
        except Exception: pass
VID = (".mp4", ".mov", ".3gp", ".avi", ".mkv", ".m4v", ".mts")

def sh(*a, **k):
    return subprocess.run(a, capture_output=True, text=True, **k)

# ---- CLIP
import torch, open_clip
torch.set_num_threads(4)
model, _, prep = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
model.eval(); tok = open_clip.get_tokenizer("ViT-B-32")
TAGS = json.load(open("scripts/opis/tags.json", encoding="utf-8"))  # [[en, ru], ...]
with torch.no_grad():
    T = model.encode_text(tok([f"a photo of {e}" for e, r in TAGS])); T /= T.norm(dim=-1, keepdim=True)

def clip(imgs):
    with torch.no_grad():
        x = torch.stack([prep(i.convert("RGB")) for i in imgs])
        E = model.encode_image(x); E /= E.norm(dim=-1, keepdim=True)
    e = E.mean(0); e /= e.norm()
    p = (100 * E @ T.T).softmax(-1).max(0).values
    top = [(TAGS[i][1], round(float(p[i]), 2)) for i in p.argsort(descending=True)[:6] if p[i] > 0.04]
    return e.numpy().astype(np.float16), top

# ---- речь
from faster_whisper import WhisperModel
wm = WhisperModel(os.environ.get("WMODEL", "medium"), device="cpu", compute_type="int8", cpu_threads=4,
                  download_root="models")

# ---- место
import reverse_geocoder as rg

def gps(meta):
    la, lo = meta.get("GPSLatitude"), meta.get("GPSLongitude")
    if la is None or lo is None:
        pos = meta.get("GPSCoordinates") or meta.get("GPSPosition")
        if isinstance(pos, str) and len(pos.split()) >= 2:
            try: la, lo = [float(v.rstrip(",")) for v in pos.replace(",", " ").split()[:2]]
            except Exception: pass
    try: la, lo = float(la), float(lo)
    except Exception: return None
    if abs(la) < 0.001 and abs(lo) < 0.001: return None
    r = rg.search([(la, lo)], mode=1)[0]
    return {"lat": round(la, 5), "lon": round(lo, 5), "city": r["name"], "region": r["admin1"], "cc": r["cc"]}

def when(meta, name):
    for k in ("DateTimeOriginal", "CreateDate", "MediaCreateDate", "TrackCreateDate", "ModifyDate"):
        v = meta.get(k)
        if v and not str(v).startswith("0000"): return str(v)[:19].replace(":", "-", 2), k
    import re
    m = re.search(r"(20\d\d|19\d\d)(\d\d)(\d\d)[_-]?(\d\d)(\d\d)(\d\d)", name)
    if m: return f"{m[1]}-{m[2]}-{m[3]} {m[4]}:{m[5]}:{m[6]}", "имя"
    return None, None

def channels_silent(f):
    # один канал тихий (моно с внешнего микрофона) — у Евгения так у многих старых видео
    r = sh("ffmpeg", "-v", "info", "-t", "120", "-i", f, "-af", "astats=measure_overall=none:measure_perchannel=RMS_level", "-f", "null", "-")
    lv = [float(l.split(":")[-1]) for l in r.stderr.splitlines() if "RMS level dB" in l and "inf" not in l.split(":")[-1]]
    if len(lv) >= 2 and abs(lv[0] - lv[1]) > 25: return "один канал"
    return "стерео" if len(lv) >= 2 else ("моно" if len(lv) == 1 else "тихо")

out = open(f"{OUT}/results.jsonl", "a", encoding="utf-8")
embs = {}
if os.path.exists(f"{OUT}/emb.npz"):
    z = np.load(f"{OUT}/emb.npz"); embs = {k: z[k] for k in z.files}
t0 = time.time(); n = 0; err = 0
for it in man:
    p = it["path"]
    if p in done: continue
    if time.time() - t0 > float(os.environ.get("BUDGET", 19000)): print("бюджет времени исчерпан"); break
    key = hashlib.md5(p.encode()).hexdigest()[:16]
    loc = "w/" + key + os.path.splitext(p)[1].lower(); os.makedirs("w", exist_ok=True)
    rec = {"path": p, "id": key, "size": it["size"]}
    try:
        r = sh("rclone", "copyto", it["remote"], loc, "--retries", "3")
        if r.returncode or not os.path.exists(loc): raise RuntimeError("скачать: " + r.stderr[-300:])
        meta = json.loads(sh("exiftool", "-j", "-n", "-api", "LargeFileSupport=1", loc).stdout or "[{}]")[0]
        rec["when"], rec["when_src"] = when(meta, os.path.basename(p))
        rec["geo"] = gps(meta)
        rec["camera"] = " ".join(str(meta.get(k, "")) for k in ("Make", "Model")).strip() or meta.get("AndroidModel") or None
        isv = p.lower().endswith(VID); rec["kind"] = "video" if isv else "photo"
        if isv:
            pr = json.loads(sh("ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", loc).stdout or "{}")
            vs = [s for s in pr.get("streams", []) if s.get("codec_type") == "video"]
            au = [s for s in pr.get("streams", []) if s.get("codec_type") == "audio"]
            d = float(pr.get("format", {}).get("duration", 0) or 0); rec["dur"] = round(d, 1)
            if vs:
                w, h = vs[0].get("width", 0), vs[0].get("height", 0)
                rot = 0
                for sd in vs[0].get("side_data_list", []) or []:
                    rot = int(sd.get("rotation", 0) or 0)
                rot = rot or int((vs[0].get("tags") or {}).get("rotate", 0) or 0)
                if abs(rot) in (90, 270): w, h = h, w
                rec["wh"] = f"{w}x{h}"; rec["orient"] = "верт" if h > w else ("гор" if w > h else "квадрат")
                rec["fps"] = vs[0].get("avg_frame_rate")
            rec["audio"] = channels_silent(loc) if au else "без звука"
            frames = []
            for k, fr in enumerate((0.1, 0.35, 0.6, 0.85)):
                fp = f"w/{key}_{k}.jpg"
                sh("ffmpeg", "-v", "error", "-ss", f"{max(0.0, d * fr):.2f}", "-i", loc, "-frames:v", "1", "-vf", "scale=320:-2", "-y", fp)
                if os.path.exists(fp): frames.append(Image.open(fp).copy())
            if frames:
                W = sum(f.width for f in frames); H = max(f.height for f in frames)
                strip = Image.new("RGB", (W, H)); x = 0
                for f in frames: strip.paste(f, (x, 0)); x += f.width
                strip.save(f"{OUT}/thumbs/{key}.jpg", quality=72)
                e, top = clip(frames); embs[key] = e; rec["tags"] = top
            if au and d > 1.5:
                pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", loc, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
                audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
                segs, info = wm.transcribe(audio, beam_size=1, vad_filter=True, condition_on_previous_text=False)
                txt = []
                for s in segs:
                    txt.append(f"[{int(s.start)}] {s.text.strip()}")
                rec["lang"] = info.language; rec["speech"] = " ".join(txt)[:6000]
        else:
            im = ImageOps.exif_transpose(Image.open(loc)); im.load()
            rec["wh"] = f"{im.width}x{im.height}"; rec["orient"] = "верт" if im.height > im.width else "гор"
            th = im.convert("RGB"); th.thumbnail((384, 384)); th.save(f"{OUT}/thumbs/{key}.jpg", quality=72)
            e, top = clip([th]); embs[key] = e; rec["tags"] = top
            rec["screenshot"] = "screenshot" in p.lower() or "скрин" in p.lower()
    except Exception as ex:
        rec["error"] = str(ex)[-400:]; err += 1
    for f in glob.glob(f"w/{key}*"): os.remove(f)
    out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush(); n += 1
    if n % 50 == 0:
        np.savez(f"{OUT}/emb.npz", **embs)
        print(f"шард {SHARD}: {n} готово, ошибок {err}, {int(time.time() - t0)} с", flush=True)
np.savez(f"{OUT}/emb.npz", **embs)
print(f"шард {SHARD}: итог {n}, ошибок {err}, всего в шарде {len(man)}, уже было {len(done)}")
