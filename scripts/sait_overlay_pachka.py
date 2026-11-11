# 11.11.2026: пачка окошек сайта в готовые ролики из «Готовых» (запуск через ves-bash.yml, JOBS — список в JSON, OUTDIR=REPLACE — замена с бэкапом в «Брокер/Бэкап/До окошка сайта 11.11»)
import subprocess, os, json
G = "ves:Монтаж!/Брокер/Готовые/Шортсы"
OUT = os.environ.get("OUTDIR", "")
JOBS = json.loads(os.environ["JOBS"])
os.makedirs("pics", exist_ok=True)
for i, j in enumerate(JOBS, 1):
    v = f"o{i}"; os.makedirs(v, exist_ok=True)
    subprocess.run(["rclone", "copy", (f"ves:Монтаж!/Брокер/Бэкап/До окошка сайта 11.11/{j['d']}" if j.get("from_backup") else f"{G}/{j['d']}"), v, "--include", "!!!*.mp4"])
    fs = [x for x in os.listdir(v) if x.endswith(".mp4")]
    if not fs: print("НЕТ ВИДЕО", j["d"]); continue
    src = f"{v}/{fs[0]}"; dst = f"{v}/new.mp4"
    r = subprocess.run(["python3", "scripts/sait_overlay.py", src, dst, j["img"], j["text"], str(j["t"]), str(j.get("top", 200)), str(j.get("h", 300)), str(j.get("dur", 3.6))], capture_output=True, text=True)
    print(i, j["d"], r.stdout.strip(), r.stderr.strip()[-300:])
    if r.returncode: continue
    t = j["t"]
    for k, x in enumerate([t - 0.3, t + 0.1, t + 0.6, t + 2.0, t + 3.4, t + 3.8]):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0,x):.2f}", "-i", dst, "-frames:v", "1", "-vf", "scale=270:-2", f"{v}/k{k}.jpg"])
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + sum([["-i", f"{v}/k{k}.jpg"] for k in range(6)], []) + ["-filter_complex", "hstack=6", f"pics/{i}.jpg"])
    a = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
    b = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst], capture_output=True, text=True).stdout.strip()
    print("   длина было/стало:", a, b)
    if OUT == "REPLACE":
        bk = f"ves:Монтаж!/Брокер/Бэкап/До окошка сайта 11.11/{j['d']}/{fs[0]}"
        r1 = subprocess.run(["rclone", "copyto", f"{G}/{j['d']}/{fs[0]}", bk]) if not j.get("from_backup") else subprocess.CompletedProcess([], 0)
        if r1.returncode: print("   БЭКАП НЕ ВЫШЕЛ — не заменяю"); continue
        r2 = subprocess.run(["rclone", "copyto", dst, f"{G}/{j['d']}/{fs[0]}"])
        print("   заменён в «Готовых», оригинал в бэкапе" if not r2.returncode else "   ЗАМЕНА НЕ ВЫШЛА")
    elif OUT:
        name = os.path.basename(j["d"])
        subprocess.run(["rclone", "copyto", dst, f"ves:Монтаж!/Брокер/{OUT}/{name}.mp4"]); print("   залит в", OUT)
