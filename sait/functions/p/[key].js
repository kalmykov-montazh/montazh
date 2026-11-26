// /p/<партнёр>-wa и /p/<партнёр>-tg — кнопки на страницах партнёров (22.11.2026).
// WhatsApp: номер заявки, строка в таблицу, сразу чат партнёра с текстом «от Kalmykov Group, заявка …».
// Telegram: через бот @kalmykov_spain_bot (в личку текст не подставить) — бот сам даёт номер, пишет партнёру и в таблицу.
import { PARTNERS, nextNumber, logLead, waText } from '../../_kg/partners.js';
const BOT = 'kalmykov_spain_bot';
export async function onRequestGet({ params, request, env }) {
  const [key, ch] = String(params.key).split('-');
  const p = PARTNERS[key];
  if (!p) return Response.redirect('https://kalmykovgroup.com/', 302);
  const src = (new URL(request.url).searchParams.get('src') || 'site').replace(/[^a-z0-9]/gi, '').slice(0, 20) || 'site';
  const lang = (new URL(request.url).searchParams.get('lang') || 'ru').replace(/[^a-z]/g, '').slice(0, 2);
  if (ch === 'tg') return Response.redirect(`https://t.me/${BOT}?start=p_${key}_${src}${['ua', 'en', 'es'].includes(lang) ? '_' + lang : ''}`, 302);
  const num = await nextNumber(env, key);
  await logLead(key, num, 'WhatsApp', '', lang === 'ru' ? src : src + '-' + lang);
  return Response.redirect(`https://wa.me/${p.wa}?text=${encodeURIComponent(waText(key, num, lang))}`, 302);
}
