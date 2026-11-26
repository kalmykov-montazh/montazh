// 26.11.2026 (решение Евгения): перед WhatsApp к партнёру — окошко «имя и фамилия + телефон».
// Данные уходят POST-ом на /p/<партнёр>-wa, пишутся в таблицу партнёра, потом открывается WhatsApp с текстом заявки.
// Подключается на страницах с кнопками /p/<ключ>-wa (tools/waform.py). Без JS кнопка работает как раньше.
(function () {
  var T = {
    ru: { h: 'Чтобы специалист точно вам ответил', n: 'Имя и фамилия', p: 'Телефон (WhatsApp)', b: 'Продолжить в WhatsApp', c: 'Нажимая кнопку, вы соглашаетесь передать имя и телефон специалисту', e: 'Введите имя и телефон', x: 'Закрыть', w: 'Открываю WhatsApp…' },
    ua: { h: 'Щоб фахівець точно вам відповів', n: 'Ім’я та прізвище', p: 'Телефон (WhatsApp)', b: 'Продовжити у WhatsApp', c: 'Натискаючи кнопку, ви погоджуєтеся передати ім’я та телефон фахівцю', e: 'Введіть ім’я та телефон', x: 'Закрити', w: 'Відкриваю WhatsApp…' },
    en: { h: 'So the specialist can reply to you', n: 'First and last name', p: 'Phone (WhatsApp)', b: 'Continue to WhatsApp', c: 'By tapping the button you agree to share your name and phone with the specialist', e: 'Please enter your name and phone', x: 'Close', w: 'Opening WhatsApp…' },
    es: { h: 'Para que el especialista te responda', n: 'Nombre y apellido', p: 'Teléfono (WhatsApp)', b: 'Continuar en WhatsApp', c: 'Al pulsar el botón aceptas compartir tu nombre y teléfono con el especialista', e: 'Escribe tu nombre y teléfono', x: 'Cerrar', w: 'Abriendo WhatsApp…' }
  };
  function lsGet(k) { try { return localStorage.getItem(k) || ''; } catch (e) { return ''; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  var css = '.wf-bg{position:fixed;inset:0;background:rgba(10,20,40,.55);z-index:99999;display:flex;align-items:center;justify-content:center;padding:16px}' +
    '.wf{background:#fff;color:#16294A;border-radius:16px;max-width:380px;width:100%;padding:22px 20px 18px;box-shadow:0 12px 40px rgba(0,0,0,.3);font:16px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;position:relative}' +
    '.wf h3{margin:0 28px 14px 0;font-size:19px;line-height:1.3}.wf label{display:block;font-size:14px;margin:10px 0 4px;color:#334}' +
    '.wf input{width:100%;box-sizing:border-box;padding:12px;border:1.5px solid #c9d1de;border-radius:10px;font-size:17px;color:#16294A;background:#fff}.wf input:focus{outline:none;border-color:#25D366}' +
    '.wf button.go{margin-top:16px;width:100%;padding:14px;border:0;border-radius:12px;background:#25D366;color:#fff;font-size:17px;font-weight:700;cursor:pointer}.wf button.go[disabled]{opacity:.6}' +
    '.wf .cx{position:absolute;top:10px;right:12px;border:0;background:none;font-size:26px;line-height:1;color:#889;cursor:pointer}' +
    '.wf .er{color:#c0392b;font-size:14px;min-height:18px;margin-top:8px}.wf .cs{font-size:12px;color:#778;margin-top:10px}';
  function langOf(a) {
    var m = /[?&]lang=([a-z]{2})/.exec(a.getAttribute('href') || '');
    if (m && T[m[1]]) return m[1];
    var l = (document.documentElement.lang || 'ru').slice(0, 2);
    return l === 'uk' ? 'ua' : (T[l] ? l : 'ru');
  }
  function open(a) {
    var href = a.getAttribute('href'), u = new URL(href, location.href), t = T[langOf(a)];
    var lang = u.searchParams.get('lang') || langOf(a), src = u.searchParams.get('src') || 'site';
    if (!document.getElementById('wf-css')) { var st = document.createElement('style'); st.id = 'wf-css'; st.textContent = css; document.head.appendChild(st); }
    var bg = document.createElement('div'); bg.className = 'wf-bg';
    bg.innerHTML = '<form class="wf" novalidate><button type="button" class="cx" aria-label="' + t.x + '">×</button><h3>' + t.h + '</h3>' +
      '<label>' + t.n + '</label><input name="n" autocomplete="name" required>' +
      '<label>' + t.p + '</label><input name="p" type="tel" inputmode="tel" autocomplete="tel" placeholder="+34 …" required>' +
      '<div class="er"></div><button class="go" type="submit">' + t.b + '</button><div class="cs">' + t.c + '</div></form>';
    document.body.appendChild(bg);
    var f = bg.querySelector('form'), n = f.elements.n, p = f.elements.p, er = f.querySelector('.er'), go = f.querySelector('.go');
    n.value = lsGet('wf_n'); p.value = lsGet('wf_p');
    function close() { bg.remove(); }
    f.querySelector('.cx').onclick = close;
    bg.addEventListener('click', function (e) { if (e.target === bg) close(); });
    setTimeout(function () { (n.value ? p : n).focus(); }, 50);
    f.onsubmit = function (e) {
      e.preventDefault();
      var nv = n.value.trim(), pv = p.value.trim();
      if (nv.length < 2 || pv.replace(/\D/g, '').length < 7) { er.textContent = t.e; return; }
      lsSet('wf_n', nv); lsSet('wf_p', pv);
      go.disabled = true; go.textContent = t.w;
      fetch(u.pathname, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name: nv, phone: pv, src: src, lang: lang }) })
        .then(function (r) { return r.json(); })
        .then(function (d) { if (d && d.url) location.href = d.url; else location.href = href; })
        .catch(function () { location.href = href; });
    };
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href*="/p/"]');
    if (!a || !/\/p\/[a-z]+-wa(\?|$)/.test(a.getAttribute('href') || '')) return;
    e.preventDefault(); open(a);
  }, true);
})();
