/* Новогоднее оформление (28.11.2026): гирлянда с лампочками, шары, снег на обложке,
   снежинки по странице, снежные шапки на карточках. Включает праздничный скрипт страницы
   (fest=ny), сам по себе ничего не делает. Без внешних библиотек. */
(function(){
if(window.__kgNY)return;window.__kgNY=1;
var d=document,cv=d.querySelector('.cover');if(!cv)return;
var RM=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
var MOB=window.matchMedia&&matchMedia('(max-width:600px)').matches;

var host=MOB?(d.querySelector('.profile')||cv):cv;
var css=`
.nyg{position:absolute;left:0;top:0;width:100%;height:74px;z-index:3;pointer-events:none;overflow:visible}
.nyg .w{fill:none;stroke:#1b2a1e;stroke-width:2.2;stroke-linecap:round}
.nyg .w2{fill:none;stroke:#3d5a40;stroke-width:1;opacity:.7}
.nyg .cap{fill:#c9a24b}
.nyg .b{transform-box:fill-box;transform-origin:50% 0;animation:nyb 2.6s ease-in-out infinite}
.nyg .b ellipse{filter:url(#nyglow)}
@keyframes nyb{0%,100%{opacity:1}45%{opacity:.35}55%{opacity:.35}}
.nyball{position:absolute;top:0;z-index:3;pointer-events:none;transform-origin:50% 0;animation:nysw 4.5s ease-in-out infinite}
.nyball i{display:block;width:1px;margin:0 auto;background:linear-gradient(#c9a24b,#8a6d2a)}
.nyball b{display:block;margin:0 auto;width:8px;height:6px;border-radius:2px 2px 1px 1px;background:linear-gradient(90deg,#8a6d2a,#f3d27a,#8a6d2a)}
.nyball s{display:block;margin:-1px auto 0;border-radius:50%;box-shadow:inset -5px -6px 10px rgba(0,0,0,.35),0 6px 14px rgba(0,0,0,.35)}
.nyball s:after{content:"";display:block;width:32%;height:26%;margin:18% 0 0 22%;border-radius:50%;background:rgba(255,255,255,.75);filter:blur(1.5px)}
@keyframes nysw{0%,100%{transform:rotate(-4deg)}50%{transform:rotate(4deg)}}
.nysnow{position:absolute;inset:0;z-index:2;pointer-events:none}
.nyfl{position:fixed;inset:0;z-index:-1;pointer-events:none}
.nycap{position:absolute;left:14px;right:14px;top:-8px;height:15px;z-index:5;pointer-events:none;filter:drop-shadow(0 2px 2px rgba(40,60,90,.25))}
.go3 a .nycap{right:96px}
.go3 a.g2 .nycap,.go3 a.g3 .nycap{right:40%}
.fcard.ny{background:radial-gradient(120% 140% at 0% 0%,#a3162b 0%,#6e0c1b 55%,#4a0712 100%);border:2px solid #c9a24b;box-shadow:0 0 0 3px rgba(201,162,75,.25),0 12px 30px rgba(0,0,0,.35);color:#fff;backdrop-filter:none;overflow:visible}
.fcard.ny b{color:#ffe7a3!important;text-shadow:0 2px 0 rgba(0,0,0,.35),0 0 14px rgba(255,210,110,.45)}
.fcard.ny span{color:#fbe9ea}
.fcard.ny i{font-size:0;line-height:0}
.fcard.ny i svg{width:40px;height:40px;display:block}
@media (min-width:601px){.fcard.ny{top:58px;bottom:auto}}
@media (max-width:600px){.fcard.ny{position:relative;left:auto;transform:none;margin-top:18px}body .profile.nyh{padding-top:30px!important}.profile .nyg{top:-4px}.fcard.ny i svg{width:34px;height:34px}}
@media (prefers-reduced-motion:reduce){.nyg .b,.nyball{animation:none}}
`;
var st=d.createElement('style');st.textContent=css;d.head.appendChild(st);

/* ---------- гирлянда ---------- */
var COL=['#ff3b3b','#ffd23f','#2fd06a','#3fa9ff','#ff7ad9','#ffb03b'];
var NS='http://www.w3.org/2000/svg';
var svg=d.createElementNS(NS,'svg');svg.setAttribute('class','nyg');svg.setAttribute('aria-hidden','true');
host.appendChild(svg);if(host!==cv)host.classList.add('nyh');if(getComputedStyle(host).position==='static')host.style.position='relative';
function el(n,a){var e=d.createElementNS(NS,n);for(var k in a)e.setAttribute(k,a[k]);return e}
function q(p0,p1,p2,t){var u=1-t;return[u*u*p0[0]+2*u*t*p1[0]+t*t*p2[0],u*u*p0[1]+2*u*t*p1[1]+t*t*p2[1]]}
function qd(p0,p1,p2,t){return[2*(1-t)*(p1[0]-p0[0])+2*t*(p2[0]-p1[0]),2*(1-t)*(p1[1]-p0[1])+2*t*(p2[1]-p1[1])]}
var balls=[];
function garland(){
  var W=host.clientWidth;if(!W)return;
  while(svg.firstChild)svg.removeChild(svg.firstChild);
  balls.forEach(function(b){b.remove()});balls=[];
  svg.setAttribute('viewBox','0 0 '+W+' 74');
  var defs=el('defs',{});var f=el('filter',{id:'nyglow',x:'-150%',y:'-150%',width:'400%',height:'400%'});
  f.appendChild(el('feGaussianBlur',{stdDeviation:'2.6',result:'g'}));
  var m=el('feMerge',{});m.appendChild(el('feMergeNode',{in:'g'}));m.appendChild(el('feMergeNode',{in:'g'}));m.appendChild(el('feMergeNode',{in:'SourceGraphic'}));
  f.appendChild(m);defs.appendChild(f);svg.appendChild(defs);
  var seg=MOB?130:190, n=Math.max(2,Math.round(W/seg)), sw=W/n, sag=MOB?9:28, top=-2;
  var gw=el('g',{}),gb=el('g',{});svg.appendChild(gw);svg.appendChild(gb);
  var ci=0,per=MOB?5:6;
  for(var i=0;i<n;i++){
    var p0=[i*sw,top],p2=[(i+1)*sw,top],p1=[(i+.5)*sw,top+sag*2];
    var dP='M'+p0+' Q'+p1+' '+p2;
    gw.appendChild(el('path',{d:dP,class:'w'}));
    gw.appendChild(el('path',{d:'M'+p0+' Q'+[p1[0],p1[1]+3]+' '+p2,class:'w2'}));
    for(var j=1;j<=per;j++){
      var t=j/(per+1),pt=q(p0,p1,p2,t),dv=qd(p0,p1,p2,t);
      var ang=Math.atan2(dv[1],dv[0])*180/Math.PI;
      var c=COL[ci++%COL.length];
      var g=el('g',{transform:'translate('+pt[0].toFixed(1)+','+pt[1].toFixed(1)+') rotate('+(ang*.5).toFixed(1)+')'});
      var b=el('g',{class:'b'});
      b.style.animationDelay=(-Math.random()*2.6).toFixed(2)+'s';
      b.style.animationDuration=(2+Math.random()*1.6).toFixed(2)+'s';
      b.appendChild(el('rect',{x:-3,y:0,width:6,height:5,rx:1.2,class:'cap'}));
      b.appendChild(el('ellipse',{cx:0,cy:12,rx:MOB?4.6:5.6,ry:MOB?7:8.6,fill:c}));
      b.appendChild(el('ellipse',{cx:-1.6,cy:9.5,rx:1.4,ry:2.6,fill:'#fff',opacity:.75}));
      if(RM)b.style.animation='none';
      g.appendChild(b);gb.appendChild(g);
    }
  }
  /* шары висят в нижних точках дуг: через одну, кроме крайних, где кнопки языков и eSIM */
  var spots=[];if(!MOB){for(var k=1;k<n-1;k+=2)spots.push(k);if(!spots.length)spots=[Math.floor(n/2)]}
  var BC=[['#e0162f','#ff6b6b'],['#c9a24b','#ffe29a'],['#0f6b46','#38c98a'],['#1f4fbf','#7fb2ff']];
  spots.forEach(function(k,ix){
    var x=(k+.5)*sw, y=top+sag, L=(MOB?14:22)+(ix%2)*(MOB?10:16), D=MOB?18:24+(ix%3)*4;
    var cc=BC[ix%BC.length];
    var a=d.createElement('div');a.className='nyball';
    a.style.left=(x-D/2)+'px';a.style.top=y+'px';a.style.width=D+'px';
    a.style.animationDelay=(-ix*1.3)+'s';
    a.innerHTML='<i style="height:'+L+'px"></i><b></b><s style="width:'+D+'px;height:'+D+'px;background:radial-gradient(circle at 35% 30%,'+cc[1]+','+cc[0]+' 60%,#000 140%)"></s>';
    cv.appendChild(a);balls.push(a);
  });
}
garland();
var rt;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(garland,200)});

/* ---------- снег на обложке ---------- */
if(!RM){
var c=d.createElement('canvas');c.className='nysnow';cv.appendChild(c);
var x=c.getContext('2d'),fl=[],W,H,dpr=Math.min(2,window.devicePixelRatio||1);
function size(){W=cv.clientWidth;H=cv.clientHeight;c.width=W*dpr;c.height=H*dpr;x.setTransform(dpr,0,0,dpr,0,0)}
size();window.addEventListener('resize',size);
var N=MOB?45:110;
for(var i=0;i<N;i++)fl.push({x:Math.random()*W,y:Math.random()*H,r:.8+Math.random()*2.4,s:.25+Math.random()*.7,w:Math.random()*6.28,o:.45+Math.random()*.5});
var vis=true;
function frame(){
  if(vis){x.clearRect(0,0,W,H);
  for(var i=0;i<fl.length;i++){var p=fl[i];p.y+=p.s;p.w+=.012;p.x+=Math.sin(p.w)*.35;
    if(p.y>H+4){p.y=-4;p.x=Math.random()*W}
    x.beginPath();x.arc(p.x,p.y,p.r,0,6.283);x.fillStyle='rgba(255,255,255,'+p.o+')';x.fill()}}
  requestAnimationFrame(frame)}
if('IntersectionObserver'in window)new IntersectionObserver(function(e){vis=e[0].isIntersecting}).observe(cv);
d.addEventListener('visibilitychange',function(){if(d.hidden)vis=false});
frame();

/* ---------- редкие крупные снежинки по всей странице ---------- */
var c2=d.createElement('canvas');c2.className='nyfl';d.body.appendChild(c2);
var y2=c2.getContext('2d'),F=[],W2,H2;
function size2(){W2=innerWidth;H2=innerHeight;c2.width=W2*dpr;c2.height=H2*dpr;y2.setTransform(dpr,0,0,dpr,0,0)}
size2();window.addEventListener('resize',size2);
var N2=MOB?7:14;
for(var k=0;k<N2;k++)F.push({x:Math.random()*W2,y:Math.random()*H2,r:(MOB?6:7)+Math.random()*(MOB?5:8),s:.25+Math.random()*.35,a:Math.random()*6.28,v:(Math.random()-.5)*.01,w:Math.random()*6.28});
function flake(p){y2.save();y2.translate(p.x,p.y);y2.rotate(p.a);
  y2.strokeStyle='rgba(150,190,235,.75)';y2.lineWidth=1.6;y2.lineCap='round';
  y2.shadowColor='rgba(255,255,255,.9)';y2.shadowBlur=3;
  for(var i=0;i<6;i++){y2.rotate(Math.PI/3);y2.beginPath();y2.moveTo(0,0);y2.lineTo(0,-p.r);
    y2.moveTo(0,-p.r*.55);y2.lineTo(p.r*.28,-p.r*.8);y2.moveTo(0,-p.r*.55);y2.lineTo(-p.r*.28,-p.r*.8);y2.stroke()}
  y2.restore()}
var on2=true;d.addEventListener('visibilitychange',function(){on2=!d.hidden;if(on2)vis=true});
function f2(){if(on2){y2.clearRect(0,0,W2,H2);
  for(var i=0;i<F.length;i++){var p=F[i];p.y+=p.s;p.w+=.01;p.x+=Math.sin(p.w)*.3;p.a+=p.v;
    if(p.y>H2+20){p.y=-20;p.x=Math.random()*W2}flake(p)}}
  requestAnimationFrame(f2)}
f2();
}

/* ---------- снежные шапки ---------- */
function cap(host){if(!host||host.querySelector(':scope>.nycap'))return;
  if(getComputedStyle(host).position==='static')host.style.position='relative';
  var s=d.createElementNS(NS,'svg');s.setAttribute('class','nycap');s.setAttribute('viewBox','0 0 200 16');s.setAttribute('preserveAspectRatio','none');s.setAttribute('aria-hidden','true');
  s.innerHTML='<path fill="#fff" d="M0 10 C6 2 14 2 20 6 C26 0 38 0 44 6 C50 2 58 3 62 8 C70 1 84 1 92 7 C98 3 106 3 112 8 C120 2 132 2 140 7 C146 3 154 3 160 8 C168 2 182 2 190 7 C194 5 198 6 200 9 L200 11 C190 15 176 12 168 15 C156 12 146 16 134 13 C122 16 112 12 100 15 C88 12 76 16 64 13 C52 16 40 12 28 15 C18 12 8 15 0 12 Z"/>';
  host.appendChild(s)}
d.querySelectorAll('.go3 a').forEach(cap);


/* ---------- открытка ---------- */
function card(){var fc=d.querySelector('.fcard');if(!fc){return setTimeout(card,100)}
  fc.classList.add('ny');cap(fc);
  var ic=fc.querySelector('i');if(ic)ic.innerHTML='<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M8 30c6-2 10-7 12-14M6 22c7 1 12-2 16-8M30 8c-2 8 0 14 6 18M38 12c-4 6-3 12 2 18" stroke="#2f7d4a" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M10 27l-3-1M12 24l-2-3M15 21l-3-1M17 18l-2-3M10 21l-1-3M14 18l-1-3M33 12l3-1M33 16l3 0M34 20l3 1M38 17l2-2M38 21l3 0" stroke="#3f9a5c" stroke-width="2" stroke-linecap="round"/><path d="M24 14v8" stroke="#c9a24b" stroke-width="1.5"/><rect x="21" y="20" width="6" height="4" rx="1" fill="#e8c46a"/><circle cx="24" cy="33" r="10" fill="url(#nyb1)"/><circle cx="20.5" cy="29.5" r="2.6" fill="#fff" opacity=".8"/><defs><radialGradient id="nyb1" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#ffe29a"/><stop offset=".55" stop-color="#c9a24b"/><stop offset="1" stop-color="#6b4f17"/></radialGradient></defs></svg>'}
card();
})();
