// /go/<ключ> — «скачать без Telegram»: считаем и отдаём PDF.
const GUIDES = {
  shtrafy:  { slug: 'shtrafy-v-ispanii', title: 'Штрафы в Испании: 15 самых частых для приезжих', rent: false },
  vnzh:     { slug: 'vnzh-posle-vremennoy-zashchity', title: 'Временная защита → ВНЖ на 4 года', rent: false },
  lovushki: { slug: 'lovushki-arendy-v-ispanii', title: 'Аренда в Испании: 17 ловушек и мошенничеств', rent: true },
  otkazy:   { slug: 'pochemu-slozhno-snyat-kvartiru-v-ispanii', title: 'Как снять квартиру в Испании: 7 причин отказов', rent: true },
  klimat:   { slug: 'gde-zhit-v-ispanii-klimat-i-arenda', title: 'Где жить в Испании: климат и аренда по регионам', rent: true },
};
const SITE = 'https://kalmykovgroup.com';
export async function onRequestGet({ params, env }) {
  const g = GUIDES[params.key];
  if (!g) return Response.redirect('https://kalmykovgroup.com/gaidy/', 302);
  if (env.BOT_KV) { const n = parseInt(await env.BOT_KV.get('dl:' + params.key) || '0', 10) + 1; await env.BOT_KV.put('dl:' + params.key, String(n)); }
  return Response.redirect(`https://kalmykovgroup.com/gaidy/${g.slug}.pdf`, 302);
}
