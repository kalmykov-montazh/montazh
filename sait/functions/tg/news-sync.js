// Новости сайта → Telegram-канал новостей (17.11.2026, решение Евгения: в канал идут ВСЕ новости, что вышли в Facebook и на сайт — обычно 2–3, бывает 4; по воскресеньям вечером — итог недели).
// Вызывает задача novosti-sait.yml после каждой сборки сайта: GET https://kalmykovgroup.com/tg/news-sync
// Переменные Cloudflare: TG_TOKEN, NEWS_CHANNEL (@имя канала). Бот должен быть админом канала.
const SITE = 'https://kalmykovgroup.com';
const PER_DAY = 6; // предохранитель от сбоя, не план

function short(paras, max = 650) {
  let out = '';
  for (const p of paras) {
    const t = p.join(' ').trim();
    if (!t) continue;
    if ((out + '\n\n' + t).length > max) { if (!out) out = t.slice(0, max).replace(/\s\S*$/, '') + '…'; break; }
    out = out ? out + '\n\n' + t : t;
  }
  return out;
}
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

export async function onRequestGet({ env }) {
  if (!env.TG_TOKEN || !env.NEWS_CHANNEL || !env.BOT_KV) return new Response('нет настроек', { status: 200 });
  const data = await (await fetch(`${SITE}/novosti/_data.json`, { cf: { cacheTtl: 0 } })).json();
  const now = Date.now();
  const day = new Date(now + 3600e3).toISOString().slice(0, 10); // день по Испании (зима)
  let done = parseInt(await env.BOT_KV.get('newsday:' + day) || '0', 10);
  const items = Object.values(data)
    .filter(it => it.published && now - Date.parse(it.published) < 20 * 3600e3 && Date.parse(it.published) <= now)
    .sort((a, b) => Date.parse(a.published) - Date.parse(b.published));
  const posted = [];
  for (const it of items) {
    if (done >= PER_DAY) break;
    if (await env.BOT_KV.get('news:' + it.slug)) continue;
    const url = `${SITE}/novosti/${it.slug}`;
    const text = `<b>${esc(it.title)}</b>\n\n${esc(short(it.paras || []))}\n\n<a href="${url}">Подробно, что делать и источники — на сайте</a>`;
    const r = await (await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendMessage`, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chat_id: env.NEWS_CHANNEL, text, parse_mode: 'HTML', link_preview_options: { url, prefer_large_media: true, show_above_text: false } }),
    })).json();
    if (r.ok) { await env.BOT_KV.put('news:' + it.slug, day); done++; await env.BOT_KV.put('newsday:' + day, String(done), { expirationTtl: 3 * 86400 }); posted.push(it.slug); }
    else posted.push('ошибка: ' + r.description);
  }
  // Воскресенье после 19:00 по Испании — итог недели (один раз)
  const es = new Date(now + 3600e3);
  if (es.getUTCDay() === 0 && es.getUTCHours() >= 19 && !(await env.BOT_KV.get('week:' + day))) {
    const week = Object.values(data)
      .filter(it => it.published && now - Date.parse(it.published) < 7 * 86400e3)
      .sort((a, b) => Date.parse(a.published) - Date.parse(b.published));
    if (week.length >= 3) {
      const lines = week.map(it => `• <a href="${SITE}/novosti/${it.slug}">${esc(it.title.replace(/^\d+ [а-я]+: /i, ''))}</a>`).join('\n');
      const text = `<b>🗓 Испания за неделю: главное</b>\n\n${lines}\n\nВсе новости с подробностями — ${SITE}/novosti/`;
      const r = await (await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendMessage`, {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chat_id: env.NEWS_CHANNEL, text, parse_mode: 'HTML', link_preview_options: { is_disabled: true } }),
      })).json();
      if (r.ok) { await env.BOT_KV.put('week:' + day, '1', { expirationTtl: 8 * 86400 }); posted.push('итог недели'); }
    }
  }
  return new Response(JSON.stringify({ day, done, posted }), { headers: { 'content-type': 'application/json; charset=utf-8' } });
}
