# kalmykovgroup.com на хостинге NetX (с 22.11.2026)

Почему: во время матчей ЛаЛиги испанские провайдеры блокируют адреса Cloudflare, сайт у людей в Испании не открывался.

- Хостинг: NetX, тариф «Мастер» (тот же, что у обменки), сервер в Нидерландах, IP 31.42.189.93. Папка сайта: www/kalmykovgroup.com
- DNS в Cloudflare: A kalmykovgroup.com → 31.42.189.93 и CNAME www → kalmykovgroup.com, оба «DNS only» (серое облако). Почта (Email Routing) не тронута
- Сертификат Let's Encrypt выпускает и продлевает ISPManager (kalmykovgroup.com_le2)
- _sync.php — каждые 3 минуты (cron в ISPManager) забирает папку sait/ из GitHub (ветка main) и раскладывает на хостинг, генерирует .htaccess (короткие ссылки из sait/_redirects, .html без расширения, остальное → главная). Ручной запуск: https://kalmykovgroup.com/_sync.php?force=1
- _proxy.php — /go/, /p/, /tg/, /montazh/start передаёт на kalmykovgroup.pages.dev (функции, бот, счётчики в KV остаются на Cloudflare; сервер-сервер из Нидерландов не блокируется)
- _s.php — короткие ссылки из шапок (/ig, /fb…): пишет переход в _data/hits-ГГГГ-ММ.log и показывает главную (вместо счётчика Cloudflare)
- Откат на Cloudflare: в DNS вернуть CNAME kalmykovgroup.com → kalmykovgroup.pages.dev (проксирование включить) и в Pages → Custom domains нажать «Reactivate»
