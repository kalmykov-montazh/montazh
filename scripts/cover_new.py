#!/usr/bin/env python3
"""Обложка нового стиля (утверждено 21.10.2026), одна команда на все 7 стилей:
python cover_new.py кадр.png СТИЛЬ "ВЕРХ|..." "НИЗ|..." обложка.jpg

Стили по кругу (чтобы лента была разной):
  1 yellow       — верх на чёрной плашке, низ жёлтый с чёрной обводкой
  2 whiteyellow  — белый текст, последняя строка жёлтая
  3 gold5        — золото, текст сверху и снизу
  4 gold         — золото, одно слово сверху + крупно снизу
  5 torn         — рваная чёрная полоса на груди: НИЗ = «белая|красная», ВЕРХ (можно пусто) — строка над головой
  6 goldpill     — золото: ВЕРХ над головой, НИЗ = «короткое слово в плашке|крупное золотое»
  7 ladder       — лесенка: ВЕРХ белая, НИЗ = «крупная жёлтая|белое на красной плашке»
Можно писать номер стиля вместо названия."""
import os, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
SRC, ST, TOP, BOT, OUT = sys.argv[1:6]
ORDER = ['yellow', 'whiteyellow', 'gold5', 'gold', 'torn', 'goldpill', 'ladder']
if ST.isdigit(): ST = ORDER[(int(ST) - 1) % len(ORDER)]
py = sys.executable
top = [x for x in TOP.split('|') if x.strip()]
bot = [x for x in BOT.split('|') if x.strip()]

if ST in ('yellow', 'whiteyellow', 'gold'):
    cmd = [py, f'{D}/cover_style.py', SRC, TOP, BOT, ST, OUT]
elif ST == 'gold5':
    cmd = [py, f'{D}/gold2.py', SRC, TOP, BOT, OUT, 'a']
elif ST in ('torn', 'goldpill', 'ladder'):
    lines = (bot + top) if ST == 'torn' else (top + bot)
    need = {'torn': (2, 3), 'goldpill': (3,), 'ladder': (3,)}[ST]
    if len(lines) not in need or (ST == 'torn' and len(bot) != 2):
        sys.exit(f'стиль {ST}: нужно {need} строки (ВЕРХ и НИЗ через |), а дано {len(lines)}: {lines}')
    cmd = [py, f'{D}/cover_text2.py', SRC, ST, OUT] + lines
else:
    sys.exit(f'нет стиля {ST}; есть: {", ".join(ORDER)}')
subprocess.run(cmd, check=True)
print('обложка', ST, OUT)
