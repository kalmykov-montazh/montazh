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
// 17.11.2026: значок рубрики перед заголовком в канале (легенда Евгения). Из файла новости (@значок:) или по словам
const RUBRICS = [
  ['🚨', /срочн|сегодня|с завтра|вступ(ил|ает|ит)|последний день/],
  ['⚠️', /штраф|мошен|провер|предупрежд|непогод|ливн|alerta|наводн|осторожн/],
  ['🏠', /аренд|квартир|жиль|окупас|ипотек|хозяин|жилец|недвижим/],
  ['📜', /внж|\bnie\b|\btie\b|закон|документ|миграц|легализ|паспорт|декрет|указ|прописк|empadron/],
  ['✈️', /рейс|самол[её]т|аэропорт|авиа/],
  ['🚆', /поезд|железн|электрич|автобус|забаст|транспорт|renfe|метро|трамва/],
  ['💶', /цен[аыу]|налог|пособ|зарплат|подорож|деньг|пенси|€|евро\b|ипц|инфляц/],
];
const rubric = it => it.emo || (RUBRICS.find(([, re]) => re.test((it.title + ' ' + (it.desc || '')).toLowerCase())) || ['🇪🇸'])[0];
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// 22.11.2026 (решение Евгения): под новостью — одна строка с услугой по теме (если подходит) и одна постоянная на сайт. Ссылки через /go/ — со счётчиком
const SVC = [
  [/(отмен|задерж)\S*.{0,15}(рейс|вылет)|забаст\S*.{0,40}(аэропорт|авиа|пилот|ryanair|vueling|iberia)/, 'kompensaciya', '✈️ Задержали или отменили рейс — проверьте, положена ли компенсация'],
  [/рейс|самол[её]т|аэропорт|авиа|лоукост|ryanair|vueling|iberia|wizz/, 'bilety', '✈️ Дешёвые авиабилеты из Испании'],
  [/поезд|железн|электрич|автобус|renfe|\bave\b/, 'avtobus', '🚌 Билеты на автобусы по Испании и Европе'],
  [/машин|авто|водител|дтп|\bdgt\b|прав[ао]? |бензин|трасс|itv|парков/, 'avto', '🚗 Аренда авто по Испании и Европе'],
  [/страхов|аренд|квартир|жиль|ипотек|хозяин|жилец|недвижим|окупас|комунидад/, 'strahovka', '🛡 Страховка квартиры, здоровья, жизни — напишите специалисту'],
  [/роуминг|мобильн|связь|интернет|сим-карт|\besim\b/, 'esim', '📲 Интернет в поездке без роуминга'],
  [/отпуск|турист|туризм|отел|путешеств|праздник|пасх|рождеств/, 'oteli', '🏨 Отели по всему миру'],
];
function svcLine(it) {
  const t = (it.title + ' ' + (it.desc || '')).toLowerCase();
  const m = SVC.find(([re]) => re.test(t));
  return m ? `<a href="${SITE}/go/${m[1]}">${m[2]}</a>` : '';
}
const SITE_LINE = `🇪🇸 <a href="${SITE}">Всё для жизни в Испании — kalmykovgroup.com</a>`;
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
  // 17.11.2026: v2 — фото сверху, под ним заголовок (Евгений 14:23). Переход на «богатые» сообщения с крупным заголовком — один раз перевыложить всё, что уже вышло
  if (!(await env.BOT_KV.get('rich:v5'))) {
    await env.BOT_KV.put('rich:v5', '1');
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
    const svc = svcLine(it);
    const foot = '\n\n' + (svc ? svc + '\n' : '') + SITE_LINE;
    let r;
    // 17.11.2026 (Евгений: «красивое название, как у Нестеренко»): rich-сообщение — крупный заголовок, фото, текст, ссылка
    const paras = [];
    let len = 0;
    for (const p of (it.paras || [])) { const t = p.join(' ').trim(); if (!t) continue; if ((len + t.length > 1000 || paras.length >= 4) && paras.length) break; paras.push(t); len += t.length; }
    // 17.11.2026 (Евгений выбрал вариант 1): фото 16:9 на всю ширину, крупный заголовок, пустая строка, текст
    let pic = it.img ? SITE + it.img : '';
    if (pic) { const wide = pic.replace('/novosti/img/', '/novosti/img-wide/'); if ((await fetch(wide, { method: 'HEAD' })).ok) pic = wide; }
    const html = (pic ? `<img src="${pic}"/>` : '') + `<h2>${rubric(it)} ${esc(it.title)}</h2><p>\u00a0</p>` +
      `<p>${paras.map(esc).join('<br/><br/>')}<br/><br/><b>${link}</b><br/><br/>${svc ? svc + '<br/>' : ''}${SITE_LINE}<br/>🔹 <a href="https://t.me/ispaniya_zakony">Подписаться на канал</a></p>`;
    r = await (await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendRichMessage`, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chat_id: env.NEWS_CHANNEL, rich_message: { html } }),
    })).json();
    if (!r.ok) posted.push('rich не вышел: ' + r.description);
    if (r.ok) {} else if (it.img) {
      const head = `<b>${esc(it.title)}</b>\n\n`;
      const caption = head + esc(short(it.paras || [], 1000 - head.length - 70 - foot.length)) + '\n\n' + link + foot;
      r = await (await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendPhoto`, {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chat_id: env.NEWS_CHANNEL, photo: SITE + it.img, caption, parse_mode: 'HTML' }),
      })).json();
    } else {
      const text = `<b>${esc(it.title)}</b>\n\n${esc(short(it.paras || []))}\n\n${link}${foot}`;
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
