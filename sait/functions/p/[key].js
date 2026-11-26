// /p/<партнёр>-wa и /p/<партнёр>-tg — кнопки на страницах партнёров (22.11.2026).
// WhatsApp: номер заявки, строка в таблицу, сразу чат партнёра с текстом «от Kalmykov Group, заявка …».
// Telegram: через бот @kalmykov_spain_bot (в личку текст не подставить) — бот сам даёт номер, пишет партнёру и в таблицу.
// 26.11.2026 (решение Евгения): при нажатии WhatsApp бот сразу шлёт партнёру в Telegram «заявка №, сейчас напишет в WhatsApp, время» —
// если человек сотрёт подставленный текст, партнёр всё равно сопоставит его по времени. Копия — админу, как у Telegram-заявок.
import { PARTNERS, nextNumber, logLead, waText } from '../../_kg/partners.js';
const BOT = 'kalmykov_spain_bot';

async function notifyWa(env, key, num, lang, client) {
  if (!env.TG_TOKEN || !env.BOT_KV) return;
  const p = PARTNERS[key];
  const time = new Date().toLocaleTimeString('ru-RU', { timeZone: 'Europe/Madrid', hour: '2-digit', minute: '2-digit' });
  const card = `🆕 Заявка ${num} от Kalmykov Group\nТема: ${p.topic}${lang === 'ru' ? '' : '\nЯзык клиента: ' + lang.toUpperCase()}${client ? '\nКлиент: ' + client : ''}\nКлиент нажал WhatsApp в ${time} и сейчас напишет вам туда.\nЕсли номера заявки в его сообщении не будет — это он, сверяйте по ${client ? 'телефону и ' : ''}времени`;
  const send = (chat, text) => fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendMessage`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ chat_id: chat, text }),
  }).catch(() => {});
  const pchat = await env.BOT_KV.get('pchat3:' + key);
  if (pchat) await send(pchat, card);
  const admin = await env.BOT_KV.get('admin');
  if (admin) await send(admin, card.replace(' и сейчас напишет вам туда', ' (уведомление партнёру ' + (pchat ? 'ушло' : 'НЕ ушло — партнёр не подключён к боту') + ')'));
}

export async function onRequestGet({ params, request, env, waitUntil }) {
  const [key, ch] = String(params.key).split('-');
  const p = PARTNERS[key];
  if (!p) return Response.redirect('https://kalmykovgroup.com/', 302);
  const src = (new URL(request.url).searchParams.get('src') || 'site').replace(/[^a-z0-9]/gi, '').slice(0, 20) || 'site';
  const lang = (new URL(request.url).searchParams.get('lang') || 'ru').replace(/[^a-z]/g, '').slice(0, 2);
  if (ch === 'tg') return Response.redirect(`https://t.me/${BOT}?start=p_${key}_${src}${['ua', 'en', 'es'].includes(lang) ? '_' + lang : ''}`, 302);
  // 26.11.2026: ночью поисковые роботы прошли по кнопкам на 4 языках и создали пустые заявки ЮР-18…21 —
  // роботов и превью ссылок пропускаем в WhatsApp без номера, таблицы и уведомлений
  const ua = request.headers.get('user-agent') || '';
  if (!ua || /bot|crawl|spider|slurp|preview|gpt|claude|anthropic|perplexity|bytespider|amazonbot|facebookexternalhit|whatsapp\/|telegrambot|headless|lighthouse|python|curl|wget|httpclient|okhttp|java\//i.test(ua) || request.headers.get('purpose') === 'prefetch' || request.headers.get('sec-purpose')
      // кнопки на самом сайте (src=main/page/site): живой человек приходит со страницы сайта — без Referer считаем роботом
      || (/^(main|page|site)$/.test(src) && !/kalmykovgroup\.(com|pages\.dev)/.test(request.headers.get('referer') || ''))) {
    return Response.redirect(`https://wa.me/${p.wa}`, 302);
  }
  // 26.11.2026 22:40 (ЮР-14 в 22:21 пришла без клиента: человек открыл ссылку в обход окошка —
  // долгим нажатием, до загрузки скрипта или со старой страницы). Теперь GET заявку НЕ создаёт и никого не будит:
  // показывает страницу с тем же окошком «имя, фамилия, телефон». Заявка и карточка партнёру — только после POST
  return new Response(formPage(key, p, src, lang), {
    headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'x-robots-tag': 'noindex, nofollow' },
  });
}

const PT = {
  ru: { t: 'Написать специалисту в WhatsApp', s: 'Оставьте имя и телефон — специалист увидит, что вы от Kalmykov Group, и точно ответит', b: 'Написать в WhatsApp', h: 'На сайт' },
  ua: { t: 'Написати фахівцю у WhatsApp', s: 'Залиште ім’я та телефон — фахівець побачить, що ви від Kalmykov Group, і точно відповість', b: 'Написати у WhatsApp', h: 'На сайт' },
  en: { t: 'Message the specialist on WhatsApp', s: 'Leave your name and phone so the specialist sees you come from Kalmykov Group and replies', b: 'Message on WhatsApp', h: 'Back to site' },
  es: { t: 'Escribir al especialista por WhatsApp', s: 'Deja tu nombre y teléfono para que el especialista sepa que vienes de Kalmykov Group y te responda', b: 'Escribir por WhatsApp', h: 'Volver a la web' },
};
function formPage(key, p, src, lang) {
  const t = PT[lang] || PT.ru, hl = lang === 'ua' ? 'uk' : (PT[lang] ? lang : 'ru');
  const home = lang === 'ru' || !PT[lang] ? '/' : '/' + lang + '/';
  const href = `/p/${key}-wa?src=${encodeURIComponent(src)}${lang === 'ru' ? '' : '&lang=' + lang}`;
  return `<!doctype html><html lang="${hl}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>${t.t} — Kalmykov Group</title>
<style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#16294A;font:17px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#16294A;padding:16px;box-sizing:border-box}.c{background:#fff;border-radius:16px;max-width:400px;width:100%;padding:26px 22px;text-align:center}h1{font-size:21px;margin:0 0 10px}p{margin:0 0 18px;color:#445}.b{display:block;padding:15px;border-radius:12px;background:#25D366;color:#fff;font-weight:700;text-decoration:none}.h{display:inline-block;margin-top:14px;color:#667;font-size:15px}</style></head>
<body><div class="c"><h1>${t.t}</h1><p>${t.s}</p><a class="b" id="go" href="${href}">${t.b}</a><a class="h" href="${home}">${t.h}</a></div>
<script src="/waform.js"></script><script>setTimeout(function(){var a=document.getElementById('go');if(a)a.click();},150)</script></body></html>`;
}

// 26.11.2026 (решение Евгения 18:06): перед WhatsApp человек вводит имя, фамилию и телефон (окошко sait/waform.js) —
// они сами пишутся в таблицу партнёра в «Клиент». Партнёр ничего не заполняет. Без ботов и платных сообщений.
export async function onRequestPost({ params, request, env, waitUntil }) {
  const [key, ch] = String(params.key).split('-');
  const p = PARTNERS[key];
  const json = (o, st = 200) => new Response(JSON.stringify(o), { status: st, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });
  if (!p || ch !== 'wa') return json({ error: 'no' }, 404);
  let d = {};
  try { d = await request.json(); } catch (e) { return json({ error: 'bad' }, 400); }
  const name = String(d.name || '').replace(/[\r\n\t]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 80);
  const phone = String(d.phone || '').replace(/[^0-9+]/g, '').slice(0, 20);
  if (name.length < 2 || phone.replace(/\D/g, '').length < 7) return json({ error: 'fields' }, 400);
  const src = String(d.src || 'site').replace(/[^a-z0-9]/gi, '').slice(0, 20) || 'site';
  const lang = String(d.lang || 'ru').replace(/[^a-z]/g, '').slice(0, 2) || 'ru';
  const client = name + ', ' + phone;
  const num = await nextNumber(env, key);
  await logLead(key, num, 'WhatsApp', client, lang === 'ru' ? src : src + '-' + lang);
  const n = notifyWa(env, key, num, lang, client);
  if (typeof waitUntil === 'function') waitUntil(n); else await n;
  return json({ url: `https://wa.me/${p.wa}?text=${encodeURIComponent(waText(key, num, lang))}` });
}
