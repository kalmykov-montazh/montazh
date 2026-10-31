#!/bin/bash
# Шортс «Медицина в Испании» NN целиком на машине GitHub: основа из сырых → обложка → сцены → «На проверке».
set -e
ID="$1"; R="$(cd "$(dirname "$0")" && pwd)"; ROOT="$R/../.."; W="$ROOT/w$ID"; mkdir -p "$W"
NAME=$(python -c "import json;print([n for i,n,a,b in json.load(open('$R/shorts.json')) if i=='$ID'][0])")
python "$R/sbase.py" "$ID" "$ROOT/raw.mp4" "$ROOT/cam.mp4" "$ROOT/rvm.onnx" "$W"
python "$ROOT/scripts/cover_new.py" "$W/cvframe.png" whiteyellow "" "$(cat "$R/$ID.cover.txt")" "$W/обложка.jpg"
cp "$W/обложка.jpg" "$W/cover.jpg"; cp "$R/$ID.config.json" "$W/config.json"; cp "$R/$ID.words.json" "$W/words_out.json"
cd "$W"
python "$ROOT/scripts/sceny/engine.py" info | grep -E "::" || true
python "$ROOT/scripts/sceny/engine.py" audio
python "$ROOT/scripts/sceny/engine.py" render out.mp4 $(nproc)
L=$(ffmpeg -i out.mp4 -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out.mp4)
python - "$R/$ID.pack.txt" <<'PY'
import json, sys
c = json.load(open("config.json")); q = c.get("pack_q", "")
lines = open(sys.argv[1], encoding="utf-8").read().rstrip("\n").split("\n")
hi = next((i for i, l in enumerate(lines) if l.strip().startswith("#")), len(lines))
body = lines[:hi]
while body and body[-1].strip() in ("", "⠀"): body.pop()
txt = "\n".join(body + ["⠀", q, "⠀"] + lines[hi:]).rstrip()
while txt.endswith("."): txt = txt[:-1]
open("упаковка.txt", "w", encoding="utf-8").write(txt + "\n")
PY
DST="Брокер/На проверке/Шортс Медицина в Испании $ID $NAME"
rclone copyto out.mp4 "montazh:$DST/!!! $ID $NAME — сцены v2.mp4"
rclone copyto обложка.jpg "montazh:$DST/обложка.jpg"
rclone copyto упаковка.txt "montazh:$DST/упаковка.txt"
echo "::notice::$ID $NAME готов: $D с, $L LUFS → $DST"
