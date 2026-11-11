# Праздничное оформление по датам (сайт Валенсии). Само включается у посетителя.
p = '/tmp/claude-0/var/out/seryj.html'
s = open(p, encoding='utf-8').read()
assert 'fest-' not in s

css = '''
/* праздники */
.fest{position:absolute;right:12px;bottom:12px;z-index:4;display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:99px;font-size:14px;font-weight:700;background:#fff;color:#16294a;box-shadow:0 2px 8px rgba(22,41,74,.10)}
.fest-ny .fest{background:#c62828;color:#fff}
.fest-hw .fest{background:#1d1d1d;color:#ff9a3c}
.fest-fl .fest{background:#ff6b4a;color:#fff}
.fest-ea .fest{background:#fff6d6;color:#7a5a00}
.garland{position:absolute;left:0;right:0;top:0;height:26px;pointer-events:none;z-index:3;display:flex;justify-content:space-around;padding:0 10px}
.garland i{width:12px;height:16px;border-radius:50% 50% 45% 45%;margin-top:6px;box-shadow:0 0 10px currentColor;animation:blink 1.6s infinite alternate}
.garland i:nth-child(4n+1){color:#ff3b3b;background:#ff3b3b}.garland i:nth-child(4n+2){color:#ffd166;background:#ffd166;animation-delay:.4s}
.garland i:nth-child(4n+3){color:#3bd16f;background:#3bd16f;animation-delay:.8s}.garland i:nth-child(4n){color:#4fc3ff;background:#4fc3ff;animation-delay:1.2s}
@keyframes blink{from{opacity:.35}to{opacity:1}}
.cover{position:relative}
.flake{position:fixed;top:-20px;z-index:30;pointer-events:none;color:#fff;text-shadow:0 0 4px rgba(22,41,74,.35);animation:fall linear forwards}
@keyframes fall{to{transform:translateY(105vh) rotate(200deg)}}
@media (prefers-reduced-motion:reduce){.flake{display:none}.garland i{animation:none}}
'''
s = s.replace('</style>\n</head>', css + '</style>\n</head>', 1)

js = r'''<script>
(function(){
/* какой праздник сегодня; для проверки можно открыть сайт с ?fest=ny / hw / fl / ea */
var L=document.documentElement.lang==='uk'?'uk':'ru';
var T={ru:{ny1:'🎄 С наступающим Новым годом!',ny2:'🎄 С Новым годом!',re:'👑 С праздником Трёх королей!',hw:'🎃 Счастливого Хэллоуина!',fl:'🎆 Фальяс в Валенсии!',ea:'🐣 Со Светлой Пасхой!'},
       uk:{ny1:'🎄 З наступаючим Новим роком!',ny2:'🎄 З Новим роком!',re:'👑 Зі святом Трьох королів!',hw:'🎃 Щасливого Гелловіну!',fl:'🎆 Фальяс у Валенсії!',ea:'🐣 Зі Світлим Великоднем!'}}[L];
function easter(y,orth){var a,b,c,d,e,m,day;
 if(orth){a=y%4;b=y%7;c=y%19;d=(19*c+15)%30;e=(2*a+4*b-d+34)%7;m=Math.floor((d+e+114)/31);day=((d+e+114)%31)+1;return new Date(y,m-1,day+13)}
 a=y%19;b=Math.floor(y/100);c=y%100;d=Math.floor(b/4);e=b%4;var f=Math.floor((b+8)/25),g=Math.floor((b-f+1)/3),h=(19*a+b-d-g+15)%30,i=Math.floor(c/4),k=c%4,l=(32+2*e+2*i-h-k)%7,mm=Math.floor((a+11*h+22*l)/451);
 m=Math.floor((h+l-7*mm+114)/31);day=((h+l-7*mm+114)%31)+1;return new Date(y,m-1,day)}
function near(d,ref,before,after){var t=(d-ref)/864e5;return t>=-before&&t<=after}
var now=new Date(),y=now.getFullYear(),M=now.getMonth()+1,D=now.getDate(),f=null,txt='';
var q=(location.search.match(/fest=(\w+)/)||[])[1];
if(q){f=q;txt={ny:T.ny1,hw:T.hw,fl:T.fl,ea:T.ea}[q]||''}
else if(M===12){f='ny';txt=T.ny1}
else if(M===1&&D<=5){f='ny';txt=T.ny2}
else if(M===1&&D===6){f='ny';txt=T.re}
else if((M===10&&D>=28)||(M===11&&D===1)){f='hw';txt=T.hw}
else if(M===3&&D>=15&&D<=19){f='fl';txt=T.fl}
else{var t0=new Date(y,M-1,D);if(near(t0,easter(y,false),3,1)||near(t0,easter(y,true),1,1)){f='ea';txt=T.ea}}
if(!f)return;
document.body.classList.add('fest-'+f);
var cv=document.querySelector('.cover');if(cv&&txt)cv.insertAdjacentHTML('beforeend','<span class="fest">'+txt+'</span>');
if(f==='ny'&&cv){var g='<div class="garland" aria-hidden="true">';for(var i=0;i<14;i++)g+='<i></i>';cv.insertAdjacentHTML('afterbegin',g+'</div>')}
var sym={ny:['❄','❅','❆'],hw:['🦇','🍂'],fl:['✨','🎉'],ea:['🌸','🌼']}[f];
if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)return;
var n=0,tm=setInterval(function(){if(++n>(f==='ny'?40:14)){clearInterval(tm);return}
 var e=document.createElement('span');e.className='flake';e.textContent=sym[n%sym.length];
 e.style.left=Math.random()*100+'vw';e.style.fontSize=(12+Math.random()*14)+'px';e.style.opacity=.5+Math.random()*.5;
 e.style.animationDuration=(6+Math.random()*6)+'s';document.body.appendChild(e);setTimeout(function(){e.remove()},13000)},350);
})();
</script>
'''
s = s.replace('</body>', js + '</body>', 1)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
