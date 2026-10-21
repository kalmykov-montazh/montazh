import subprocess, sys
sys.path.insert(0, '/home/claude/s'); import layout
A, B, E0, E1 = 429.98, 453.06, 658.30, 659.30
SLF, OH = layout.slide('06'); CAMY = 300 + OH + 6
total = (B - A) + (E1 - E0)
for k in ['blur', 'shelf', 'corner']:
    vf = (f"[0:v]setpts=PTS-STARTPTS[s0];[s0]trim=0:{B-A-1.0:.3f},{SLF},tpad=stop_mode=clone:stop_duration={E1-E0+1.2:.2f}[sl];"
          f"[2:v]setpts=PTS-STARTPTS,scale=1080:660:flags=lanczos,unsharp=5:5:0.5:5:5:0[cm];"
          f"color=c=0x0E1A2A:s=1080x1920:r=60:d={total:.3f}[bg];"
          f"[bg][sl]overlay=0:300:shortest=1[t1];[t1][cm]overlay=0:{CAMY}:shortest=1,subtitles=/home/claude/s/w/06/subs.ass,format=yuv420p[v];"
          f"[0:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={B-A-0.01}:d=0.01[x];[1:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={E1-E0-0.03}:d=0.03[y];[x][y]concat=n=2:v=0:a=1[a]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(A), '-to', str(B), '-i', '/home/claude/s/src.mp4', '-ss', str(E0), '-to', str(E1), '-i', '/home/claude/s/src.mp4',
                    '-i', f'cam_{k}.mp4', '-filter_complex', vf, '-map', '[v]', '-map', '[a]', '-threads', '2',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-profile:v', 'high', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', f'out_{k}.mp4'], check=True)
    print(k, flush=True)
