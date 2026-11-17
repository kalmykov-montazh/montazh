// Публичный бот: выдаёт PDF-шпаргалки с сайта и запоминает людей (лиды).
// Переменные в Cloudflare Pages: TG_TOKEN (секрет, вносит Евгений), ADMIN_USERNAME (Kalmykov_broker). Секрет вебхука выводится из токена.
// Хранилище KV с привязкой BOT_KV.
const GUIDES = {
  shtrafy:  { slug: 'shtrafy-v-ispanii', title: 'Штрафы в Испании: 15 самых частых для приезжих', rent: false },
  vnzh:     { slug: 'vnzh-posle-vremennoy-zashchity', title: 'Временная защита → ВНЖ на 4 года', rent: false },
  lovushki: { slug: 'lovushki-arendy-v-ispanii', title: 'Аренда в Испании: 17 ловушек и мошенничеств', rent: true },
  otkazy:   { slug: 'pochemu-slozhno-snyat-kvartiru-v-ispanii', title: 'Как снять квартиру в Испании: 7 причин отказов', rent: true },
  klimat:   { slug: 'gde-zhit-v-ispanii-klimat-i-arenda', title: 'Где жить в Испании: климат и аренда по регионам', rent: true },
};
const SITE = 'https://kalmykovgroup.com';

const MENU = Object.entries(GUIDES).map(([k, g]) => [{ text: g.title, callback_data: 'g:' + k }]).concat([[{ text: '📰 Новости и законы Испании — каждый день', url: 'https://t.me/+DF-daga43CM5MzVk' }]]);

async function hookSecret(env) {
  const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('kalmykov-bot:' + env.TG_TOKEN));
  return [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 40);
}

async function tg(env, method, body) {
  const r = await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/${method}`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body),
  });
  return r.json();
}

async function sendGuide(env, chat, key) {
  const g = GUIDES[key];
  if (!g) return sendMenu(env, chat);
  await tg(env, 'sendDocument', {
    chat_id: chat,
    document: `${SITE}/gaidy/${g.slug}.pdf`,
    caption: `${g.title}\n\nСохраните, чтобы была под рукой. Подробнее на сайте: ${SITE}/gaidy/${g.slug}`,
  });
  const extra = g.rent
    ? 'Ищете квартиру? Свежие варианты аренды и продажи — в моём канале @kalmykov_realty'
    : 'Если будут вопросы по Испании, пишите сюда, отвечу';
  await tg(env, 'sendMessage', {
    chat_id: chat, text: extra + '\n\nДругие шпаргалки — по кнопкам ниже',
    reply_markup: { inline_keyboard: MENU },
  });
}

async function sendMenu(env, chat) {
  await tg(env, 'sendMessage', {
    chat_id: chat,
    text: 'Добрый день! Я Евгений Калмыков, живу в Валенсии. Здесь бесплатные шпаргалки по жизни в Испании. Выберите, какую прислать',
    reply_markup: { inline_keyboard: MENU },
  });
}

async function remember(env, from, key) {
  if (!env.BOT_KV || !from) return;
  const id = String(from.id);
  const old = await env.BOT_KV.get('u:' + id, 'json');
  const now = new Date().toISOString();
  const u = old || { id, first: now, name: [from.first_name, from.last_name].filter(Boolean).join(' '), username: from.username || '', lang: from.language_code || '', guides: [] };
  if (key && !u.guides.includes(key)) u.guides.push(key);
  u.last = now;
  await env.BOT_KV.put('u:' + id, JSON.stringify(u));
  // Евгению — уведомление о каждом новом человеке
  if (!old && env.ADMIN_USERNAME && from.username !== env.ADMIN_USERNAME) {
    const admin = await env.BOT_KV.get('admin');
    if (admin) await tg(env, 'sendMessage', { chat_id: admin, text: `🆕 Новый в боте: ${u.name}${u.username ? ' @' + u.username : ''}, взял: ${key || 'меню'}` });
  }
}

export async function onRequestPost({ request, env }) {
  if (!env.TG_TOKEN || request.headers.get('x-telegram-bot-api-secret-token') !== await hookSecret(env)) return new Response('no', { status: 403 });
  const up = await request.json();
  try {
    if (up.message) {
      const m = up.message, chat = m.chat.id, text = (m.text || '').trim();
      if (m.from && env.ADMIN_USERNAME && m.from.username === env.ADMIN_USERNAME && env.BOT_KV) await env.BOT_KV.put('admin', String(chat));
      if (text.startsWith('/start')) {
        const key = text.split(' ')[1] || '';
        await remember(env, m.from, key);
        if (GUIDES[key]) await sendGuide(env, chat, key); else await sendMenu(env, chat);
      } else if (text === '/stat' && m.from && m.from.username === env.ADMIN_USERNAME) {
        const list = await env.BOT_KV.list({ prefix: 'u:' });
        const cnt = {};
        for (const k of list.keys) { const u = await env.BOT_KV.get(k.name, 'json'); (u.guides.length ? u.guides : ['меню']).forEach(g => cnt[g] = (cnt[g] || 0) + 1); }
        const dl = {};
        for (const k of Object.keys(GUIDES)) dl[k] = (await env.BOT_KV.get('dl:' + k)) || 0;
        await tg(env, 'sendMessage', { chat_id: chat, text: `Людей в боте: ${list.keys.length}\nПо шпаргалкам: ${JSON.stringify(cnt)}\nСкачали с сайта без бота: ${JSON.stringify(dl)}` });
      } else {
        // Любое сообщение человека — Евгению, чтобы ответил сам
        const admin = env.BOT_KV && await env.BOT_KV.get('admin');
        if (admin && String(chat) !== admin) await tg(env, 'forwardMessage', { chat_id: admin, from_chat_id: chat, message_id: m.message_id });
        await remember(env, m.from, '');
        if (String(chat) !== admin) await tg(env, 'sendMessage', { chat_id: chat, text: 'Получил, отвечу лично. А пока шпаргалки — по кнопкам', reply_markup: { inline_keyboard: MENU } });
      }
    } else if (up.callback_query) {
      const q = up.callback_query, key = (q.data || '').replace('g:', '');
      await tg(env, 'answerCallbackQuery', { callback_query_id: q.id });
      await remember(env, q.from, key);
      await sendGuide(env, q.message.chat.id, key);
    }
  } catch (e) { /* не роняем вебхук, Telegram иначе будет повторять */ }
  return new Response('ok');
}
