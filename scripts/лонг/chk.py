import json,subprocess,sys
from pywhispercpp.model import Model
E=json.load(open('edlq.json'));t=0;m=[]
for k in ('hook','body'):
  for s,e in E[k]: m.append((t,s,e,k));t+=e-s
def o(src):
  for ot,s,e,k in m:
    if k=='body' and s<=src<=e: return ot+src-s
  for ot,s,e,k in m:
    if k=='body' and s>src: return ot
M=Model('model.bin',n_threads=2,print_progress=False,print_realtime=False,redirect_whispercpp_logs_to=None)
for name,a,b in [(str(v),o(v)-6,o(v)+5) for v in (176.2,369.5,397,406,445,597,606.6)]:
  subprocess.run(['ffmpeg','-v','error','-y','-ss',str(a),'-to',str(b),'-i','cut.wav','-ar','16000','-ac','1','k.wav'],check=True)
  print(name,round(a,1),'|',' '.join(s.text for s in M.transcribe('k.wav',language='ru')),flush=True)
