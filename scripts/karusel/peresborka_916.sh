# 16.11.2026 (Евгений 21:55): пересобрать все невышедшие рилсы из каруселей во весь экран 9:16.
# Запуск через ves-bash.yml (bash с доступом к Диску). Ничего не публикует, только файлы на Диске:
#   старые reel.mp4 / shorts.mp4 → <папка>/_старое 16.11/ ; новые reel/ (слайды 9:16), reel.mp4, shorts.mp4 (если был).
# Список папок — аргументом-файлом karuseli/peresborka_916.txt (одна строка = путь от корня Диска «Монтаж!»).
set -u
cd "$GITHUB_WORKSPACE"
pip install -q --break-system-packages opencv-python-headless pillow numpy 2>/dev/null || pip install -q opencv-python-headless pillow numpy
mkdir -p pics
while IFS= read -r P <&3; do
  [ -z "$P" ] && continue
  N=$(basename "$P"); D="w/$N"; rm -rf "$D"; mkdir -p "$D"
  rclone copy "montazh:$P" "$D" --include "[0-9][0-9].jpg" --include "spec.json" --include "spec_reel.json" \
     --include "karusel_slajdy.json" --include "_музыка.txt" --include "src/**" --include "reel.mp4" --include "shorts.mp4"
  had_sh=0; [ -f "$D/shorts.mp4" ] && had_sh=1
  python3 scripts/karusel/foto_dlya_rilsa.py "$D" >/dev/null 2>&1
  ok=$(python3 - "$D" <<'PY'
import json,os,sys
d=sys.argv[1]
for n in ("spec_reel.json","spec.json"):
    p=os.path.join(d,n)
    if os.path.exists(p):
        sl=json.load(open(p,encoding="utf-8"))["slides"]
        print("spec" if all(os.path.exists(os.path.join(d,x["photo"])) for x in sl) else "no"); break
else: print("no")
PY
)
  if [ "$ok" != spec ]; then python3 scripts/karusel/rils_916_iz_slajdov.py "$D"; else echo "$N: из spec.json"; fi
  T=$(python3 - "$D" <<'PY'
import sys,os
sys.path.insert(0,'scripts/karusel')
from slajdshou import FREEPD
p=os.path.join(sys.argv[1],'_музыка.txt'); t=open(p,encoding='utf-8').read() if os.path.exists(p) else ''
print(next((i for i,f in enumerate(FREEPD) if f in t), ''))
PY
)
  mv "$D/reel.mp4" "$D/_old_reel.mp4" 2>/dev/null; mv "$D/shorts.mp4" "$D/_old_shorts.mp4" 2>/dev/null
  if python3 scripts/karusel/slajdshou.py "$D" "$D/reel.mp4" ${T:+--trek $T} > "$D/_log.txt" 2>&1 && [ -f "$D/reel.mp4" ]; then
    wh=$(ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0 "$D/reel.mp4")
    du=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$D/reel.mp4")
    [ -f "$D/_old_reel.mp4" ] && rclone copyto "$D/_old_reel.mp4" "montazh:$P/_старое 16.11/reel.mp4"
    [ -f "$D/_old_shorts.mp4" ] && rclone copyto "$D/_old_shorts.mp4" "montazh:$P/_старое 16.11/shorts.mp4"
    rclone copyto "$D/reel.mp4" "montazh:$P/reel.mp4"
    [ $had_sh = 1 ] && rclone copyto "$D/reel.mp4" "montazh:$P/shorts.mp4"
    rclone copy "$D/reel" "montazh:$P/reel"
    rclone copyto "$D/_музыка.txt" "montazh:$P/_музыка.txt"
    n=$(python3 -c "print(int(float('$du')*30))")
    ffmpeg -loglevel error -y -i "$D/reel.mp4" -vf "select='eq(n\,10)+eq(n\,$((n/3)))+eq(n\,$((2*n/3)))+eq(n\,$((n-30)))',scale=180:320,tile=4x1" -frames:v 1 "pics/$N.jpg"
    echo "ГОТОВО $N | $wh | ${du%.*} с | shorts:$had_sh | $(tail -1 "$D/_log.txt" | cut -c1-90)"
  else
    echo "ОШИБКА $N | $(tail -3 "$D/_log.txt" | tr '\n' ' ' | cut -c1-200)"
  fi
done 3< karuseli/peresborka_916.txt
