import json,subprocess
P=json.load(open('plan.json'));W=P['W'];SUB=P['SUB']
F='/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
en='+'.join(f'between(t,{a:.3f},{b:.3f})' for a,b,_ in W)
CW=json.load(open('cw.json'))
fc='';last='2:v'
for k,(o,st) in enumerate(CW):
    fc+=f"[{8+k}:v]setpts=PTS+{st:.4f}/TB[c{k}];[{last}][c{k}]overlay=0:0:eof_action=pass[o{k}];"
    last=f'o{k}'
fc+=f"[{last}]null"
for i,(a,b,t) in enumerate(W):
    if not t: continue
    open(f'txt/p{i}.txt','w').write(t)
    fc+=f",drawtext=expansion=none:fontfile={F}:textfile=txt/p{i}.txt:fontsize=56:fontcolor=white:box=1:boxcolor=0x0D192B@0.88:boxborderw=30:x=(w-tw)/2:y=h-190:enable='between(t,{a+0.8:.3f},{b-0.4:.3f})'"
fc+="[v1]"
last='v1'
for k,s in enumerate(SUB):
    fc+=f";[{3+k}:v]setpts=PTS+{s:.3f}/TB[s{k}];[{last}][s{k}]overlay=60:H-300:eof_action=pass[w{k}]";last=f'w{k}'
fc+=f";[0:v][1:v][{last}]concat=n=3:v=1:a=0,setpts=PTS/1.2,fps=60,format=yuv420p,setsar=1[vb]"
fc+=";[6:a]atempo=1.2[ab]"
fc+=";[7:v]fps=60,format=yuv420p,fade=t=in:st=0:d=0.4,setsar=1[ve];anullsrc=r=48000:cl=stereo,atrim=0:12[ae]"
fc+=";[vb][ab][ve][ae]concat=n=2:v=1:a=1[v][a]"
open('final_fc.txt','w').write(fc)
cmd=['ffmpeg','-v','error','-y','-i','hook.mp4','-i','rw.mp4','-i','body.mp4','-i','sub.mov','-i','sub.mov','-i','sub.mov','-i','final_norm.wav',
     '-loop','1','-t','12','-framerate','60','-i','endcard.png']+sum([['-i',o] for o,_ in CW],[])+['-filter_complex_script','final_fc.txt','-map','[v]','-map','[a]',
     '-c:v','libx264','-preset','veryfast','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart','final.mp4']
r=subprocess.run(cmd,capture_output=True,text=True);print(r.returncode,r.stderr[-1500:])
