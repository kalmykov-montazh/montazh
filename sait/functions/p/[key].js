// /p/<партнёр>-wa и /p/<партнёр>-tg — кнопки на страницах партнёров (22.11.2026).
// WhatsApp: номер заявки, строка в таблицу, сразу чат партнёра с текстом «от Kalmykov Group, заявка …».
// Telegram: через бот @kalmykov_spain_bot (в личку текст не подставить) — бот сам даёт номер, пишет партнёру и в таблицу.
// 26.11.2026 (решение Евгения): при нажатии WhatsApp бот сразу шлёт партнёру в Telegram «заявка №, сейчас напишет в WhatsApp, время» —
// если человек сотрёт подставленный текст, партнёр всё равно сопоставит его по времени. Копия — админу, как у Telegram-заявок.
import { PARTNERS, nextNumber, logLead, waText } from '../../_kg/partners.js';
const BOT = 'kalmykov_spain_bot';

async function notifyWa(env, key, num, lang) {
  if (!env.TG_TOKEN || !env.BOT_KV) return;
  const p = PARTNERS[key];
  const time = new Date().toLocaleTimeString('ru-RU', { timeZone: 'Europe/Madrid', hour: '2-digit', minute: '2-digit' });
  const card = `🆕 Заявка ${num} от Kalmykov Group\nТема: ${p.topic}${lang === 'ru' ? '' : '\nЯзык клиента: ' + lang.toUpperCase()}\nКлиент нажал WhatsApp в ${time} и сейчас напишет вам туда.\nЕсли номера заявки в его сообщении не будет — это он, сверяйте по времени`;
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
  const num = await nextNumber(env, key);
  await logLead(key, num, 'WhatsApp', '', lang === 'ru' ? src : src + '-' + lang);
  const n = notifyWa(env, key, num, lang);
  if (typeof waitUntil === 'function') waitUntil(n); else await n;
  return Response.redirect(`https://wa.me/${p.wa}?text=${encodeURIComponent(waText(key, num, lang))}`, 302);
}
