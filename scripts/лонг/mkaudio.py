import numpy as np,wave
SR=48000;rng=np.random.default_rng(1)
w=wave.open('cut2.wav');x=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)/32768
H=int(round(12.2*SR));R=int(round(74/60*SR))
def bandsweep(n,f0,f1):
    out=np.zeros(n);hop=512;win=np.hanning(1024)
    noise=rng.standard_normal(n+1024)
    for i in range(0,n,hop):
        seg=noise[i:i+1024]*win;S=np.fft.rfft(seg);fr=np.fft.rfftfreq(1024,1/SR)
        fc=f0*(f1/f0)**(i/n);S*=np.exp(-((np.log(fr+1)-np.log(fc))**2)/0.35)
        y=np.fft.irfft(S);j=min(1024,n-i);out[i:i+j]+=y[:j]
    return out/np.abs(out).max()
def whoosh():
    n=int(0.45*SR);y=bandsweep(n,400,4000);t=np.linspace(0,1,n);env=np.sin(np.pi*t)**2*np.exp(-t)
    return 0.22*y*env
def rewind():
    n=R;t=np.arange(n)/SR;f=900-500*t/ (n/SR)+120*np.sin(2*np.pi*14*t)
    ph=2*np.pi*np.cumsum(f)/SR;tone=(2*((ph/(2*np.pi))%1)-1)*0.35
    y=tone+0.5*bandsweep(n,3000,600);env=np.minimum(1,np.minimum(t/0.05,(n/SR-t)/0.12))
    am=0.7+0.3*np.sign(np.sin(2*np.pi*11*t))
    return 0.2*y*env*am/np.abs(y).max()
def click():
    n=int(0.04*SR);t=np.arange(n)/SR;return 0.35*rng.standard_normal(n)*np.exp(-t*180)
def ding():
    n=int(1.4*SR);t=np.arange(n)/SR
    y=sum(a*np.sin(2*np.pi*f*t)*np.exp(-t*d) for f,a,d in [(1568,1,3),(3136,.45,5),(4704,.2,8),(2093,.3,4)])
    return 0.16*y*np.minimum(1,t/0.004)
def add(buf,pos,s):
    p=int(round(pos*SR));e=min(len(buf),p+len(s));buf[p:e]+=s[:e-p,None]
hook=x[:H].copy();add(hook,3.183-0.25,whoosh());add(hook,6.3-0.25,whoosh())
rw=np.zeros((R,2),np.float32);add(rw,0,rewind())
body=x[H:].copy()
for b in (107.5,697.0):
    add(body,b+0.05,whoosh()*0.6);add(body,b+1.5,click());add(body,b+1.6,ding())
y=np.concatenate([hook,rw,body])
o=wave.open('final_raw.wav','wb');o.setnchannels(2);o.setsampwidth(2);o.setframerate(SR)
o.writeframes((np.clip(y,-1,1)*32767).astype(np.int16).tobytes());o.close();print(len(y)/SR)
