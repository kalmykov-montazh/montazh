import json,subprocess
P=json.load(open('plan.json'))
v=open('hook_vf.txt').read()
v=v.split("setpts=N/60/TB,",1)[1].replace('drawtext=','drawtext=expansion=none:')
open('hook_vf2.txt','w').write(v)
fs=[]
for k,(s,e) in enumerate(P['hook']):
    a=(round(s*60)-3)/60;n=round(e*60)-round(s*60)
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{a-2:.4f}','-i','cam.mp4','-ss','2','-frames:v',str(n),'-an','-r','60','-c:v','libx264','-preset','veryfast','-crf','14',f'h{k}.mp4'],check=True);fs.append(f"file 'h{k}.mp4'\n")
open('h.txt','w').write(''.join(fs))
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-i','h.txt','-filter_script:v','hook_vf2.txt','-an','-r','60','-c:v','libx264','-preset','veryfast','-crf','16','hook.mp4'],check=True)
r=open('rw_vf.txt').read().replace('drawtext=','drawtext=expansion=none:')
subprocess.run(['ffmpeg','-v','error','-y','-i','hook.mp4','-vf',r,'-an','-r','60','-c:v','libx264','-preset','veryfast','-crf','16','rw.mp4'],check=True)
