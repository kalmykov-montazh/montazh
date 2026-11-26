// /go/<ключ> — «скачать без Telegram»: считаем и отдаём PDF.
const GUIDES = {
  chek:     { slug: 'chek-list-arenda' },
  chekua:   { slug: 'chek-list-arenda-ua' },
  shtrafy:  { slug: 'shtrafy-v-ispanii', title: 'Штрафы в Испании: 15 самых частых для приезжих', rent: false },
  vnzh:     { slug: 'vnzh-posle-vremennoy-zashchity', title: 'Временная защита → ВНЖ на 4 года', rent: false },
  lovushki: { slug: 'lovushki-arendy-v-ispanii', title: 'Аренда в Испании: 17 ловушек и мошенничеств', rent: true },
  otkazy:   { slug: 'pochemu-slozhno-snyat-kvartiru-v-ispanii', title: 'Как снять квартиру в Испании: 7 причин отказов', rent: true },
  klimat:   { slug: 'gde-zhit-v-ispanii-klimat-i-arenda', title: 'Где жить в Испании: климат и аренда по регионам', rent: true },
};
// 22.11.2026: короткие ссылки на услуги для постов и каналов — kalmykovgroup.com/go/<услуга>. Партнёра меняем здесь, старые посты не трогаем
const SERVICES = {
  avto: 'https://www.discovercars.com/?a_aid=kalmykovgroup',
  bilety: 'https://aviasales.tpk.ro/Y9TqwkLa?erid=2VtzqvviSsy',
  oteli: 'https://trip.tpk.ro/uSJdIAwK?erid=2Vtzqwjgr3R',
  esim: 'https://yesim.tpk.ro/PINKVK34?erid=2VtzqvYUdeo',
  kompensaciya: 'https://compensair.tpk.ro/lAi8i3Do?erid=2VtzqvygRSf',
  avtobus: 'https://unitiki.tpk.ro/AsxlAvk3?erid=2VtzqvWzeNT',
  transfer: 'https://kiwitaxi.tpk.ro/MxN3zjHJ?erid=2VtzqvZxcw9',
  ekskursii: 'https://tripster.tpk.ro/tejFlUxc?erid=2Vtzqw2eQ1M',
  bagazh: 'https://radicalstorage.tpk.ro/fQvALFGI?erid=2VtzqvuETbd',
  muzei: 'https://getyourguide.tpk.ro/uFPhTm0U?erid=2VtzqwNw26b',
  strahovka: 'https://kalmykovgroup.com/strahovka/',
  yuristy: 'https://kalmykovgroup.com/yuristy/',   // 26.11.2026: юристы-партнёры (Алина, ProSpain)
  poezdki: 'https://kalmykovgroup.com/poezdki/',
  // 22.11.2026: платные гайды — своя ссылка на каждый язык, счётчик переходов go:gaid-<язык> в KV.
  // Пока гайды не продаются (до автономо) — ведут на страницы «скоро». Со страницей оплаты — заменить адрес здесь;
  // в платёжке тоже держать отдельный товар/цену на каждый язык, чтобы продажи считались по языкам.
  'gaid-ru': 'https://kalmykovgroup.com/gaidy/',
  'gaid-ua': 'https://kalmykovgroup.com/gaidy/',
  'gaid-es': 'https://kalmykovgroup.com/es/guias/nacionalidad-espanola-2-anos-latinoamericanos',
  'gaid-en': 'https://kalmykovgroup.com/en/guides/',
};
const SITE = 'https://kalmykovgroup.com';
export async function onRequestGet({ params, env }) {
  if (SERVICES[params.key]) {
    if (env.BOT_KV) { const n = parseInt(await env.BOT_KV.get('go:' + params.key) || '0', 10) + 1; await env.BOT_KV.put('go:' + params.key, String(n)); }
    return Response.redirect(SERVICES[params.key], 302);
  }
  const g = GUIDES[params.key];
  if (!g) return Response.redirect('https://kalmykovgroup.com/gaidy/', 302);
  if (env.BOT_KV) { const n = parseInt(await env.BOT_KV.get('dl:' + params.key) || '0', 10) + 1; await env.BOT_KV.put('dl:' + params.key, String(n)); }
  return Response.redirect(`https://kalmykovgroup.com/gaidy/${g.slug}.pdf`, 302);
}
