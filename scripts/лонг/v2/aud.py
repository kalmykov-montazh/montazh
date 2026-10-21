import json,numpy as np,wave,subprocess,re
P=json.load(open('plan.json'));SR=48000
w=wave.open('a48.wav');x=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)/32768
F=int(0.006*SR);ramp=np.linspace(0,1,F)[:,None]
def piece(s,e):
    p=x[int(round(s*SR)):int(round(e*SR))].copy();p[:F]*=ramp;p[-F:]*=ramp[::-1];return p
y=np.concatenate([piece(s,e) for s,e in P['hook']]+[piece(s,e) for s,e in P['body']])
def wr(fn,a):
    o=wave.open(fn,'wb');o.setnchannels(2);o.setsampwidth(2);o.setframerate(SR);o.writeframes((np.clip(a,-1,1)*32767).astype(np.int16).tobytes());o.close()
wr('cut.wav',y)
# voice chain + loudnorm two-pass
CH='highpass=f=70,equalizer=f=3000:width_type=o:width=1.5:g=2.5,acompressor=threshold=-24dB:ratio=3:attack=10:release=150:makeup=2'
r=subprocess.run(['ffmpeg','-i','cut.wav','-af',CH+',loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
j=json.loads(re.findall(r'\{[^{}]*\}',r)[-1])
ln=f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
subprocess.run(['ffmpeg','-v','error','-y','-i','cut.wav','-af',CH+','+ln,'-ar','48000','cut2.wav'],check=True)
print('voice',j['input_i'],'->-14')
