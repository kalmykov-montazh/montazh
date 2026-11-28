/* Новогоднее оформление kalmykovgroup.com, v4 (28.11.2026): БЕЗ отдельной открытки — услуги не сдвигаются.
   Украшаем пустые места: фон страницы в снежинках, живые еловые ветки с шарами в свободных углах блоков,
   снег по сайту, снежные шапки на трёх кнопках, шапка Санты на аватаре (из index.html).
   v3 (открытка) — prazdniki/ny_v3.js, v2 (гирлянда) — ny_v2.js. Подключается из pwa.js (fest=ny) */
(function(){
if(window.__kgNY)return;window.__kgNY=1;
var d=document;
var RM=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
var mob=window.innerWidth<=700;
var UF='https://images.unsplash.com/photo-';
var flake=function(x,y,s,o){return '<g transform="translate('+x+' '+y+') scale('+s+')" opacity="'+o+'"><g stroke="%23b9cbe0" stroke-width="2" stroke-linecap="round" fill="none"><path d="M0-14V14M-12-7 12 7M-12 7 12-7"/><path d="M-4-11 0-7 4-11M-4 11 0 7 4 11M-13-2-9-4-10-9M13 2 9 4 10 9M-13 2-9 4-10 9M13-2 9-4 10-9"/></g></g>'};
var tile='<svg xmlns="http://www.w3.org/2000/svg" width="260" height="260" viewBox="0 0 260 260">'+flake(40,46,1,.9)+flake(170,30,.6,.75)+flake(210,150,1.15,.8)+flake(95,175,.7,.7)+flake(30,232,.55,.6)+flake(150,235,.45,.55)+'</svg>';
var css=''+
'.fcard{display:none!important}'+
'html,body{background-color:#eef2f7!important;background-image:url("data:image/svg+xml,'+tile.replace(/"/g,"'").replace(/</g,'%3C').replace(/>/g,'%3E')+'")!important;background-size:260px 260px!important}'+
'.kg4-k{position:absolute;z-index:-1;top:-4px;right:-4px;width:520px;height:280px;pointer-events:none;transform-origin:100% 0}'+
'.kg4-k.l{right:auto;left:-4px;transform-origin:0 0}'+
'.kg4-pb{position:absolute;left:0;right:0;top:100%;height:60px;z-index:2;pointer-events:none}'+
'.kg4-fir{position:absolute;top:0;right:0;width:520px;height:260px;overflow:hidden;mix-blend-mode:multiply;'+
'-webkit-mask-image:radial-gradient(130% 120% at 100% 0%,#000 46%,transparent 76%);mask-image:radial-gradient(130% 120% at 100% 0%,#000 46%,transparent 76%)}'+
'.kg4-fir img{position:absolute;top:0;right:0;width:346px;height:519px;transform-origin:top right;transform:translateX(-519px) rotate(-90deg);max-width:none}'+
'.kg4-host{isolation:isolate}.kg4-host.kg4-st{position:relative}'+
'.kg3-bb{position:absolute;transform-origin:50% 0;animation:kg3s 4s ease-in-out infinite alternate;filter:drop-shadow(0 6px 7px rgba(0,0,0,.35))}'+
'@keyframes kg3s{from{transform:rotate(-8deg)}to{transform:rotate(8deg)}}'+
'.kg3-snow{position:fixed;inset:0;width:100vw;height:100vh;z-index:45;pointer-events:none}'+
'.nycap{position:absolute;left:14px;top:-8px;height:15px;z-index:5;pointer-events:none;filter:drop-shadow(0 2px 2px rgba(40,60,90,.25))}'+
'.go3 a .nycap{right:96px}.go3 a.g2 .nycap,.go3 a.g3 .nycap{right:40%}'+
'@media (prefers-reduced-motion:reduce){.kg3-bb{animation:none}}';
var st=d.createElement('style');st.textContent=css;d.head.appendChild(st);

function orn(id,cls,x,top,len,r,c,dur,delay){
 var h=len+6+r*2+4,w=r*2+8,cx=w/2;
 return '<svg class="kg3-bb '+cls+'" style="left:'+(x-w/2)+'px;top:'+top+'px;width:'+w+'px;height:'+h+'px;animation-duration:'+dur+'s;animation-delay:'+delay+'s" viewBox="0 0 '+w+' '+h+'" aria-hidden="true">'+
 '<defs><radialGradient id="'+id+'" cx="35%" cy="30%" r="75%"><stop offset="0" stop-color="'+c[0]+'"/><stop offset=".45" stop-color="'+c[1]+'"/><stop offset="1" stop-color="'+c[2]+'"/></radialGradient>'+
 '<linearGradient id="'+id+'c" x1="0" x2="1"><stop offset="0" stop-color="#8a6420"/><stop offset=".5" stop-color="#f3d98e"/><stop offset="1" stop-color="#8a6420"/></linearGradient></defs>'+
 '<line x1="'+cx+'" y1="0" x2="'+cx+'" y2="'+len+'" stroke="#a07a24" stroke-width="1.2"/>'+
 '<rect x="'+(cx-4)+'" y="'+len+'" width="8" height="6" rx="1.2" fill="url(#'+id+'c)"/>'+
 '<circle cx="'+cx+'" cy="'+(len+6+r)+'" r="'+r+'" fill="url(#'+id+')"/>'+
 '<path d="M'+(cx-r+2)+' '+(len+6+r)+'q'+(r-2)+' '+(r*.35)+' '+(2*r-4)+' 0" stroke="#fff3c9" stroke-opacity=".45" stroke-width="1" fill="none"/>'+
 '<ellipse cx="'+(cx-r*.38)+'" cy="'+(len+6+r*.6)+'" rx="'+(r*.28)+'" ry="'+(r*.16)+'" fill="#fff" fill-opacity=".65" transform="rotate(-30 '+(cx-r*.38)+' '+(len+6+r*.6)+')"/></svg>'}
var RED=['#ffb0b0','#d21f2f','#5c0710'],GOLD=['#fff3c4','#e0a93a','#6b4409'],SILV=['#ffffff','#e3e6ec','#7d8696'],BLUE=['#cfe0ff','#2c5fc0','#0b2257'];


/* ветка с шарами в угол блока: el — блок, s — масштаб, left — левый угол (зеркально), n — сколько шаров */
var K=0;
function fir(el,s,left,n){if(!el||el.querySelector(':scope>.kg4-k'))return;
 el.classList.add('kg4-host');if(getComputedStyle(el).position==='static')el.classList.add('kg4-st');
 var k=d.createElement('div');k.className='kg4-k'+(left?' l':'');k.setAttribute('aria-hidden','true');
 k.style.transform=left?'translateX('+(520*s)+'px) scale('+(-s)+','+s+')':'scale('+s+')';
 var B=[['b1',488,30,30,19,RED,4.2,0],['b2',426,36,80,16,GOLD,3.6,-1.3],['b3',366,26,48,14,SILV,4.6,-2.1],['b4',312,20,20,12,BLUE,5,-.7]];
 var h='<div class="kg4-fir"><img alt="" loading="lazy" src="'+UF+'1737100932584-c57dcac311e2?auto=format&fit=crop&w=700&q=75"></div>';
 for(var i=0;i<(n||3);i++){var b=B[i];K++;h+=orn('kg4o'+K,b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7])}
 k.innerHTML=h;el.insertBefore(k,el.firstChild)}

function q(s){return d.querySelector(s)}
var pr=q('.profile');
/* профиль: шары свисают с нижнего края карточки в пустую полосу над тремя кнопками (широкий экран) */
if(pr&&window.innerWidth>=1000){pr.classList.add('kg4-host');var pb=d.createElement('div');pb.className='kg4-pb';pb.setAttribute('aria-hidden','true');
 var w=pr.offsetWidth,PB=[[.40,6,9,GOLD,4.4,-.5],[.47,18,11,RED,3.8,-1.6],[.53,4,8,SILV,4.9,-2.4],[.86,10,10,BLUE,4.1,-1],[.92,22,12,RED,3.6,-2],[.97,6,9,GOLD,4.6,-.3]],hh='';
 for(var j=0;j<PB.length;j++){var b=PB[j];K++;hh+=orn('kg4p'+K,'',Math.round(w*b[0]),-2,b[1],b[2],b[3],b[4],b[5])}
 pb.innerHTML=hh;pr.appendChild(pb)}
/* светлые блоки ниже: живые ветки с шарами в свободных углах */
if(!mob)fir(q('.bonus'),.42,0,3);
/* «Скоро»: справа от карточек пусто — ветка от заголовка свисает туда */
d.querySelectorAll('section.head').forEach(function(h){var n=h.nextElementSibling;if(!mob&&n&&n.classList.contains('soon'))fir(h,.5,0,3)});
var nb=d.querySelectorAll('.newsbox');if(!mob&&nb[0])fir(nb[0],.38,1,2);

/* снежные шапки на трёх больших кнопках */
var NS='http://www.w3.org/2000/svg';
d.querySelectorAll('.go3 a').forEach(function(h){if(h.querySelector('.nycap'))return;
  var s=d.createElementNS(NS,'svg');s.setAttribute('class','nycap');s.setAttribute('viewBox','0 0 200 16');s.setAttribute('preserveAspectRatio','none');s.setAttribute('aria-hidden','true');
  s.innerHTML='<path fill="#fff" d="M0 10 C6 2 14 2 20 6 C26 0 38 0 44 6 C50 2 58 3 62 8 C70 1 84 1 92 7 C98 3 106 3 112 8 C120 2 132 2 140 7 C146 3 154 3 160 8 C168 2 182 2 190 7 C194 5 198 6 200 9 L200 11 C190 15 176 12 168 15 C156 12 146 16 134 13 C122 16 112 12 100 15 C88 12 76 16 64 13 C52 16 40 12 28 15 C18 12 8 15 0 12 Z"/>';
  h.appendChild(s)});

/* снег по всему сайту, как на обменке */
if(RM)return;
var cv=d.createElement('canvas');cv.className='kg3-snow';cv.setAttribute('aria-hidden','true');d.body.appendChild(cv);
var R=Math.random,cx=cv.getContext('2d'),P=[],W=0,H=0,dpr=Math.min(window.devicePixelRatio||1,2);
function rs(){W=window.innerWidth;H=window.innerHeight;cv.width=W*dpr;cv.height=H*dpr;cx.setTransform(dpr,0,0,dpr,0,0)}
rs();window.addEventListener('resize',rs);
var N=mob?38:90;for(var i=0;i<N;i++)P.push({x:R()*W,y:R()*H,r:.8+R()*2.2,v:.35+R()*.8,w:R()*6.28,a:.5+R()*.45});
(function loop(){requestAnimationFrame(loop);if(d.hidden)return;cx.clearRect(0,0,W,H);cx.shadowColor='rgba(60,80,120,.55)';cx.shadowBlur=2;
 for(var i=0;i<P.length;i++){var p=P[i];p.y+=p.v;p.w+=.012;p.x+=Math.sin(p.w)*.35;if(p.y>H+5){p.y=-5;p.x=R()*W}if(p.x<-5)p.x=W+5;if(p.x>W+5)p.x=-5;
  cx.beginPath();cx.arc(p.x,p.y,p.r,0,6.283);cx.fillStyle='rgba(255,255,255,'+p.a+')';cx.fill()}})();
})();
