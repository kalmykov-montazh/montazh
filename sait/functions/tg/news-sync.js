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
  let done = parseInt(await env.BOT_KV.get('nday:' + day) || '0', 10);
  // Перевыложить вручную: в Cloudflare KV (kalmykov-bot) ключ «redo» = слаги через запятую. Выкладывает их сейчас, ключ стирает (17.11.2026)
  // Сменить аватар канала: ключ KV «setphoto» = адрес картинки на сайте (17.11.2026)
  // Логотип ES (17.11.2026): ставится один раз, флаг logo:v2
  const ph = (await env.BOT_KV.get('setphoto')) || ((await env.BOT_KV.get('logo:v2')) ? null : SITE + '/tg-kanal-logo-full.jpg?v=' + now);
  if (ph && !(await env.BOT_KV.get('setphoto'))) await env.BOT_KV.put('logo:v2', '1');
  if (ph) {
    await env.BOT_KV.delete('setphoto');
    const blob = await (await fetch(ph)).blob();
    const fd = new FormData(); fd.append('chat_id', env.NEWS_CHANNEL); fd.append('photo', blob, 'logo.jpg');
    const rr = await (await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/setChatPhoto`, { method: 'POST', body: fd })).json();
    await env.BOT_KV.put('setphoto-result', JSON.stringify(rr), { expirationTtl: 86400 });
  }
  const redo = ((await env.BOT_KV.get('redo')) || '').split(',').map(x => x.trim()).filter(Boolean);
  // 17.11.2026: переход на «богатые» сообщения с крупным заголовком — один раз перевыложить всё, что уже вышло
  if (!(await env.BOT_KV.get('rich:v1'))) {
    await env.BOT_KV.put('rich:v1', '1');
    for (const k of (await env.BOT_KV.list({ prefix: 'msg:' })).keys) redo.push(k.name.slice(4));
  }
  if (redo.length) {
    await env.BOT_KV.delete('redo');
    for (const sl of redo) {
      await env.BOT_KV.delete('news:' + sl);
      const old = await env.BOT_KV.get('msg:' + sl);
      if (old) await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/deleteMessage`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ chat_id: env.NEWS_CHANNEL, message_id: Number(old) }) });
    }
  }
  const items = Object.values(data)
    .filter(it => redo.includes(it.slug) || (it.published && now - Date.parse(it.published) < 20 * 3600e3 && Date.parse(it.published) <= now))
    .sort((a, b) => Date.parse(a.published) - Date.parse(b.published));
  const posted = [];
  for (const it of items) {
    const isRedo = redo.includes(it.slug);
    if (done >= PER_DAY && !isRedo) continue;
    if (await env.BOT_KV.get('news:' + it.slug)) continue;
    // 17.11.2026: ждём фото из Facebook (робот публикует в окно слота) — до 4 часов, потом без фото
    if (!isRedo && !it.img && now - Date.parse(it.published) < 4 * 3600e3) continue;
    const url = `${SITE}/novosti/${it.slug}`;
    const link = `<a href="${url}">Подробно, что делать и источники — на сайте</a>`;
    let r;
    // 17.11.2026 (Евгений: «красивое название, как у Нестеренко»): rich-сообщение — крупный заголовок, фото, текст, ссылка
    const paras = [];
    let len = 0;
    for (const p of (it.paras || [])) { const t = p.join(' ').trim(); if (!t) continue; if (len + t.length > 1400 && paras.length) break; paras.push(t); len += t.length; }
    const html = `<h2>${esc(it.title)}</h2>` + (it.img ? `<img src="${SITE + it.img}"/>` : '') +
      paras.map(t => `<p>${esc(t)}</p>`).join('') + `<p><b>${link}</b></p>`;
    r = await (await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendRichMessage`, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chat_id: env.NEWS_CHANNEL, rich_message: { html } }),
    })).json();
    if (!r.ok) posted.push('rich не вышел: ' + r.description);
    if (r.ok) {} else if (it.img) {
      const head = `<b>${esc(it.title)}</b>\n\n`;
      const caption = head + esc(short(it.paras || [], 1000 - head.length - 70)) + '\n\n' + link;
      r = await (await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendPhoto`, {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chat_id: env.NEWS_CHANNEL, photo: SITE + it.img, caption, parse_mode: 'HTML' }),
      })).json();
    } else {
      const text = `<b>${esc(it.title)}</b>\n\n${esc(short(it.paras || []))}\n\n${link}`;
      r = await (await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendMessage`, {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chat_id: env.NEWS_CHANNEL, text, parse_mode: 'HTML', link_preview_options: { is_disabled: true } }),
      })).json();
    }
    if (r.ok) { await env.BOT_KV.put('news:' + it.slug, day); await env.BOT_KV.put('msg:' + it.slug, String(r.result.message_id), { expirationTtl: 60 * 86400 }); if (!isRedo) done++; await env.BOT_KV.put('nday:' + day, String(done), { expirationTtl: 3 * 86400 }); posted.push(it.slug); }
    else posted.push('ошибка: ' + r.description);
  }
  // Воскресенье после 19:00 по Испании — итог недели (один раз)
  const es = new Date(now + 3600e3);
  if (es.getUTCDay() === 0 && es.getUTCHours() >= 19 && !(await env.BOT_KV.get('week:' + day))) {
    const week = Object.values(data)
      .filter(it => it.published && now - Date.parse(it.published) < 7 * 86400e3)
      .sort((a, b) => Date.parse(a.published) - Date.parse(b.published));
    if (week.length >= 3) {
      const items2 = week.map(it => `<li><a href="${SITE}/novosti/${it.slug}">${esc(it.title.replace(/^\d+ [а-я]+: /i, ''))}</a></li>`).join('');
      const html = `<h2>🗓 Испания за неделю: главное</h2><ul>${items2}</ul><p>Все новости с подробностями — <a href="${SITE}/novosti/">на сайте</a></p>`;
      const r = await (await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendRichMessage`, {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chat_id: env.NEWS_CHANNEL, rich_message: { html } }),
      })).json();
      if (r.ok) { await env.BOT_KV.put('week:' + day, '1', { expirationTtl: 8 * 86400 }); posted.push('итог недели'); }
    }
  }
  return new Response(JSON.stringify({ day, done, posted }), { headers: { 'content-type': 'application/json; charset=utf-8' } });
}
