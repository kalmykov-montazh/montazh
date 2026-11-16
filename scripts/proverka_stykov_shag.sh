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
s = [x for x in d['flags'] if x['strong']]
for x in s: print(f"{x['kind']} {x['t']} с: {x['why']}")
PY
if [ -s sty/otchet.txt ]; then
  echo "::error::Стыки — есть замечания ($(wc -l < sty/otchet.txt)): $(head -5 sty/otchet.txt | tr '\n' ' ' | cut -c1-900)"
  rclone copyto sty/otchet.txt "montazh:$DEST/СТЫКИ — проверить.txt"
else
  echo "::notice::Стыки чистые: каждое слово слышно, резы не по словам"
  rclone deletefile "montazh:$DEST/СТЫКИ — проверить.txt" 2>/dev/null
fi
rclone copyto sty/otchet.json "montazh:Брокер/работа/$KEY/stykov_proverka.json" 2>/dev/null
exit 0
