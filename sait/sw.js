// Значок сайта на телефоне (22.11.2026). Страницы — сначала из сети, без сети — сохранённая копия.
// Короткие ссылки /go/, заявки /p/, бот /tg/ не трогаем, чтобы считались все переходы
const C = 'kg-v1';
self.addEventListener('install', e => { self.skipWaiting(); e.waitUntil(caches.open(C).then(c => c.addAll(['/', '/poezdki/', '/novosti/'])).catch(() => {})); });
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(k => Promise.all(k.filter(n => n !== C).map(n => caches.delete(n)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET' || r.mode !== 'navigate') return;
  const u = new URL(r.url);
  if (u.origin !== location.origin || /^\/(go|p|tg|montazh|_)/.test(u.pathname)) return;
  e.respondWith(fetch(r).then(res => { if (res.ok) { const cp = res.clone(); caches.open(C).then(c => c.put(r, cp)); } return res; })
    .catch(() => caches.match(r).then(m => m || caches.match('/'))));
});
