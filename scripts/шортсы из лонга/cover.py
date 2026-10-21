import json, subprocess, layout
S = {x['id']: x for x in json.load(open('shorts.json'))}
T = {'01': 147.46, '02': 129.22, '03': 235.61, '04': 284.71, '05': 334.95, '06': 443.17, '07': 471.96, '08': 517.71, '09': 589.02}
for k, t in T.items():
    sh = S[k]
    ev = []
    for i, ln in enumerate(sh['title']):
        st = 'TitleW' if ln == sh['hl'] else 'TitleY'
        z = min(100, int(1750 / len(ln))) if len(ln) > 17 else 100
        ev.append(f'Dialogue: 0,0:00:00.00,0:00:05.00,{st},,0,0,0,,' + r'{\an8\pos(540,' + str(360 + i * 140) + r')\fscx' + str(z) + r'\fscy' + str(z) + '}' + ln)
    ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitleY,Inter Black,96,&H000C0C0C,&H000C0C0C,&H0000D6FF,&H0000D6FF,0,0,0,0,100,100,0,0,3,22,0,8,30,30,0,1
Style: TitleW,Inter Black,96,&H000C0C0C,&H000C0C0C,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,3,22,0,8,30,30,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + '\n'.join(ev) + '\n'
    open(f'w/{k}/cover.ass', 'w').write(ass)
    SLF, OH = layout.slide(k)
    vf = (f"[0:v]setpts=PTS-STARTPTS,split=2[s][b];[b]scale=1080:1920,drawbox=c=0x0E1A2A:t=fill[bg];[s]{SLF}[sl];"
          f"[1:v]setpts=PTS-STARTPTS,scale=1080:660:flags=lanczos,unsharp=5:5:0.5:5:5:0[cm];"
          f"[bg][sl]overlay=0:300[t1];[t1][cm]overlay=0:{300+OH+6},subtitles=w/{k}/cover.ass[v]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', 'src.mp4', '-ss', f"{t - sh['seg'][0]:.3f}", '-i', f'/home/claude/bg/cams/{k}.mp4', '-filter_complex', vf, '-map', '[v]', '-frames:v', '1', '-q:v', '1', f'w/{k}/обложка.jpg'], check=True)
    print(k)
