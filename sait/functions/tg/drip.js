// /tg/drip — прогрев людей в боте. Вызывает задача GitHub novosti-sait.yml каждые ~20 минут.
// Шлёт одно сообщение через 7 дней после первой шпаргалки про аренду (поле u.d7 ставит webhook.js).
// Решение Евгения 18.11.2026: через неделю — предложение разбора договора. Пишем только с 10:00 до 20:00 по Мадриду.
const DAY7_ON = false; // включить после «да» Евгения на текст
const TEXT7 = [
  'Добрый день! Неделю назад вы брали у меня чек-лист по аренде',
  'Если уже нашли квартиру или вот-вот подписываете договор, могу посмотреть его до подписи: разберу по пунктам, где он расходится с законом и что попросить поменять у хозяина',
  'Это моя консультация, 50 €, отвечу в максимально короткие сроки. Пришлите фото всех страниц договора прямо сюда или в WhatsApp +34 624 916 605',
].join('\n\n');

async function tg(env, method, body) {
  const r = await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/${method}`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body),
  });
  return r.json();
}

export async function onRequestGet({ env }) {
  if (!env.TG_TOKEN || !env.BOT_KV) return new Response('no env', { status: 500 });
  const h = Number(new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Madrid', hour: 'numeric', hour12: false }).format(new Date()));
  if (!DAY7_ON) return new Response('day7 off');
  if (h < 10 || h >= 20) return new Response('quiet hours');
  const now = Date.now(); let sent = 0, cursor;
  do {
    const list = await env.BOT_KV.list({ prefix: 'u:', cursor });
    for (const k of list.keys) {
      const u = await env.BOT_KV.get(k.name, 'json');
      if (!u || !u.d7 || u.d7done || u.d7 > now) continue;
      if (now - u.d7 > 14 * 864e5) { u.d7done = 'просрочено'; await env.BOT_KV.put(k.name, JSON.stringify(u)); continue; }
      const r = await tg(env, 'sendMessage', { chat_id: u.id, text: TEXT7 });
      u.d7done = r.ok ? new Date().toISOString() : 'ошибка: ' + (r.description || '');
      await env.BOT_KV.put(k.name, JSON.stringify(u));
      if (r.ok) sent++;
      if (sent >= 25) break; // не больше 25 за проход
    }
    cursor = list.list_complete ? null : list.cursor;
  } while (cursor && sent < 25);
  return new Response('sent ' + sent);
}
