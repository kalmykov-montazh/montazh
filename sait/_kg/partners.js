// Партнёры сайта: кнопки WhatsApp / Telegram → заявка с номером → строка в Google-таблицу партнёра (через Google-форму).
// Решение Евгения 22.11.2026 (план 15.11 и 20.11): человек сам попадает к специалисту одним нажатием, заявка записана за Kalmykov Group.
// Добавить партнёра = новая запись здесь + страница sait/<ключ>/index.html + Google-форма (поля Номер, Канал, Тема, Клиент, Откуда), связанная с таблицей партнёра.
export const PARTNERS = {
  strahovka: {
    prefix: 'СТР', who: 'Анна', topic: 'страхование',
    wa: '34695321898',                       // WhatsApp Анны (Ocaso)
    tg: 'https://t.me/+34695321898',         // Telegram Анны по номеру
    form: '1FAIpQLSeVLPgIln1kyJpIERR7NH7TIsKF0LGod8rjH-5-l6WhN6WjlQ', // таблица «Заявки — Страхование (Анна)»
    e: { num: '1324185143', ch: '1482698654', topic: '1744528285', client: '1273831132', src: '1373185980' },
  },
  yuristy: {
    prefix: 'ЮР', who: 'Алина', topic: 'юристы',
    start: 12,                               // ЮР-1…ЮР-11 переданы вручную до сайта (08.10–25.11), ЮР-12 — ручная передача 26.11; с сайта и бота — с ЮР-13
    wa: '34655749954',                       // рабочий WhatsApp Алины (ProSpain Consulting), дала 25.11.2026
    tg: 'https://t.me/+34655749954',         // Telegram по тому же номеру
    form: '1FAIpQLSdPyyyeAt_BfMmI7UjuDVwjWU4QUPRLzaP11EwRUl3ESOtZfw', // таблица «Заявки — Юристы (Алина, ProSpain)»
    e: { num: '1324185143', ch: '1482698654', topic: '1744528285', client: '1273831132', src: '1373185980' },
    wat: {
      ru: 'Здравствуйте, Алина! Я от Kalmykov Group (kalmykovgroup.com), хочу бесплатную консультацию юриста. Заявка {num}',
      ua: 'Добрий день, Аліно! Я від Kalmykov Group (kalmykovgroup.com), хочу безкоштовну консультацію юриста. Заявка {num}',
      en: 'Hello Alina! I found you via Kalmykov Group (kalmykovgroup.com) and would like a free legal consultation. Request {num}',
      es: '¡Hola, Alina! Vengo de Kalmykov Group (kalmykovgroup.com) y quiero una consulta gratuita con un abogado. Solicitud {num}',
    },
  },
};

export async function nextNumber(env, key) {
  const p = PARTNERS[key];
  let n = 1;
  if (env.BOT_KV) { n = Math.max(parseInt(await env.BOT_KV.get('lead:' + key) || '0', 10), p.start || 0) + 1; await env.BOT_KV.put('lead:' + key, String(n)); }
  return p.prefix + '-' + n;
}

export async function logLead(key, num, channel, client, src) {
  const p = PARTNERS[key]; if (!p || !p.form) return;
  const b = new URLSearchParams();
  b.set('entry.' + p.e.num, num); b.set('entry.' + p.e.ch, channel); b.set('entry.' + p.e.topic, p.topic);
  b.set('entry.' + p.e.client, client || ''); b.set('entry.' + p.e.src, src || '');
  try { await fetch(`https://docs.google.com/forms/d/e/${p.form}/formResponse`, { method: 'POST', body: b }); } catch (e) {}
}

export function waText(key, num, lang) {
  const p = PARTNERS[key];
  if (p.wat) return (p.wat[lang] || p.wat.ru).replace('{num}', num);
  return `Здравствуйте, ${p.who}! Я от Kalmykov Group (kalmykovgroup.com), интересует ${p.topic}. Заявка ${num}`;
}
