# python3 pick_frame.py raw.mp4 out.png  — лучший кадр для обложки: глаза открыты, рот закрыт, резкий
import sys, subprocess, numpy as np, cv2, os, wave
raw, out = sys.argv[1], sys.argv[2]
D = os.path.dirname(os.path.abspath(__file__))
trc = subprocess.run(['ffprobe','-v','error','-select_streams','v','-show_entries','stream=color_transfer','-of','csv=p=0',raw],capture_output=True,text=True).stdout.strip().strip(',').split(',')[0]
TM = ('zscale=t=linear:npl=80,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,') if trc in ('arib-std-b67','smpte2084') else ''
GR = ''
SW, SH = 540, 960; STEP = 0.2
# громкость звука по кадрам: тишина = рот закрыт
subprocess.run(['ffmpeg','-v','error','-y','-i',raw,'-ar','8000','-ac','1','/tmp/pa.wav'],check=True)
w = wave.open('/tmp/pa.wav'); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float)
def rms(t):
    i = int(t*8000); seg = a[max(0,i-400):i+400]; return np.sqrt((seg**2).mean()) if len(seg) else 0
p = subprocess.Popen(['ffmpeg','-v','error','-i',raw,'-vf',f'fps={1/STEP},{TM}{GR}scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH}','-f','rawvideo','-pix_fmt','bgr24','-'],stdout=subprocess.PIPE)
fc = cv2.CascadeClassifier(f'{D}/haar.xml')
fm = cv2.face.createFacemarkLBF(); fm.loadModel(f'{D}/lbf.yaml')
def dist(p, q): return float(np.hypot(*(p - q)))
best = None; n = 0; rmax = max(1, np.percentile(np.abs(a), 99))
while True:
    b = p.stdout.read(SW*SH*3)
    if len(b) < SW*SH*3: break
    t = n*STEP; n += 1
    if t < 0.5: continue
    fr = np.frombuffer(b, np.uint8).reshape(SH, SW, 3); g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    f = fc.detectMultiScale(g, 1.1, 5, minSize=(40,40))   # 04.10.2026: шортсы в полный рост
    if not len(f): continue
    x,y,fw,fh = max(f, key=lambda r: r[2]*r[3])
    ok, lm = fm.fit(g, np.array([[x, y, fw, fh]]))
    if not ok: continue
    P = np.array(lm[0]).reshape(-1, 2)
    ear = np.mean([(dist(P[i+1], P[i+5]) + dist(P[i+2], P[i+4])) / (2 * dist(P[i], P[i+3])) for i in (36, 42)])
    mar = (dist(P[61], P[67]) + dist(P[62], P[66]) + dist(P[63], P[65])) / (3 * dist(P[60], P[64]))
    if ear < 0.22 or mar > 0.06: continue        # глаза прикрыты или рот открыт
    sharp = cv2.Laplacian(g[y:y+fh, x:x+fw], cv2.CV_64F).var()
    loud = rms(t) / rmax
    score = min(sharp, 600) / 150 + ear * 8 - mar * 40 - loud * 2
    dark, eyes = mar, ear
    if best is None or score > best[0]: best = (score, t, dark, loud, sharp)
p.wait()
t = best[1] if best else 1.0
print('cover frame', round(t,2), 'score', [round(v,3) for v in best] if best else None)
# кадр для обложки (с 03.10.2026): мягче перевод HDR (npl=200), чуть контраста и резкости — иначе обложка бледная и мутная
TMC = TM.replace('npl=80', 'npl=250').replace('desat=0', 'desat=2')
subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{t:.2f}','-i',raw,'-frames:v','1','-vf',f'{TMC}scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,eq=contrast=1.06:saturation=1.15,unsharp=5:5:0.5',out],check=True)
