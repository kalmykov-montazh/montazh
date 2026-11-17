/* Перемикач мови UA / RU для obmen-gagarina.site (з 17.11.2026, версія 3)
   Українська — основна, відкривається за замовчуванням (закон № 2704, ст. 27). Російська — окремі сторінки /ru/...
   (сервер перекладає їх за словником i18n_dict.json — так їх бачить і Google).
   Тут: кнопки UA | RU, запам'ятати вибір, і на /ru/ — переклад того, що скрипти сторінки малюють уже після завантаження */
(function(){
var KEY='og_lang', path=location.pathname, isRu=/^\/ru(\/|$)/.test(path);
function ua(p){var x=p.replace(/^\/ru(?=\/|$)/,'');return x||'/';}
function ru(p){var x=ua(p).replace(/\.php$/,'').replace(/^\/index\.html$/,'/');return x==='/'?'/ru/':'/ru'+x;}
function qs(){try{var u=new URLSearchParams(location.search);u.delete('lang');var s=u.toString();return s?'?'+s:'';}catch(e){return '';}}
function go(p){location.replace(p+qs()+location.hash);}
try{
  var m=location.search.match(/[?&]lang=(ru|uk|ua)\b/);
  if(m){var want=m[1]==='ru'?'ru':'uk';localStorage.setItem(KEY,want);
    if(want==='ru'&&!isRu){go(ru(path));return;}
    if(want==='uk'&&isRu){go(ua(path));return;}}
  else if(!isRu&&localStorage.getItem(KEY)==='ru'){go(ru(path));return;}
}catch(e){}

/* ---- кнопки ---- */
var css='.lang-sw{display:inline-flex;border:1px solid rgba(212,175,55,.55);border-radius:999px;overflow:hidden;font:700 12px/1 system-ui,sans-serif;vertical-align:middle;margin-left:8px;flex:0 0 auto}'+
'.lang-sw a{padding:6px 9px;color:#d4af37;text-decoration:none;cursor:pointer;letter-spacing:.5px}'+
'.lang-sw a.on{background:#d4af37;color:#121a2a}'+
'@media(max-width:600px){.lang-sw{margin-left:5px}.lang-sw a.on{display:none}.lang-sw a{padding:6px 8px}}';
function ui(){
  var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
  var sw=document.createElement('div');sw.className='lang-sw';sw.setAttribute('data-noi18n','');
  var q=qs();
  sw.innerHTML='<a data-l="uk" href="'+ua(path)+q+'" hreflang="uk"'+(isRu?'':' class="on"')+'>UA</a>'+
               '<a data-l="ru" href="'+ru(path)+q+'" hreflang="ru"'+(isRu?' class="on"':'')+'>RU</a>';
  var place=document.querySelector('header .hbtns')||document.querySelector('header .hi')||document.querySelector('header')||document.body;
  place.appendChild(sw);
  sw.addEventListener('click',function(e){var l=e.target.getAttribute&&e.target.getAttribute('data-l');if(!l)return;
    try{localStorage.setItem(KEY,l)}catch(x){} try{window.ogTrack&&window.ogTrack('lang-'+l)}catch(x){}});
}

/* ---- переклад того, що з'являється після завантаження (тільки на /ru/) ---- */
var DICT=window.I18N||{D:{},S:[]}, L='а-яА-ЯіІїЇєЄґҐёЁa-zA-Z', RX=[];
try{for(var i=0;i<DICT.S.length;i++)RX.push([DICT.S[i][0],new RegExp('(^|[^'+L+'])'+DICT.S[i][0].replace(/[.*+?^${}()|[\]\\\/]/g,'\\$&')+'(?!['+L+'])','g'),DICT.S[i][1]]);}catch(e){RX=[];}
function tr(s){
  var t=s.replace(/\s+/g,' ').trim();if(!t)return s;
  var lead=s.match(/^\s*/)[0],tail=s.match(/\s*$/)[0];
  if(DICT.D[t])return lead+DICT.D[t]+tail;
  var o=t;for(var i=0;i<RX.length;i++){if(o.indexOf(RX[i][0])<0)continue;RX[i][1].lastIndex=0;var r=RX[i][2];o=o.replace(RX[i][1],function(a,b){return b+r;});}
  return o===t?s:lead+o+tail;
}
var UAL=/[іїєґІЇЄҐ]/;
function need(s){var t=s.replace(/\s+/g,' ').trim();return !!t&&(!!DICT.D[t]||UAL.test(t));}
function skip(el){return !el||(el.closest&&el.closest('script,style,#mo,.lang-sw,[data-noi18n]'));}
var done=typeof WeakMap!=='undefined'?new WeakMap():null;
function setT(n){
  if(skip(n.parentNode))return;
  if(done&&done.get(n)===n.nodeValue)return;
  if(!need(n.nodeValue))return;
  var v=tr(n.nodeValue);if(v!==n.nodeValue)n.nodeValue=v;
  if(done)done.set(n,n.nodeValue);
}
function setA(el){['placeholder','aria-label','title'].forEach(function(a){var x=el.getAttribute&&el.getAttribute(a);if(x&&UAL.test(x)||x&&DICT.D[x]){var y=tr(x);if(y!==x)el.setAttribute(a,y);}});}
function walk(root,first){
  if(root.nodeType===3){setT(root);return;}
  if(root.nodeType!==1||skip(root))return;
  setA(root);
  var w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT,null,false),n;
  while(n=w.nextNode()){if(n.nodeType===3)setT(n);else setA(n);}
}
function title(){var t=document.title,o=tr(t);if(o!==t)document.title=o;}
var busy=false;
function start(){
  ui();
  if(!isRu)return;
  busy=true;walk(document.body,true);title();busy=false;
  var obs=new MutationObserver(function(ms){
    if(busy)return;busy=true;
    for(var i=0;i<ms.length;i++){var m=ms[i];
      if(m.type==='characterData')walk(m.target,false);
      else for(var j=0;j<m.addedNodes.length;j++)walk(m.addedNodes[j],false);}
    obs.takeRecords();busy=false;
  });
  obs.observe(document.body,{childList:true,subtree:true,characterData:true});
  var tt=document.querySelector('title');
  if(tt)new MutationObserver(function(){if(!busy){busy=true;title();busy=false;}}).observe(tt,{childList:true,characterData:true,subtree:true});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
