# Лист лиц крупно для проверки ГЛАЗАМИ (24.11.2026, Замок 4).
# Автомерка 106 точек ошибается в обе стороны (открытый рот с зубами может пройти, закрытый — завалиться),
# поэтому перед сдачей обложек каждый лист смотреть глазами: глаза открыты, рот закрыт.
# python3 scripts/list_lic.py out_prefix обложка1.jpg обложка2.jpg ...   → out_prefix_0.jpg, _1.jpg … (по 12 лиц, глаза+рот крупно)
import sys,os,cv2
from PIL import Image,ImageDraw,ImageFont
D=os.path.dirname(os.path.abspath(__file__)); out=sys.argv[1]; files=sys.argv[2:]
hx=os.environ.get("HAAR") or os.path.join(D,"haar.xml")
if not os.path.exists(hx): hx=cv2.data.haarcascades+"haarcascade_frontalface_default.xml"
fc=cv2.CascadeClassifier(hx)
F=ImageFont.truetype(os.path.join(D,'..','fonts','montserrat-900.ttf'),20); cells=[]
for i,p in enumerate(files):
    im=cv2.resize(cv2.imread(p),(1080,1920))
    f=fc.detectMultiScale(cv2.cvtColor(cv2.resize(im,(540,960)),cv2.COLOR_BGR2GRAY),1.1,5,minSize=(40,40))
    if len(f):
        x,y,w,h=[int(c*2) for c in max(f,key=lambda r:r[2]*r[3])]; c=im[y+int(.2*h):y+h,x+int(.1*w):x+int(.9*w)]; nm=''
    else: c=im[300:1600,140:940]; nm=' (лицо не найдено — смотреть всю)'
    cells.append((f'{i} {os.path.basename(os.path.dirname(p))[:28]}{nm}',Image.fromarray(cv2.cvtColor(c,cv2.COLOR_BGR2RGB)).resize((440,440))))
for s in range(0,len(cells),12):
    part=cells[s:s+12]; sh=Image.new('RGB',(1760,480*((len(part)+3)//4)),'white'); d=ImageDraw.Draw(sh)
    for j,(lb,c) in enumerate(part):
        X,Y=(j%4)*440,(j//4)*480; sh.paste(c,(X,Y+40)); d.text((X+4,Y+8),lb,font=F,fill='black')
    sh.save(f'{out}_{s//12}.jpg')
