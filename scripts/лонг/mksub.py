from PIL import Image,ImageDraw,ImageFont
import math
F=ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf',44)
W,H=620,190;fps=30;N=int(4.0*fps)
def bell(d,cx,cy,s,fill,ring):
    d.pieslice([cx-s,cy-s*1.1,cx+s,cy+s*0.9],180,360,fill=fill)
    d.polygon([(cx-s,cy-s*0.1),(cx+s,cy-s*0.1),(cx+s*1.25,cy+s*0.6),(cx-s*1.25,cy+s*0.6)],fill=fill)
    d.ellipse([cx-s*0.28,cy+s*0.55,cx+s*0.28,cy+s*1.0],fill=fill)
    if ring:
        for k in (1,2):
            r=s*(1.35+0.35*k)
            d.arc([cx-r,cy-r,cx+r,cy+r],200,240,fill=fill,width=6);d.arc([cx-r,cy-r,cx+r,cy+r],300,340,fill=fill,width=6)
def cursor(d,x,y,sc=1.0):
    p=[(0,0),(0,46),(12,35),(21,55),(29,51),(20,32),(36,32)]
    p=[(x+a*sc,y+b*sc) for a,b in p];d.polygon(p,fill='white',outline='black',width=3)
for i in range(N):
    t=i/fps;im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im)
    sub=t>=1.5
    bw=420;bx,by=10,50
    d.rounded_rectangle([bx+4,by+6,bx+bw+4,by+96],22,fill=(0,0,0,110))
    d.rounded_rectangle([bx,by,bx+bw,by+90],22,fill=(90,90,90,255) if sub else (230,33,23,255))
    txt='ВЫ ПОДПИСАНЫ' if sub else 'ПОДПИСАТЬСЯ'
    tw=d.textlength(txt,font=F);d.text((bx+(bw-tw)/2,by+18),txt,font=F,fill='white')
    # bell button
    cx,cy=bx+bw+85,by+45
    d.ellipse([cx-48,cy-48,cx+48,cy+48],fill=(255,255,255,235))
    ring=t>=1.6 and t<3.0
    ang=math.sin((t-1.6)*30)*14*math.exp(-(t-1.6)*2) if t>=1.6 else 0
    b=Image.new('RGBA',(120,120),(0,0,0,0));bell(ImageDraw.Draw(b),60,55,26,(20,20,20,255),ring)
    b=b.rotate(ang,center=(60,30),resample=Image.BICUBIC);im.alpha_composite(b,(int(cx-60),int(cy-55)))
    # cursor moves to button 0.8..1.4, click 1.5
    if t>=0.7:
        k=min(1,(t-0.7)/0.7);k=k*k*(3-2*k)
        x=bx+bw+10+(bx+bw*0.6-(bx+bw+10))*k;y=by+150+(by+40-(by+150))*k
        cursor(d,x,y,0.85 if 1.45<t<1.6 else 1.0)
    # slide in/out
    a=min(1,t/0.3,(4.0-t)/0.3);off=int((1-a)*-(W+40)) if t<0.3 else (int((1-a)*-(W+40)) if t>3.7 else 0)
    fr=Image.new('RGBA',(W,H),(0,0,0,0));fr.alpha_composite(im,(off,0)) if off>-W else None
    fr.save(f'sub/{i:03d}.png')
