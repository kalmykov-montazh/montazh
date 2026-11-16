# 16.11.2026: перед сборкой рилса 9:16 подтянуть фото к spec.json, если в папке карусели их нет.
#   python3 scripts/karusel/foto_dlya_rilsa.py <папка>
# Есть reel/01.jpg … 1080×1920 — ничего не делает. Иначе для каждого фото из spec.json, которого нет в папке,
# берёт файл с тем же именем из «Брокер/Посты/Фото» (rclone, удалённое имя montazh:). Панели p_NN.jpg (вырезки
# из novye_pachka.py) так не достать — их надо пересобрать новой novye_pachka.py, она теперь кладёт reel/ на Диск сама.
import os, sys, json, glob, subprocess
from PIL import Image

d = sys.argv[1]
fs = sorted(glob.glob(os.path.join(d, "reel", "[0-9][0-9].jpg")))
if fs and all(Image.open(p).size == (1080, 1920) for p in fs):
    print("reel/ уже есть:", len(fs)); sys.exit(0)
sp = os.path.join(d, "spec.json")
if not os.path.exists(sp):
    print("НЕТ spec.json — рилс 9:16 не собрать, нужен spec"); sys.exit(0)
miss = [x["photo"] for x in json.load(open(sp, encoding="utf-8"))["slides"] if not os.path.exists(os.path.join(d, x["photo"]))]
for p in miss:
    r = subprocess.run(["rclone", "copyto", "montazh:Брокер/Посты/Фото/" + os.path.basename(p), os.path.join(d, p)],
                       capture_output=True, text=True)
    print(("взято " if r.returncode == 0 else "НЕТ на Диске ") + p)
