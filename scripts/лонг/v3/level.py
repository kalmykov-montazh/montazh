# Выравнивание громкости по времени (после aud.py, до aud2.py): cut2.wav -> cut2.wav
import numpy as np,wave,subprocess,re,json,shutil
shutil.copy('cut2.wav','cut2_orig.wav')
w=wave.open('cut2_orig.wav');SR=w.getframerate();N=w.getnframes();B=SR//2
db=[]
for i in range(N//B):
    a=np.frombuffer(w.readframes(B),np.int16).reshape(-1,2).astype(np.float32).mean(1)/32768
    db.append(20*np.log10(np.sqrt((a**2).mean())+1e-6))
db=np.array(db);n=len(db);act=db>db.max()-30
L=np.array([np.median(db[max(0,i-60):i+60][act[max(0,i-60):i+60]]) if act[max(0,i-60):i+60].any() else np.nan for i in range(n)])
L=np.where(np.isnan(L),np.nanmedian(L),L);ref=np.median(L)
g=np.clip(ref-L,-4,4);g=np.convolve(np.pad(g,40,mode='edge'),np.ones(81)/81,'valid')
w.rewind();o=wave.open('cut3.wav','wb');o.setnchannels(2);o.setsampwidth(2);o.setframerate(SR)
tc=(np.arange(n)+0.5)*B/SR;pos=0;C=SR*30
while pos<N:
    a=np.frombuffer(w.readframes(C),np.int16).reshape(-1,2).astype(np.float32)
    t=(pos+np.arange(len(a)))/SR;gc=10**(np.interp(t,tc,g)/20)
    o.writeframes(np.clip(a*gc[:,None],-32768,32767).astype(np.int16).tobytes());pos+=len(a)
o.close()
r=subprocess.run(['ffmpeg','-i','cut3.wav','-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
j=json.loads(re.findall(r'\{[^{}]*\}',r)[-1])
ln=f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
subprocess.run(['ffmpeg','-v','error','-y','-i','cut3.wav','-af',ln,'-ar','48000','cut2.wav'],check=True)
print('gain',g.min().round(2),g.max().round(2))
# дальше: python3 aud2.py && ffmpeg -i mix.wav -af alimiter=limit=0.79:level=false final_norm.wav
