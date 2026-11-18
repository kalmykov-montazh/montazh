# Тело перезапуска 66 «Эвакуатор под окном» (18.11.2026): голос из TikTok-версии 20.08 (11.6–73.5 с),
# картинка — чистые клипы 18–19.08.2025 из архива Google Фото, субтитры по словам (ASS), плашки, тёплый цвет.
import json, subprocess, sys, numpy as np
from faster_whisper import WhisperModel
A0, A1 = 11.6, 73.55
sh = lambda *a: subprocess.run(list(a), check=True)
sh("ffmpeg","-nostdin","-v","error","-y","-ss",str(A0),"-to",str(A1),"-i","t/66.mp4","-vn","-ac","2","-ar","48000","voice.wav")
sh("ffmpeg","-nostdin","-v","error","-y","-i","voice.wav","-ac","1","-ar","16000","v16.wav")
m = WhisperModel("medium", device="cpu", compute_type="int8")
a = np.frombuffer(open("v16.wav","rb").read()[44:], dtype=np.int16).astype(np.float32)/32768
W = []
for s in m.transcribe(a, language="ru", word_timestamps=True, beam_size=5)[0]:
    for w in s.words: W.append(dict(w=w.word.strip(), s=w.start, e=w.end))
FIX = {"клютанциям":"квитанциям","клютанциям,":"квитанциям,","по":"по","штраф":"штраф"}
for w in W:
    k = w["w"].lower()
    if k in FIX: w["w"] = FIX[k]
cut = next((w["s"]-0.05 for w in W if w["w"].lower().startswith("поставьте")), None)
if cut:
    W = [w for w in W if w["e"] <= cut]
    sh("ffmpeg","-nostdin","-v","error","-y","-i","voice.wav","-t",f"{cut+0.25:.3f}","-af","afade=t=out:st=%.3f:d=0.2"%(cut+0.05),"voice2.wav")
    import os; os.replace("voice2.wav","voice.wav")
json.dump(W, open("words66.json","w"), ensure_ascii=False)
D = (cut+0.25) if cut else (A1 - A0)
print("слов", len(W), "длина", round(D,2)); print(" ".join(w["w"] for w in W))
def at(word, after=0):
    for w in W:
        if w["s"] >= after and w["w"].lower().strip(".,!?").startswith(word): return w["s"]
    return None
# клипы: (файл, начало, длительность до следующей точки)
t1 = at("если", 20) or 22.8          # «Если же водитель не появился»
t2 = at("бордюре", t1) or 29.0        # наклейки
t3 = at("почему", t2) or 36.1         # «Почему здесь запрещена парковка»
t4 = at("знак", t3+5) or 52.0         # «вот такой знак»
plan = [("20250818_160751", 0.5, 11.5), ("20250818_161540", 0.0, t1-11.5),
        ("20250818_161540", 17.5, t2-t1-0.3), ("20250818_163542", 0.0, None), ("20250818_164543", 0.0, None), ("20250819_000747", 0.0, None)]
dur = [11.5, t1-11.5, t2-0.3-t1, min(6.2, t3-(t2-0.3)), None, None]
rest = t3 - (t2-0.3) - dur[3]
segs = []
segs.append(("20250818_160751", 0.5, 11.5)); segs.append(("20250818_161540", 0.0, t1-11.5))
segs.append(("20250818_161540", 17.0, (t2-0.3)-t1))
s4 = t3-(t2-0.3)
segs.append(("20250818_163542", 0.0, min(6.2, s4)))
if s4 > 6.2: segs.append(("20250818_164543", 9.5, s4-6.2))
segs.append(("20250818_164543", 0.0, min(13.2, t4-t3)))
if t4-t3 > 13.2: segs.append(("20250819_000747", 6.0, t4-t3-13.2))
segs.append(("20250819_000747", 0.0, D-t4))
VF = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,"
      "eq=saturation=1.08:contrast=1.04,colorbalance=rs=0.04:gs=0.01:bs=-0.04")
parts = []
for i,(f,ss,d) in enumerate(segs):
    o=f"s{i}.mp4"; parts.append(o)
    sh("ffmpeg","-nostdin","-v","error","-y","-ss",f"{ss:.2f}","-i",f"src/{f}.mp4","-t",f"{d:.3f}","-an","-vf",VF,"-c:v","libx264","-crf","18","-preset","veryfast",o)
open("cat.txt","w").write("".join(f"file '{p}'\n" for p in parts))
sh("ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i","cat.txt","-c","copy","pic.mp4")
print("куски:", [(f, round(ss,2), round(d,2)) for f,ss,d in segs])
# субтитры: группы по 2–3 слова, текущее слово жёлтым
def ts(t): h=int(t//3600); m_=int(t%3600//60); s=t%60; return f"{h}:{m_:02d}:{s:05.2f}"
L = ["[Script Info]","PlayResX: 1080","PlayResY: 1920","[V4+ Styles]",
 "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
 "Style: S,Montserrat Black,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,6,2,2,60,60,520,1",
 "Style: P,Montserrat Black,58,&H00101010,&H00101010,&H0000D7FF,&H0000D7FF,1,0,0,0,100,100,0,0,3,18,0,8,80,80,260,1",
 "[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
G=[]; cur=[]
for w in W:
    cur.append(w)
    if len(cur)==3 or w["w"].endswith((".",",","?","!")): G.append(cur); cur=[]
if cur: G.append(cur)
for g in G:
    for j,w in enumerate(g):
        e = g[j+1]["s"] if j+1<len(g) else w["e"]+0.15
        txt=" ".join(("{\\c&H00D7FF&}"+x["w"].upper()+"{\\c&HFFFFFF&}") if k==j else x["w"].upper() for k,x in enumerate(g))
        L.append(f"Dialogue: 0,{ts(w['s'])},{ts(e)},S,,0,0,0,,{txt}")
PL=[("приезжает",None,"ПОЛИЦИЯ + ЭВАКУАТОР"),("оплачивал","штраф","ПРИШЁЛ ВОВРЕМЯ —\\NШТРАФ И ЭВАКУАТОР НА МЕСТЕ"),
    ("наклейки",None,"ИЩИТЕ НАКЛЕЙКУ\\NНА БОРДЮРЕ"),("разметку",None,"СМОТРИТЕ РАЗМЕТКУ\\NИ ЗНАКИ"),("полиции",None,"ПАРКОВКА\\NТОЛЬКО ДЛЯ ПОЛИЦИИ")]
for wd,_,txt in PL:
    s=at(wd) 
    if s is None: continue
    L.append(f"Dialogue: 1,{ts(s)},{ts(min(D,s+3.2))},P,,0,0,0,,{{\\fad(150,150)}}{txt}")
open("subs66.ass","w").write("\n".join(L)+"\n")
sh("ffmpeg","-nostdin","-v","error","-y","-i","pic.mp4","-i","voice.wav","-filter_complex",
   "[0:v]ass=subs66.ass:fontsdir=fonts[v];[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]","-map","[v]","-map","[a]",
   "-c:v","libx264","-crf","17","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest","body66.mp4")
