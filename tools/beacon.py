#!/usr/bin/env python3
# Счётчик посетителей Cloudflare Web Analytics на всех страницах kalmykovgroup.com (решение Евгения 24.11.2026).
# После переезда на хостинг NetX (22.11.2026) Cloudflare больше не подставляет счётчик сам — ставим код в каждую страницу.
# Запускается в конце tools/intl_build.py (его вызывают сборки новостей и «Полезного»), можно и вручную:
#   python3 tools/beacon.py
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / 'sait'
TOKEN = 'ef679be80f984a5b876121ecba20c470'
SNIPPET = ("<!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' "
           f"data-cf-beacon='{{\"token\": \"{TOKEN}\"}}'></script><!-- End Cloudflare Web Analytics -->")
SKIP = {'tg-test', 'montazh'}  # служебные страницы не считаем


def add_all():
    n = 0
    for f in SITE.rglob('*.html'):
        if SKIP & set(f.relative_to(SITE).parts):
            continue
        s = f.read_text(encoding='utf-8', errors='ignore')
        if TOKEN in s or '</body>' not in s:
            continue
        i = s.rindex('</body>')
        f.write_text(s[:i] + SNIPPET + s[i:], encoding='utf-8')
        n += 1
    return n


if __name__ == '__main__':
    print('счётчик добавлен в страниц:', add_all())
