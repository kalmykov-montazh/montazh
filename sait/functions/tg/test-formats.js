// 17.11.2026: одноразовая проверка трёх оформлений новости — шлёт в личку админу бота (Евгению), не в канал
const SITE = 'https://kalmykovgroup.com';
const SLUG = '2026-11-17-zheleznaya-doroga-bastuet-do-polunochi-vot-chto-segodnya-hod';
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
export async function onRequestGet({ env }) {
  if (await env.BOT_KV.get('testfmt:v1')) return new Response('уже отправлено');
  const admin = await env.BOT_KV.get('admin');
  if (!admin) return new Response('нет админа');
  await env.BOT_KV.put('testfmt:v1', '1', { expirationTtl: 86400 });
  const data = await (await fetch(`${SITE}/novosti/_data.json`)).json();
  const it = Object.values(data).find(x => x.slug === SLUG);
  const tg = async (m, b) => (await (await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/${m}`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ chat_id: admin, ...b }) })).json());
  const paras = (it.paras || []).map(p => p.join(' ').trim()).filter(Boolean).slice(0, 3);
  const url = `${SITE}/novosti/${SLUG}`;
  const link = `<a href="${url}">Подробно, что делать и источники — на сайте</a>`;
  const body = `<p>${paras.map(esc).join('<br/><br/>')}<br/><br/><b>${link}</b></p>`;
  const out = [];
  out.push(await tg('sendMessage', { text: '⬇️ ВАРИАНТ 1: фото на всю ширину, под ним крупный заголовок' }));
  out.push(await tg('sendRichMessage', { rich_message: { html: `<img src="${SITE}/tg-test/wide.jpg"/><h2>${esc(it.title)}</h2>` + body } }));
  out.push(await tg('sendMessage', { text: '⬇️ ВАРИАНТ 2: как было раньше — фото и подпись, заголовок жирным' }));
  const head = `<b>${esc(it.title)}</b>\n\n`;
  out.push(await tg('sendPhoto', { photo: SITE + it.img, parse_mode: 'HTML', caption: head + esc(paras.join('\n\n')).slice(0, 1000 - head.length - 80) + '\n\n' + link }));
  out.push(await tg('sendMessage', { text: '⬇️ ВАРИАНТ 3: без фото, только крупный заголовок' }));
  out.push(await tg('sendRichMessage', { rich_message: { html: `<h2>${esc(it.title)}</h2>` + body } }));
  return new Response(JSON.stringify(out.map(r => r.ok || r.description)), { headers: { 'content-type': 'application/json; charset=utf-8' } });
}
