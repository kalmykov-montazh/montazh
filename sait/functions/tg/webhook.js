import { PARTNERS, nextNumber, logLead } from '../../_kg/partners.js';
// Публичный бот: выдаёт PDF-шпаргалки с сайта и запоминает людей (лиды).
// Переменные в Cloudflare Pages: TG_TOKEN (секрет, вносит Евгений), ADMIN_USERNAME (Kalmykov_broker). Секрет вебхука выводится из токена.
// Хранилище KV с привязкой BOT_KV.
const GUIDES = {
  chek:     { slug: 'chek-list-arenda', title: 'Чек-лист: 10 пунктов проверить до подписи договора аренды', rent: true, nopage: true, btn: '✅ Чек-лист: 10 пунктов до подписи договора' },
  chekua:   { slug: 'chek-list-arenda-ua', title: 'Чек-лист: 10 пунктів перевірити до підпису договору оренди', rent: true, nopage: true, ua: true, hidden: true },
  shtrafy:  { slug: 'shtrafy-v-ispanii', title: 'Штрафы в Испании: 15 самых частых для приезжих', rent: false },
  vnzh:     { slug: 'vnzh-posle-vremennoy-zashchity', title: 'Временная защита → ВНЖ на 4 года', rent: false },
  lovushki: { slug: 'lovushki-arendy-v-ispanii', title: 'Аренда в Испании: 17 ловушек и мошенничеств', rent: true },
  otkazy:   { slug: 'pochemu-slozhno-snyat-kvartiru-v-ispanii', title: 'Как снять квартиру в Испании: 7 причин отказов', rent: true },
  klimat:   { slug: 'gde-zhit-v-ispanii-klimat-i-arenda', title: 'Где жить в Испании: климат и аренда по регионам', rent: true },
};
const SITE = 'https://kalmykovgroup.com';
// Прогрев (решение Евгения 18.11.2026): сразу после PDF — следующая шпаргалка по теме первой кнопкой
const NEXT = { chek: 'lovushki', lovushki: 'chek', otkazy: 'chek', klimat: 'otkazy', shtrafy: 'vnzh', vnzh: 'shtrafy' };

const MENU = Object.entries(GUIDES).filter(([k, g]) => !g.hidden).map(([k, g]) => [{ text: g.btn || g.title, callback_data: 'g:' + k }]).concat([[{ text: '📰 Новости и законы Испании — каждый день', url: 'https://t.me/+DF-daga43CM5MzVk' }]]);

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
    caption: g.ua ? `${g.title}\n\nЗбережіть, щоб був під рукою` : g.nopage ? `${g.title}\n\nСохраните, чтобы был под рукой` : `${g.title}\n\nСохраните, чтобы была под рукой. Подробнее на сайте: ${SITE}/gaidy/${g.slug}`,
  });
  const extra = g.ua ? 'Шукаєте житло? Свіжі варіанти оренди та продажу — в моєму каналі @kalmykov_realty' : g.rent
    ? 'Ищете квартиру? Свежие варианты аренды и продажи — в моём канале @kalmykov_realty'
    : 'Если будут вопросы по Испании, пишите сюда, отвечу';
  const news = g.ua ? '\n\nНовини та закони Іспанії щодня — в каналі https://t.me/+DF-daga43CM5MzVk' : '\n\nНовости и законы Испании каждый день — в канале https://t.me/+DF-daga43CM5MzVk';
  await tg(env, 'sendMessage', {
    chat_id: chat, text: extra + news + (NEXT[key] ? `\n\nСледом пригодится: «${GUIDES[NEXT[key]].btn || GUIDES[NEXT[key]].title}»` : '') + '\n\nДругие шпаргалки — по кнопкам ниже',
    reply_markup: { inline_keyboard: NEXT[key] ? [[{ text: '👉 ' + (GUIDES[NEXT[key]].btn || GUIDES[NEXT[key]].title), callback_data: 'g:' + NEXT[key] }]].concat(MENU) : MENU },
  });
}

async function sendMenu(env, chat) {
  await tg(env, 'sendMessage', {
    chat_id: chat,
    text: 'Добрый день! Я Евгений Калмыков, живу в Валенсии. Здесь бесплатные шпаргалки по жизни в Испании. Выберите, какую прислать',
    reply_markup: { inline_keyboard: MENU },
  });
}

async function remember(env, from, key, src) {
  if (!env.BOT_KV || !from) return;
  const id = String(from.id);
  const old = await env.BOT_KV.get('u:' + id, 'json');
  const now = new Date().toISOString();
  const u = old || { id, first: now, name: [from.first_name, from.last_name].filter(Boolean).join(' '), username: from.username || '', lang: from.language_code || '', guides: [] };
  if (key && !u.guides.includes(key)) u.guides.push(key);
  if (src && !u.src) u.src = src; // откуда пришёл впервые: site, ig, fb, tt, yt…
  // Прогрев: через 7 дней после первой шпаргалки про аренду — одно сообщение (отправляет /tg/drip)
  if (key && GUIDES[key] && GUIDES[key].rent && !GUIDES[key].ua && !u.d7) u.d7 = Date.now() + 7 * 864e5;
  u.last = now;
  await env.BOT_KV.put('u:' + id, JSON.stringify(u));
  // Евгению — уведомление о каждом новом человеке
  if (!old && env.ADMIN_USERNAME && from.username !== env.ADMIN_USERNAME) {
    const admin = await env.BOT_KV.get('admin');
    if (admin) await tg(env, 'sendMessage', { chat_id: admin, text: `🆕 Новый в боте: ${u.name}${u.username ? ' @' + u.username : ''}, взял: ${key || 'меню'}${src ? ', откуда: ' + src : ''}` });
  }
}


// Заявки партнёрам через бот (22.11.2026): /start p_<партнёр>_<откуда> — клиент; /start reg_<партнёр> — партнёр один раз подключается
async function partnerLead(env, m, key, src) {
  const p = PARTNERS[key]; const chat = m.chat.id; const f = m.from || {};
  const num = await nextNumber(env, key);
  const name = [f.first_name, f.last_name].filter(Boolean).join(' ');
  const who = name + (f.username ? ' @' + f.username : '');
  await logLead(key, num, 'Telegram', who, src);
  await remember(env, f, '', src);
  const card = `🆕 Заявка ${num} от Kalmykov Group\nТема: ${p.topic}\nКлиент: ${who}\nОн сейчас напишет вам в Telegram${f.username ? '' : ' (ника нет — ждите его сообщения)'}`;
  const btn = f.username ? { reply_markup: { inline_keyboard: [[{ text: 'Написать клиенту', url: 'https://t.me/' + f.username }]] } } : {};
  const pchat = env.BOT_KV && await env.BOT_KV.get('pchat2:' + key);
  if (pchat) await tg(env, 'sendMessage', Object.assign({ chat_id: pchat, text: card }, btn));
  const admin = env.BOT_KV && await env.BOT_KV.get('admin');
  if (admin) await tg(env, 'sendMessage', { chat_id: admin, text: card + (pchat ? '' : '\n⚠️ Партнёр ещё не подключён к боту') });
  await tg(env, 'sendMessage', { chat_id: chat, text: `Ваша заявка ${num}. Нажмите кнопку ниже — откроется чат со специалистом (${p.who}, ${p.topic}). Напишите, что вы от Kalmykov Group, заявка ${num}, и коротко ваш вопрос`, reply_markup: { inline_keyboard: [[{ text: 'Написать специалисту', url: p.tg }]] } });
}
async function partnerReg(env, m, key) {
  const chat = String(m.chat.id); const f = m.from || {};
  if (env.ADMIN_USERNAME && f.username === env.ADMIN_USERNAME) { await tg(env, 'sendMessage', { chat_id: chat, text: 'Ссылка работает. Это ссылка для партнёра — вас не подключаю, заявки пойдут партнёру, вам копия' }); return; }
  const old = await env.BOT_KV.get('pchat2:' + key);
  const admin = await env.BOT_KV.get('admin');
  if (admin && chat === admin) { await tg(env, 'sendMessage', { chat_id: chat, text: 'Ссылка работает. Это ссылка для партнёра — этот аккаунт не подключаю, сюда и так приходят копии заявок' }); return; }
  if (old && old !== chat) { await tg(env, 'sendMessage', { chat_id: chat, text: 'Этот раздел уже подключён. Если это ошибка — напишите Евгению' }); if (admin) await tg(env, 'sendMessage', { chat_id: admin, text: `⚠️ Попытка подключиться к заявкам «${key}» с другого аккаунта: ${f.first_name || ''} @${f.username || '—'}` }); return; }
  await env.BOT_KV.put('pchat2:' + key, chat);
  await tg(env, 'sendMessage', { chat_id: chat, text: 'Готово! Сюда будут приходить заявки от Kalmykov Group с номером и контактом клиента' });
  if (admin) await tg(env, 'sendMessage', { chat_id: admin, text: `✅ К заявкам «${key}» подключился ${f.first_name || ''} @${f.username || '—'}` });
}

export async function onRequestPost({ request, env }) {
  if (!env.TG_TOKEN || request.headers.get('x-telegram-bot-api-secret-token') !== await hookSecret(env)) return new Response('no', { status: 403 });
  const up = await request.json();
  try {
    if (up.message) {
      const m = up.message, chat = m.chat.id, text = (m.text || '').trim();
      if (m.from && env.ADMIN_USERNAME && m.from.username === env.ADMIN_USERNAME && env.BOT_KV) await env.BOT_KV.put('admin', String(chat));
      const pl = text.startsWith('/start') ? (text.split(' ')[1] || '') : '';
      const pm = pl.match(/^p_([a-z]+)_?([a-z0-9]*)$/i), rm = pl.match(/^reg_([a-z]+)$/i);
      if (pm && PARTNERS[pm[1]]) { await partnerLead(env, m, pm[1], pm[2] || 'site'); }
      else if (rm && PARTNERS[rm[1]] && env.BOT_KV) { await partnerReg(env, m, rm[1]); }
      else if (text.startsWith('/start')) {
        // ?start=<ключ>_<метка источника>, например chek_site, shtrafy_ig
        const [key = '', src = ''] = (text.split(' ')[1] || '').split('_');
        await remember(env, m.from, key, src);
        if (GUIDES[key]) await sendGuide(env, chat, key); else await sendMenu(env, chat);
      } else if (text === '/stat' && m.from && m.from.username === env.ADMIN_USERNAME) {
        const list = await env.BOT_KV.list({ prefix: 'u:' });
        const cnt = {}, srcs = {};
        for (const k of list.keys) { const u = await env.BOT_KV.get(k.name, 'json'); (u.guides.length ? u.guides : ['меню']).forEach(g => cnt[g] = (cnt[g] || 0) + 1); const sr = u.src || 'без метки'; srcs[sr] = (srcs[sr] || 0) + 1; }
        const dl = {};
        for (const k of Object.keys(GUIDES)) dl[k] = (await env.BOT_KV.get('dl:' + k)) || 0;
        await tg(env, 'sendMessage', { chat_id: chat, text: `Людей в боте: ${list.keys.length}\nПо шпаргалкам: ${JSON.stringify(cnt)}\nОткуда пришли: ${JSON.stringify(srcs)}\nСкачали с сайта без бота: ${JSON.stringify(dl)}` });
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
