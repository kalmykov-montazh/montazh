#!/usr/bin/env python3
"""Текст готового ролика для Claude + проверка (Евгений 28.10.2026, «Задание для чата монтажа»):
вводная связка в начале, оборванный хвост в конце, отсылки к другим видео. words_out.json или plan.json."""
import json, re, sys
d = json.load(open(sys.argv[1]))
if d and isinstance(d[0], dict) and 'words' in d[0]: ws = [w for p in d if p.get('keep', True) for w in p['words']]
else: ws = d
def tm(w): return w.get('s', w.get('os', 0))
txt = ' '.join(w['w'].strip() for w in ws)
t = txt.replace('%', '%25').replace('\n', ' ')
for i in range(0, min(len(t), 9000), 3000): print(f"::notice title=Текст ролика [{i // 3000 + 1}]::{t[i:i + 3000]}")
low = txt.lower()
head = ' '.join(w['w'] for w in ws[:6]).lower()
INTRO = r'^(значит|итак|так[, ]|ну[, ]|вот[, ]|дальше мы поговорим|дальше поговорим|далее|также следующ|следующ(ий|ая|ее|ее)|потом из минусов|по школе давайте|давайте дальше|продолжим)'
if re.search(INTRO, head.strip()): print(f"::warning::Начало со связки: «{head}» — срезать до первой сути (start_at в vyrezat.yml или trim)")
tail = ' '.join(w['w'] for w in ws[-6:]).lower()
if re.search(r'(вот если|вот как бы|\[музыка\]|\.\.\.|…|и вот|ну вот|короче)\W*$', tail):
    print(f"::warning::Хвост в конце: «{tail}» — ролик должен кончаться законченной фразой (end_after в vyrezat.yml)")
for m in re.finditer(r'(делал(и)? видео|снимал(и)? видео|можете посмотреть|в прошлом видео|в другом видео|в предыдущем видео|в следующем видео|на канале есть|ссылк)', low):
    i = len(low[:m.start()].split()); w = ws[min(i, len(ws) - 1)]
    print(f"::warning::Отсылка к другому видео на {tm(w):.1f} с: «{' '.join(x['w'] for x in ws[max(0, i - 3):i + 6])}» — вырезать")
