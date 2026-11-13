# 13.11.2026: опись роликов для перерисовки обложек крупно (oblozhki-krupno.yml).
# python3 oblozhki_opis.py all.txt _blotato.json lock.txt "<номера>"  → opis.txt (для глаз) + items.json (для матрицы)
# Ключ ролика ищется по имени файла «!!! <имя>.mp4» в списках пачек hf/pachka/*.json и hf/skleiki/*.json (поле name → key).
# Пропускаем: нет ключа или novyj/<ключ>.json без cover (старый монтаж), ролик уже в Blotato, «К публикации» при живом замке.
import sys, os, re, json, glob

ALL, BL, LOCK, ONLY = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else ""
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

names = {}
for f in sorted(glob.glob("hf/pachka/*.json") + glob.glob("hf/skleiki/*.json"), key=os.path.getmtime):
    try:
        for x in json.load(open(f)):
            if isinstance(x, dict) and x.get("name") and x.get("key"):
                names[x["name"].strip()] = x["key"]
    except Exception:
        pass


def norm(s): return re.sub(r"\s+", " ", re.sub(r"^\d+\s+", "", s)).strip().lower()


bynorm = {norm(k): v for k, v in names.items()}
try:
    bl = json.load(open(BL))
except Exception:
    bl = {}
bltxt = json.dumps(bl, ensure_ascii=False)
locked = bool(open(LOCK).read().strip()) if os.path.exists(LOCK) else False

files = [l.strip() for l in open(ALL, encoding="utf-8") if l.strip().endswith(".mp4")]
items, rows, n = [], [], 0
only = {int(x) for x in ONLY.replace(" ", "").split(",") if x}
for f in files:
    base = os.path.basename(f)
    if not base.startswith("!!! "):
        continue                       # в папке ролика рядом лежит сырой — его не трогаем
    nm = base[4:-4].strip()
    folder = os.path.basename(os.path.dirname(f))
    key = names.get(nm) or bynorm.get(norm(nm)) or bynorm.get(norm(folder))
    why = ""
    if not key:
        why = "нет ключа (старый монтаж)"
    elif not os.path.exists(f"novyj/{key}.json") or not (json.load(open(f"novyj/{key}.json")).get("cover")):
        why = "нет cover в novyj"
    elif "/К публикации/" in f and (folder in bltxt):
        why = "уже в Blotato — не трогаем"
    elif "/К публикации/" in f and locked:
        why = "робот грузит в Blotato (замок) — позже"
    rows.append(f"{n:3d} | {'ДА ' if not why else 'нет'} | {f} | {key or '-'} | {why}")
    if not why and (not only or n in only):
        items.append({"n": n, "name": nm[:60], "key": key, "file": f})
    n += 1

open("items.json", "w").write(json.dumps(items, ensure_ascii=False))
print("\n".join(rows))
print(f"ИТОГО роликов: {n}, к замене: {sum(1 for r in rows if '| ДА ' in r)}, взято сейчас: {len(items)}")
