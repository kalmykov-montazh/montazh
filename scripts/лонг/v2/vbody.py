import json,subprocess,sys
P=json.load(open('plan.json'))
def expr(segs,off):
    return '+'.join(f'between(n,{round(s*60)-off},{round(e*60)-1-off})' for s,e in segs)
open('sel_body.txt','w').write(f"select='{expr(P['body'],0)}',setpts=N/60/TB")
open('sel_cam.txt','w').write(f"select='{expr(P['body'],3)}',setpts=N/60/TB")
j=[]
for src,f,out in (('raw.mp4','sel_body.txt','body.mp4'),('cam.mp4','sel_cam.txt','camb.mp4')):
    j.append(subprocess.Popen(['ffmpeg','-v','error','-y','-i',src,'-filter_script:v',f,'-an','-r','60','-c:v','libx264','-preset','veryfast','-crf','16','-threads','1',out]))
for p in j: print(p.wait())
