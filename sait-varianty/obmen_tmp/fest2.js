/* Святкове оформлення obmen-gagarina.site, версія 2 (11.11.2026): гірлянда під шапкою, листівка над курсами, золотий сніг.
   Вмикається саме за датою. Перевірка: obmen-gagarina.site/?fest=ny (або xm, hw, ea, ind) */
(function(){
var d=new Date(),M=d.getMonth()+1,D=d.getDate(),y=d.getFullYear(),f=null,k=null;
function orthEaster(y){var a=y%4,b=y%7,c=y%19,dd=(19*c+15)%30,e=(2*a+4*b-dd+34)%7,m=Math.floor((dd+e+114)/31),day=((dd+e+114)%31)+1;return new Date(y,m-1,day+13)}
var q=(location.search.match(/fest=(\w+)/)||[])[1];
var T={
 ny1:['З наступаючим!','Новим роком і Різдвом. Спокійних свят і стабільного курсу'],
 xm:['Щасливого Різдва!','Тепла, миру і спокою вашій родині'],
 ny2:['З Новим роком!','Нехай цей рік буде мирним і щедрим'],
 hw:['Щасливого Гелловіну!','Страшно буває тільки без актуального курсу'],
 ea:['Христос воскрес!','Зі Світлим Великоднем. Миру і добра вашому дому'],
 ind:['З Днем Незалежності!','Слава Україні! Героям слава!']};
if(q){f={ny:'ny',xm:'ny',hw:'hw',ea:'ea',ind:'ind'}[q];k={ny:'ny1',xm:'xm',hw:'hw',ea:'ea',ind:'ind'}[q]}
else if(M===12&&D>=24&&D<=26){f='ny';k='xm'}
else if(M===12||(M===11&&D>=28)){f='ny';k='ny1'}
else if(M===1&&D<=7){f='ny';k='ny2'}
else if((M===10&&D>=28)||(M===11&&D===1)){f='hw';k='hw'}
else if(M===8&&(D===23||D===24)){f='ind';k='ind'}
else{var e=orthEaster(y),t=(new Date(y,M-1,D)-e)/864e5;if(t>=-1&&t<=1){f='ea';k='ea'}}
if(!f||!T[k])return;
var A={ny:'#d4a843',hw:'#ff8a2a',ea:'#e9c46a',ind:'#ffd500'}[f];
var lights={ny:['#ffd27a','#ff5a4e','#7ee08f','#7cc8ff','#ffd27a'],hw:['#ff8a2a','#ffb347','#b066ff'],ea:['#ffe9a8','#ffc2d1','#b8f2c6'],ind:['#0a6cff','#ffd500']}[f];
/* малюнки для листівки */
var ART={
ny:'<svg viewBox="0 0 120 120" aria-hidden="true"><path d="M60 8l6 14 15 1-12 9 4 15-13-8-13 8 4-15-12-9 15-1z" fill="#d4a843"/><path d="M60 40L28 98h64z" fill="#1f5a3a"/><path d="M60 40L36 84h48z" fill="#2a7a4e"/><path d="M60 40L44 70h32z" fill="#349160"/><rect x="54" y="98" width="12" height="12" rx="2" fill="#7a4a24"/><circle cx="50" cy="66" r="4" fill="#ff5a4e"/><circle cx="70" cy="78" r="4" fill="#d4a843"/><circle cx="46" cy="88" r="4" fill="#7cc8ff"/><circle cx="74" cy="92" r="3.5" fill="#ff5a4e"/><circle cx="62" cy="58" r="3" fill="#7cc8ff"/><path d="M40 76q20 8 40-4M36 90q24 9 48-2" stroke="#d4a843" stroke-width="1.6" fill="none" opacity=".8"/></svg>',
hw:'<svg viewBox="0 0 120 120" aria-hidden="true"><circle cx="92" cy="26" r="14" fill="#f6e3b0" opacity=".9"/><path d="M58 30q2-10 10-12" stroke="#4a6b2a" stroke-width="5" fill="none" stroke-linecap="round"/><ellipse cx="44" cy="74" rx="22" ry="30" fill="#e8741c"/><ellipse cx="76" cy="74" rx="22" ry="30" fill="#e8741c"/><ellipse cx="60" cy="74" rx="22" ry="32" fill="#f28a2e"/><path d="M42 64l8-9 8 9zM62 64l8-9 8 9z" fill="#ffd36a"/><path d="M40 82h40l-6 10-6-6-8 8-8-8-6 6z" fill="#ffd36a"/><path d="M14 30q6-6 12 0q6-6 12 0q-6 2-12 8q-6-6-12-8z" fill="#2a1a33"/></svg>',
ea:'<svg viewBox="0 0 120 120" aria-hidden="true"><path d="M20 100q40-30 80 0" stroke="#7a9a4a" stroke-width="3" fill="none"/><ellipse cx="42" cy="70" rx="18" ry="24" fill="#c0392b"/><path d="M26 64h32M25 76h34" stroke="#ffd36a" stroke-width="3"/><path d="M30 70l4-4 4 4 4-4 4 4 4-4 4 4" stroke="#fff" stroke-width="2" fill="none"/><ellipse cx="80" cy="72" rx="17" ry="22" fill="#2a6fdb"/><path d="M65 70h30" stroke="#ffd36a" stroke-width="3"/><circle cx="80" cy="60" r="3" fill="#fff"/><circle cx="80" cy="82" r="3" fill="#fff"/><path d="M96 30q-6 14 2 28M100 26q4 10 0 22" stroke="#9aa86a" stroke-width="2" fill="none"/><circle cx="96" cy="34" r="3" fill="#eee"/><circle cx="98" cy="44" r="3" fill="#eee"/><circle cx="101" cy="30" r="2.6" fill="#eee"/></svg>',
ind:'<svg viewBox="0 0 120 120" aria-hidden="true"><rect x="18" y="26" width="84" height="34" rx="4" fill="#0a6cff"/><rect x="18" y="60" width="84" height="34" rx="4" fill="#ffd500"/><path d="M60 40v40M50 46q0 22 10 30q10-8 10-30" stroke="#fff" stroke-width="3" fill="none" opacity=".9"/></svg>'}[f];
var css=''+
'.fx2-gar{position:sticky;top:62px;z-index:49;height:0;pointer-events:none}'+
'.fx2-gar svg{position:absolute;left:0;top:-4px;width:100%;height:38px;overflow:visible}'+
'.fx2-gar .b{animation:fx2b 2.4s ease-in-out infinite alternate}'+
'@keyframes fx2b{from{opacity:.35}to{opacity:1}}'+
'.fx2-card{position:relative;display:flex;align-items:center;gap:18px;margin:0 0 18px;padding:16px 22px;border-radius:14px;background:radial-gradient(120% 140% at 0% 0%,rgba(255,255,255,.06),rgba(255,255,255,0) 60%),#161616;border:1px solid '+A+'55;box-shadow:0 0 0 1px rgba(0,0,0,.4),0 10px 40px -12px '+A+'55;overflow:hidden}'+
'.fx2-card:before{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 30%,'+A+'22 50%,transparent 70%);transform:translateX(-100%);animation:fx2s 5s ease-in-out 1s infinite}'+
'@keyframes fx2s{0%{transform:translateX(-100%)}40%,100%{transform:translateX(100%)}}'+
'.fx2-card svg{flex:0 0 auto;width:74px;height:74px;filter:drop-shadow(0 4px 10px rgba(0,0,0,.5))}'+
'.fx2-card b{display:block;font-family:Lobster,"Brush Script MT",cursive;font-weight:400;font-size:32px;line-height:1.1;color:'+A+';text-shadow:0 0 18px '+A+'55}'+
'.fx2-card span{display:block;margin-top:4px;font:500 14px/1.4 Inter,system-ui,sans-serif;color:#cfcfcf}'+
'.fx2-fl{position:fixed;top:-12px;z-index:60;pointer-events:none;border-radius:50%;background:'+A+';box-shadow:0 0 6px '+A+';animation:fx2f linear forwards}'+
'@keyframes fx2f{to{transform:translate3d(var(--dx),105vh,0)}}'+
'@media (max-width:600px){.fx2-card{gap:12px;padding:12px 14px}.fx2-card svg{width:56px;height:56px}.fx2-card b{font-size:25px}.fx2-card span{font-size:12.5px}}'+
'@media (prefers-reduced-motion:reduce){.fx2-fl{display:none}.fx2-gar .b,.fx2-card:before{animation:none}}';
var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
var lf=document.createElement('link');lf.rel='stylesheet';lf.href='https://fonts.googleapis.com/css2?family=Lobster&display=swap';document.head.appendChild(lf);
/* гірлянда: провиси дроту з вогниками */
var hd=document.querySelector('header');
if(hd){var W=1000,sv='<svg viewBox="0 0 '+W+' 34" preserveAspectRatio="none"><g fill="none" stroke="#3a3a3a" stroke-width="1.4">',bulbs='',seg=6,sw=W/seg,ci=0;
 for(var s=0;s<seg;s++){var x0=s*sw,x1=x0+sw;sv+='<path d="M'+x0+' 2Q'+(x0+sw/2)+' 30 '+x1+' 2"/>';
  for(var j=1;j<6;j++){var t=j/6,bx=x0+sw*t,by=2+28*2*t*(1-t)*1;var c=lights[ci++%lights.length];
   bulbs+='<g class="b" style="animation-delay:'+((ci*0.37)%2.4).toFixed(2)+'s"><circle cx="'+bx.toFixed(1)+'" cy="'+(by+4).toFixed(1)+'" r="9" fill="'+c+'" opacity=".25"/><ellipse cx="'+bx.toFixed(1)+'" cy="'+(by+4).toFixed(1)+'" rx="3.4" ry="4.6" fill="'+c+'"/></g>'}}
 sv+='</g>'+bulbs+'</svg>';
 var g=document.createElement('div');g.className='fx2-gar';g.setAttribute('aria-hidden','true');g.innerHTML=sv;hd.insertAdjacentElement('afterend',g)}
/* листівка над курсами */
var t=T[k],card=document.createElement('div');card.className='fx2-card';card.innerHTML=ART+'<div><b>'+t[0]+'</b><span>'+t[1]+'</span></div>';
var host=document.querySelector('.rates-hero-inner');if(host)host.insertBefore(card,host.firstChild);
/* легкий золотий сніг — тільки зимові свята */
if(f!=='ny'||(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches))return;
var n=0,tm=setInterval(function(){if(++n>45){clearInterval(tm);return}
 var s=document.createElement('i'),z=2+Math.random()*3;s.className='fx2-fl';
 s.style.cssText='left:'+(Math.random()*100)+'vw;width:'+z+'px;height:'+z+'px;opacity:'+(.35+Math.random()*.5)+';--dx:'+((Math.random()-.5)*80)+'px;animation-duration:'+(8+Math.random()*7)+'s';
 document.body.appendChild(s);setTimeout(function(){s.remove()},16000)},300);
})();
