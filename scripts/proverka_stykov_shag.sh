#!/bin/bash
# Шаг «Проверка стыков» для задач монтажа (правило Евгения 16.11.2026: каждый ролик слушают две программы,
# каждое слово и каждый рез). Аргументы: готовое_видео  папка_на_Диске(DEST)  ключ_работы(KEY)  [сырое.mp4]
# Есть сильные замечания — кладёт рядом с роликом «СТЫКИ — проверить.txt» и пишет ::error (ролик чинить до сдачи).
V="$1"; DEST="$2"; KEY="$3"; RAW="$4"
set +e
pip install -q sherpa-onnx faster-whisper pymorphy3 pymorphy3-dicts-ru > /dev/null 2>&1
G="$GITHUB_WORKSPACE/models/gigaam"
if [ ! -f "$G/encoder.int8.onnx" ]; then
  mkdir -p "$GITHUB_WORKSPACE/models" && curl -sSL https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19.tar.bz2 | tar xj -C "$GITHUB_WORKSPACE/models" \
    && mv "$GITHUB_WORKSPACE/models/sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19" "$G"
fi
mkdir -p sty; rm -f sty/*.json
export GIGAAM="$G" WORDS="" PLAN="" SKLEIKA=""
rclone copyto "montazh:Брокер/работа/$KEY/osnova_words.json" sty/words.json 2>/dev/null && export WORDS=sty/words.json
rclone copyto "montazh:Брокер/работа/$KEY/plan.json" sty/plan.json 2>/dev/null && export PLAN=sty/plan.json
rclone copyto "montazh:Брокер/работа/$KEY/skleika.json" sty/skleika.json 2>/dev/null && export SKLEIKA=sty/skleika.json
python3 "$GITHUB_WORKSPACE/scripts/proverka_stykov.py" "$V" "$RAW" > sty/otchet.json 2> sty/err.txt || { tail -3 sty/err.txt; exit 0; }
python3 - <<'PY' > sty/otchet.txt
import json
d = json.load(open('sty/otchet.json'))
import sys, os
sys.path.insert(0, os.path.join(os.environ.get('GITHUB_WORKSPACE', '.'), 'scripts'))
from priemka_rules import classify   # правила брака — одно место для приёмки и монтажа
s, soft = classify(d['flags'])
for x in s: print(f"{x['kind']} {x['t']} с: {x['why']}")
with open('sty/myagkie.txt', 'w') as f:
    for x in soft: f.write(f"{x['kind']} {x['t']} с: {x['why']}\n")
PY
if [ -s sty/myagkie.txt ]; then
  echo "::warning::разобрать вручную ($(wc -l < sty/myagkie.txt)): $(head -3 sty/myagkie.txt | tr '\n' ' ' | cut -c1-500)"
  rclone copyto sty/myagkie.txt "montazh:Брокер/работа/$KEY/разобрать вручную.txt" 2>/dev/null
fi
if [ -s sty/otchet.txt ]; then
  echo "::error::Стыки — есть замечания ($(wc -l < sty/otchet.txt)): $(head -5 sty/otchet.txt | tr '\n' ' ' | cut -c1-900)"
  if [ "${STRICT:-1}" = "1" ]; then rclone copyto sty/otchet.txt "montazh:$DEST/СТЫКИ — проверить.txt"
  else rclone copyto sty/otchet.txt "montazh:Брокер/работа/$KEY/СТЫКИ — проверить.txt"; fi
  # 17.11.2026 (Евгений: «чтобы такого никогда не могло быть»): ролик с замечаниями НЕ остаётся там, где его смотрит
  # Евгений. Папка целиком уезжает в карантин «Брокер/работа/_не прошли проверку», чинить там, проверять заново,
  # и только чистый — обратно. STRICT=0 — оставить на месте (для ручных разборов).
  case "$DEST" in
    *"На проверке"*|*"Готовые"*|*"К публикации"*)
      if [ "${STRICT:-1}" = "1" ]; then
        Q="Брокер/работа/_не прошли проверку/$(basename "$DEST")"
        printf '%s\n' "$DEST" > sty/otkuda.txt
        rclone copyto sty/otkuda.txt "montazh:$DEST/откуда.txt"
        rclone moveto "montazh:$DEST" "montazh:$Q" && echo "::error::КАРАНТИН: «$DEST» → «$Q» (в «На проверке» не попал)"
      fi;;
  esac
else
  echo "::notice::Стыки чистые: каждое слово слышно, резы не по словам"
  rclone deletefile "montazh:$DEST/СТЫКИ — проверить.txt" 2>/dev/null
fi
rclone copyto sty/otchet.json "montazh:Брокер/работа/$KEY/stykov_proverka.json" 2>/dev/null
if [ -n "$SVODKA" ]; then
  { echo "=== $DEST"; [ -s sty/otchet.txt ] && sed 's/^/  ЖЁСТКО /' sty/otchet.txt; [ -s sty/myagkie.txt ] && sed 's/^/  мягко /' sty/myagkie.txt; [ -s sty/otchet.txt ] || [ -s sty/myagkie.txt ] || echo "  чисто"; } >> "$SVODKA"
fi
exit 0
