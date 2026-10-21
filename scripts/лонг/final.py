import json,subprocess
Hs=12.2+74/60
W=[(16.0,27.4,'Все пути от защиты к ВНЖ'),
(58.3,77.1,'Защита держится только на войне'),
(93.3,106.9,'Не ждите конца защиты'),
(139.7,149.9,'Годы на защите не сгорают'),
(168.2,181.9,'Не отказывайтесь от защиты до одобрения ВНЖ'),
(204.9,215.1,'Иногда лучше дотянуть до года'),
(294.6,304.6,'Месяц-два до года — лучше подождать'),
(349.6,357.8,'Слабый контракт — частая причина отказа'),
(381.3,402.5,'Аутонома только на бумаге не пройдёт'),
(423.7,442.6,'Арраиго — запасная дверь на 1 год'),
(518.1,531.4,'Детям ВНЖ можно оформить в любой момент'),
(571.2,595.5,'Справка о несудимости из всех стран за 5 лет'),
(619.7,630.0,'Сохраняйте билеты и посадочные талоны'),
(674.1,684.6,'Дальше 5 ошибок, на которых теряют время'),
(714.2,722.7,'Гарантий не даёт никто'),
(730.1,760.3,'Мой путь: аутонома и ВНЖ на 4 года'),
(777.7,780.0,None)]
tot=sum(b-a for a,b,_ in W);print('camera share',tot/779)
en='+'.join(f'between(t,{a+Hs:.2f},{b+Hs:.2f})' for a,b,_ in W)
F='/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
fc=f"[0:v]split[m][c];[c]crop=630:354:1289:660,scale=1920:1080:flags=lanczos,unsharp=5:5:0.4[cz];[m][cz]overlay=0:0:enable='{en}'"
for i,(a,b,t) in enumerate(W):
    if not t: continue
    open(f'txt/p{i}.txt','w').write(t)
    fc+=f",drawtext=fontfile={F}:textfile=txt/p{i}.txt:fontsize=56:fontcolor=white:box=1:boxcolor=0x0D192B@0.88:boxborderw=30:x=(w-tw)/2:y=h-190:enable='between(t,{a+Hs+0.8:.2f},{b+Hs-0.4:.2f})'"
fc+="[v1]"
fc+=f";[1:v]setpts=PTS+{107.5+Hs:.3f}/TB[s1];[2:v]setpts=PTS+{697.0+Hs:.3f}/TB[s2]"
fc+=";[v1][s1]overlay=60:H-300:eof_action=pass[v2];[v2][s2]overlay=60:H-300:eof_action=pass,setpts=PTS/1.2,fps=60,format=yuv420p,setsar=1[vb]"
fc+=";[3:a]atempo=1.2[ab]"
fc+=";[4:v]fps=60,format=yuv420p,fade=t=in:st=0:d=0.4,setsar=1[ve];anullsrc=r=48000:cl=stereo,atrim=0:12[ae]"
fc+=";[vb][ab][ve][ae]concat=n=2:v=1:a=1[v][a]"
cmd=['ffmpeg','-v','error','-y','-i','vcat3.mp4','-i','sub.mov','-i','sub.mov','-i','final_norm.wav','-loop','1','-t','12','-framerate','60','-i','endcard.png',
     '-filter_complex',fc,'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','20','-c:a','aac','-b:a','192k','-movflags','+faststart','final.mp4']
open('final_cmd.txt','w').write(fc)
r=subprocess.run(cmd,capture_output=True,text=True);print(r.returncode,r.stderr[-800:])
