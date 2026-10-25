#!/bin/bash
# Шортс со сценами v2: основа (задача 5С) + сцены из sceny/<тема>/<NN>.json → рядом со старым роликом.
# Пути с запасом на переезд папок 26.10.2026 («Готовые!» → «Брокер/Готовые/Шортсы»).
set -e
TOPIC="$1"; ID="$2"; W=work; mkdir -p $W
first() { for p in "$@"; do if rclone lsf "montazh:$p" --max-depth 1 >/dev/null 2>&1 && [ -n "$(rclone lsf "montazh:$p" --max-depth 1 2>/dev/null | head -1)" ]; then echo "$p"; return; fi; done; }
WORK=$(first "работа/Сцены/$TOPIC/$ID" "Брокер/работа/Сцены/$TOPIC/$ID")
[ -n "$WORK" ] || { echo "::error::нет основы для $ID — сначала задача 5С"; exit 1; }
SH=$(first "Готовые!/ШОРТС $TOPIC" "Брокер/Готовые/Шортсы/$TOPIC" "Брокер/Готовые/Шортсы/ШОРТС $TOPIC")
[ -n "$SH" ] || { echo "::error::не нашёл папку шортсов «$TOPIC»"; exit 1; }
FOLDER=$(rclone lsf "montazh:$SH" --dirs-only | sed 's#/$##' | grep "^$ID " | head -1)
[ -n "$FOLDER" ] || { echo "::error::нет папки $ID в $SH"; exit 1; }
echo "::notice::основа: $WORK; ролик: $SH/$FOLDER"
rclone copy "montazh:$WORK" $W --include base.mp4 --include words_out.json
rclone copy "montazh:$SH/$FOLDER" $W --include обложка.jpg --include упаковка.txt
cp $W/обложка.jpg $W/cover.jpg
cp "sceny/$TOPIC/$ID.json" $W/config.json
cd $W
python ../scripts/sceny/engine.py info | tee info.txt | grep -E "::" || true
python ../scripts/sceny/engine.py audio
NP=$(nproc); python ../scripts/sceny/engine.py render "out.mp4" $NP
# проверки
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out.mp4)
L=$(ffmpeg -i out.mp4 -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
ffmpeg -v error -y -i out.mp4 -frames:v 1 f0.png
python - <<'PY'
from PIL import Image, ImageChops
import numpy as np
a = np.asarray(Image.open("f0.png").convert("L").resize((108, 192)), float)
b = np.asarray(Image.open("cover.jpg").convert("L").resize((108, 192)), float)
d = abs(a - b).mean(); print(f"::notice::первый кадр vs обложка: {d:.1f}")
assert d < 25, "первый кадр не обложка"
PY
echo "::notice::готово: $D с, громкость $L LUFS"
NAME="!!! $FOLDER — сцены v2.mp4"
python - "$FOLDER" <<'PY'
import json, sys
c = json.load(open("config.json")); q = c.get("pack_q", "")
try: old = open("упаковка.txt", encoding="utf-8").read().rstrip("\n").split("\n")
except Exception: old = [sys.argv[1]]
hi = next((i for i, l in enumerate(old) if l.strip().startswith("#")), len(old))
body = old[:hi]
while body and body[-1].strip() in ("", "⠀"): body.pop()
out = body + (["⠀", q] if q else []) + ["⠀"] + old[hi:]
txt = "\n".join(out).rstrip()
while txt.endswith("."): txt = txt[:-1]
open("упаковка — сцены.txt", "w", encoding="utf-8").write(txt + "\n")
print(txt)
PY
rclone copyto out.mp4 "montazh:$SH/$FOLDER/$NAME"
rclone copyto "упаковка — сцены.txt" "montazh:$SH/$FOLDER/упаковка — сцены.txt"
rclone lsl "montazh:$SH/$FOLDER" | sed 's/^/::notice::/'
