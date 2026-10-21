import json,os,re,subprocess
from pywhispercpp.model import Model
dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0','a.wav'],capture_output=True,text=True).stdout)
log=subprocess.run(['ffmpeg','-i','a.wav','-af','silencedetect=noise=-45dB:d=0.3','-f','null','-'],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',log)];en=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',log)]
sil=list(zip(st,en+[dur]*(len(st)-len(en))))
ch=[];cur=0.0
for a,b in sil:
    if a-cur>0.12: ch.append([cur,a])
    cur=b
if dur-cur>0.12: ch.append([cur,dur])
# merge chunks into <=25s groups for context, split long ones? keep as is
json.dump(ch,open('chunks.json','w'))
m=Model('model.bin',n_threads=2,print_progress=False,print_realtime=False,redirect_whispercpp_logs_to=None)
P='Временная защита в Испании, ВНЖ, ПМЖ, арраиго, NIE, Валенсия, юристы.'
cache=json.load(open('asr.json')) if os.path.exists('asr.json') else {}
prev=''
for i,(a,b) in enumerate(ch):
    k=f'{a:.3f}-{b:.3f}'
    if k in cache: prev=' '.join(w for *_,w in cache[k]);continue
    A=max(0,a-0.05);B=min(dur,b+0.1)
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{A:.3f}','-to',f'{B:.3f}','-i','a.wav','-af','apad=pad_dur=0.4','c.wav'],check=True)
    segs=m.transcribe('c.wav',language='ru',token_timestamps=True,max_len=1,split_on_word=True,initial_prompt=(P+' '+prev)[-200:])
    ws=[(A+s.t0/100,A+s.t1/100,s.text.strip()) for s in segs if s.text.strip()]
    cache[k]=ws; json.dump(cache,open('asr.json','w'),ensure_ascii=False)
    prev=' '.join(w for *_,w in ws)
    print(i,len(ch),f'{a:.1f}',prev,flush=True)
print('DONE',flush=True)
