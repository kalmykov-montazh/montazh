#!/usr/bin/env python3
# Шортс из лонга «со сценами v2» (утверждён на «02 Сдаёт не хозяин», 25.10.2026).
# Вход в рабочей папке: base.mp4 + words_out.json (задача 5С), cover.jpg, config.json (сцены ролика).
# 28.10.2026: субтитры — «микс» (белые и жёлтые, по слову), мельче обычных шортсов; тёмная плашка v2 убрана.
# Режимы: info | frames t1 t2 … | audio | render out.mp4 [процессов]
import sys, os, json, math, re, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from snd import snd
from style2 import (W, H, F, BLK, BLD, SB, GOLD, WH, TERRA, G, R, INK, PAPER, glass, sweep, edge_glow, text, kicker,
                    ic_person, ic_key, ic_house, ic_clock, check, cross, badge, nota)

FPS = 30
BASE = "base.mp4"
CFG = json.load(open("config.json"))
COLS = {"G": G, "R": R, "GOLD": GOLD, "TERRA": TERRA, "WH": WH}
def col(c): return COLS.get(c, GOLD) if isinstance(c, str) or c is None else tuple(c)
def ease_back(x):
    x = max(0, min(1, x)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def ease_out(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def clamp(x, a=0, b=1): return max(a, min(b, x))
def warn(s): print(f"::warning::{s}", flush=True)

WORDS = json.load(open("words_out.json"))
def nw(x): return re.sub(r"[^\wё]", "", x.lower()).replace("ё", "е")
LW = [nw(x["w"]) for x in WORDS]
def _match(i, ph):
    for k in range(len(ph)):
        if i + k >= len(LW): return False
        a, b = LW[i + k], ph[k]
        if not b: continue
        n = max(3, len(b) - 2) if len(b) > 3 else len(b)
        if not a.startswith(b[:n]): return False
    return True
def find(phrase, after=0.0):
    ph = [nw(x) for x in phrase.split()]
    for i in range(len(LW)):
        if WORDS[i]["s"] + 0.01 < after: continue
        if _match(i, ph): return i
    return None
def at(phrase, after=0.0):
    i = find(phrase, after)
    return None if i is None else WORDS[i]["s"]
def end_of(phrase, after=0.0):
    i = find(phrase, after)
    if i is None: return None
    return WORDS[min(len(WORDS) - 1, i + len(phrase.split()) - 1)]["e"]

END = WORDS[-1]["e"] + 0.25
COV = 5 / 30
GAP = 0.25
# ---- холодное начало ----
co = CFG.get("cold")
if co:
    a = at(co["from"]); b = end_of(co["to"], a or 0) if a is not None else None
    if a is None or b is None or b <= a or b - a > 6: warn(f"холодное начало не найдено: {co}"); co = None
    else: CO = (a - 0.05, b + 0.05)
if not co: CO = (0.0, 0.0)
CO_LEN = CO[1] - CO[0]
# ---- стоп-кадр ----
fz = CFG.get("freeze"); FRZ = 1.35
SPL = None
if fz:
    SPL = at(fz["before"], fz.get("after", 0.0))
    if SPL is None: warn(f"стоп-кадр не найден: {fz['before']}"); fz = None
    else: SPL -= 0.06
if not fz: SPL = END; FRZ = 0.0
tA = (CO_LEN + GAP) if CO_LEN > 0 else COV
tB = tA + SPL + FRZ
A_END = tB + (END - SPL) if fz else tA + END
ASK = CFG.get("ask")
TT = A_END + (3.6 if ASK else 0.4)
def m(s): return tA + s if s < SPL else tB + (s - SPL)

# ---- фон сцены ----
_bg = {}
def scene_bg(src_t):
    k = round(src_t, 1)
    if k in _bg: return _bg[k]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, src_t):.2f}", "-i", BASE, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    if len(raw) < W * H * 3: raw = b"\x00" * (W * H * 3)
    im = Image.frombytes("RGB", (W, H), raw[:W * H * 3]).resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BICUBIC).convert("RGBA")
    im.alpha_composite(Image.new("RGBA", (W, H), (30, 14, 8, 175)))
    v = Image.new("L", (W // 4, H // 4), 0); ImageDraw.Draw(v).ellipse([-75, 50, W // 4 + 75, H // 4 - 50], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(55)).resize((W, H))
    im = Image.composite(im, Image.new("RGBA", (W, H), (10, 5, 3, 255)), v)
    _bg[k] = im; return im

def pop_layer(dst, layer, u, t_in=0.0, dur=0.3):
    if u < t_in: return
    s = ease_back((u - t_in) / dur); a = clamp((u - t_in) / 0.1)
    bb = layer.getbbox()
    if not bb: return
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    if abs(s - 1) > 0.01:
        L = layer.resize((max(1, int(W * s)), max(1, int(H * s))), Image.BILINEAR)
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); tmp.paste(L, (int(cx - cx * s), int(cy - cy * s))); layer = tmp
    if a < 1: layer = layer.copy(); layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    dst.alpha_composite(layer)

def fit(s, size, maxw, font=BLK):
    while size > 24 and F(size, font).getlength(s) > maxw: size -= 2
    return size
def wtext(dst, xy, s, size, c=WH, font=BLK, u=1, t_in=0.0, maxw=W - 140):
    if u < t_in: return
    size = fit(s, size, maxw, font)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); text(ImageDraw.Draw(L), xy, s, size, c, font); pop_layer(dst, L, u, t_in)
def head(dst, u, kick, title, y=330, size=96):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    if kick: kicker(d, y - 95, kick)
    if title: text(d, (W / 2, y), title, fit(title, size, W - 120), WH)
    pop_layer(dst, L, u, 0)

def ic_doc(d, cx, cy, s, c, w=8):
    d.rounded_rectangle([cx - 0.38 * s, cy - 0.5 * s, cx + 0.38 * s, cy + 0.5 * s], int(0.08 * s), outline=c, width=w)
    for k in range(3): d.line([(cx - 0.22 * s, cy - 0.2 * s + k * 0.2 * s), (cx + 0.22 * s, cy - 0.2 * s + k * 0.2 * s)], fill=c, width=w - 2)
def ic_euro(d, cx, cy, s, c, w=8):
    d.ellipse([cx - 0.5 * s, cy - 0.5 * s, cx + 0.5 * s, cy + 0.5 * s], outline=c, width=w)
    text(d, (cx, cy + 0.02 * s), "€", int(0.62 * s), c, BLK, sh=False)
def ic_bank(d, cx, cy, s, c, w=8):
    d.polygon([(cx - 0.55 * s, cy - 0.25 * s), (cx, cy - 0.6 * s), (cx + 0.55 * s, cy - 0.25 * s)], outline=c, width=w)
    for k in range(4): x = cx - 0.36 * s + k * 0.24 * s; d.line([(x, cy - 0.15 * s), (x, cy + 0.35 * s)], fill=c, width=w)
    d.line([(cx - 0.6 * s, cy + 0.5 * s), (cx + 0.6 * s, cy + 0.5 * s)], fill=c, width=w)
def ic_cal(d, cx, cy, s, c, w=8):
    d.rounded_rectangle([cx - 0.5 * s, cy - 0.4 * s, cx + 0.5 * s, cy + 0.5 * s], int(0.08 * s), outline=c, width=w)
    d.line([(cx - 0.5 * s, cy - 0.12 * s), (cx + 0.5 * s, cy - 0.12 * s)], fill=c, width=w)
    for x in (-0.25, 0.25): d.line([(cx + x * s, cy - 0.55 * s), (cx + x * s, cy - 0.3 * s)], fill=c, width=w)
def ic_tool(d, cx, cy, s, c, w=8):
    d.line([(cx - 0.45 * s, cy + 0.45 * s), (cx + 0.2 * s, cy - 0.2 * s)], fill=c, width=w + 4)
    d.arc([cx + 0.02 * s, cy - 0.58 * s, cx + 0.58 * s, cy - 0.02 * s], 100, 350, fill=c, width=w)
def ic_camera(d, cx, cy, s, c, w=8):
    d.rounded_rectangle([cx - 0.55 * s, cy - 0.3 * s, cx + 0.55 * s, cy + 0.4 * s], int(0.1 * s), outline=c, width=w)
    d.rectangle([cx - 0.2 * s, cy - 0.45 * s, cx + 0.2 * s, cy - 0.3 * s], outline=c, width=w)
    d.ellipse([cx - 0.2 * s, cy - 0.15 * s, cx + 0.2 * s, cy + 0.25 * s], outline=c, width=w)
def ic_door(d, cx, cy, s, c, w=8):
    d.rectangle([cx - 0.32 * s, cy - 0.55 * s, cx + 0.32 * s, cy + 0.55 * s], outline=c, width=w)
    d.ellipse([cx + 0.12 * s, cy - 0.04 * s, cx + 0.22 * s, cy + 0.06 * s], fill=c)
def ic_bolt(d, cx, cy, s, c, w=8):
    d.line([(cx + 0.1 * s, cy - 0.6 * s), (cx - 0.25 * s, cy + 0.05 * s), (cx + 0.2 * s, cy + 0.05 * s), (cx - 0.1 * s, cy + 0.6 * s)], fill=c, width=w, joint="curve")
def ic_drop(d, cx, cy, s, c, w=8):
    d.line([(cx, cy - 0.6 * s), (cx - 0.38 * s, cy + 0.1 * s)], fill=c, width=w); d.line([(cx, cy - 0.6 * s), (cx + 0.38 * s, cy + 0.1 * s)], fill=c, width=w)
    d.arc([cx - 0.4 * s, cy - 0.25 * s, cx + 0.4 * s, cy + 0.55 * s], 0, 180, fill=c, width=w)
def ic_bed(d, cx, cy, s, c, w=8):
    d.line([(cx - 0.6 * s, cy - 0.4 * s), (cx - 0.6 * s, cy + 0.4 * s)], fill=c, width=w)
    d.line([(cx - 0.6 * s, cy + 0.15 * s), (cx + 0.6 * s, cy + 0.15 * s), (cx + 0.6 * s, cy + 0.4 * s)], fill=c, width=w)
    d.rounded_rectangle([cx - 0.5 * s, cy - 0.15 * s, cx - 0.15 * s, cy + 0.08 * s], 8, outline=c, width=w - 2)
def ic_sign(d, cx, cy, s, c, w=8):
    d.line([(cx - 0.5 * s, cy + 0.3 * s), (cx - 0.2 * s, cy), (cx, cy + 0.25 * s), (cx + 0.25 * s, cy - 0.15 * s), (cx + 0.5 * s, cy + 0.2 * s)], fill=c, width=w, joint="curve")
    d.line([(cx - 0.55 * s, cy + 0.5 * s), (cx + 0.55 * s, cy + 0.5 * s)], fill=c, width=w - 3)
def ic_shield(d, cx, cy, s, c, w=8):
    d.line([(cx, cy - 0.6 * s), (cx + 0.5 * s, cy - 0.4 * s), (cx + 0.45 * s, cy + 0.15 * s), (cx, cy + 0.6 * s), (cx - 0.45 * s, cy + 0.15 * s), (cx - 0.5 * s, cy - 0.4 * s), (cx, cy - 0.6 * s)], fill=c, width=w, joint="curve")
def ic_chart(d, cx, cy, s, c, w=8):
    d.line([(cx - 0.55 * s, cy + 0.5 * s), (cx + 0.55 * s, cy + 0.5 * s)], fill=c, width=w)
    d.line([(cx - 0.45 * s, cy + 0.25 * s), (cx - 0.1 * s, cy - 0.05 * s), (cx + 0.1 * s, cy + 0.1 * s), (cx + 0.5 * s, cy - 0.45 * s)], fill=c, width=w, joint="curve")
def ic_ban(d, cx, cy, s, c, w=8):
    d.ellipse([cx - 0.5 * s, cy - 0.5 * s, cx + 0.5 * s, cy + 0.5 * s], outline=c, width=w)
    d.line([(cx - 0.35 * s, cy - 0.35 * s), (cx + 0.35 * s, cy + 0.35 * s)], fill=c, width=w)
def ic_clock0(d, cx, cy, s, c, w=8): ic_clock(d, cx, cy, s * 0.5, c, 2.0, w)
def ic_flame(d, cx, cy, s, c, w=8):
    d.line([(cx, cy - 0.6 * s), (cx + 0.35 * s, cy - 0.05 * s), (cx + 0.3 * s, cy + 0.35 * s), (cx, cy + 0.55 * s), (cx - 0.3 * s, cy + 0.35 * s), (cx - 0.35 * s, cy - 0.05 * s), (cx, cy - 0.6 * s)], fill=c, width=w, joint="curve")
    d.line([(cx, cy + 0.05 * s), (cx + 0.14 * s, cy + 0.3 * s), (cx, cy + 0.45 * s), (cx - 0.14 * s, cy + 0.3 * s), (cx, cy + 0.05 * s)], fill=c, width=w - 3)
ICONS = {"person": ic_person, "key": ic_key, "house": ic_house, "clock": ic_clock0, "doc": ic_doc, "euro": ic_euro, "bank": ic_bank,
         "cal": ic_cal, "tool": ic_tool, "camera": ic_camera, "door": ic_door, "bolt": ic_bolt, "drop": ic_drop, "bed": ic_bed,
         "sign": ic_sign, "flame": ic_flame, "shield": ic_shield, "chart": ic_chart, "ban": ic_ban}
def icon(d, name, cx, cy, s, c=WH):
    f = ICONS.get(name)
    if f: f(d, cx, cy, s, c)

def rel(phrase, t0src, dflt):
    """время от начала сцены до фразы (по исходному времени основы)"""
    if not phrase: return dflt
    a = at(phrase, t0src - 1.0)
    if a is None: warn(f"не нашёл «{phrase}» в сцене"); return dflt
    return max(0.12, m(a) - m(t0src))

# ---------- типы сцен ----------
def s_title(dst, u, t0, sc):
    edge_glow(dst, GOLD, clamp(1 - u / 0.5))
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); kicker(ImageDraw.Draw(L), 560, CFG.get("series", "17 ЛОВУШЕК АРЕНДЫ")); pop_layer(dst, L, u, 0)
    wtext(dst, (W / 2, 720), CFG.get("num", ""), 130, WH, u=u, t_in=0.1)
    if u > 0.35:
        t = CFG["title"]; sz = fit(t, 64, 640)
        bw = F(sz).getlength(t) + 120; box = (int(W / 2 - bw / 2), 840, int(W / 2 + bw / 2), 960)
        glass(dst, box); sweep(dst, box, (u - 0.35) / 0.6)
        text(ImageDraw.Draw(dst), (W / 2, 900), t, sz, GOLD)

def s_cards(dst, u, t0, sc):
    """2–3 карточки в ряд: иконка, подпись, бейдж ✓/✕"""
    edge_glow(dst, col(sc.get("glow", "GOLD")), clamp(1 - u / 0.45))
    head(dst, u, sc.get("kicker"), sc.get("title"), 420, 100)
    its = sc["items"]; n = len(its); gap = 340 if n == 3 else 480; x0 = W / 2 - gap * (n - 1) / 2; hw = 150 if n == 3 else 200
    for i, it in enumerate(its):
        ti = rel(it.get("at"), t0, 0.15 + i * 0.25)
        if u < ti: continue
        cx = x0 + i * gap; k = ease_back((u - ti) / 0.3)
        ok = it.get("ok"); bc = G if ok is True else R if ok is False else GOLD
        bx = (int(cx - hw * k), int(750 - 170 * k), int(cx + hw * k), int(750 + 170 * k))
        if k > 0.3: glass(dst, bx, border=bc)
        if k > 0.8:
            d = ImageDraw.Draw(dst); icon(d, it.get("icon", "person"), cx, 700 if it.get("icon", "person") != "person" else 720, 150, WH)
            lab = it["label"]; text(d, (cx, 870), lab, fit(lab, 36, hw * 2 - 30, BLD), WH, BLD)
            if it.get("sub"): text(d, (cx, 905), it["sub"], fit(it["sub"], 28, hw * 2 - 30, SB), (220, 205, 190), SB)
        if ok is not None and u > ti + 0.45: badge(dst, int(cx + hw - 40), 610, 36, bc, ok)
    if sc.get("note"):
        tn = rel(sc.get("note_at"), t0, 1.6)
        wtext(dst, (W / 2, 1080), sc["note"], 46, col(sc.get("note_col", "GOLD")), SB, u, tn)

def s_list(dst, u, t0, sc):
    """вертикальный список строк в стекле, ✓ / ✕ / цифры"""
    edge_glow(dst, col(sc.get("glow", "GOLD")), clamp(1 - u / 0.45))
    its = sc["items"]; n = len(its)
    step = 150 if n <= 4 else 128 if n <= 5 else 112
    y0 = 1000 - (n - 1) * step / 2 - 60
    head(dst, u, sc.get("kicker"), sc.get("title"), min(380, int(y0 - 150)), 92)
    mode = sc.get("mark", "check")
    for i, it in enumerate(its):
        if isinstance(it, str): it = {"text": it}
        ti = rel(it.get("at"), t0, 0.2 + i * 0.35)
        if u < ti: continue
        y = int(y0 + i * step); k = ease_out((u - ti) / 0.25)
        ok = it.get("ok", True if mode == "check" else None)
        bc = (G if ok else R) if mode in ("check", "mixed") and ok is not None else GOLD
        if mode == "check" and u <= ti + 0.3: bc = GOLD
        hh = int(step * 0.4)
        glass(dst, (int(150 + 300 * (1 - k)), y - hh, 930, y + hh), border=bc)
        if k > 0.9:
            d = ImageDraw.Draw(dst)
            if mode == "num":
                d.ellipse([190, y - 38, 266, y + 38], outline=GOLD, width=5); text(d, (228, y), str(i + 1), 46, GOLD)
                tx0 = 300
            else: tx0 = 200
            t = it["text"]; text(d, (tx0, y), t, fit(t, 54 if step >= 128 else 48, 820 - tx0 - (0 if mode == "num" else 60)), WH, BLK, "lm")
            if mode in ("check", "mixed") and ok is not None and u > ti + 0.15:
                p = clamp((u - ti - 0.15) / 0.3)
                if ok:
                    a = (820, y); b = (850, y + 28); c = (895, y - 30)
                    d.line([a, (a[0] + (b[0] - a[0]) * min(1, p * 2), a[1] + (b[1] - a[1]) * min(1, p * 2))], fill=G, width=12)
                    if p > 0.5: d.line([b, (b[0] + (c[0] - b[0]) * (p - 0.5) * 2, b[1] + (c[1] - b[1]) * (p - 0.5) * 2)], fill=G, width=12)
                elif p > 0.3: cross(d, 860, y, 26, R, 12)
        sweep(dst, (150, y - hh, 930, y + hh), (u - ti - 0.3) / 0.6)
    if sc.get("note"):
        tn = rel(sc.get("note_at"), t0, 2.0)
        wtext(dst, (W / 2, int(y0 + n * step + 10)), sc["note"], 44, col(sc.get("note_col", "GOLD")), SB, u, tn)

def s_number(dst, u, t0, sc):
    """крупная цифра со счётчиком в стеклянной карточке"""
    gl = col(sc.get("glow", "G"))
    edge_glow(dst, gl, clamp(1 - (u - 0.6) / 0.5) if u > 0.6 else 0)
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if sc.get("kicker"): kicker(ImageDraw.Draw(L), 380, sc["kicker"])
    pop_layer(dst, L, u, 0)
    box = (150, 480, 930, 1010); glass(dst, box, border=gl); sweep(dst, box, (u - 0.7) / 0.6)
    v = float(sc["value"]); dec = int(sc.get("dec", 0)); cur = v * ease_out(clamp(u / 0.65)) if sc.get("count", True) else v
    num = f"{cur:,.{dec}f}".replace(",", " ").replace(".", ",") if dec else f"{cur:,.0f}".replace(",", " ")
    s = f"{sc.get('pre', '')}{num}{sc.get('suf', '')}"
    d = ImageDraw.Draw(dst); text(d, (W / 2, 690), s, fit(s, 200, 720), col(sc.get("color", "GOLD")))
    if sc.get("sub") and u > 0.8:
        d.line([(300, 820), (780, 820)], fill=(255, 255, 255, 90), width=2)
        wtext(dst, (W / 2, 900), sc["sub"], 50, WH, BLD, u, 0.8, maxw=720)
    if sc.get("note"):
        tn = rel(sc.get("note_at"), t0, 1.6)
        wtext(dst, (W / 2, 1110), sc["note"], 46, col(sc.get("note_col", "GOLD")), SB, u, tn)

def s_compare(dst, u, t0, sc):
    """две карточки рядом (было/стало, договор/выписка), бейдж посередине"""
    head(dst, u, sc.get("kicker"), sc.get("title"), 300, 86)
    ok = sc.get("ok"); bc = G if ok is True else R if ok is False else GOLD
    for i, side in enumerate([sc["left"], sc["right"]]):
        ti = rel(side.get("at"), t0, 0.1 + i * 0.3)
        if u < ti: continue
        cx = 290 + i * 500; k = ease_back((u - ti) / 0.3)
        sbc = col(side["col"]) if side.get("col") else bc
        box = (int(cx - 220 * k), int(660 - 240 * k), int(cx + 220 * k), int(660 + 240 * k))
        if k > 0.3: glass(dst, box, border=sbc)
        if k > 0.85:
            d = ImageDraw.Draw(dst); text(d, (cx, 470), side["title"], fit(side["title"], 40, 400, BLD), GOLD, BLD)
            icon(d, side.get("icon", "doc"), cx, 610, 130, WH)
            for j, ln in enumerate(side.get("lines", [])[:3]):
                text(d, (cx, 760 + j * 52), ln, fit(ln, 44 if j == 0 else 36, 400, BLK if j == 0 else SB), WH if j == 0 else (220, 205, 190), BLK if j == 0 else SB)
    tv = rel(sc.get("verdict_at"), t0, 1.0)
    if ok is not None and u > tv: badge(dst, W / 2, 660, 58, bc, ok); edge_glow(dst, bc, clamp(1 - (u - tv) / 0.6))
    if sc.get("note"):
        tn = rel(sc.get("note_at"), t0, tv + 0.2)
        if u > tn:
            k = ease_back((u - tn) / 0.3); glass(dst, (140, int(1060 - 90 * k), 940, int(1060 + 90 * k)), border=col(sc.get("note_col", "GOLD")))
            if k > 0.8:
                d = ImageDraw.Draw(dst); n1 = sc["note"]; text(d, (W / 2, 1035 if sc.get("note2") else 1060), n1, fit(n1, 54, 760), GOLD)
                if sc.get("note2"): text(d, (W / 2, 1105), sc["note2"], fit(sc["note2"], 42, 760, SB), WH, SB)

def s_doc(dst, u, t0, sc):
    """документ-макет: шапка, строки, выделенное поле маркером, печать"""
    edge_glow(dst, GOLD, clamp(1 - u / 0.45))
    head(dst, u, sc.get("kicker"), sc.get("title"), 320, 92)
    y = 880 + 600 * (1 - ease_out(u / 0.45)); rot = -3 + 3 * (1 - ease_out(u / 0.45))
    sc_ = 1.0; w, h = int(640 * sc_), int(820 * sc_)
    doc = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(doc)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 14, fill=PAPER)
    d.rectangle([0, 0, w, 110], fill=(232, 224, 205))
    d.text((w / 2, 40), sc.get("doc_top", "DOCUMENTO"), font=F(fit(sc.get("doc_top", "DOCUMENTO"), 30, w - 60, BLD), BLD), fill=(110, 90, 70), anchor="mm")
    d.text((w / 2, 80), sc.get("doc_title", ""), font=F(fit(sc.get("doc_title", ""), 36, w - 60), BLK), fill=INK, anchor="mm")
    hl_p = clamp((u - rel(sc.get("hl_at"), t0, 0.9)) / 0.8)
    yy = 170
    for ln in sc.get("lines", [None, None, "", None]):
        if ln is None:
            for k in range(2): d.line([(50, yy - 10 + k * 22), (w - 50 - 90 * k, yy - 10 + k * 22)], fill=(205, 195, 175), width=6)
        elif isinstance(ln, dict):   # выделенная строка
            if hl_p > 0: d.rectangle([40, yy - 26, 40 + (w - 80) * hl_p, yy + 26], fill=(255, 214, 80))
            d.text((50, yy), ln["hl"], font=F(fit(ln["hl"], 30, w - 100), BLK), fill=INK, anchor="lm")
        elif ln: d.text((50, yy), ln, font=F(fit(ln, 24, w - 100, BLD), BLD), fill=(150, 120, 90), anchor="lm")
        yy += 72
    if sc.get("stamp"):
        sx, sy, r = w - 140, h - 130, 90
        d.ellipse([sx - r, sy - r, sx + r, sy + r], outline=(40, 70, 160, 200), width=7)
        d.ellipse([sx - r * 0.7, sy - r * 0.7, sx + r * 0.7, sy + r * 0.7], outline=(40, 70, 160, 160), width=4)
        d.text((sx, sy), sc["stamp"], font=F(fit(sc["stamp"], 22, 120), BLK), fill=(40, 70, 160, 200), anchor="mm")
    doc = doc.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([W / 2 - w / 2 + 20, y - h / 2 + 30, W / 2 + w / 2 + 20, y + h / 2 + 30], fill=(0, 0, 0, 150))
    dst.alpha_composite(sh.filter(ImageFilter.GaussianBlur(28)))
    dst.alpha_composite(doc, (int(W / 2 - doc.width / 2), int(y - doc.height / 2)))
    sweep(dst, (220, 470, 860, 1290), (u - 1.9) / 0.7)

def s_stamp(dst, u, t0, sc):
    """крупное слово-штамп с ударом (ЗАПРЕЩЕНО / ШТРАФ / ОБЯЗАТЕЛЬНО)"""
    c = col(sc.get("color", "R"))
    head(dst, u, sc.get("kicker"), sc.get("title"), 420, 90)
    ti = rel(sc.get("stamp_at"), t0, 0.35)
    if u > ti:
        k = clamp((u - ti) / 0.18); s = 1.8 - 0.8 * ease_out(k)
        wd = sc["word"]; sz = fit(wd, 120, 760)
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        tw = F(sz).getlength(wd); bx = [W / 2 - tw / 2 - 50, 640, W / 2 + tw / 2 + 50, 640 + sz + 70]
        d.rounded_rectangle(bx, 22, outline=c, width=12); d.text((W / 2, 640 + (sz + 70) / 2), wd, font=F(sz), fill=c, anchor="mm")
        L = L.rotate(sc.get("rot", -6), center=(W / 2, 640 + (sz + 70) / 2), resample=Image.BICUBIC)
        if abs(s - 1) > 0.01:
            cy = 640 + (sz + 70) / 2; L2 = L.resize((int(W * s), int(H * s)), Image.BILINEAR)
            tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); tmp.paste(L2, (int(W / 2 - W / 2 * s), int(cy - cy * s))); L = tmp
        if k < 1: L.putalpha(L.getchannel("A").point(lambda v: int(v * k)))
        dst.alpha_composite(L)
        edge_glow(dst, c, clamp(1 - (u - ti) / 0.6))
    if sc.get("note"):
        tn = rel(sc.get("note_at"), t0, ti + 0.6)
        if u > tn:
            k = ease_back((u - tn) / 0.3); glass(dst, (150, int(1060 - 85 * k), 930, int(1060 + 85 * k)))
            if k > 0.8:
                d = ImageDraw.Draw(dst); text(d, (W / 2, 1035 if sc.get("note2") else 1060), sc["note"], fit(sc["note"], 52, 740), GOLD)
                if sc.get("note2"): text(d, (W / 2, 1102), sc["note2"], fit(sc["note2"], 40, 740, SB), WH, SB)

def s_clock(dst, u, t0, sc):
    """срок: часы с кольцом-таймером и крупная надпись"""
    edge_glow(dst, GOLD, clamp(1 - u / 0.45))
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if sc.get("kicker"): kicker(ImageDraw.Draw(L), 300, sc["kicker"])
    pop_layer(dst, L, u, 0)
    r = 150; cx, cy = W / 2, 600; dur = max(1.0, sc.get("_dur", 3.0))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    left = 1 - clamp(u / dur)
    od.ellipse([cx - r - 40, cy - r - 40, cx + r + 40, cy + r + 40], outline=(255, 255, 255, 50), width=14)
    if left > 0: od.arc([cx - r - 40, cy - r - 40, cx + r + 40, cy + r + 40], -90, -90 + 360 * left, fill=GOLD, width=14)
    dst.alpha_composite(ov); ic_clock(ImageDraw.Draw(dst), cx, cy, r, WH, u * 6)
    wtext(dst, (W / 2, 900), sc["big"], 130, col(sc.get("color", "GOLD")), u=u, t_in=0.15, maxw=900)
    if sc.get("sub"): wtext(dst, (W / 2, 1030), sc["sub"], 50, WH, SB, u, rel(sc.get("sub_at"), t0, 0.6), maxw=860)

def s_flow(dst, u, t0, sc):
    """два шага со стрелкой: кто → кому (иконки в карточках)"""
    edge_glow(dst, GOLD, clamp(1 - u / 0.45))
    head(dst, u, sc.get("kicker"), sc.get("title"), 420, 96)
    a, b = sc["left"], sc["right"]
    for i, (cx, it) in enumerate([(240, a), (840, b)]):
        ti = rel(it.get("at"), t0, 0.15 if i == 0 else 0.9)
        if u < ti: continue
        k = ease_back((u - ti) / 0.3); glass(dst, (int(cx - 170 * k), int(720 - 180 * k), int(cx + 170 * k), int(720 + 180 * k)), border=col(it.get("col", "GOLD")))
        if k > 0.85:
            d = ImageDraw.Draw(dst); icon(d, it.get("icon", "person"), cx, 690, 150, WH); text(d, (cx, 850), it["label"], fit(it["label"], 34, 310, BLD), WH, BLD)
    p = clamp((u - 0.5) / 0.45); d = ImageDraw.Draw(dst)
    if p > 0:
        x1 = 430 + (650 - 430) * p; d.line([(430, 720), (x1, 720)], fill=GOLD, width=8)
        if p >= 1: d.polygon([(660, 720), (630, 700), (630, 740)], fill=GOLD)
    if sc.get("mid"): icon(d, sc["mid"], 540, 640, 110, GOLD) if u > 0.7 else None
    if sc.get("mid_text") and u > 0.7: text(d, (540, 650), sc["mid_text"], fit(sc["mid_text"], 40, 200, BLD), GOLD, BLD)
    if sc.get("note"): wtext(dst, (W / 2, 1010), sc["note"], 44, col(sc.get("note_col", "GOLD")), SB, u, rel(sc.get("note_at"), t0, 1.4))

def s_freeze(dst, u, t0, sc):
    dst.alpha_composite(Image.new("RGBA", (W, H), (8, 4, 2, 150)))
    edge_glow(dst, GOLD, 0.5 + 0.3 * math.sin(u * 9))
    r = 150; cx, cy = W / 2, 560
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    left = 1 - u / FRZ
    od.ellipse([cx - r - 40, cy - r - 40, cx + r + 40, cy + r + 40], outline=(255, 255, 255, 50), width=14)
    if left > 0: od.arc([cx - r - 40, cy - r - 40, cx + r + 40, cy + r + 40], -90, -90 + 360 * left, fill=GOLD, width=14)
    dst.alpha_composite(ov); ic_clock(ImageDraw.Draw(dst), cx, cy, r, WH, u * 9)
    wtext(dst, (W / 2, 870), fz.get("q1", ""), 120, WH, u=u, t_in=0)
    wtext(dst, (W / 2, 1000), fz.get("q2", ""), 140, GOLD, u=u, t_in=0.12)

def s_ask(dst, u, t0, sc):
    edge_glow(dst, GOLD, clamp(1 - u / 0.5))
    wtext(dst, (W / 2, 470), ASK["l1"], 90, WH, u=u, t_in=0)
    wtext(dst, (W / 2, 600), ASK["l2"], 120, GOLD, u=u, t_in=0.15)
    opts = ASK.get("opts", ["ДА", "НЕТ"]); n = len(opts)
    cols = ASK.get("cols") or ([G, R] if n == 2 else [GOLD] * n)
    gap = 420 if n == 2 else 320; hw = 160 if n == 2 else 140
    for i, t in enumerate(opts):
        tin = 0.45 + i * 0.15
        if u < tin: continue
        c = col(cols[i]) if isinstance(cols[i], str) else cols[i]
        s = ease_back((u - tin) / 0.3); cx = W / 2 - gap * (n - 1) / 2 + i * gap; cy = 840
        glass(dst, (int(cx - hw * s), int(cy - 85 * s), int(cx + hw * s), int(cy + 85 * s)), border=c)
        if s > 0.85: text(ImageDraw.Draw(dst), (cx, cy), t, fit(t, 100, hw * 2 - 30), c)
    if u > 0.9: wtext(dst, (W / 2, 1010), "ответьте в комментариях", 50, WH, SB, u, 0.9)

def band_pill(dst, u, txt, c, ok=True):
    k = ease_back(u / 0.3); fs = fit(txt, 58, W - 300); w = F(fs).getlength(txt) + 160
    x0, x1 = W / 2 - w / 2 * k, W / 2 + w / 2 * k
    if k > 0.2: glass(dst, (int(x0), 95, int(x1), 205), border=c)
    if k > 0.85:
        d = ImageDraw.Draw(dst); text(d, (W / 2 + 40, 150), txt, fs, WH)
        badge(dst, int(W / 2 - w / 2 + 70), 150, 30, c, ok)
    edge_glow(dst, c, clamp(1 - u / 0.5))

TYPES = {"cards": s_cards, "list": s_list, "number": s_number, "compare": s_compare, "doc": s_doc, "stamp": s_stamp,
         "clock": s_clock, "flow": s_flow}
SOUNDS = {"number": None}

# ---- таймлайн ----
TL = []
def add(a, b, kind, fn, sound=None, sc=None, s0=None): TL.append([a, b, kind, fn, sound, sc or {}, s0])
add(0, COV, "cover", None)
if CO_LEN > 0:
    cb = co.get("band"); cc = col(co.get("color", "R")); cok = co.get("ok", False)
    add(COV, CO_LEN, "cold", (lambda dst, u, t0, sc, cb=cb, cc=cc, cok=cok: band_pill(dst, u - 1.0, cb, cc, cok) if cb and u >= 1.0 else None))
    t_title_end = CFG.get("title_until")
    te = at(t_title_end) if t_title_end else None
    te_m = m(te) if te is not None and m(te) - CO_LEN > 1.2 else CO_LEN + 2.4
    add(CO_LEN, min(te_m, CO_LEN + 3.2), "scene", s_title, "whoosh", s0=0.0)
for sc in CFG.get("scenes", []):
    a = at(sc["from"], sc.get("after", 0.0))
    if a is None: warn(f"сцена {sc['type']}: не нашёл начало «{sc['from']}» — пропускаю"); continue
    a -= sc.get("lead", 0.1)
    if sc.get("to"):
        b = end_of(sc["to"], a)
        if b is None: warn(f"сцена {sc['type']}: не нашёл конец «{sc['to']}», беру {sc.get('dur', 3.5)} с"); b = a + sc.get("dur", 3.5)
        else: b += sc.get("tail", 0.2)
    else: b = a + sc.get("dur", 3.5)
    b = min(b, a + sc.get("max", 6.5), END)
    if fz and a < SPL < b:   # сцена не должна перекрывать стоп-кадр
        if SPL - a > 1.5: b = SPL
        else: a = SPL
    if b - a < 1.2: warn(f"сцена {sc['type']} слишком короткая — пропускаю"); continue
    sc["_dur"] = m(b) - m(a)
    add(m(a), m(b), "scene", TYPES[sc["type"]], sc.get("sound", "whoosh"), sc, a)
if fz:
    add(tA + SPL, tB, "freeze", s_freeze, "click")
for bd in CFG.get("bands", []):
    a = at(bd["at"], bd.get("after", 0.0))
    if a is None: warn(f"плашка «{bd['text']}» не найдена"); continue
    c = col(bd.get("color", "G")); ok = bd.get("ok", bd.get("color", "G") != "R")
    add(m(a), m(a) + bd.get("dur", 2.0), "band", (lambda dst, u, t0, sc, txt=bd["text"], c=c, ok=ok: band_pill(dst, u, txt, c, ok)), "pop")
if ASK: add(A_END, TT, "scene", s_ask, "whoosh", s0=END - 0.5)
# сортировка и разведение пересечений: сцены главнее плашек
TL.sort(key=lambda s: s[0])
clean = []
for s in TL:
    if s[2] == "band" and any(o[2] in ("scene", "freeze") and o[0] < s[1] and s[0] < o[1] for o in TL):
        warn(f"плашка на {s[0]:.1f} с попала на сцену — убрал"); continue
    if clean and s[2] in ("scene", "freeze") and clean[-1][2] in ("scene", "freeze") and s[0] < clean[-1][1]:
        if clean[-1][2] == "freeze" or s[2] == "freeze":
            if s[2] == "freeze": clean[-1][1] = s[0]
            else: s[0] = clean[-1][1]
        else:
            clean[-1][1] = s[0]
        if s[1] - s[0] < 1.0 or clean[-1][1] - clean[-1][0] < 1.0:
            warn(f"сцены пересеклись на {s[0]:.1f} с");
    if clean and s[2] == "band" and clean[-1][2] == "band" and s[0] < clean[-1][1]: clean[-1][1] = s[0]
    clean.append(s)
TL = [s for s in clean if s[1] - s[0] > 0.3 or s[2] == "cover"]

def evs():
    e = []
    if CO_LEN > 0 and co.get("band"): e.append((COV + 1.0, "boom"))
    if fz: e += [(tA + SPL + 0.12 + k * 0.3, "click") for k in range(4)]
    for s in TL:
        sc = s[5]
        if s[2] == "scene" and sc.get("type") == "number": e.append((s[0] + 0.7, "cash" if sc.get("glow", "G") == "G" else "boom"))
        if s[2] == "scene" and sc.get("type") == "stamp": e.append((s[0] + rel(sc.get("stamp_at"), s[6], 0.35), "boom"))
        if s[2] == "scene" and sc.get("type") == "list":
            for i, it in enumerate(sc["items"]):
                it = it if isinstance(it, dict) else {}
                e.append((s[0] + rel(it.get("at"), s[6], 0.2 + i * 0.35) + 0.15, "ding" if sc.get("mark", "check") == "check" else "pop"))
        if s[2] == "scene" and sc.get("type") == "cards":
            for i, it in enumerate(sc["items"]): e.append((s[0] + rel(it.get("at"), s[6], 0.15 + i * 0.25), "pop"))
    return [x for x in e if x[0] < TT]

# ---- субтитры ----
FIX = {nw(k): v for k, v in CFG.get("fix", {}).items()}
def build_subs():
    out = []
    for x in WORDS:
        if x["s"] >= END: continue
        raw = x["w"]; core = raw.strip(".,!?:;—-«»\"").upper()
        if not core: continue
        core = FIX.get(nw(raw), core).upper()
        t = x["s"]; p = raw[-1] in ".,!?:;"
        if CO_LEN > 0 and CO[0] <= t < CO[1]: out.append([t - CO[0], core, p, x["e"] - CO[0]])
        if fz: out.append([m(t), core, p, m(x["e"]) if x["e"] < SPL or t >= SPL else tA + SPL])
        else: out.append([m(t), core, p, m(x["e"])])
    out.sort(key=lambda w: w[0])
    ch = []; cur = []
    for i, w in enumerate(out):
        if cur and w[0] < cur[-1][0]: continue
        cur.append(w); ln = sum(len(x[1]) + 1 for x in cur)
        far = i + 1 < len(out) and out[i + 1][0] - w[3] > 0.5
        if w[2] or len(cur) >= 3 or ln >= 18 or far: ch.append(cur); cur = []
    if cur: ch.append(cur)
    res = []
    for i, c in enumerate(ch):
        nxt = ch[i + 1][0][0] if i + 1 < len(ch) else A_END
        res.append((c[0][0], min(nxt, c[-1][3] + 0.35), c))
    return res
SUBS = build_subs()
SUBY_FACE, SUBY_SCENE = 1490, 1440
_cache = {}
# 28.10.2026 Евгений: вместо тёмной плашки v2 — «микс» как в обычных шортсах (белые и жёлтые, слова по одному,
# разные шрифты по кругу), но мельче — шортсы из лонга, крупные закрывают его на треть.
_FD = os.path.join(HERE, "..", "..", "fonts") + "/"
from PIL import ImageFont
def _mf(n, sz): return ImageFont.truetype(_FD + n, sz)
MIXK = 0.68
MIXSTY = [dict(fn="oswald-700.ttf", sz=118, col=(255, 214, 0), up=True, al="l"),
          dict(fn="montserrat-900.ttf", sz=64, col=(255, 255, 255), up=False, al="c"),
          dict(fn="unbounded-800.ttf", sz=74, col=(255, 255, 255), up=True, al="r"),
          dict(fn="playfair-display-800.ttf", sz=86, col=(255, 214, 0), up=False, al="c")]
MIXKEYS = set(nw(k) for k in CFG.get("keys", []))
def _iskey(w): return nw(w) in MIXKEYS or bool(re.search(r"\d", w))
def _mix_img(ci, c, upto):
    k = ("m", ci, upto)
    if k in _cache: return _cache[k]
    st = MIXSTY[ci % len(MIXSTY)]
    toks = [((w[1] if st["up"] else w[1].capitalize() if j == 0 else w[1].lower()), _iskey(w[1])) for j, w in enumerate(c)]
    maxw = W - 240; lines, cur, curw = [], [], 0
    for t_, kk in toks:
        f = _mf(st["fn"], max(46, int(st["sz"] * MIXK * (1.25 if kk else 1))))
        while f.getlength(t_) > maxw and f.size > 24: f = _mf(st["fn"], f.size - 4)
        ww = f.getlength(t_ + " ")
        if cur and curw + ww > maxw: lines.append(cur); cur, curw = [], 0
        cur.append((t_, kk, f)); curw += ww
    if cur: lines.append(cur)
    hh = sum(max(f.size for _, _, f in l) * 1.05 for l in lines)
    im = Image.new("RGBA", (W, int(hh) + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im); y = 15; n = 0
    for l in lines:
        lw = sum(f.getlength(t_ + " ") for t_, _, f in l)
        x = {"l": 120, "c": (W - lw) / 2, "r": W - 120 - lw}[st["al"]]; x = max(100, min(x, W - 100 - lw))
        lh = max(f.size for _, _, f in l) * 1.05
        for t_, kk, f in l:
            if n <= upto:
                col = (255, 214, 0) if kk and st["col"] == (255, 255, 255) else ((255, 255, 255) if kk else st["col"])
                d.text((x, y + lh * 0.82), t_, font=f, fill=col, anchor="ls", stroke_width=max(3, f.size // 16), stroke_fill=(0, 0, 0))
            x += f.getlength(t_ + " "); n += 1
        y += lh
    bb = im.getbbox() or (0, 0, 1, 1); im = im.crop(bb)
    sh = Image.new("RGBA", (im.width + 40, im.height + 40), (0, 0, 0, 0)); a_ = im.split()[3].point(lambda v: int(v * 0.45))
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255)); blk.putalpha(a_); sh.alpha_composite(blk, (20, 26)); sh = sh.filter(ImageFilter.GaussianBlur(8))
    sh.alpha_composite(im, (20, 20)); _cache[k] = sh; return sh
MIX_DY = [0, -30, 20, -15]
def draw_sub(dst, t, y):
    for ci, (a, b, c) in enumerate(SUBS):
        if a <= t < b:
            cur = max([i for i, w in enumerate(c) if w[0] <= t + 0.04] or [0])
            im = _mix_img(ci, c, cur)
            yy = y + MIX_DY[ci % len(MIX_DY)] - im.height / 2
            yy = max(150, min(yy, H - 380 - im.height + 40))
            dst.alpha_composite(im, (int(W / 2 - im.width / 2), int(yy))); return

# ---- кадры основы ----
NB = None
class Src:
    def __init__(self): self.p = None; self.pos = None; self.last = None
    def get(self, s):
        fi = max(0, int(round(s * FPS)))
        if self.p is None or fi < self.pos or fi - self.pos > 45:
            if self.p: self.p.kill()
            self.p = subprocess.Popen(["ffmpeg", "-v", "quiet", "-ss", f"{fi / FPS:.4f}", "-i", BASE, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            self.pos = fi
        while self.pos <= fi:
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            self.last = b; self.pos += 1
        if self.last is None: self.last = b"\x00" * (W * H * 3)
        return Image.frombytes("RGB", (W, H), self.last).convert("RGBA")
SRC = Src()
COVER = Image.open("cover.jpg").convert("RGBA").resize((W, H))
_frz = None
def src_of(t):
    if CO_LEN > 0 and t < CO_LEN: return CO[0] + max(0, t)
    if t < tA: return max(0, CO[1] - 0.02) if CO_LEN > 0 else 0.0
    if t < tA + SPL: return t - tA
    if t < tB: return SPL - 0.3
    return min(SPL + (t - tB), END + 1.0)

EVS = evs()
# 28.10.2026 (из «Всё о крипте», Евгений): резкие наезды +8% на первом слове и 3–5 ключевых словах (не чаще раза в 5 с),
# вход 0,12 с, держать 0,4 с, отъезд 0,25 с, на каждом — «вжух»; «дыхание» сцен дольше 2 с: 1,00 → 1,04
PUNCHT = []
_ks = set(nw(k) for k in CFG.get("punch", CFG.get("keys", [])))
_ws = [x for x in WORDS if x["s"] < END]
if _ws and os.environ.get("PUNCH", "1") != "0":
    PUNCHT.append(m(_ws[0]["s"]))
    for x in _ws:
        if len(PUNCHT) >= 6: break
        tt = m(x["s"])
        if tt > A_END - 2.5: break
        if (nw(x["w"]) in _ks or re.search(r"\d", x["w"])) and tt - PUNCHT[-1] >= 5.0: PUNCHT.append(tt)
EVS += [(tp, "whoosh") for tp in PUNCHT[1:]]
def punch_z(t):
    for tp in PUNCHT:
        d = t - tp
        if 0 <= d < 0.12: return 1 + 0.08 * ease_out(d / 0.12)
        if 0.12 <= d < 0.52: return 1.08
        if 0.52 <= d < 0.77: return 1 + 0.08 * (1 - ease_out((d - 0.52) / 0.25))
    return 1.0
def zoom_layer(layer, z, cy=H / 2):
    if z < 1.001: return layer
    L = layer.resize((int(W * z), int(H * z)), Image.BILINEAR)
    x0 = (L.width - W) // 2; y0 = int(max(0, min(L.height - H, cy * z - cy)))
    return L.crop((x0, y0, x0 + W, y0 + H))
def frame(t):
    global _frz
    sg = next((s for s in TL if s[0] <= t < s[1] and s[2] != "band"), None) or next((s for s in TL if s[0] <= t < s[1]), None)
    kind = sg[2] if sg else "face"
    if kind == "cover": return COVER.convert("RGB")
    if kind == "scene":
        t0 = sg[0]; u = t - t0
        s0 = sg[6] if sg[6] is not None else src_of(t0)
        layer = scene_bg(src_of(t0) if t0 < A_END else END - 0.5).copy(); sg[3](layer, u, s0, sg[5])
        if u < 0.2:
            s = 1.07 - 0.07 * ease_out(u / 0.2); bg_ = layer.resize((int(W * s), int(H * s)), Image.BILINEAR)
            layer = bg_.crop(((bg_.width - W) // 2, (bg_.height - H) // 2, (bg_.width - W) // 2 + W, (bg_.height - H) // 2 + H))
        dur_ = sg[1] - sg[0]
        if dur_ > 2.0: layer = zoom_layer(layer, 1 + 0.04 * clamp(u / dur_), 740)   # «дыхание»: к центру сцены (зона 220–1260)
        suby = SUBY_SCENE; sub = t < A_END
    elif kind == "freeze":
        if _frz is None: _frz = SRC.get(SPL - 0.3)
        layer = _frz.copy(); sg[3](layer, t - sg[0], 0, sg[5]); sub = False
    else:
        layer = SRC.get(src_of(t))
        if sg and sg[3]: sg[3](layer, t - sg[0], 0, sg[5])
        suby = SUBY_FACE; sub = t < A_END
    for te, k in EVS:
        if k == "boom" and 0 <= t - te < 0.35:
            amp = 14 * (1 - (t - te) / 0.35); r = random.Random(int(t * 1000))
            base = Image.new("RGBA", (W, H), (10, 5, 3, 255)); base.paste(layer, (int(r.uniform(-amp, amp)), int(r.uniform(-amp, amp)))); layer = base
    pz = punch_z(t)
    if pz > 1.001 and kind != "freeze": layer = zoom_layer(layer, pz, 740 if kind == "scene" else H * 0.45)
    if sub: draw_sub(layer, t, suby)
    return layer.convert("RGB")

SR = 48000
def build_audio(out="mix.wav"):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", BASE, "-ac", "2", "-ar", str(SR), "-f", "s16le", "v.raw"], check=True)
    v = np.fromfile("v.raw", np.int16).reshape(-1, 2).astype(float) / 32768
    def cut(a, b, fi=0.02, fo=0.03):
        x = v[int(a * SR): int(b * SR)].copy(); n1, n2 = int(fi * SR), int(fo * SR)
        if len(x) > n1 + n2: x[:n1] *= np.linspace(0, 1, n1)[:, None]; x[-n2:] *= np.linspace(1, 0, n2)[:, None]
        return x
    sil = lambda s: np.zeros((int(round(s * SR)), 2))
    parts = []
    if CO_LEN > 0: parts += [cut(*CO), sil(GAP)]
    else: parts += [sil(COV)]
    if fz: parts += [cut(0, SPL, 0.005), sil(FRZ), cut(SPL, END, 0.005, 0.08)]
    else: parts += [cut(0, END, 0.005, 0.08)]
    y = np.concatenate(parts)
    n = int(TT * SR); mix = np.zeros((n, 2)); mix[:min(n, len(y))] += y[:n]
    lv = {"whoosh": 0.22, "click": 0.25, "boom": 0.20, "pop": 0.25, "ding": 0.2, "alarm": 0.16, "cash": 0.24}   # 28.10.2026: бум и тревога мягче (не выше 0,20)
    fx = np.zeros(n)
    for te, k in [(s[0], s[4]) for s in TL if s[4]] + EVS:
        if k not in lv: continue
        s = snd(k) * lv[k]; i0 = max(0, int((te - 0.06) * SR)); j = min(n, i0 + len(s))
        if j > i0: fx[i0:j] += s[: j - i0]
    mix += fx[:, None]
    (np.clip(mix, -1, 1) * 32767).astype(np.int16).tofile("mix.raw")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "mix.raw",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), out], check=True)

def render_part(f0, f1, out):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(f0, f1): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()

def info():
    scn = sum(s[1] - s[0] for s in TL if s[2] in ("scene", "freeze"))
    print(f"CO={CO_LEN:.2f} SPL={SPL:.2f} END={END:.2f} TT={TT:.2f}")
    print(f"::notice::длина {TT:.1f} с, сцены {scn:.1f} с → лицо {100 * (1 - scn / TT):.0f}%")
    if 100 * (1 - scn / TT) < 57: warn(f"лицо меньше 60%: {100 * (1 - scn / TT):.0f}%")
    for s in TL:
        sc = s[5]; dur = s[1] - s[0]; bad = []
        if s[2] == "scene" and sc.get("type"):
            keys = [(k, sc.get(k)) for k in ("note_at", "stamp_at", "verdict_at", "hl_at", "sub_at") if sc.get(k)]
            for side in ("left", "right"):
                if isinstance(sc.get(side), dict) and sc[side].get("at"): keys.append((side, sc[side]["at"]))
            for it in sc.get("items", []):
                if isinstance(it, dict) and it.get("at"): keys.append(("item", it["at"]))
            for k, ph in keys:
                a = at(ph, s[6] - 1.0)
                r_ = None if a is None else m(a) - m(s[6])
                if r_ is None or r_ > dur - 0.6 or r_ < -0.5: bad.append(f"{ph}→{'нет' if r_ is None else round(r_, 1)}")
        print(f"{s[0]:7.2f}-{s[1]:7.2f} {s[2]} {sc.get('type', '')} {sc.get('title', '') or sc.get('word', '')}" + (f"  !! {bad}" if bad else ""))

if __name__ == "__main__":
    md = sys.argv[1]
    if md == "info": info()
    elif md == "frames":
        for x in sys.argv[2:]: frame(float(x)).save(f"q_{float(x):06.2f}.png")
    elif md == "audio": build_audio()
    elif md == "render":
        out = sys.argv[2]; npr = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        NF = int(TT * FPS)
        if npr <= 1: render_part(0, NF, "video.mp4")
        else:
            import multiprocessing as mp
            bnd = [NF * k // npr for k in range(npr + 1)]
            ps = [mp.Process(target=render_part, args=(bnd[k], bnd[k + 1], f"part{k}.mp4")) for k in range(npr)]
            for p in ps: p.start()
            for p in ps: p.join()
            bad = [k for k, p in enumerate(ps) if p.exitcode != 0]   # 29.10.2026: упавшая часть давала укороченный ролик без ошибки
            if bad: sys.exit(f"рендер: упали части {bad}")
            open("parts.txt", "w").write("".join(f"file 'part{k}.mp4'\n" for k in range(npr)))
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "parts.txt", "-c", "copy", "video.mp4"], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "video.mp4", "-i", "mix.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", out], check=True)
        print("DONE", out)
