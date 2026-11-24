# 24.11.2026 (Евгений, 01:45: «лицо с закрытыми глазами… рот открытый… глаза открытые максимально нормально,
# рот максимально закрыт, может быть легонечко приоткрыт»). Строгий выбор кадра для обложки.
# Точки лица — 106 точек (scripts/2d106det.onnx, onnxruntime) по кадру в полном размере: LBF из pick_frame
# на губах ошибается (говорящий рот считал закрытым). Проверено 24.11 на 201 обложке против разметки глазами.
# Берём кадр, если и он, и соседние ±0,2 с спокойные: глаза открыты, рот закрыт (не на полуслове и не моргнул).
#   python3 scripts/kadr_glaza.py video.mp4 [--top N] [--from S] [--to S] > кадры.txt
# Вывод: «секунда глаза рот_внутри рот_снаружи резкость», лучшие первыми.
# Пороги (по разметке 24.11): глаза ≥ 0,28 и не ниже медианы ролика −0,03; рот внутри ≤ 0,030, снаружи ≤ 0,355.
import sys, os, subprocess, numpy as np, cv2
a = sys.argv[1:]; v = a[0]
def arg(k, d):
    return type(d)(a[a.index(k) + 1]) if k in a else d
TOP, T0, T1 = arg("--top", 8), arg("--from", 0.6), arg("--to", 1e9)
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D); from lico106 import landmarks, metr
hx = os.environ.get("HAAR") or os.path.join(D, "haar.xml")
fc = cv2.CascadeClassifier(hx)
FPS = 5
trc = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'stream=color_transfer', '-of', 'csv=p=0', v],
                     capture_output=True, text=True).stdout.strip().strip(',').split(',')[0]
TM = 'zscale=t=linear:npl=80,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,' if trc in ('arib-std-b67', 'smpte2084') else ''
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(T0), '-i', v, '-vf', f'fps={FPS},{TM}scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920',
                      '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
SZ = 1080 * 1920 * 3
res = []; n = 0
while True:
    b = p.stdout.read(SZ)
    if len(b) < SZ: break
    t = T0 + n / FPS; n += 1
    if t > T1: continue
    im = np.frombuffer(b, np.uint8).reshape(1920, 1080, 3)
    sm = cv2.cvtColor(cv2.resize(im, (540, 960)), cv2.COLOR_BGR2GRAY)
    f = fc.detectMultiScale(sm, 1.1, 5, minSize=(45, 45))
    if not len(f): res.append((t, None)); continue
    x, y, w, h = [int(c * 2) for c in max(f, key=lambda r: r[2] * r[3])]
    P = landmarks(im, (x, y, w, h)); emin, eavg, mi, mo = metr(P)
    g = cv2.cvtColor(im[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
    sharp = cv2.Laplacian(g, cv2.CV_64F).var()
    res.append((t, (emin, mi, mo, sharp, w)))
p.wait()
ok = [r for r in res if r[1]]
if not ok: print("лица нет", file=sys.stderr); sys.exit(2)
med = float(np.median([r[1][0] for r in ok]))
def good(i, soft=False):
    r = res[i]
    if r[1] is None: return False
    e, mi, mo = r[1][:3]
    if soft: return e >= max(0.25, med - 0.06) and mi <= 0.05 and mo <= 0.40
    return e >= max(0.28, med - 0.03) and mi <= 0.030 and mo <= 0.355
cands = []
for i, r in enumerate(res):
    if not good(i): continue
    nb = [j for j in (i - 1, i + 1) if 0 <= j < len(res)]
    if not all(good(j, True) for j in nb): continue
    e, mi, mo, sh, w = r[1]
    sc = min(sh, 300) / 100 - abs(e - (med + 0.02)) * 30 - mi * 150 - mo * 25 + w / 500   # рот важнее всего
    cands.append((sc, r[0], e, mi, mo, sh))
cands.sort(reverse=True); pick = []
for c in cands:
    if all(abs(c[1] - q[1]) >= 1.0 for q in pick): pick.append(c)
    if len(pick) == TOP: break
print(f"кадров с лицом {len(ok)}/{len(res)}, медиана глаз {med:.3f}, подходящих {len(cands)}", file=sys.stderr)
if not pick:   # строгих нет — самый закрытый рот при открытых глазах
    ok.sort(key=lambda r: r[1][1] * 4 + r[1][2] - r[1][0] * 2)
    pick = [(0, r[0], r[1][0], r[1][1], r[1][2], r[1][3]) for r in ok[:TOP]]
    print("строгих нет — взял самые закрытые рты", file=sys.stderr)
for c in pick: print(f"{c[1]:.2f} {c[2]:.3f} {c[3]:.3f} {c[4]:.3f} {c[5]:.0f}")
