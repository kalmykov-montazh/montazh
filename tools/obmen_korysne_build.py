#!/usr/bin/env python3
# Розділ «Корисне» на сайті обмінника obmen-gagarina.site/korysne (рішення Євгенія 21.11.2026, «да»).
# Джерело: obmen-korysne/_src/<адреса>.md — шапка до «---»: title, title_ru, description, description_ru, date (РРРР-ММ-ДД);
# далі український текст, рядок «=== RU ===», далі російський. Розмітка як у sait/polezno: «## », «- », «1. », «> », **жирний**.
# Запуск: python3 tools/obmen_korysne_build.py → obmen-korysne/articles.json (його сам бере korysne.php на хостингу з GitHub, кеш 20 хв)
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from polezno_build import render

ROOT = Path(__file__).resolve().parent.parent / 'obmen-korysne'
items = []
for f in sorted((ROOT / '_src').glob('*.md')):
    t = f.read_text(encoding='utf-8').replace('\r\n', '\n').replace('﻿', '')
    head, _, body = t.partition('\n---\n')
    m = {}
    for l in head.split('\n'):
        if ':' in l:
            k, v = l.split(':', 1); m[k.strip().lower()] = v.strip()
    ua, _, ru = body.partition('\n=== RU ===\n')
    if not (m.get('title') and m.get('title_ru') and ua.strip() and ru.strip()):
        sys.exit(f'ПОМИЛКА {f.name}: потрібні title, title_ru, український і російський текст')
    items.append({'slug': f.stem, 'date': m.get('date', ''), 'title': m['title'], 'title_ru': m['title_ru'],
                  'desc': m.get('description', ''), 'desc_ru': m.get('description_ru', ''),
                  'html': render(ua.strip()), 'html_ru': render(ru.strip())})
items.sort(key=lambda x: x['date'], reverse=True)
(ROOT / 'articles.json').write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'Корисне: {len(items)} статей')
