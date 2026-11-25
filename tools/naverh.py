#!/usr/bin/env python3
# Кнопка «Наверх» на ВСЕХ страницах kalmykovgroup.com (решение Евгения 26.11.2026: «добавь сразу, чтобы мы не забыли»).
# Образец — блок «24.11.2026: кнопка «Наверх»» в sait/index.html. Подпись по языку страницы (<html lang>).
# Запускается в конце tools/intl_build.py, можно вручную: python3 tools/naverh.py
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / 'sait'
SKIP = {'tg-test', 'montazh'}
LBL = {'uk': 'Вгору', 'en': 'Top', 'es': 'Arriba'}
ARIA = {'uk': 'Вгору', 'en': 'Back to top', 'es': 'Volver arriba'}


def snippet():
    s = (SITE / 'index.html').read_text(encoding='utf-8')
    i = s.index('<!-- 24.11.2026: кнопка «Наверх»')
    j = s.index('</script>', s.index('id="naverh"')) + len('</script>')
    return s[i:j]


def add_all():
    base = snippet()
    n = 0
    for f in SITE.rglob('*.html'):
        if SKIP & set(f.relative_to(SITE).parts) or f.name in ('index.html', 'ua.html') and f.parent == SITE:
            continue
        s = f.read_text(encoding='utf-8', errors='ignore')
        if 'id="naverh"' in s or '</body>' not in s:
            continue
        m = re.search(r'<html[^>]*\blang="([a-z]{2})', s)
        lang = m.group(1) if m else 'ru'
        sn = base
        if lang in LBL:
            sn = sn.replace('aria-label="Наверх"', f'aria-label="{ARIA[lang]}"').replace('</svg>Наверх<', f'</svg>{LBL[lang]}<')
        i = s.rindex('</body>')
        f.write_text(s[:i] + sn + s[i:], encoding='utf-8')
        n += 1
    return n


if __name__ == '__main__':
    print('кнопка «Наверх» добавлена в страниц:', add_all())
