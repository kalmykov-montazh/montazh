import json,numpy as np,wave
ch=json.load(open('chunks.json'))
w=wave.open('a.wav');x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
fr=x[:len(x)//160*160].reshape(-1,160);R=20*np.log10(np.sqrt((fr**2).mean(1))+1e-9)
def snap(t,win=0.12):
    i0=max(0,int((t-win)*100));i1=int((t+win)*100);return (i0+int(np.argmin(R[i0:i1])))/100
DROP={0,1,94,95,99,100,102,103,112,113,114,146,182,183,184,185,186,187}
PL,PR=0.10,0.15
segs=[]
for i,(a,b) in enumerate(ch):
    if i in DROP: continue
    segs.append([a-PL,b+PR])
# word-level cuts
def cut(a,b):
    out=[]
    for s,e in segs:
        if b<=s or a>=e: out.append([s,e]);continue
        if s<a: out.append([s,a])
        if e>b: out.append([b,e])
    segs[:]=out
cut(snap(175.27,0.05),snap(176.24,0.05))
cut(606.40,snap(606.66,0.04))
# merge overlaps
segs.sort();m=[]
for s,e in segs:
    if m and s<=m[-1][1]: m[-1][1]=max(m[-1][1],e)
    else: m.append([s,e])
segs=[[round(s,3),round(e,3)] for s,e in m]
hook=[[snap(198.08,0.08),snap(201.35,0.1)],[snap(399.62,0.08),snap(402.7,0.1)],[snap(699.6,0.1),snap(705.6,0.1)]]
json.dump({'body':segs,'hook':hook},open('edl.json','w'))
print(len(segs),sum(e-s for s,e in segs),hook,sum(e-s for s,e in hook))
