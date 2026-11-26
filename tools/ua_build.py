#!/usr/bin/env python3
# Украинская версия главной (sait/ua.html) = копия русской (sait/index.html) + перевод из sait/_i18n/ua.json.
# Решение Евгения 22.11.2026: украинская должна выглядеть как русская. Дизайн меняем только в index.html,
# потом запускаем этот скрипт. Новые русские тексты без перевода остаются по-русски — добавить их в ua.json.
# Запускается сам в конце tools/novosti_build.py и tools/polezno_build.py.
# python3 tools/ua_build.py [--check]  — --check печатает русские строки без перевода
import re, json, sys

from pathlib import Path
SITE = Path(__file__).resolve().parent.parent / 'sait'
CYR = re.compile('[а-яА-ЯёЁ]')

def translate(s, d):
    miss = []
    def tr(x):
        if x in d: return d[x]
        if CYR.search(x): miss.append(x)
        return x
    out, pos = [], 0
    # теги, скрипты, стили, комментарии, текст
    for m in re.finditer(r'<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<!--.*?-->|<[^>]+>', s, re.S):
        txt = s[pos:m.start()]
        if txt.strip():
            core = txt.strip(); txt = txt.replace(core, tr(core), 1)
        out.append(txt)
        tag = m.group(0)
        if tag.startswith('<script'):
            def q(mm):
                body = mm.group(2)
                return mm.group(1) + (d.get(body, body)) + mm.group(3) if CYR.search(body) else mm.group(0)
            tag = re.sub(r'(")((?:[^"\\\n]|\\.)*)(")', q, tag)
            tag = re.sub(r"(')((?:[^'\\\n]|\\.)*)(')", q, tag)
            tag = re.sub(r'(`)([^`]*)(`)', q, tag)
        elif tag.startswith('<') and not tag.startswith(('<!--', '<style')):
            tag = re.sub(r'(\s(?:placeholder|title|aria-label|alt|content|data-tip|value)=")([^"]*)(")',
                         lambda mm: mm.group(1) + tr(mm.group(2)) + mm.group(3), tag)
        out.append(tag); pos = m.end()
    out.append(s[pos:])
    return ''.join(out), miss

def build(check=False):
    d = json.loads((SITE / '_i18n' / 'ua.json').read_text(encoding='utf-8'))
    s = (SITE / 'index.html').read_text(encoding='utf-8')
    s, miss = translate(s, d)
    fix = [
        ('<html lang="ru"', '<html lang="uk"'),
        ('<link rel="canonical" href="https://kalmykovgroup.com/">', '<link rel="canonical" href="https://kalmykovgroup.com/ua">'),
        ('hreflang="uk" href="https://kalmykovgroup.com/ua.html"', 'hreflang="uk" href="https://kalmykovgroup.com/ua"'),
        ('content="ru_RU"', 'content="uk_UA"'),
        ('<meta property="og:url" content="https://kalmykovgroup.com/">', '<meta property="og:url" content="https://kalmykovgroup.com/ua">'),
        ('/go/chek"', '/go/chekua"'), ('start=chek_site', 'start=chekua_site'),
        ('chek-list-arenda.pdf', 'chek-list-arenda-ua.pdf'),
    ]
    for a, b in fix: s = s.replace(a, b)
    import yuristy_build; s = yuristy_build.insert(s, 'ua')   # 26.11.2026: блок юристов на украинском
    # переключатель языков: активный — UA
    s = re.sub(r'(<nav class="langsw"[^>]*>)(.*?)(</nav>)', lambda m: m.group(1) + re.sub(r' class="on"', '', m.group(2)).replace('href="ua.html"', 'class="on" href="ua.html"', 1).replace('href="/ua"', 'class="on" href="/ua"', 1) + m.group(3), s, flags=re.S)
    (SITE / 'ua.html').write_text(s, encoding='utf-8')
    miss = list(dict.fromkeys(miss))
    if check:
        for x in miss: print('БЕЗ ПЕРЕВОДА:', x[:120])
    return miss

if __name__ == '__main__':
    m = build('--check' in sys.argv)
    print('ua.html готов, строк без перевода:', len(m))
