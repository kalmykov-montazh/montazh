// Блок «Подорожі дешевше» під таблицею курсів (22.11.2026). Партнерські посилання Travelpayouts з міткою obmen
(function(){
  var ru = /^\/ru(\/|$)/.test(location.pathname) || document.documentElement.lang === 'ru';
  var U = 'https://images.unsplash.com/photo-';
  var L = [
    ['aviasales','https://aviasales.tpk.ro/kqcuiFhL?erid=2VtzqvviSsy','1436491865332-7a61a109cc05','Дешеві авіаквитки','Дешёвые авиабилеты','Усі авіакомпанії, календар цін','Все авиакомпании, календарь цен'],
    ['yesim','https://yesim.tpk.ro/zUjs2mVk?erid=2VtzqvYUdeo','1512941937669-90a1b58e7e9c','eSIM-інтернет','eSIM-интернет','Без роумінгу у 200 країнах','Без роуминга в 200 странах'],
    ['airalo','https://airalo.tpk.ro/hpwIoKAX?erid=2VtzqveQanB','1565967511849-76a60a516170','eSIM Airalo','eSIM Airalo','Пакети на тиждень чи місяць','Пакеты на неделю или месяц'],
    ['economybookings','https://economybookings.tpk.ro/73XZkSEj','1449965408869-eaa3f722e40d','Оренда авто','Аренда авто','Порівняння всіх прокатів','Сравнение всех прокатов'],
    ['kiwitaxi','https://kiwitaxi.tpk.ro/R6gWTNIb?erid=2VtzqvZxcw9','1556122071-e404eaedb77f','Трансфер з аеропорту','Трансфер из аэропорта','Фіксована ціна, з табличкою','Фиксированная цена, с табличкой'],
    ['tiqets','https://tiqets.tpk.ro/a8zFSilw?erid=2VtzqvcvbVq','1511527661048-7fe73d85e9a4','Музеї та екскурсії','Музеи и экскурсии','Квитки без черги','Билеты без очереди'],
    ['radical','https://radicalstorage.tpk.ro/GETely1E?erid=2VtzqvuETbd','1530521954074-e64f6810b32d','Камера схову','Камера хранения','Залишити валізу в місті','Оставить чемодан в городе']
  ];
  var css = '.og-trip{margin:16px 0 18px;padding:20px 18px 14px;border-radius:20px;background:linear-gradient(180deg,#fffaf0,#f6ecd6);border:2px solid #d4af37;box-shadow:0 0 0 4px rgba(212,175,55,.15),0 10px 30px rgba(0,0,0,.35);color:#1c2333;box-sizing:border-box;position:relative}'
   + '.og-trip .hd{display:flex;align-items:center;gap:12px;margin-bottom:14px}.og-trip .ic{flex:none;width:44px;height:44px;border-radius:12px;background:#121a2a;display:grid;place-items:center}.og-trip .ic svg{width:24px;height:24px;fill:#e9c766}'
   + '.og-trip h2{margin:0;font-size:22px;line-height:1.15;color:#121a2a;font-weight:800}.og-trip p.s{margin:2px 0 0;font-size:13.5px;color:#5a5140}'
   + '.og-trip .new{margin-left:auto;align-self:flex-start;background:#d4af37;color:#121a2a;font-size:11px;font-weight:800;letter-spacing:.06em;padding:4px 9px;border-radius:999px}'
   + '.og-trip .g{display:grid;grid-template-columns:repeat(7,1fr);gap:12px}'
   + '.og-trip a{display:flex;flex-direction:column;background:#fff;border-radius:16px;overflow:hidden;text-decoration:none;color:#16233a;box-shadow:0 2px 10px rgba(18,26,42,.12);border:1px solid #eadfc4;transition:transform .15s,box-shadow .15s}'
   + '.og-trip a:hover{transform:translateY(-4px);box-shadow:0 10px 24px rgba(18,26,42,.2)}'
   + '.og-trip i{display:block;height:104px;background:#121a2a center/cover no-repeat}.og-trip b{padding:10px 12px 0;font-size:15px;line-height:1.2;color:#121a2a}'
   + '.og-trip span{padding:3px 12px 0;font-size:12px;color:#6b6250;line-height:1.3;flex:1}.og-trip em{font-style:normal;padding:8px 12px 12px;font-size:12.5px;font-weight:800;color:#b8901f}'
   + '.og-trip small{display:block;margin-top:12px;font-size:10.5px;color:#8a8170}'
   + '@media(max-width:1000px){.og-trip .g{grid-template-columns:repeat(4,1fr)}}'
   + '@media(max-width:600px){.og-trip{padding:14px 10px 10px}.og-trip h2{font-size:18px}.og-trip .ic{width:38px;height:38px}.og-trip .g{grid-template-columns:repeat(2,1fr);gap:8px}.og-trip i{height:78px}.og-trip b{font-size:13.5px;padding:8px 9px 0}.og-trip span{font-size:11px;padding:2px 9px 0}.og-trip em{padding:6px 9px 9px;font-size:11.5px}}';
  function run(){
    var hero = document.getElementById('share-btn') || document.querySelector('.rate-note') || document.querySelector('.rates-hero'); if(!hero || document.querySelector('.og-trip')) return;
    var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    var PL='<svg viewBox="0 0 24 24"><path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5z"/></svg>';
    var h = '<div class="hd"><div class="ic">'+PL+'</div><div><h2>' + (ru ? 'Путешествия дешевле' : 'Подорожі дешевше') + '</h2><p class="s">' + (ru ? 'Билеты, интернет, авто и трансфер для поездки за границу' : 'Квитки, інтернет, авто й трансфер для поїздки за кордон') + '</p></div><span class="new">' + (ru ? 'НОВОЕ' : 'НОВЕ') + '</span></div><div class="g">';
    L.forEach(function(x){ h += '<a href="'+x[1]+'" target="_blank" rel="sponsored noopener" data-trip="'+x[0]+'"><i style="background-image:url('+U+x[2]+'?auto=format&fit=crop&w=400&h=220&q=70)"></i><b>'+(ru?x[4]:x[3])+'</b><span>'+(ru?x[6]:x[5])+'</span><em>'+(ru?'Смотреть →':'Дивитись →')+'</em></a>'; });
    h += '</div><small>' + (ru ? 'Реклама. Партнёрские ссылки — для вас цена как на сайте сервиса' : 'Реклама. Партнерські посилання — для вас ціна як на сайті сервісу') + '</small>';
    var s = document.createElement('section'); s.className = 'og-trip'; s.setAttribute('data-noi18n','1'); s.innerHTML = h;
    hero.parentNode.insertBefore(s, hero.nextSibling);
    s.addEventListener('click', function(e){ var a = e.target.closest('a[data-trip]'); if(a && window.ogTrack) window.ogTrack('trip-' + a.dataset.trip); });
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
})();
