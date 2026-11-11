# Праздники v2 (замена build8): праздничная обложка, аватар, открытка-поздравление. Работает и на ua.html
import re, sys
for path, lang in [('/tmp/claude-0/var/out/seryj.html','ru'), ('/tmp/claude-0/var/out/ua.html','uk')]:
    s = open(path, encoding='utf-8').read()
    # убрать старый блок праздников v1 (css + js)
    s = re.sub(r'\n/\* праздники \*/.*?@media \(prefers-reduced-motion:reduce\)\{\.flake\{display:none\}\.garland i\{animation:none\}\}\n', '\n', s, flags=re.S)
    s = re.sub(r'<script>\n\(function\(\)\{\n/\* какой праздник сегодня.*?\}\)\(\);\n</script>\n', '', s, flags=re.S)
    assert 'fest-' not in s.replace('fest2', ''), path
    css = '''
/* праздники v2: своя обложка, аватар, открытка */
.fcard{position:absolute;left:50%;bottom:12px;transform:translateX(-50%);z-index:4;width:max-content;max-width:min(520px,60%);padding:10px 18px 10px 14px;border-radius:16px;background:rgba(255,255,255,.93);box-shadow:0 10px 30px rgba(0,0,0,.25);display:flex;gap:12px;align-items:center;backdrop-filter:blur(4px)}
.fcard i{font-style:normal;font-size:28px;line-height:1}
.fcard b{display:block;font-family:Lobster,"Brush Script MT",cursive;font-weight:400;font-size:25px;line-height:1.1;color:#b3122a}
.fcard span{display:block;font-size:13.5px;color:#36414f;margin-top:2px}
.fest2-hw .fcard b{color:#d35400}.fest2-fl .fcard b{color:#c0392b}.fest2-ea .fcard b{color:#2e7d32}
.fest2-on .avatar{object-position:center 12%}
@media (max-width:600px){.fcard{position:static;transform:none;width:auto;max-width:none;margin:12px 0 0;padding:10px 14px;box-shadow:0 4px 14px rgba(22,41,74,.12)}.fcard b{font-size:21px}.fcard span{font-size:12.5px}.fcard i{font-size:24px}}
.cover img.fest2img{animation:fin 1.2s ease-out}
@keyframes fin{from{opacity:.4;filter:saturate(.6)}to{opacity:1;filter:none}}
'''
    s = s.replace('</style>\n</head>', css + '</style>\n</head>', 1)
    s = s.replace('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded', '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lobster&display=swap">\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded', 1)
    T = {'ru': {
        'ny1': ('🎄', 'С наступающим!', 'Тёплого Нового года и уюта в вашем доме в Испании'),
        'xm':  ('🎄', '¡Feliz Navidad!', 'С Рождеством — пусть в доме будет тепло и спокойно'),
        'ny2': ('✨', 'С Новым годом!', 'Пусть этот год будет вашим годом в Испании'),
        're':  ('👑', 'Día de Reyes', 'С праздником Трёх королей!'),
        'hw':  ('🎃', 'Счастливого Хэллоуина!', 'Без страшных сюрпризов в договорах'),
        'fl':  ('🎆', 'Фальяс в Валенсии!', 'Салют, огни и праздник на весь город'),
        'ea':  ('🌷', 'Со Светлой Пасхой!', 'Мира и тепла вашему дому'),
      }, 'uk': {
        'ny1': ('🎄', 'З наступаючим!', 'Теплого Нового року й затишку у вашому домі в Іспанії'),
        'xm':  ('🎄', '¡Feliz Navidad!', 'З Різдвом — нехай удома буде тепло й спокійно'),
        'ny2': ('✨', 'З Новим роком!', 'Нехай цей рік буде вашим роком в Іспанії'),
        're':  ('👑', 'Día de Reyes', 'Зі святом Трьох королів!'),
        'hw':  ('🎃', 'Щасливого Гелловіну!', 'Без страшних сюрпризів у договорах'),
        'fl':  ('🎆', 'Фальяс у Валенсії!', 'Салют, вогні та свято на все місто'),
        'ea':  ('🌷', 'Зі Світлим Великоднем!', 'Миру й тепла вашому дому'),
      }}[lang]
    import json
    js = '''<script>
(function(){
/* праздники v2: сам включается по дате. Проверка: ?fest=ny / hw / fl / ea */
var T=''' + json.dumps(T, ensure_ascii=False) + ''';
var IMG={ny:{cover:'prazdniki/cover_ny.jpg',ava:'prazdniki/ava_ny.jpg'},hw:{cover:'prazdniki/cover_hw.jpg'},fl:{cover:'prazdniki/cover_fl.jpg'},ea:{cover:'prazdniki/cover_ea.jpg'}};
function easter(y,orth){var a,b,c,d,e,m,day;
 if(orth){a=y%4;b=y%7;c=y%19;d=(19*c+15)%30;e=(2*a+4*b-d+34)%7;m=Math.floor((d+e+114)/31);day=((d+e+114)%31)+1;return new Date(y,m-1,day+13)}
 a=y%19;b=Math.floor(y/100);c=y%100;d=Math.floor(b/4);e=b%4;var f=Math.floor((b+8)/25),g=Math.floor((b-f+1)/3),h=(19*a+b-d-g+15)%30,i=Math.floor(c/4),k=c%4,l=(32+2*e+2*i-h-k)%7,mm=Math.floor((a+11*h+22*l)/451);
 m=Math.floor((h+l-7*mm+114)/31);day=((h+l-7*mm+114)%31)+1;return new Date(y,m-1,day)}
function near(d,ref,b,a){var t=(d-ref)/864e5;return t>=-b&&t<=a}
var n=new Date(),y=n.getFullYear(),M=n.getMonth()+1,D=n.getDate(),f=null,k=null;
var q=(location.search.match(/fest=(\\w+)/)||[])[1];
if(q){f=q;k={ny:'ny1',hw:'hw',fl:'fl',ea:'ea'}[q]}
else if(M===12&&D>=24&&D<=26){f='ny';k='xm'}
else if(M===12||(M===11&&D>=28)){f='ny';k='ny1'}
else if(M===1&&D<=5){f='ny';k='ny2'}
else if(M===1&&D===6){f='ny';k='re'}
else if((M===10&&D>=28)||(M===11&&D===1)){f='hw';k='hw'}
else if(M===3&&D>=15&&D<=19){f='fl';k='fl'}
else{var t0=new Date(y,M-1,D);if(near(t0,easter(y,false),3,1)||near(t0,easter(y,true),1,1)){f='ea';k='ea'}}
if(!f||!T[k])return;
document.body.classList.add('fest2-'+f);
var cv=document.querySelector('.cover'),im=cv&&cv.querySelector('img'),set=IMG[f]||{};
function swap(el,src){if(!el||!src)return;var p=new Image();p.onload=function(){el.src=src;el.classList.add('fest2img')};p.src=src}
swap(im,set.cover);swap(document.querySelector('.avatar'),set.ava);
document.body.classList.add('fest2-on');var t=T[k],h='<div class="fcard"><i>'+t[0]+'</i><div><b>'+t[1]+'</b><span>'+t[2]+'</span></div></div>';var pr=document.querySelector('.profile');if(window.matchMedia('(max-width:600px)').matches&&pr){pr.insertAdjacentHTML('afterend',h)}else if(cv){cv.insertAdjacentHTML('beforeend',h)}
})();
</script>
'''
    s = s.replace('</body>', js + '</body>', 1)
    open(path, 'w', encoding='utf-8').write(s)
print('ok')
