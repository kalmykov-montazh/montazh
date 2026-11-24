# 24.11.2026 (Евгений: «чтобы такого больше не было… все обложки чёткие»): проверка лица на готовой обложке
# или кадре под обложку. Глаза открыты, рот закрыт (106 точек лица, пороги как в kadr_glaza.py).
#   python3 scripts/proverka_oblozhki.py картинка.jpg [...]  → «ОК …» или «ПЛОХО …»; код выхода 1, если хоть одна плохая.
# Лица нет (вид из окна, предмет) — не ошибка: «без лица».
import sys, os, cv2, numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from lico106 import landmarks, metr
fc = cv2.CascadeClassifier(os.environ.get("HAAR") or os.path.join(D, "haar.xml"))
bad = 0
for p in sys.argv[1:]:
    im = cv2.imread(p)
    if im is None: print("нет файла", p); continue
    im = cv2.resize(im, (1080, 1920))
    f = fc.detectMultiScale(cv2.cvtColor(cv2.resize(im, (540, 960)), cv2.COLOR_BGR2GRAY), 1.1, 5, minSize=(40, 40))
    if not len(f): print("без лица", p); continue
    x, y, w, h = [int(c * 2) for c in max(f, key=lambda r: r[2] * r[3])]
    e, ea, mi, mo = metr(landmarks(im, (x, y, w, h)))
    why = []
    if e < 0.27: why.append(f"глаза прикрыты ({e:.2f})")
    if mi > 0.035 or mo > 0.36: why.append(f"рот открыт ({mi:.3f}/{mo:.2f})")
    if why: bad = 1; print("ПЛОХО", p, "; ".join(why))
    else: print(f"ОК {p} глаза {e:.2f} рот {mi:.3f}/{mo:.2f}")
sys.exit(bad)
