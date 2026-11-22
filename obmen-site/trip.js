// Блок «Подорожі дешевше» під таблицею курсів (22.11.2026). Партнерські посилання Travelpayouts з міткою obmen
(function(){
  var ru = /^\/ru(\/|$)/.test(location.pathname) || document.documentElement.lang === 'ru';
  var U = 'https://images.unsplash.com/photo-';
  var L = [
    ['aviasales','https://aviasales.tpk.ro/kqcuiFhL?erid=2VtzqvviSsy','1436491865332-7a61a109cc05','Дешеві авіаквитки','Дешёвые авиабилеты','Усі авіакомпанії, календар цін','Все авиакомпании, календарь цен'],
    ['yesim','https://yesim.tpk.ro/zUjs2mVk?erid=2VtzqvYUdeo','1512941937669-90a1b58e7e9c','eSIM-інтернет','eSIM-интернет','Без роумінгу у 200 країнах','Без роуминга в 200 странах'],
    ['airalo','https://airalo.tpk.ro/hpwIoKAX?erid=2VtzqveQanB','1565967511849-76a60a516170','eSIM Airalo','eSIM Airalo','Пакети на тиждень чи місяць','Пакеты на неделю или месяц'],
    ['economybookings','https://economybookings.tpk.ro/73XZkSEj','1449965408869-eaa3f722e40d','Оренда авто','Аренда авто','Порівняння прокатів Європи','Сравнение прокатов Европы'],
    ['qeeq','https://qeeq.tpk.ro/uLxHwRnG?erid=2VtzqvpnVkb','1525609004556-c46c7d6cf023','Авто на довгий термін','Авто на долгий срок','Вигідніше на місяць і більше','Выгоднее на месяц и больше'],
    ['kiwitaxi','https://kiwitaxi.tpk.ro/R6gWTNIb?erid=2VtzqvZxcw9','1556122071-e404eaedb77f','Трансфер з аеропорту','Трансфер из аэропорта','Фіксована ціна, з табличкою','Фиксированная цена, с табличкой'],
    ['welcome','https://tpk.ro/aOxEJWVl?erid=2VtzqvbScDV','1494515843206-f3117d3f51b7','Зустріч в аеропорту','Встреча в аэропорту','Водій чекає навіть при затримці','Водитель ждёт даже при задержке'],
    ['tiqets','https://tiqets.tpk.ro/a8zFSilw?erid=2VtzqvcvbVq','1511527661048-7fe73d85e9a4','Музеї та екскурсії','Музеи и экскурсии','Квитки без черги','Билеты без очереди'],
    ['radical','https://radicalstorage.tpk.ro/GETely1E?erid=2VtzqvuETbd','1530521954074-e64f6810b32d','Камера схову','Камера хранения','Залишити валізу в місті','Оставить чемодан в городе']
  ];
  var css = '.og-trip{max-width:100%;margin:14px 0 16px;padding:18px 16px 12px;border-radius:20px;background:linear-gradient(135deg,#1b2740,#121a2a);border:1px solid rgba(212,175,55,.45);box-shadow:0 8px 26px rgba(0,0,0,.25);color:#f3ead2;box-sizing:border-box}'
   + '.og-trip h2{margin:0 0 4px;font-size:21px;color:#e9c766;font-weight:800}.og-trip p.s{margin:0 0 12px;font-size:13.5px;opacity:.8}'
   + '.og-trip .g{display:grid;grid-template-columns:repeat(9,1fr);gap:8px}'
   + '.og-trip a{display:flex;flex-direction:column;background:#fff;border-radius:14px;overflow:hidden;text-decoration:none;color:#16233a;transition:transform .15s}.og-trip a:hover{transform:translateY(-3px)}'
   + '.og-trip i{display:block;height:70px;background:#121a2a center/cover no-repeat}.og-trip b{padding:7px 8px 0;font-size:13px;line-height:1.2;color:#16294a}.og-trip span{padding:2px 8px 9px;font-size:11px;color:#5f6b7a;line-height:1.25}'
   + '.og-trip small{display:block;margin-top:10px;font-size:10.5px;opacity:.55}'
   + '@media(max-width:1000px){.og-trip .g{grid-template-columns:repeat(3,1fr)}}@media(max-width:600px){.og-trip{margin:12px 0;padding:14px 10px 10px}.og-trip h2{font-size:18px}.og-trip .g{gap:7px}.og-trip i{height:60px}.og-trip b{font-size:12.5px;padding:6px 7px 0}.og-trip span{font-size:10.5px;padding:2px 7px 8px}}';
  function run(){
    var hero = document.getElementById('share-btn') || document.querySelector('.rate-note') || document.querySelector('.rates-hero'); if(!hero || document.querySelector('.og-trip')) return;
    var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    var h = '<h2>' + (ru ? '✈️ Путешествия дешевле' : '✈️ Подорожі дешевше') + '</h2><p class="s">' + (ru ? 'Билеты, интернет, авто и трансфер для поездки за границу' : 'Квитки, інтернет, авто й трансфер для поїздки за кордон') + '</p><div class="g">';
    L.forEach(function(x){ h += '<a href="'+x[1]+'" target="_blank" rel="sponsored noopener" data-trip="'+x[0]+'"><i style="background-image:url('+U+x[2]+'?auto=format&fit=crop&w=400&h=220&q=70)"></i><b>'+(ru?x[4]:x[3])+'</b><span>'+(ru?x[6]:x[5])+'</span></a>'; });
    h += '</div><small>' + (ru ? 'Реклама. Партнёрские ссылки — для вас цена как на сайте сервиса' : 'Реклама. Партнерські посилання — для вас ціна як на сайті сервісу') + '</small>';
    var s = document.createElement('section'); s.className = 'og-trip'; s.setAttribute('data-noi18n','1'); s.innerHTML = h;
    hero.parentNode.insertBefore(s, hero.nextSibling);
    s.addEventListener('click', function(e){ var a = e.target.closest('a[data-trip]'); if(a && window.ogTrack) window.ogTrack('trip-' + a.dataset.trip); });
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
})();
