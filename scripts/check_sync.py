import sys, re, subprocess, numpy as np, _pywhispercpp as pw, difflib
VID, ASS, T0, T1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
subprocess.run(['ffmpeg','-v','error','-y','-ss',str(T0),'-to',str(T1),'-i',VID,'-ar','16000','-ac','1','-f','s16le','chk.raw'],check=True)
pcm=np.fromfile('chk.raw',np.int16).astype(np.float32)/32768
cp=pw.whisper_context_default_params(); cp.dtw_token_timestamps=True; cp.flash_attn=False
cp.dtw_aheads_preset=pw.whisper_alignment_heads_preset.WHISPER_AHEADS_SMALL
ctx=pw.whisper_init_from_file_with_params('ggml-small-q8_0.bin',cp)
fp=pw.whisper_full_default_params(pw.WHISPER_SAMPLING_GREEDY); fp.language='ru'; fp.n_threads=2; fp.token_timestamps=True; fp.print_progress=False
pw.whisper_full(ctx,fp,pcm,len(pcm))
heard=[]
for s in range(pw.whisper_full_n_segments(ctx)):
    for t in range(pw.whisper_full_n_tokens(ctx,s)):
        try: txt=pw.whisper_full_get_token_text(ctx,s,t)
        except UnicodeDecodeError: continue
        if txt.startswith('[_') or txt.startswith('<|'): continue
        d=pw.whisper_full_get_token_data(ctx,s,t)
        if txt.startswith(' ') or not heard: heard.append([T0+d.t_dtw/100, txt.strip()])
        else: heard[-1][1]+=txt
def norm(w): return re.sub(r'[^\w]','',w.lower()).replace('ё','е')
# субтитры: момент, когда слово становится жёлтым
subs=[]
for ln in open(ASS):
    if ',Kar,' not in ln: continue
    p=ln.split(',',9); h,m,sec=p[1].split(':'); st=int(h)*3600+int(m)*60+float(sec)
    mm=re.search(r'\\c&H0000E1FF&[^}]*\}([^{]+)\{',p[9])
    if mm and T0<=st<=T1: subs.append([st,mm.group(1).strip()])
a=[norm(x[1]) for x in heard]; b=[norm(x[1]) for x in subs]
diffs=[]; bad=[]
for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
    if tag=='equal':
        for k in range(i2-i1): diffs.append(subs[j1+k][0]-heard[i1+k][0])
    else: bad.append((tag,' '.join(x[1] for x in heard[i1:i2]),' '.join(x[1] for x in subs[j1:j2])))
d=np.array(diffs); print(f'слов совпало {len(d)}, сдвиг субтитров: медиана {np.median(d):+.2f} с, 90% в пределах {np.percentile(abs(d),90):.2f} с, макс {abs(d).max():.2f} с')
for x in bad: print('расхождение:',x)
