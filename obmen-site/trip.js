// 22.11.2026 19:30: 6 головних (автобуси, eSIM, авіа, готелі, компенсація, авто) + кнопка «Усі сервіси» на /poyizdky + плашка eSIM до 30.11
// Блок «Подорожі дешевше» під таблицею курсів (22.11.2026; 22.11 13:05 +готелі, автобуси, екскурсії, компенсація). Партнерські посилання Travelpayouts з міткою obmen
(function(){
  var ru = /^\/ru(\/|$)/.test(location.pathname) || document.documentElement.lang === 'ru';
  var U = 'https://images.unsplash.com/photo-';
  var L = [
    ['unitiki','https://unitiki.tpk.ro/eDyJhUFe?erid=2VtzqvWzeNT','1570125909232-eb263c188f7e','Автобуси за кордон','Автобусы за границу','Квитки на міжнародні автобуси','Билеты на международные автобусы'],
    ['airalo','https://airalo.tpk.ro/hpwIoKAX?erid=2VtzqveQanB','1512941937669-90a1b58e7e9c','eSIM без роумінгу','eSIM без роуминга','Інтернет у Польщі та по Європі','Интернет в Польше и по Европе'],
    ['aviasales','https://aviasales.tpk.ro/kqcuiFhL?erid=2VtzqvviSsy','1436491865332-7a61a109cc05','Дешеві авіаквитки','Дешёвые авиабилеты','З Варшави, Кракова, Кишинева','Из Варшавы, Кракова, Кишинёва'],
    ['trip','https://trip.tpk.ro/1DeF1SSj?erid=2Vtzqwjgr3R','1566073771259-6a8506099945','Готелі та житло','Отели и жильё','Trip.com — по всьому світу','Trip.com — по всему миру'],
    ['compensair','https://compensair.tpk.ro/iHQIiKbQ?erid=2VtzqvygRSf','1530521954074-e64f6810b32d','Затримали рейс','Задержали рейс','Компенсація за правилами ЄС','Компенсация по правилам ЕС'],
    ['discovercars','https://www.discovercars.com/?a_aid=kalmykovgroup','1449965408869-eaa3f722e40d','Оренда авто в Європі','Аренда авто в Европе','Сотні прокатів в одному пошуку','Сотни прокатов в одном поиске']
  ];
  var css = '.og-trip{margin:16px 0 18px;padding:20px 18px 14px;border-radius:20px;background:linear-gradient(180deg,#fffaf0,#f6ecd6);border:2px solid #d4af37;box-shadow:0 0 0 4px rgba(212,175,55,.15),0 10px 30px rgba(0,0,0,.35);color:#1c2333;box-sizing:border-box;position:relative}'
   + '.og-trip .hd{display:flex;align-items:center;gap:12px;margin-bottom:14px}.og-trip .ic{flex:none;width:44px;height:44px;border-radius:12px;background:#121a2a;display:grid;place-items:center}.og-trip .ic svg{width:24px;height:24px;fill:#e9c766}'
   + '.og-trip h2{margin:0;font-size:24px;line-height:1.15;color:#121a2a;font-weight:800}.og-trip p.s{margin:2px 0 0;font-size:13.5px;color:#5a5140}'
   + '.og-trip .new{flex:none;margin-left:auto;align-self:flex-start;background:#d4af37;color:#121a2a;font-size:11px;font-weight:800;letter-spacing:.06em;padding:4px 9px;border-radius:999px}'
   + '.og-trip .g{display:grid;grid-template-columns:repeat(6,1fr);gap:14px}'
   + '.og-trip a{display:flex;flex-direction:column;background:#eef0f4;border-radius:16px;overflow:hidden;text-decoration:none;color:#16233a;box-shadow:0 4px 14px rgba(18,26,42,.25);border:3px solid #121a2a;transition:transform .15s,box-shadow .15s}'
   + '.og-trip a:hover{transform:translateY(-4px);box-shadow:0 10px 24px rgba(18,26,42,.2)}'
   + '.og-trip i{display:block;height:130px;border-bottom:3px solid #121a2a;background:#121a2a center/cover no-repeat}.og-trip b{padding:10px 12px 0;font-size:16px;line-height:1.2;color:#121a2a}'
   + '.og-trip a span{padding:3px 12px 0;font-size:12px;color:#6b6250;line-height:1.3;flex:1}.og-trip em{font-style:normal;padding:8px 12px 12px;font-size:12.5px;font-weight:800;color:#b8901f}'
   + '.og-trip .all{display:block;width:max-content;max-width:100%;margin:14px auto 0;padding:10px 22px;border-radius:14px;background:linear-gradient(135deg,#ffab40,#f57c00,#e65100);color:#fff!important;font-weight:900;font-size:15px;text-decoration:none;border:2px solid #d4af37;outline:3px solid #121a2a;flex-direction:row!important;box-shadow:none!important;overflow:visible!important}'
   + '.og-esim{position:fixed;right:12px;top:84px;z-index:60;display:flex;align-items:center;gap:8px;background:#121a2a;color:#fff;border:2px solid #d4af37;border-radius:999px;padding:6px 8px 6px 12px;font:700 13.5px/1.2 system-ui,sans-serif;text-decoration:none;box-shadow:0 6px 18px rgba(0,0,0,.4);animation:ogEs 2.4s ease-in-out infinite}'
   + '.og-esim b{color:#ffd54a}.og-esim button{background:none;border:0;color:#aab;font-size:16px;cursor:pointer;padding:0 4px}@keyframes ogEs{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}'
   + '@media(max-width:600px){.og-esim{top:auto;bottom:78px;right:8px;font-size:12.5px}}'
   + '.og-trip small{display:block;margin-top:12px;font-size:10.5px;color:#8a8170}'
   + '@media(max-width:1000px){.og-trip .g{grid-template-columns:repeat(3,1fr)}}'
   + '@media(max-width:600px){.og-trip{padding:14px 10px 10px}.og-trip h2{font-size:18px}.og-trip .ic{width:38px;height:38px}.og-trip .g{grid-template-columns:repeat(2,1fr);gap:8px}.og-trip i{height:78px}.og-trip b{font-size:13.5px;padding:8px 9px 0}.og-trip a span{font-size:11px;padding:2px 9px 0}.og-trip em{padding:6px 9px 9px;font-size:11.5px}}';
  function run(){
    var hero = document.getElementById('share-btn') || document.querySelector('.rate-note') || document.querySelector('.rates-hero'); if(!hero || document.querySelector('.og-trip')) return;
    var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    var PL='<svg viewBox="0 0 24 24"><path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5z"/></svg>';
    var h = '<div class="hd"><div><h2>' + (ru ? 'Путешествия дешевле' : 'Подорожі дешевше') + '</h2><p class="s">' + (ru ? 'Билеты, отели, интернет, авто и трансфер для поездки за границу' : 'Квитки, готелі, інтернет, авто й трансфер для поїздки за кордон') + '</p></div><span class="new">' + (ru ? 'НОВОЕ' : 'НОВЕ') + '</span></div><div class="g">';
    L.forEach(function(x){ h += '<a href="'+x[1]+'" target="_blank" rel="sponsored noopener" data-trip="'+x[0]+'"><i style="background-image:url('+U+x[2]+'?auto=format&fit=crop&w=400&h=220&q=70)"></i><b>'+(ru?x[4]:x[3])+'</b><span>'+(ru?x[6]:x[5])+'</span><em>'+(ru?'Смотреть →':'Дивитись →')+'</em></a>'; });
    h += '</div><a class="all" href="' + (ru ? '/ru/poyizdky' : '/poyizdky') + '">' + (ru ? 'Все сервисы для поездки →' : 'Усі сервіси для поїздки →') + '</a><small>' + (ru ? 'Реклама. Партнёрские ссылки — для вас цена как на сайте сервиса' : 'Реклама. Партнерські посилання — для вас ціна як на сайті сервісу') + '</small>';
    var s = document.createElement('section'); s.className = 'og-trip'; s.setAttribute('data-noi18n','1'); s.innerHTML = h;
    hero.parentNode.insertBefore(s, hero.nextSibling);
    try{ if(new Date() < new Date('2026-12-01T00:00:00+02:00') && !localStorage.getItem('ogEsimX')){
      var p = document.createElement('a'); p.className='og-esim'; p.href='https://airalo.tpk.ro/hpwIoKAX?erid=2VtzqveQanB'; p.target='_blank'; p.rel='sponsored noopener'; p.setAttribute('data-noi18n','1');
      p.innerHTML = '📶 eSIM <b>−25%</b> ' + (ru ? 'промокод BLACK25' : 'промокод BLACK25') + '<button aria-label="x">×</button>';
      p.querySelector('button').onclick = function(e){ e.preventDefault(); e.stopPropagation(); p.remove(); try{localStorage.setItem('ogEsimX','1')}catch(_){} };
      p.addEventListener('click', function(){ if(window.ogTrack) window.ogTrack('trip-esim-pill'); });
      setTimeout(function(){ document.body.appendChild(p); }, 4000);
    } }catch(_){}
    s.addEventListener('click', function(e){ var a = e.target.closest('a[data-trip]'); if(a && window.ogTrack) window.ogTrack('trip-' + a.dataset.trip); });
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
})();
