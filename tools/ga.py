#!/usr/bin/env python3
# Google Analytics 4 (G-6XKHV3W9L5, аккаунт «Kalmykov Group», Google evgeniy030982) на всех страницах kalmykovgroup.com.
# Решение Евгения 26.11.2026: видеть страны, возраст, пол посетителей. Сигналы Google включены (демография).
# По закону Испании (LSSI, ЕС) аналитические cookie — только с согласия: Consent Mode v2, по умолчанию «запрещено»,
# внизу плашка «Принять / Отклонить» на языке страницы. Без согласия Google получает только обезличенные сигналы.
# Запускается в конце tools/intl_build.py, можно вручную: python3 tools/ga.py
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / 'sait'
GA = 'G-6XKHV3W9L5'
SKIP = {'tg-test', 'montazh'}
MARK = '<!-- GA4 26.11.2026 -->'

TXT = {
    'ru': ('Сайт использует cookie Google Analytics, чтобы понимать, откуда приходят посетители', 'Принять', 'Отклонить', 'Подробнее'),
    'uk': ('Сайт використовує cookie Google Analytics, щоб розуміти, звідки приходять відвідувачі', 'Прийняти', 'Відхилити', 'Докладніше'),
    'en': ('We use Google Analytics cookies to understand where our visitors come from', 'Accept', 'Decline', 'Details'),
    'es': ('Usamos cookies de Google Analytics para saber de dónde vienen nuestros visitantes', 'Aceptar', 'Rechazar', 'Más info'),
}


def head_snippet():
    return (MARK +
            "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}"
            "var kgc=null;try{kgc=localStorage.getItem('kg_cookies')}catch(e){}"
            "gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied',wait_for_update:500});"
            "if(kgc==='yes')gtag('consent','update',{ad_storage:'granted',ad_user_data:'granted',ad_personalization:'granted',analytics_storage:'granted'});"
            f"gtag('js',new Date());gtag('config','{GA}');</script>"
            f"<script async src=\"https://www.googletagmanager.com/gtag/js?id={GA}\"></script>")


def banner(lang=None):
    # язык плашки — по <html lang> прямо в браузере (ua.html копируется с русской главной вместе с плашкой)
    import json
    tx = json.dumps({k: list(v) for k, v in TXT.items()}, ensure_ascii=False)
    return (MARK + '<div id="kgck" style="display:none;position:fixed;left:12px;right:12px;bottom:calc(84px + env(safe-area-inset-bottom));z-index:70;'
            'max-width:520px;margin:0 auto;background:#0b1426;color:#fff;border:2px solid #d4a24c;border-radius:16px;padding:12px 14px;'
            'font:14px/1.4 Inter,system-ui,sans-serif;box-shadow:0 10px 28px rgba(0,0,0,.35)">'
            '<span><span id="kgckt"></span>. <a id="kgckm" href="/cookies" style="color:#ffd54a"></a></span>'
            '<span style="display:flex;gap:8px;margin-top:10px">'
            '<button type="button" data-v="yes" style="flex:1;padding:9px;border-radius:999px;border:2px solid #111;background:#ffd54a;color:#111;font-weight:800;cursor:pointer"></button>'
            '<button type="button" data-v="no" style="flex:1;padding:9px;border-radius:999px;border:2px solid #ffd54a;background:transparent;color:#ffd54a;font-weight:700;cursor:pointer"></button>'
            '</span></div>'
            "<script>(function(){var b=document.getElementById('kgck');if(!b)return;var T=" + tx + ";"
            "var l=(document.documentElement.lang||'ru').slice(0,2);var t=T[l]||T.ru;"
            "document.getElementById('kgckt').textContent=t[0];document.getElementById('kgckm').textContent=t[3];"
            "var bs=b.querySelectorAll('button');bs[0].textContent=t[1];bs[1].textContent=t[2];"
            "var v=null;try{v=localStorage.getItem('kg_cookies')}catch(e){}"
            "if(!v)b.style.display='block';bs.forEach(function(x){x.addEventListener('click',function(){var a=x.dataset.v;"
            "try{localStorage.setItem('kg_cookies',a)}catch(e){}if(a==='yes'&&window.gtag)gtag('consent','update',{ad_storage:'granted',ad_user_data:'granted',ad_personalization:'granted',analytics_storage:'granted'});"
            "b.style.display='none'})})})()</script>")


def add_all():
    n = 0
    hs = head_snippet()
    for f in SITE.rglob('*.html'):
        if SKIP & set(f.relative_to(SITE).parts) or f.name.startswith('google'):
            continue
        s = f.read_text(encoding='utf-8', errors='ignore')
        if MARK in s or '</head>' not in s or '</body>' not in s:
            continue
        m = re.search(r'<html[^>]*\blang="([a-z]{2})', s)
        lang = m.group(1) if m else 'ru'
        s = s.replace('</head>', hs + '</head>', 1)
        i = s.rindex('</body>')
        s = s[:i] + banner(lang) + s[i:]
        f.write_text(s, encoding='utf-8')
        n += 1
    return n


if __name__ == '__main__':
    print('Google Analytics добавлен в страниц:', add_all())
