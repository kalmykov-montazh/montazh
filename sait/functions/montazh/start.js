// /montazh/start — считаем переходы в бота Accio и отдаём партнёрскую ссылку (20.11.2026)
// Счётчик: BOT_KV, ключ dl:montazh (как у гайдов в /go/)
const BOT = 'https://t.me/accio_pro_bot?start=seed_ac_nova';
export async function onRequestGet({ env }) {
  if (env.BOT_KV) {
    const n = parseInt(await env.BOT_KV.get('dl:montazh') || '0', 10) + 1;
    await env.BOT_KV.put('dl:montazh', String(n));
  }
  return Response.redirect(BOT, 302);
}
