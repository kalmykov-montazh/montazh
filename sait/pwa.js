// Значок Kalmykov Group на телефоне (22.11.2026): регистрируем sw.js и со 2-го визита мягко предлагаем поставить значок
(function () {
  // Пометка «Реклама…» от Travelpayouts — мелко и аккуратно, над нижними кнопками
  try { var st = document.createElement('style'); st.textContent = '.tp-advertiser-info{font:11px/1.45 system-ui,sans-serif!important;color:#8b8f94!important;opacity:.75;text-align:center;max-width:760px;margin:0 auto!important;padding:10px 16px 96px!important}.tp-advertiser-info div{font-size:11px!important}'; document.head.appendChild(st); } catch (e) {}
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(function () {});
  var standalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone;
  if (standalone) return;
  var ls = {}; try { ls = window.localStorage; } catch (e) {}
  function get(k) { try { return ls.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { ls.setItem(k, v); } catch (e) {} }
  var n = (+get('kg_visits') || 0) + 1; set('kg_visits', n);
  var off = +get('kg_pwa_off') || 0;
  if (n < 2 || Date.now() - off < 14 * 864e5) return;
  var ua = navigator.userAgent || '';
  var inApp = /FBAN|FBAV|Instagram|Line\/|TikTok|Telegram/i.test(ua);
  var ios = /iPhone|iPad|iPod/.test(ua) && /Safari/.test(ua) && !/CriOS|FxiOS|EdgiOS/.test(ua) && !inApp;
  var deferred = null;
  function show(text, btn) {
    if (document.getElementById('kg-pwa')) return;
    var d = document.createElement('div'); d.id = 'kg-pwa';
    d.style.cssText = 'position:fixed;left:12px;right:12px;bottom:12px;z-index:9999;max-width:520px;margin:0 auto;background:#0a0a0d;color:#fff;border:2px solid #C9A24B;border-radius:14px;padding:12px 14px;font:15px/1.4 system-ui,sans-serif;box-shadow:0 6px 24px rgba(0,0,0,.35);display:flex;gap:10px;align-items:center';
    d.innerHTML = '<img src="/icon-192.png" alt="" width="40" height="40" style="border-radius:9px;flex:none"><div style="flex:1">' + text + '</div>' +
      (btn ? '<button id="kg-pwa-ok" style="flex:none;background:#C9A24B;color:#0a0a0d;border:0;border-radius:10px;padding:9px 12px;font-weight:700;font-size:14px">' + btn + '</button>' : '') +
      '<button id="kg-pwa-x" aria-label="Закрыть" style="flex:none;background:none;border:0;color:#aaa;font-size:22px;line-height:1;padding:4px">×</button>';
    document.body.appendChild(d);
    document.getElementById('kg-pwa-x').onclick = function () { set('kg_pwa_off', Date.now()); d.remove(); };
    var ok = document.getElementById('kg-pwa-ok');
    if (ok) ok.onclick = function () { if (deferred) { deferred.prompt(); deferred.userChoice.then(function () { d.remove(); set('kg_pwa_off', Date.now()); }); } };
  }
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault(); deferred = e;
    setTimeout(function () { show('<b>Kalmykov Group на телефоне</b><br>Билеты, отели, авто и новости Испании — в один клик', 'Поставить'); }, 8000);
  });
  if (ios) setTimeout(function () { show('<b>Добавьте значок на экран</b><br>Нажмите «Поделиться» внизу, затем «На экран «Домой»»', ''); }, 8000);
})();
