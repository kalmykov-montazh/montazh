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
};

export async function nextNumber(env, key) {
  const p = PARTNERS[key];
  let n = 1;
  if (env.BOT_KV) { n = parseInt(await env.BOT_KV.get('lead:' + key) || '0', 10) + 1; await env.BOT_KV.put('lead:' + key, String(n)); }
  return p.prefix + '-' + n;
}

export async function logLead(key, num, channel, client, src) {
  const p = PARTNERS[key]; if (!p || !p.form) return;
  const b = new URLSearchParams();
  b.set('entry.' + p.e.num, num); b.set('entry.' + p.e.ch, channel); b.set('entry.' + p.e.topic, p.topic);
  b.set('entry.' + p.e.client, client || ''); b.set('entry.' + p.e.src, src || '');
  try { await fetch(`https://docs.google.com/forms/d/e/${p.form}/formResponse`, { method: 'POST', body: b }); } catch (e) {}
}

export function waText(key, num) {
  const p = PARTNERS[key];
  return `Здравствуйте, ${p.who}! Я от Kalmykov Group (kalmykovgroup.com), интересует ${p.topic}. Заявка ${num}`;
}
