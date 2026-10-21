import json,subprocess,os
P=json.load(open('plan.json'));W=P['W'];SUB=P['SUB']
F='/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
NB=int(subprocess.run(['ffprobe','-v','error','-count_packets','-show_entries','stream=nb_read_packets','-of','csv=p=0','body.mp4'],capture_output=True,text=True).stdout)
enc=['-an','-r','60','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p']
lst=[];prev=0
def run(c): subprocess.run(['ffmpeg','-v','error','-y']+c,check=True)
for k,(a,b,t) in enumerate(W):
    A=round(a*60);B=min(round(b*60),NB)
    if A>prev:
        o=f'seg/s{k:02d}.mp4'
        if not os.path.exists(o): run(['-ss',f'{prev/60:.4f}','-i','body.mp4','-frames:v',str(A-prev)]+enc+[o])
        lst.append(o)
    o=f'seg/c{k:02d}.mp4';n=B-A;L=n/60
    vf='setpts=N/60/TB'
    if t:
        open(f'txt/p{k}.txt','w').write(t)
        vf+=f",drawtext=expansion=none:fontfile={F}:textfile=txt/p{k}.txt:fontsize=56:fontcolor=white:box=1:boxcolor=0x0D192B@0.88:boxborderw=30:x=(w-tw)/2:y=h-190:enable='between(t,0.8,{L-0.4:.3f})'"
    if not os.path.exists(o): run(['-i',f'cw{k}.mp4','-frames:v',str(n),'-vf',vf]+enc+[o])
    lst.append(o);prev=B;print(k,flush=True)
if prev<NB:
    o='seg/zend.mp4';run(['-ss',f'{prev/60:.4f}','-i','body.mp4','-frames:v',str(NB-prev)]+enc+[o]);lst.append(o)
open('seg.txt','w').write(''.join(f"file '{x}'\n" for x in lst))
run(['-f','concat','-safe','0','-i','seg.txt','-c','copy','bodyc.mp4'])
fc='[2:v]null[v0]';last='v0'
for k,s in enumerate(SUB):
    fc+=f";[{3+k}:v]setpts=PTS+{s:.3f}/TB[s{k}];[{last}][s{k}]overlay=60:H-300:eof_action=pass[w{k}]";last=f'w{k}'
fc+=f";[0:v][1:v][{last}]concat=n=3:v=1:a=0,setpts=PTS/1.2,fps=60,format=yuv420p,setsar=1[vb]"
fc+=";[7:a]atempo=1.2[ab];[8:v]fps=60,format=yuv420p,fade=t=in:st=0:d=0.4,setsar=1[ve];anullsrc=r=48000:cl=stereo,atrim=0:12[ae];[vb][ab][ve][ae]concat=n=2:v=1:a=1[v][a]"
open('final_fc.txt','w').write(fc)
run(['-i','hook.mp4','-i','rw.mp4','-i','bodyc.mp4']+sum([['-i','sub.mov'] for _ in SUB],[])+['-i','final_norm.wav','-loop','1','-t','12','-framerate','60','-i','endcard.png',
     '-filter_complex_script','final_fc.txt','-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-c:a','aac','-b:a','192k','-movflags','+faststart','final.mp4'])
print('DONE',flush=True)
