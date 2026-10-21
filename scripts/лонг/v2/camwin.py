import json,subprocess
P=json.load(open('plan.json'));body=P['body']
fr=[]
for s,e in body: fr.extend(range(round(s*60),round(e*60)))
print('body frames',len(fr),flush=True)
outs=[]
for k,(a,b,t) in enumerate(P['W']):
    A=round(a*60);B=min(round(b*60),len(fr))
    raws=fr[A:B]; r0=raws[0]-3; base=max(0,r0-120)
    rel=[x-3-base for x in raws]
    rg=[];st=rel[0];pv=rel[0]
    for x in rel[1:]:
        if x!=pv+1: rg.append((st,pv));st=x
        pv=x
    rg.append((st,pv))
    sel='+'.join(f'between(n,{x},{y})' for x,y in rg)
    o=f'cw{k}.mp4';outs.append((o,A/60))
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{base/60:.4f}','-t',f'{(rel[-1]+10)/60:.3f}','-i','cam.mp4','-vf',f"select='{sel}',setpts=N/60/TB",'-an','-r','60','-c:v','libx264','-preset','veryfast','-crf','16',o],check=True)
    n=int(subprocess.run(['ffprobe','-v','error','-count_frames','-show_entries','stream=nb_read_frames','-of','csv=p=0',o],capture_output=True,text=True).stdout)
    print(k,len(raws),n,flush=True)
json.dump(outs,open('cw.json','w'))
