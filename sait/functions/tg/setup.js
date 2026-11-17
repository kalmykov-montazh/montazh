// Разово: открыть https://kalmykovgroup.com/tg/setup — подключает бота к сайту (вебхук).
async function hookSecret(env) {
  const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('kalmykov-bot:' + env.TG_TOKEN));
  return [...new Uint8Array(h)].map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 40);
}

export async function onRequestGet({ env }) {
  if (!env.TG_TOKEN) return new Response('Нет TG_TOKEN в настройках Cloudflare', { status: 500 });
  const r = await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/setWebhook`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ url: 'https://kalmykovgroup.com/tg/webhook', secret_token: await hookSecret(env), allowed_updates: ['message', 'callback_query'] }),
  });
  const me = await (await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/getMe`)).json();
  const j = await r.json();
  return new Response(JSON.stringify({ webhook: j.ok, bot: me.result && me.result.username, kv: !!env.BOT_KV }), { headers: { 'content-type': 'application/json; charset=utf-8' } });
}
