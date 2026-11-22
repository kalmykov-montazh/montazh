<?php
// Сторінка «Сервіси для поїздок» (22.11.2026). /poyizdky — українська, /ru/poyizdky — російська. Посилання Travelpayouts з міткою obmen
$ru = isset($_GET['ru']);
function t($ua, $ru_) { global $ru; return $ru ? $ru_ : $ua; }
$U = 'https://images.unsplash.com/photo-';
$S = [
 ['Автобуси за кордон','Автобусы за границу','1570125909232-eb263c188f7e',[
   ['Unitiki','https://unitiki.tpk.ro/eDyJhUFe?erid=2VtzqvWzeNT','Квитки на міжнародні автобуси: Польща, Чехія, Німеччина та інші країни','Билеты на международные автобусы: Польша, Чехия, Германия и другие страны']]],
 ['Інтернет без роумінгу (eSIM)','Интернет без роуминга (eSIM)','1512941937669-90a1b58e7e9c',[
   ['Airalo','https://airalo.tpk.ro/hpwIoKAX?erid=2VtzqveQanB','Найвідоміший магазин eSIM. Пакет на тиждень чи місяць — по країні або на всю Європу','Самый известный магазин eSIM. Пакет на неделю или месяц — по стране или на всю Европу'],
   ['Yesim','https://yesim.tpk.ro/zUjs2mVk?erid=2VtzqvYUdeo','eSIM для 200+ країн, ставиться за пару хвилин через застосунок','eSIM для 200+ стран, ставится за пару минут через приложение']]],
 ['Авіаквитки','Авиабилеты','1436491865332-7a61a109cc05',[
   ['Aviasales','https://aviasales.tpk.ro/kqcuiFhL?erid=2VtzqvviSsy','Пошук дешевих квитків усіх авіакомпаній, календар цін на місяць','Поиск дешёвых билетов всех авиакомпаний, календарь цен на месяц'],
   ['Застосунок Aviasales','https://aviasales.tpk.ro/wmzTbV8k?erid=2VtzqvviSsy','Стежить за цінами й повідомить, коли квиток подешевшає','Следит за ценами и сообщит, когда билет подешевеет']]],
 ['Готелі та житло','Отели и жильё','1566073771259-6a8506099945',[
   ['Trip.com','https://trip.tpk.ro/1DeF1SSj?erid=2Vtzqwjgr3R','Готелі й апартаменти по всьому світу, часто з безкоштовним скасуванням','Отели и апартаменты по всему миру, часто с бесплатной отменой'],
   ['Vio.com','https://vio.tpk.ro/Kv0gY6yp?erid=2VtzqwWLxWK','Порівнює ціни на той самий готель на різних сайтах','Сравнивает цены на один и тот же отель на разных сайтах']]],
 ['Затримали чи скасували рейс','Задержали или отменили рейс','1530521954074-e64f6810b32d',[
   ['Compensair','https://compensair.tpk.ro/iHQIiKbQ?erid=2VtzqvygRSf','За правилами ЄС може належати компенсація за затримку від 3 годин чи скасування. Сервіс перевірить рейс і сам подасть заявку','По правилам ЕС может полагаться компенсация за задержку от 3 часов или отмену. Сервис проверит рейс и сам подаст заявку']]],
 ['Оренда авто в Європі','Аренда авто в Европе','1449965408869-eaa3f722e40d',[
   ['DiscoverCars','https://www.discovercars.com/?a_aid=kalmykovgroup','Сотні прокатів в одному пошуку, в умовах видно, чи беруть дебетову картку','Сотни прокатов в одном поиске, в условиях видно, берут ли дебетовую карту'],
   ['Economybookings','https://economybookings.tpk.ro/73XZkSEj','Порівнює ціни прокатників в аеропортах і містах','Сравнивает цены прокатчиков в аэропортах и городах'],
   ['QEEQ','https://qeeq.tpk.ro/uLxHwRnG?erid=2VtzqvpnVkb','Ще один порівняльник, часто дешевше на довгий строк','Ещё один сравнитель, часто дешевле на долгий срок'],
   ['AutoEurope','https://autoeurope.tpk.ro/0rboGHqQ?erid=2VtzqvskUKH','Великий європейський брокер, базова страховка зазвичай уже в ціні','Крупный европейский брокер, базовая страховка обычно уже в цене'],
   ['GetRentacar','https://getrentacar.tpk.ro/oV2RzpxB?erid=2VtzqvirYdD','Машини напряму від місцевих прокатів, часто без великого депозиту','Машины напрямую от местных прокатов, часто без большого депозита']]],
 ['Трансфер з аеропорту','Трансфер из аэропорта','1556122071-e404eaedb77f',[
   ['Kiwitaxi','https://kiwitaxi.tpk.ro/R6gWTNIb?erid=2VtzqvZxcw9','Фіксована ціна, водій зустрічає з табличкою','Фиксированная цена, водитель встречает с табличкой'],
   ['Welcome Pickups','https://tpk.ro/aOxEJWVl?erid=2VtzqvbScDV','Зустріч в аеропорту, ціна відома заздалегідь','Встреча в аэропорту, цена известна заранее']]],
 ['Екскурсії та квитки','Экскурсии и билеты','1511527661048-7fe73d85e9a4',[
   ['GetYourGuide','https://getyourguide.tpk.ro/phs4u9iX?erid=2VtzqwNw26b','Екскурсії, тури й квитки по всьому світу, зручне скасування','Экскурсии, туры и билеты по всему миру, удобная отмена'],
   ['Tiqets','https://tiqets.tpk.ro/a8zFSilw?erid=2VtzqvcvbVq','Квитки в музеї та на пам\'ятки без черги','Билеты в музеи и на достопримечательности без очереди'],
   ['WeGoTrip','https://wegotrip.tpk.ro/CltKxUjX?erid=2VtzqvrGV2w','Аудіоекскурсії в телефоні: гуляєте самі, у своєму темпі','Аудиоэкскурсии в телефоне: гуляете сами, в своём темпе']]],
 ['Камера схову','Камера хранения','1565026057447-bc90a3dceb87',[
   ['Radical Storage','https://radicalstorage.tpk.ro/GETely1E?erid=2VtzqvuETbd','Залишити валізу на кілька годин у місті, якщо поселення пізніше чи рейс увечері','Оставить чемодан на несколько часов в городе, если заселение позже или рейс вечером']]],
];
$home = $ru ? '/ru/' : '/';
$canon = 'https://obmen-gagarina.site' . ($ru ? '/ru/poyizdky' : '/poyizdky');
?><!DOCTYPE html>
<html lang="<?= $ru ? 'ru' : 'uk' ?>"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title><?= t('Сервіси для поїздок за кордон: автобуси, eSIM, авіаквитки, готелі — Обмін валют на Гагаріна','Сервисы для поездок за границу: автобусы, eSIM, авиабилеты, отели — Обмен валют на Гагарина') ?></title>
<meta name="description" content="<?= t('Перевірені сервіси для поїздки з Харкова за кордон: квитки на автобус, eSIM без роумінгу, дешеві авіаквитки, готелі, компенсація за затримку рейсу, оренда авто','Проверенные сервисы для поездки из Харькова за границу: билеты на автобус, eSIM без роуминга, дешёвые авиабилеты, отели, компенсация за задержку рейса, аренда авто') ?>">
<link rel="canonical" href="<?= $canon ?>"><link rel="alternate" hreflang="uk" href="https://obmen-gagarina.site/poyizdky"><link rel="alternate" hreflang="ru" href="https://obmen-gagarina.site/ru/poyizdky">
<link rel="icon" href="/favicon-48.png"><meta name="theme-color" content="#121a2a">
<style>
*{box-sizing:border-box}body{margin:0;background:radial-gradient(1200px 600px at 50% -200px,#26324d,#121a2a 60%) fixed,#121a2a;color:#e8ecf3;font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.w{max-width:1000px;margin:0 auto;padding:18px 14px 60px}
.top{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:16px}
.back{color:#121a2a;background:linear-gradient(135deg,#f3d27a,#d4af37);font-weight:800;text-decoration:none;border-radius:999px;padding:7px 16px;border:2px solid #0b1426}
.lng a{color:#e9c766;font-weight:700;text-decoration:none;margin-left:10px}
.hero{text-align:center;margin:4px 0 20px}
.hero h1{display:inline-block;margin:0 0 10px;padding:12px 26px;border:2px solid #d4af37;border-radius:18px;background:#0b1426;font-size:30px;line-height:1.2;box-shadow:0 0 0 4px rgba(212,175,55,.15)}
.hero h1 span{background:linear-gradient(180deg,#fffbe6 0%,#ffe27a 30%,#ffc93c 60%,#e0a43a 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{max-width:720px;margin:0 auto;color:#c9d1df}
.fl{background:linear-gradient(180deg,#fffaf0,#f6ecd6);color:#1c2333;border:2px solid #d4af37;border-radius:20px;padding:16px;margin:0 0 20px;box-shadow:0 0 0 2px #0b1426,0 10px 28px rgba(0,0,0,.35)}
.fl h2{margin:0 0 10px;text-align:center;font-size:20px;color:#121a2a}
.fl form{display:grid;grid-template-columns:1.2fr 1.2fr 1fr 1fr .7fr;gap:8px;align-items:end;position:relative}
.fl label{display:block;font-size:12px;color:#5a5140;margin-bottom:3px}
.fl input,.fl select{width:100%;font:inherit;font-size:15px;padding:10px;border:1.5px solid #c9b27a;border-radius:12px;background:#fff;color:#16233a}
.fl button{grid-column:1/-1;justify-self:center;min-width:240px;margin-top:6px;font:inherit;font-weight:900;font-size:17px;color:#fff;padding:11px 26px;border-radius:14px;cursor:pointer;background:linear-gradient(135deg,#ffab40,#f57c00,#e65100);border:2px solid #d4af37;outline:3px solid #0b1426}
.fl small{display:block;text-align:center;margin-top:8px;font-size:12px;color:#6b6250}
.ac{position:absolute;z-index:5;background:#fff;border:1.5px solid #c9b27a;border-radius:12px;box-shadow:0 8px 20px rgba(0,0,0,.2);max-height:260px;overflow:auto;min-width:240px}
.ac div{padding:8px 12px;cursor:pointer;font-size:14px}.ac div:hover{background:#fff3d6}.ac i{color:#8a8170;font-style:normal;font-size:12px}
.sec{background:linear-gradient(180deg,#fffaf0,#f6ecd6);border-radius:20px;overflow:hidden;margin:0 0 18px;border:2px solid #d4af37;box-shadow:0 0 0 2px #0b1426,0 10px 28px rgba(0,0,0,.35)}
.ph{height:140px;background:#121a2a center/cover no-repeat;display:flex;align-items:flex-end;justify-content:center;padding-bottom:12px;position:relative}
.ph:before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(11,20,38,0) 30%,rgba(11,20,38,.6))}
.ph h2{position:relative;margin:0;font-size:20px}
.ph h2 span{display:inline-block;background:linear-gradient(135deg,#1d3a7a,#2c4596);border:2px solid #d4af37;border-radius:14px;padding:6px 18px;color:#ffd54a;font-weight:900;-webkit-text-stroke:2.5px #000;paint-order:stroke fill;text-shadow:0 2px 0 #000;box-shadow:0 5px 14px rgba(0,0,0,.35)}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;padding:14px}
.it{display:flex;flex-direction:column;gap:5px;text-align:center;text-decoration:none;color:#16233a;background:#fff;border:2px solid #121a2a;border-radius:16px;padding:14px;transition:transform .15s}
.it:hover{transform:translateY(-3px)}.it b{font-size:18px;color:#121a2a}.it span{font-size:14px;color:#5a5140;line-height:1.45;flex:1}
.it em{font-style:normal;align-self:center;margin-top:6px;background:linear-gradient(135deg,#ffab40,#f57c00,#e65100);color:#fff;font-weight:900;padding:7px 20px;border-radius:12px;border:2px solid #0b1426}
.note{text-align:center;color:#8a93a6;font-size:12.5px;margin-top:8px}
@media(max-width:700px){.hero h1{font-size:22px;padding:10px 16px}.fl form{grid-template-columns:1fr 1fr}.fl .pax{grid-column:span 2}.ph{height:110px}.g{padding:10px}}
</style></head><body><div class="w">
<div class="top"><a class="back" href="<?= $home ?>">← <?= t('Курси валют','Курсы валют') ?></a><span class="lng"><a href="/poyizdky">UA</a><a href="/ru/poyizdky">RU</a></span></div>
<div class="hero"><h1><span><?= t('Сервіси для поїздок','Сервисы для поездок') ?></span></h1><p><?= t('Зібрали в одному місці те, що знадобиться в дорозі за кордон: автобус, інтернет без роумінгу, квитки на літак, готель. Ціни звичайні, як на сайтах самих сервісів','Собрали в одном месте то, что пригодится в дороге за границу: автобус, интернет без роуминга, билеты на самолёт, отель. Цены обычные, как на сайтах самих сервисов') ?></p></div>
<div class="fl"><h2>✈️ <?= t('Знайти авіаквитки','Найти авиабилеты') ?></h2>
<form id="flf" autocomplete="off">
<div><label><?= t('Звідки','Откуда') ?></label><input name="o" value="<?= t('Варшава','Варшава') ?>" data-code="WAW"></div>
<div><label><?= t('Куди','Куда') ?></label><input name="d" placeholder="<?= t('Місто чи аеропорт','Город или аэропорт') ?>"></div>
<div><label><?= t('Туди','Туда') ?></label><input type="date" name="d1"></div>
<div><label><?= t('Назад','Обратно') ?></label><input type="date" name="d2"></div>
<div class="pax"><label><?= t('Пасажири','Пассажиры') ?></label><select name="p"><option>1</option><option selected>2</option><option>3</option><option>4</option><option>5</option></select></div>
<button type="submit"><?= t('Знайти квитки','Найти билеты') ?></button></form>
<small><?= t('З Харкова зазвичай летять з Варшави, Кракова, Жешува, Кишинева — оберіть своє місто','Из Харькова обычно летят из Варшавы, Кракова, Жешува, Кишинёва — выберите свой город') ?></small></div>
<?php foreach ($S as $s): ?><section class="sec"><div class="ph" style="background-image:url(<?= $U . $s[2] ?>?auto=format&fit=crop&w=1000&h=300&q=70)"><h2><span><?= t($s[0], $s[1]) ?></span></h2></div><div class="g"><?php foreach ($s[3] as $it): ?><a class="it" href="<?= htmlspecialchars($it[1]) ?>" target="_blank" rel="sponsored noopener" data-trip="<?= strtolower(preg_replace('/\W/', '', $it[0])) ?>"><b><?= $it[0] ?></b><span><?= t($it[2], $it[3]) ?></span><em><?= t('Перейти','Перейти') ?></em></a><?php endforeach; ?></div></section>
<?php endforeach; ?>
<p class="note"><?= t('Реклама. Посилання партнерські: якщо ви щось оформите за ними, сервіс платить невелику комісію, для вас ціна не змінюється','Реклама. Ссылки партнёрские: если вы что-то оформите по ним, сервис платит небольшую комиссию, для вас цена не меняется') ?></p>
</div>
<script src="/track.js?v=3"></script>
<script>
(function(){var f=document.getElementById('flf'),L='<?= $ru ? 'ru' : 'uk' ?>',box=null,tm;
function dm(v){if(!v)return'';var p=v.split('-');return p[2]+p[1]}
function close(){if(box){box.remove();box=null}}
['o','d'].forEach(function(n){var i=f[n];i.addEventListener('input',function(){i.dataset.code='';clearTimeout(tm);var q=i.value.trim();if(q.length<2){close();return}tm=setTimeout(function(){fetch('https://autocomplete.travelpayouts.com/places2?term='+encodeURIComponent(q)+'&locale='+L+'&types[]=city&types[]=airport').then(function(r){return r.json()}).then(function(a){close();if(!a.length)return;i.dataset.first=a[0].code;box=document.createElement('div');box.className='ac';a.slice(0,7).forEach(function(x){var d=document.createElement('div');d.innerHTML=x.name+' <i>'+x.code+(x.country_name?', '+x.country_name:'')+'</i>';d.onclick=function(){i.value=x.name;i.dataset.code=x.code;close()};box.appendChild(d)});var r=i.getBoundingClientRect(),fr=f.getBoundingClientRect();box.style.left=(r.left-fr.left)+'px';box.style.top=(r.bottom-fr.top+4)+'px';f.appendChild(box)})},250)})});
document.addEventListener('click',function(e){if(box&&!box.contains(e.target))close()});
var t=new Date(Date.now()+14*864e5).toISOString().slice(0,10);f.d1.value=t;f.d1.min=new Date().toISOString().slice(0,10);
f.addEventListener('submit',function(e){e.preventDefault();var o=f.o.dataset.code||f.o.dataset.first,d=f.d.dataset.code||f.d.dataset.first;if(!o){f.o.focus();return}if(!d){f.d.focus();return}
var u='https://www.aviasales.com/search/'+o+dm(f.d1.value)+d+dm(f.d2.value)+f.p.value+'?marker=809770.obmen&locale='+(L=='uk'?'uk':'ru')+'&currency=uah';if(window.ogTrack)ogTrack('trip-form');window.open(u,'_blank','noopener')});
document.addEventListener('click',function(e){var a=e.target.closest('a[data-trip]');if(a&&window.ogTrack)ogTrack('trip-'+a.dataset.trip)});
})();
</script></body></html>
