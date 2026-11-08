# Список файлов для описи: «Архив Google Фото» целиком + старая папка «Google Фото»
# (2011–2019, синхронизация с компьютера) без дублей по имени и размеру. Делит на шарды по объёму.
import json, os, sys
N = int(os.environ.get("SHARDS", 28))
MED = (".jpg", ".jpeg", ".png", ".heic", ".gif", ".webp", ".mp4", ".mov", ".3gp", ".avi", ".mkv", ".m4v", ".mts")
items = []
seen = set()
for x in json.load(open("arh.json")):
    if not x["Name"].lower().endswith(MED): continue
    items.append({"path": "Архив Google Фото/" + x["Path"], "remote": "montazh:Брокер/Архив Google Фото/" + x["Path"], "size": x["Size"]})
    seen.add((x["Name"].lower(), x["Size"]))
dup = 0
for x in json.load(open("old.json")):
    if not x["Name"].lower().endswith(MED): continue
    if (x["Name"].lower(), x["Size"]) in seen: dup += 1; continue
    items.append({"path": "Google Фото (старая)/" + x["Path"], "remote": "ves:Google Фото/" + x["Path"], "size": x["Size"]})
    seen.add((x["Name"].lower(), x["Size"]))
only = os.environ.get("ONLY", "")
if only: items = [i for i in items if only in i["path"]]
# видео тяжелее по времени — вес = размер + 40 МБ за видео (расшифровка)
def w(i): return i["size"] + (40e6 if i["path"].lower().endswith(MED[6:]) else 2e6)
load = [0.0] * N
for i in sorted(items, key=w, reverse=True):
    k = load.index(min(load)); i["shard"] = k; load[k] += w(i)
json.dump(items, open("manifest.json", "w"), ensure_ascii=False)
v = sum(1 for i in items if i["path"].lower().endswith(MED[6:]))
print(f"файлов {len(items)}, видео {v}, фото {len(items) - v}, дублей старой папки пропущено {dup}, шардов {N}")
print("matrix=" + json.dumps(sorted({i['shard'] for i in items})))
