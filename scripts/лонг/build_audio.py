import json,numpy as np,wave,sys
E=json.load(open('edl.json'))
q=lambda t: round(t*60)/60
for k in E: E[k]=[[q(s),q(e)] for s,e in E[k] if e-s>0.1]
json.dump(E,open('edlq.json','w'))
w=wave.open('a48.wav');x=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)
SR=48000;F=int(0.006*SR);ramp=np.linspace(0,1,F)[:,None]
def piece(s,e):
    p=x[int(round(s*SR)):int(round(e*SR))].copy()
    p[:F]*=ramp;p[-F:]*=ramp[::-1];return p
gap=np.zeros((int(0.25*SR),2),np.float32)
hook=[piece(s,e) for s,e in E['hook']]
out=hook
body=[piece(s,e) for s,e in E['body']]
y=np.concatenate(out+body)
wv=wave.open('cut.wav','wb');wv.setnchannels(2);wv.setsampwidth(2);wv.setframerate(SR)
wv.writeframes(np.clip(y,-32768,32767).astype(np.int16).tobytes());wv.close()
print(len(y)/SR)
