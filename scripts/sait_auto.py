# 11.11.2026 (Евгений 21:31: «чтобы окошки были на месте»): при ЛЮБОМ перемонтаже ролика, в который 11.11
# вручную накладывали окошко сайта (41 ролик, списки hf/sait_skriny/gotovye_1111/pachka1-3.json),
# окошко накладывается заново на готовый файл — само, без отдельного шага.
#
#   python3 scripts/sait_auto.py <final.mp4> "<DEST>" [build.txt]
#
# Ищет ролик по концу пути DEST («НЕДВ/НЕДВ Съехать раньше срока»). Нет в списке — ничего не делает.
# Если сборка уже поставила своё окошко (в build.txt есть «окошко сайта:») — второе не ставит.
import sys, os, json, glob, subprocess, shutil

final, dest = sys.argv[1], sys.argv[2].rstrip("/")
blog = sys.argv[3] if len(sys.argv) > 3 else ""
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if blog and os.path.exists(blog) and "окошко сайта:" in open(blog, encoding="utf-8", errors="ignore").read():
    print("окошко сайта: уже стоит из сборки — повторно не ставлю"); sys.exit(0)
items = []
for f in sorted(glob.glob(f"{R}/hf/sait_skriny/gotovye_1111/pachka*.json")):
    items += json.load(open(f))
hit = [j for j in items if dest.endswith(j["d"]) or os.path.basename(dest) == os.path.basename(j["d"])]
if not hit:
    sys.exit(0)
j = hit[0]
img = j["img"]   # путь относительно hf/sait_skriny — так его ждёт sait_overlay.py
tmp = final + ".sait.mp4"
r = subprocess.run([sys.executable, f"{R}/scripts/sait_overlay.py", final, tmp, img, j["text"], str(j["t"]),
                    str(j.get("top", 200)), str(j.get("h", 300)), str(j.get("dur", 3.6))], capture_output=True, text=True)
if r.returncode or not os.path.exists(tmp):
    print("::warning::окошко сайта НЕ наложилось:", j["d"], (r.stderr or "")[-300:]); sys.exit(0)
shutil.move(tmp, final)
print(f"окошко сайта наложено заново: {j['d']} — {j['img']} в {j['t']} с")
