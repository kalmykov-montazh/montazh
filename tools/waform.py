#!/usr/bin/env python3
# Окошко «имя, фамилия, телефон» перед WhatsApp к партнёру (решение Евгения 26.11.2026) — подключает /waform.js
# на всех страницах, где есть кнопки /p/<партнёр>-wa. Запускается в конце tools/intl_build.py, можно вручную: python3 tools/waform.py
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / 'sait'
TAG = '<script src="/waform.js" defer></script>'
RX = re.compile(r'/p/[a-z]+-wa')


def add_all():
    n = 0
    for f in SITE.rglob('*.html'):
        s = f.read_text(encoding='utf-8', errors='ignore')
        if TAG in s or '</body>' not in s or not RX.search(s):
            continue
        i = s.rindex('</body>')
        f.write_text(s[:i] + TAG + s[i:], encoding='utf-8')
        n += 1
    return n


if __name__ == '__main__':
    print('окошко WhatsApp подключено на страниц:', add_all())
