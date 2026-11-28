/* Новогоднее оформление kalmykovgroup.com, v3 (28.11.2026) — в стиле открытки сайта обменки (v6):
   светлая открытка с золотой рамкой, живая еловая ветка и заснеженный лес (фото Unsplash),
   качающиеся шары, табличка, золотые цифры года, снег по сайту, снежные шапки на кнопках.
   v2 (лампочки-гирлянда) — prazdniki/ny_v2.js. Включает праздничный скрипт страницы (fest=ny) через pwa.js */
(function(){
if(window.__kgNY)return;window.__kgNY=1;
var d=document,M=new Date().getMonth()+1,Y=new Date().getFullYear(),yr=(M===1?Y:Y+1);
var UA=(d.documentElement.lang||'').indexOf('uk')===0||/^\/ua/.test(location.pathname);
var RM=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
var mob=window.innerWidth<=700;
var DD=new Date().getDate(),xm=(M===12&&DD>=24&&DD<=26),ny2=(M===1);
var TX=UA?{h1:ny2?'З Новим роком!':xm?'Щасливого Різдва!':'З наступаючим!',h2:'Новим роком і Різдвом!',h3:'Нехай '+yr+' стане вашим роком в Іспанії',p1:'Теплих свят',p2:'з Валенсії!'}
         :{h1:ny2?'С Новым годом!':xm?'Счастливого Рождества!':'С наступающим!',h2:'Новым годом и Рождеством!',h3:'Пусть '+yr+' станет вашим годом в Испании',p1:'Тёплых праздников',p2:'из Валенсии!'};
var UF='https://images.unsplash.com/photo-';

var css=''+
'.fcard{display:none!important}'+
'.kg3{position:relative;margin:18px 0 6px;padding:24px 30px 118px;min-height:270px;border-radius:20px;overflow:hidden;isolation:isolate;'+
'background:radial-gradient(60% 80% at 20% 10%,#fffefa 0%,rgba(255,254,250,0) 70%),linear-gradient(180deg,#fffaf0 0%,#fbf3e2 100%);'+
'border:2px solid #d4af37;box-shadow:0 0 0 4px rgba(212,175,55,.22),0 14px 34px -14px rgba(0,0,0,.45)}'+
'.kg3-fo{position:absolute;left:0;right:0;bottom:0;height:150px;z-index:0;background:url('+UF+'1641919238084-448ec0bfd446?auto=format&fit=crop&w=1800&q=70) center 62%/cover no-repeat;'+
'-webkit-mask-image:linear-gradient(180deg,transparent 0,#000 55%);mask-image:linear-gradient(180deg,transparent 0,#000 55%)}'+
'.kg3-fir{position:absolute;z-index:1;top:-6px;right:-4px;width:520px;height:260px;overflow:hidden;mix-blend-mode:multiply;pointer-events:none;'+
'-webkit-mask-image:radial-gradient(130% 120% at 100% 0%,#000 48%,transparent 78%);mask-image:radial-gradient(130% 120% at 100% 0%,#000 48%,transparent 78%)}'+
'.kg3-fir img{position:absolute;top:0;right:0;width:346px;height:519px;transform-origin:top right;transform:translateX(-519px) rotate(-90deg);max-width:none}'+
'.kg3-txt{position:relative;z-index:4;max-width:50%}'+
'.kg3-h1{display:block;font-family:Lobster,"Brush Script MT",cursive;font-weight:400;font-size:58px;line-height:1.02;color:#c1121f;text-shadow:0 2px 0 #fff,0 4px 0 #e2b85a,0 10px 18px rgba(120,20,20,.22)}'+
'.kg3-h2{display:block;margin-top:10px;font-family:Lobster,"Brush Script MT",cursive;font-weight:400;font-size:32px;line-height:1.1;color:#17603a;text-shadow:0 2px 0 #fff,0 3px 6px rgba(0,60,20,.15)}'+
'.kg3 .kg3-h3{display:block;margin-top:6px;font-family:"Cormorant Garamond",Georgia,serif;font-style:italic;font-weight:700;font-size:26px;line-height:1.15;color:#7a5412}'+
'.kg3-yr{position:absolute;z-index:3;right:28px;bottom:10px;font-family:"Cormorant Garamond",Georgia,serif;font-weight:700;font-size:80px;line-height:1;letter-spacing:3px;'+
'background:linear-gradient(180deg,#fff6c9 0%,#ffd75a 45%,#d9a12e 100%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 2px 0 #6b4a12) drop-shadow(0 6px 10px rgba(0,0,0,.45))}'+
'.kg3-bz{position:absolute;z-index:3;top:0;right:0;width:520px;height:280px;pointer-events:none}'+
'.kg3-bb{position:absolute;transform-origin:50% 0;animation:kg3s 4s ease-in-out infinite alternate;filter:drop-shadow(0 6px 7px rgba(0,0,0,.35))}'+
'@keyframes kg3s{from{transform:rotate(-8deg)}to{transform:rotate(8deg)}}'+
'.kg3-pl{position:absolute;z-index:5;right:230px;top:84px;width:280px;text-align:center;transform-origin:50% -34px;animation:kg3p 5s ease-in-out infinite alternate;'+
'padding:10px 14px 16px;border-radius:16px;background:radial-gradient(120% 90% at 50% 0%,#2d5bb0 0%,#173a7a 55%,#102a5c 100%);border:2px solid #f0c35a;box-shadow:inset 0 0 0 3px #102a5c,inset 0 0 0 4px rgba(255,213,0,.55),0 12px 24px -6px rgba(16,42,92,.65)}'+
'.kg3-pl:before,.kg3-pl:after{content:"";position:absolute;top:-56px;width:1.5px;height:56px;background:linear-gradient(#a07a24,#f3d98e)}.kg3-pl:before{left:26px}.kg3-pl:after{right:26px}'+
'@keyframes kg3p{from{transform:rotate(-1.8deg)}to{transform:rotate(1.8deg)}}'+
'.kg3-pl em{display:block;font-family:"Cormorant Garamond",Georgia,serif;font-style:italic;font-weight:700;line-height:1.05;letter-spacing:.3px;'+
'background:linear-gradient(180deg,#fffbe6 0%,#ffe27a 40%,#ffc93c 70%,#f0a93a 100%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 2px 0 #0b1d44)}'+
'.kg3-pl .a{font-size:27px;white-space:nowrap}.kg3-pl .c{font-size:25px;margin-top:1px}'+
'.kg3-pl svg{display:block;width:150px;height:12px;margin:3px auto 0}'+
'.kg3-pl .s1,.kg3-pl .s2{position:absolute;top:12px;color:#ffd500;font-size:13px;line-height:1;font-style:normal}.kg3-pl .s1{left:12px}.kg3-pl .s2{right:12px}'+
'.kg3-snow{position:fixed;inset:0;width:100vw;height:100vh;z-index:45;pointer-events:none}'+
'.nycap{position:absolute;left:14px;top:-8px;height:15px;z-index:5;pointer-events:none;filter:drop-shadow(0 2px 2px rgba(40,60,90,.25))}'+
'.go3 a .nycap{right:96px}.go3 a.g2 .nycap,.go3 a.g3 .nycap{right:40%}'+
'@media (max-width:1100px){.kg3-txt{max-width:44%}.kg3-h1{font-size:46px}.kg3-h2{font-size:27px}.kg3 .kg3-h3{font-size:22px}.kg3-yr{font-size:66px}}'+
'@media (max-width:700px){.kg3{padding:30px 16px 100px;min-height:0}.kg3-txt{max-width:100%}.kg3-h1{font-size:34px;white-space:nowrap}.kg3-h2{font-size:21px;margin-top:6px}.kg3 .kg3-h3{font-size:19px;max-width:78%}'+
'.kg3-fo{height:120px}.kg3-yr{font-size:44px;right:12px;bottom:8px}.kg3-fir{transform:scale(.5);transform-origin:100% 0}.kg3-bz{transform:scale(.42);transform-origin:100% 0}.kg3-bz .b3,.kg3-bz .b4,.kg3-bz .b5{display:none}'+
'.kg3-pl{position:relative;right:auto;top:auto;margin:14px 0 0;width:auto;max-width:250px;animation:none}.kg3-pl:before,.kg3-pl:after{display:none}.kg3-pl .a{font-size:23px}.kg3-pl .c{font-size:21px}}'+
'@media (prefers-reduced-motion:reduce){.kg3-bb,.kg3-pl{animation:none}}';
var st=d.createElement('style');st.textContent=css;d.head.appendChild(st);
var lf=d.createElement('link');lf.rel='stylesheet';lf.href='https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,700;1,700&family=Lobster&display=swap';d.head.appendChild(lf);

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

var card=d.createElement('section');card.className='kg3';card.setAttribute('aria-label',TX.h1);
card.innerHTML='<div class="kg3-fo" aria-hidden="true"></div>'+
 '<div class="kg3-fir" aria-hidden="true"><img alt="" src="'+UF+'1737100932584-c57dcac311e2?auto=format&fit=crop&w=700&q=75"></div>'+
 '<div class="kg3-txt"><b class="kg3-h1">'+TX.h1+'</b><strong class="kg3-h2">'+TX.h2+'</strong><span class="kg3-h3">'+TX.h3+'</span></div>'+
 '<div class="kg3-yr" aria-hidden="true">'+yr+'</div>'+
 '<div class="kg3-bz" aria-hidden="true">'+
  orn('kg3a','b1',488,30,30,19,RED,4.2,0)+
  orn('kg3b','b2',426,36,80,16,GOLD,3.6,-1.3)+
  orn('kg3c','b3',366,26,48,14,SILV,4.6,-2.1)+
  orn('kg3d','b4',312,20,20,12,BLUE,5,-0.7)+
  orn('kg3e','b5',160,16,8,13,RED,4.4,-1.8)+
 '</div>'+
 '<div class="kg3-pl"><i class="s1">✦</i><i class="s2">✦</i><em class="a">'+TX.p1+'</em><em class="c">'+TX.p2+'</em>'+
 '<svg viewBox="0 0 150 12" aria-hidden="true"><path d="M4 8 C40 1, 90 1, 146 6" stroke="#ffd500" stroke-width="2.4" fill="none" stroke-linecap="round"/><path d="M20 10 C60 5, 100 5, 132 9" stroke="#ffd500" stroke-opacity=".55" stroke-width="1.3" fill="none" stroke-linecap="round"/></svg></div>';
var go=d.querySelector('.go3'),pr=d.querySelector('.profile');
if(go)go.parentNode.insertBefore(card,go);else if(pr)pr.insertAdjacentElement('afterend',card);
if(mob)card.querySelector('.kg3-txt').appendChild(card.querySelector('.kg3-pl'));

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
