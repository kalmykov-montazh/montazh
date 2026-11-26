#!/usr/bin/env python3
# Юристы-партнёры (ProSpain, Алина) на сайте — решение Евгения 26.11.2026.
# Один источник текста на 4 языка: блок в «Поездках» на главной (RU/UA/EN/ES) и страница «Все услуги юристов».
#   блок:      между <!--lw--> и <!--/lw--> в sait/index.html (RU); ua_build.py, intl_build.py ставят свой язык через block(lang)
#   страницы:  sait/yuristy/index.html (RU), sait/yuristy/ua.html (UA), sait/en/lawyers/index.html, sait/es/abogados/index.html
# Кнопки: WhatsApp /p/yuristy-wa?src=...&lang=.. (номер ЮР-N, строка в таблицу «Заявки — Юристы»), Telegram /p/yuristy-tg (бот).
# Цен НЕ ставим (решение 25.11). Название компании не пишем — человек идёт к юристу через наши кнопки.
# python3 tools/yuristy_build.py
import re
from html import escape as esc
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / 'sait'
BASE = 'https://kalmykovgroup.com'

T = {
 'ru': dict(
  page='/yuristy/', html_lang='ru', title='Юристы в Испании — бесплатная консультация | Kalmykov Group',
  desc='Юридическая компания-партнёр в Испании: ВНЖ, модификация временной защиты, налоги, аутономо, покупка жилья, наследство. Бесплатная консультация на русском',
  kick='Юридическая компания-партнёр', free='БЕСПЛАТНАЯ КОНСУЛЬТАЦИЯ', freesub='Юрист разберёт вашу ситуацию и скажет, что делать',
  hl='Модификация: временная защита → ВНЖ', hlsub='По трудовому контракту или как ИП. Без бизнес-плана, если ИП работает больше 6 месяцев',
  chips=[('🛂', 'ВНЖ цифрового кочевника'), ('🔁', 'Продление и смена ВНЖ'), ('💼', 'Аутономо: открыть и вести'), ('🧾', 'Налоги и декларации'),
         ('🏠', 'Покупка жилья с юристом'), ('🏢', 'Открыть компанию'), ('📜', 'Наследство в Испании'), ('⚖️', 'Адвокаты: семья, суд, налоги')],
  trust='10 лет в Испании · 35+ юристов и налоговиков · 4 000+ дел', langs='Говорят по-русски, по-украински, по-испански и по-английски',
  wa='WhatsApp', tg='Telegram', all='Все услуги юристов →', back='← На главную', home='/', tgon=True,
  h1='Юристы в Испании: бесплатная консультация', intro='Проверенная юридическая компания, с которой я работаю. Напишите в WhatsApp или Telegram — юрист разберёт вашу ситуацию бесплатно и скажет, что делать и сколько это стоит',
  cats=[
   ('🛂 ВНЖ и документы', ['Модификация временной защиты на ВНЖ — по контракту или как ИП', 'ВНЖ цифрового кочевника — для работы на иностранную компанию или как ИП', 'Виза высококвалифицированного специалиста', 'ВНЖ предпринимателя и стартапа', 'Перевод сотрудника в испанскую компанию', 'Студенческая виза', 'Продление и смена вида ВНЖ', 'Массовая легализация', 'Гражданство Испании']),
   ('🧾 Налоги и бухгалтерия', ['Консультация налогового специалиста', 'Аутономо: постановка на учёт и ведение', 'Бухгалтерия компании', 'Годовая декларация о доходах (модель 100)', 'Налог для владельцев жилья без резидентства (модель 210)', 'Декларация имущества за границей (модель 720)', 'Налог на богатство (модель 714)', 'Смена налоговой резиденции (модель 030)', 'Закон Бекхема — особый налоговый режим и продление']),
   ('🏠 Недвижимость и наследство', ['Сопровождение покупки и продажи: проверка задатка (аррас), договора, обременений и долгов', 'Вступление в наследство на имущество в Испании']),
   ('🏢 Бизнес', ['Открытие компании под ключ и сопровождение']),
   ('⚖️ Адвокаты', ['Семейное, гражданское, уголовное, административное и налоговое право — стоимость по каждому делу']),
   ('📎 Сопутствующее', ['Присяжные переводы документов', 'Медицинская страховка', 'Заказ справок']),
  ],
  note='Цену юрист называет после консультации, под вашу ситуацию', ad='Партнёрская ссылка: заявка уходит юристу с пометкой «от Kalmykov Group»'),
 'ua': dict(
  page='/yuristy/ua', html_lang='uk', title='Юристи в Іспанії — безкоштовна консультація | Kalmykov Group',
  desc='Юридична компанія-партнер в Іспанії: ВНЖ, модифікація тимчасового захисту, податки, автономо, купівля житла, спадщина. Безкоштовна консультація українською',
  kick='Юридична компанія-партнер', free='БЕЗКОШТОВНА КОНСУЛЬТАЦІЯ', freesub='Юрист розбере вашу ситуацію і скаже, що робити',
  hl='Модифікація: тимчасовий захист → ВНЖ', hlsub='За трудовим контрактом або як ФОП. Без бізнес-плану, якщо ФОП працює понад 6 місяців',
  chips=[('🛂', 'ВНЖ цифрового кочівника'), ('🔁', 'Продовження і зміна ВНЖ'), ('💼', 'Автономо: відкрити і вести'), ('🧾', 'Податки і декларації'),
         ('🏠', 'Купівля житла з юристом'), ('🏢', 'Відкрити компанію'), ('📜', 'Спадщина в Іспанії'), ('⚖️', 'Адвокати: сім\'я, суд, податки')],
  trust='10 років в Іспанії · 35+ юристів і податківців · 4 000+ справ', langs='Говорять українською, російською, іспанською та англійською',
  wa='WhatsApp', tg='Telegram', all='Усі послуги юристів →', back='← На головну', home='/ua', tgon=True,
  h1='Юристи в Іспанії: безкоштовна консультація', intro='Перевірена юридична компанія, з якою я працюю. Напишіть у WhatsApp або Telegram — юрист безкоштовно розбере вашу ситуацію і скаже, що робити і скільки це коштує',
  cats=[
   ('🛂 ВНЖ і документи', ['Модифікація тимчасового захисту на ВНЖ — за контрактом або як ФОП', 'ВНЖ цифрового кочівника — для роботи на іноземну компанію або як ФОП', 'Віза висококваліфікованого спеціаліста', 'ВНЖ підприємця і стартапу', 'Переведення працівника в іспанську компанію', 'Студентська віза', 'Продовження і зміна виду ВНЖ', 'Масова легалізація', 'Громадянство Іспанії']),
   ('🧾 Податки і бухгалтерія', ['Консультація податкового спеціаліста', 'Автономо: постановка на облік і ведення', 'Бухгалтерія компанії', 'Річна декларація про доходи (модель 100)', 'Податок для власників житла без резидентства (модель 210)', 'Декларація майна за кордоном (модель 720)', 'Податок на багатство (модель 714)', 'Зміна податкової резидентності (модель 030)', 'Закон Бекхема — особливий податковий режим і продовження']),
   ('🏠 Нерухомість і спадщина', ['Супровід купівлі та продажу: перевірка завдатку (аррас), договору, обтяжень і боргів', 'Вступ у спадщину на майно в Іспанії']),
   ('🏢 Бізнес', ['Відкриття компанії під ключ і супровід']),
   ('⚖️ Адвокати', ['Сімейне, цивільне, кримінальне, адміністративне і податкове право — вартість за кожною справою']),
   ('📎 Супутнє', ['Присяжні переклади документів', 'Медичне страхування', 'Замовлення довідок']),
  ],
  note='Ціну юрист називає після консультації, під вашу ситуацію', ad='Партнерське посилання: заявка йде юристу з позначкою «від Kalmykov Group»'),
 'en': dict(
  page='/en/lawyers/', html_lang='en', title='Lawyers in Spain — free consultation | Kalmykov Group',
  desc='Our partner law firm in Spain: buying property with a lawyer, Spanish taxes, Beckham Law, non-resident tax, Digital Nomad Visa, inheritance. Free consultation in English',
  kick='Our partner law firm in Spain', free='FREE CONSULTATION', freesub='A lawyer reviews your case and tells you what to do',
  hl='Buying property in Spain?', hlsub='A lawyer checks the deposit contract (arras), the title and any debts on the property before you pay',
  chips=[('🧾', 'Spanish taxes and returns'), ('⭐', 'Beckham Law tax regime'), ('🏠', 'Non-resident property tax'), ('🛂', 'Digital Nomad Visa'),
         ('💼', 'Self-employed (autónomo)'), ('🏢', 'Company setup'), ('📜', 'Inheritance in Spain'), ('⚖️', 'Lawyers: family, court, tax')],
  trust='10 years in Spain · 35+ lawyers and tax advisers · 4,000+ cases', langs='They work in English, Spanish, Russian and Ukrainian',
  wa='Write on WhatsApp', tg='', all='All legal services →', back='← Home', home='/en/', tgon=False,
  h1='Lawyers in Spain: free consultation', intro='A law firm we work with and trust. Message them on WhatsApp: a lawyer will look at your case for free and tell you what to do and what it costs',
  cats=[
   ('🏠 Property and inheritance', ['Buying or selling property: review of the deposit contract (arras), the sale contract, charges and debts', 'Inheritance of property in Spain']),
   ('🧾 Taxes and accounting', ['One-to-one tax consultation', 'Annual income tax return (Modelo 100)', 'Non-resident property owners tax (Modelo 210)', 'Declaration of assets abroad (Modelo 720)', 'Wealth tax (Modelo 714)', 'Change of tax residence (Modelo 030)', 'Beckham Law special tax regime and renewal', 'Self-employed (autónomo): registration and bookkeeping', 'Company accounting']),
   ('🛂 Visas and residence', ['Digital Nomad Visa', 'Highly qualified professional visa', 'Entrepreneur residence', 'Intra-company transfer', 'Student visa', 'Residence renewals and changes', 'Spanish citizenship']),
   ('🏢 Business', ['Company setup in Spain and ongoing support']),
   ('⚖️ Lawyers', ['Family, civil, criminal, administrative and tax law — priced case by case']),
   ('📎 Extras', ['Sworn translations', 'Health insurance', 'Official certificates']),
  ],
  note='The lawyer quotes a price after the consultation, based on your case', ad='Partner link: your request reaches the lawyer marked “from Kalmykov Group”'),
 'es': dict(
  page='/es/abogados/', html_lang='es', title='Abogados en España — consulta gratuita | Kalmykov Group',
  desc='Despacho de abogados colaborador en España: residencia, arraigo, regularización, nacionalidad española, impuestos, autónomos y compra de vivienda. Consulta gratuita en español',
  kick='Despacho de abogados colaborador', free='CONSULTA GRATUITA', freesub='Un abogado revisa tu caso y te dice qué hacer',
  hl='Residencia y nacionalidad española', hlsub='Arraigo, regularización, renovaciones y cambios de residencia: te acompañan en todo el trámite',
  chips=[('🛂', 'Residencia y arraigo'), ('🇪🇸', 'Nacionalidad española'), ('🔁', 'Renovación y modificación'), ('🎓', 'Visado de estudiante'),
         ('💻', 'Visado nómada digital'), ('🧾', 'Impuestos y declaraciones'), ('💼', 'Alta de autónomo y gestoría'), ('🏠', 'Compra de vivienda segura')],
  trust='10 años en España · 35+ abogados y asesores fiscales · 4 000+ casos', langs='Atienden en español, inglés, ruso y ucraniano',
  wa='Escribir por WhatsApp', tg='', all='Todos los servicios →', back='← Inicio', home='/es/', tgon=False,
  h1='Abogados en España: consulta gratuita', intro='Un despacho con el que trabajamos y en el que confiamos. Escríbeles por WhatsApp: un abogado revisa tu caso gratis y te dice qué hacer y cuánto cuesta',
  cats=[
   ('🛂 Residencia y documentos', ['Regularización extraordinaria', 'Arraigo y renovaciones de residencia', 'Cambio de tipo de residencia (modificación)', 'Nacionalidad española', 'Visado de estudiante', 'Visado nómada digital', 'Visado de profesional altamente cualificado', 'Residencia de emprendedor', 'Traslado intraempresarial']),
   ('🧾 Impuestos y contabilidad', ['Consulta con asesor fiscal', 'Alta de autónomo y gestoría mensual', 'Contabilidad de empresa', 'Declaración de la renta (Modelo 100)', 'Impuesto de no residentes (Modelo 210)', 'Bienes en el extranjero (Modelo 720)', 'Impuesto sobre el patrimonio (Modelo 714)', 'Cambio de residencia fiscal (Modelo 030)', 'Ley Beckham y su renovación']),
   ('🏠 Vivienda y herencias', ['Compraventa de vivienda: revisión de arras, contrato, cargas y deudas', 'Herencias de bienes en España']),
   ('🏢 Empresa', ['Constitución de sociedad y acompañamiento']),
   ('⚖️ Abogados', ['Derecho de familia, civil, penal, administrativo y fiscal — presupuesto según el caso']),
   ('📎 Otros', ['Traducciones juradas', 'Seguro médico', 'Certificados y documentos']),
  ],
  note='El abogado te da el precio después de la consulta, según tu caso', ad='Enlace de colaboración: tu solicitud llega al abogado como «de Kalmykov Group»'),
}

WA_ICO = '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.5-3.9-4.7-4.1-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 1.9c.1.2.1.4 0 .5l-.3.5-.4.4c-.1.1-.3.3-.1.6.1.3.6 1.1 1.4 1.8 1 .9 1.8 1.1 2.1 1.3.3.1.4.1.6-.1l.8-1c.2-.3.4-.2.6-.1l1.8.9c.3.1.4.2.5.3.1.2.1.6-.1 1.2Z"/></svg>'
TG_ICO = '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M21.9 4.3 18.6 20c-.2 1.1-.9 1.4-1.8.9l-5-3.7-2.4 2.3c-.3.3-.5.5-1 .5l.4-5.1 9.2-8.3c.4-.4-.1-.6-.6-.2L6 13.6l-4.9-1.5c-1.1-.3-1.1-1.1.2-1.6L20.5 3c.9-.3 1.7.2 1.4 1.3Z"/></svg>'


def wa_link(lang, src):
    return f'/p/yuristy-wa?src={src}' + ('' if lang == 'ru' else f'&amp;lang={lang}')


def buttons(lang, src):
    d = T[lang]
    b = f'<a class="lwb lwwa" href="{wa_link(lang, src)}" target="_blank" rel="noopener">{WA_ICO}{esc(d["wa"])}</a>'
    if d['tgon']:
        b += f'<a class="lwb lwtg" href="/p/yuristy-tg?src={src}" target="_blank" rel="noopener">{TG_ICO}{esc(d["tg"])}</a>'
    return f'<div class="lwbtns{"" if d["tgon"] else " one"}">{b}</div>'


def block(lang):
    d = T[lang]
    ch = ''.join(f'<span><i>{a}</i>{esc(b)}</span>' for a, b in d['chips'])
    return ('<!--lw--><aside class="lw" aria-label="' + esc(d['kick']) + '">'
            f'<span class="lwk">⚖️ {esc(d["kick"])}</span>'
            f'<div class="lwfree">{esc(d["free"])}</div><p class="lwfs">{esc(d["freesub"])}</p>'
            f'<div class="lwhl"><b>{esc(d["hl"])}</b><span>{esc(d["hlsub"])}</span></div>'
            f'<div class="lwch">{ch}</div>'
            f'<p class="lwtr">{esc(d["trust"])}</p><p class="lwlg">{esc(d["langs"])}</p>'
            + buttons(lang, 'main') +
            f'<a class="lwall" href="{d["page"]}">{esc(d["all"])}</a></aside><!--/lw-->')


BLOCK_CSS = '''<style>/* 26.11.2026: юристы-партнёры в «Поездках» — слева, сервисы справа (Евгений) */
.tw{display:grid;grid-template-columns:minmax(360px,5fr) 8fr;gap:12px;align-items:stretch;margin-top:12px}
.tw>.trip-g{grid-template-columns:repeat(4,1fr)!important;grid-auto-rows:1fr;margin:0}
.tw>.trip-g a{min-height:0}
.tw>.trip-g i.tph{flex:1 1 auto;height:auto!important;min-height:64px}
.tw>.trip-g a b{font-size:14px}
.tw>.trip-g a span{padding-bottom:9px}
.lw{grid-row:1;background:radial-gradient(120% 80% at 100% 0,#1d3a6b 0,#0b1426 55%);color:#fff;border:3px solid #d4a24c;border-radius:22px;padding:16px 15px 15px;box-shadow:0 0 0 5px rgba(212,162,76,.18),0 12px 28px rgba(0,0,0,.35);display:flex;flex-direction:column}
.lwk{align-self:flex-start;font:800 11.5px/1 var(--body);letter-spacing:.07em;text-transform:uppercase;color:#ffd54a;border:1.5px solid #ffd54a;border-radius:999px;padding:6px 10px}
.lwfree{margin:12px 0 3px;text-align:center;padding:12px 8px;border-radius:16px;background:linear-gradient(100deg,#00c853,#64dd17 45%,#b2ff59 50%,#64dd17 55%,#00c853);background-size:250% 100%;border:3px solid #111;color:#0b1426;font:900 24px/1.05 var(--display);box-shadow:0 5px 0 #111;animation:lwbg 2.8s linear infinite,lwpl 1.7s ease-out infinite}
@keyframes lwbg{to{background-position:250% 0}}@keyframes lwpl{0%{box-shadow:0 5px 0 #111,0 0 0 0 rgba(100,221,23,.8)}70%{box-shadow:0 5px 0 #111,0 0 0 13px rgba(100,221,23,0)}100%{box-shadow:0 5px 0 #111,0 0 0 0 rgba(100,221,23,0)}}
.lwfs{text-align:center;font-size:13.5px;opacity:.92;margin:7px 0 11px;color:#fff}
.lwhl{background:linear-gradient(180deg,#2b2b2b,#0c0c0c);border:2px solid #d4a24c;border-radius:14px;padding:11px 12px;margin-bottom:11px}
.lwhl b{display:block;font:900 19px/1.15 var(--display);color:#ffcf40;text-shadow:0 2px 0 #000}.lwhl span{display:block;font-size:13px;line-height:1.4;margin-top:4px;opacity:.92}
.lwch{display:grid;grid-template-columns:1fr 1fr;gap:7px}.lwch span{display:flex;gap:7px;align-items:center;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:11px;padding:8px 9px;font:700 13px/1.2 var(--body);color:#fff}.lwch i{font-style:normal;font-size:17px}
.lwtr{font-size:12.5px;text-align:center;margin:12px 0 2px;color:#ffd54a;font-weight:700}.lwlg{font-size:12.5px;text-align:center;opacity:.8;margin:0 0 12px;color:#fff}
.lwbtns{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:auto}.lwbtns.one{grid-template-columns:1fr}
.lwb{display:flex;align-items:center;justify-content:center;gap:7px;padding:13px 8px;border-radius:999px;border:3px solid #111;font:900 16px var(--display);text-decoration:none;box-shadow:0 4px 0 #111}
.lwb:active{transform:translateY(3px);box-shadow:0 1px 0 #111}.lwwa{background:#25d366;color:#0b1426}.lwtg{background:#2aabee;color:#fff}
.lwall{display:block;text-align:center;margin-top:9px;padding:11px;border-radius:999px;border:2px solid #ffd54a;color:#ffd54a;font:800 15px var(--body);text-decoration:none}
@media(max-width:900px){.tw{display:flex;flex-direction:column}.tw>.lw{order:2}.tw>.trip-g{order:1}}
@media(max-width:600px){.lwfree{font-size:22px}.lwhl b{font-size:18px}}
@media(prefers-reduced-motion:reduce){.lwfree{animation:none}}
</style>'''


def page(lang):
    d = T[lang]
    cats = ''.join(f'<section class="yc"><h2>{esc(h)}</h2><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in items) + '</ul></section>' for h, items in d['cats'])
    alts = {'ru': '/yuristy/', 'uk': '/yuristy/ua', 'en': '/en/lawyers/', 'es': '/es/abogados/'}
    hl = ''.join(f'<link rel="alternate" hreflang="{k}" href="{BASE}{v}">' for k, v in alts.items())
    sw = ''.join(f'<a{" class=on" if alts[k] == d["page"] else ""} href="{v}">{n}</a>' for k, v, n in [('ru', '/yuristy/', 'RU'), ('uk', '/yuristy/ua', 'UA'), ('en', '/en/lawyers/', 'EN'), ('es', '/es/abogados/', 'ES')])
    css = BLOCK_CSS.replace('<style>', '').replace('</style>', '') + '''
:root{--display:"Unbounded",system-ui,sans-serif;--body:"Inter",system-ui,sans-serif}
*{box-sizing:border-box}body{margin:0;background:#eef1f5;font-family:var(--body);color:#16233a}
.yw{max-width:980px;margin:0 auto;padding:14px 14px 40px}.ytop{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.ytop a{color:#16294a;font-weight:700;text-decoration:none}.ysw a{margin-left:8px;color:#16294a;text-decoration:none;font-weight:700;opacity:.55}.ysw a.on{opacity:1;text-decoration:underline}
.yhero{display:grid;grid-template-columns:1fr 1fr;gap:18px;align-items:start}.yhero h1{font:900 30px/1.15 var(--display);margin:6px 0 10px;color:#0b1426}.yhero p{font-size:16px;line-height:1.5;margin:0 0 10px}
.yn{font-size:13.5px;opacity:.8}.ycats{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:20px}
.yc{background:#fff;border-radius:18px;padding:14px 16px;border:2px solid #0f2a5c;box-shadow:0 4px 12px rgba(0,0,0,.08)}.yc h2{font:800 18px/1.2 var(--display);margin:0 0 8px;color:#0b1426}
.yc ul{margin:0;padding-left:18px}.yc li{margin:5px 0;line-height:1.4}.ycta{max-width:460px;margin:22px auto 0}.yad{font-size:12px;opacity:.6;text-align:center;margin-top:18px}
@media(max-width:760px){.yhero,.ycats{grid-template-columns:1fr}.yhero h1{font-size:24px}}'''
    return (f'<!doctype html>\n<html lang="{d["html_lang"]}">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'<title>{esc(d["title"])}</title>\n<meta name="description" content="{esc(d["desc"])}">\n<link rel="canonical" href="{BASE}{d["page"]}">\n{hl}\n'
            f'<meta property="og:title" content="{esc(d["title"])}"><meta property="og:description" content="{esc(d["desc"])}"><meta property="og:image" content="{BASE}/og.jpg">\n'
            '<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Unbounded:wght@700;800;900&display=swap">\n'
            f'<style>{css}</style>\n</head>\n<body><div class="yw">'
            f'<div class="ytop"><a href="{d["home"]}">{esc(d["back"])}</a><nav class="ysw">{sw}</nav></div>'
            f'<div class="yhero"><div><h1>{esc(d["h1"])}</h1><p>{esc(d["intro"])}</p><p class="yn">{esc(d["note"])}</p></div>'
            + block(lang).replace(f'<a class="lwall" href="{d["page"]}">{esc(d["all"])}</a>', '').replace('src=main', 'src=page')
            + '</div>'
            f'<div class="ycats">{cats}</div>'
            f'<div class="ycta">{buttons(lang, "page")}</div><p class="yad">{esc(d["ad"])}</p>'
            '</div></body></html>\n')


def insert(html, lang):
    return re.sub(r'<!--lw-->.*?<!--/lw-->', lambda m: block(lang), html, flags=re.S)


def main():
    p = SITE / 'index.html'
    s = p.read_text(encoding='utf-8')
    s = insert(s, 'ru')
    if '/* 26.11.2026: юристы-партнёры' not in s:
        s = s.replace('</head>', BLOCK_CSS + '\n</head>', 1)
    else:
        s = re.sub(r'<style>/\* 26\.11\.2026: юристы-партнёры.*?</style>', lambda m: BLOCK_CSS, s, flags=re.S)
    p.write_text(s, encoding='utf-8')
    out = {'ru': SITE / 'yuristy' / 'index.html', 'ua': SITE / 'yuristy' / 'ua.html',
           'en': SITE / 'en' / 'lawyers' / 'index.html', 'es': SITE / 'es' / 'abogados' / 'index.html'}
    for lang, f in out.items():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(page(lang), encoding='utf-8')
    sm = SITE / 'sitemap.xml'
    t = sm.read_text(encoding='utf-8')
    for u in ('/yuristy/', '/yuristy/ua'):
        if f'<loc>{BASE}{u}</loc>' not in t:
            t = t.replace('</urlset>', f'<url><loc>{BASE}{u}</loc></url>\n</urlset>')
    sm.write_text(t, encoding='utf-8')
    print('юристы: блок RU обновлён, страницы', ', '.join(str(f.relative_to(SITE)) for f in out.values()))


if __name__ == '__main__':
    main()
