#!/usr/bin/env python3
"""Безопасная раскладка надписей обложки (Евгений, 31.10.2026, по скрину сетки Instagram).

Ошибки, которые чиним:
1. Нижняя надпись (рваная полоса, крупное слово) ложилась на рот и подбородок: стояла на фиксированной
   высоте (64% кадра, низ 1590), а лицо у всех роликов на разной высоте. Теперь ищем лицо и ставим
   нижний блок СТРОГО под подбородком; не помещается — переносим весь текст НАД головой.
2. Верхняя строка залезала под значок ролика Instagram (справа вверху сетки) — «ПОСЛЕ ХЭЛЛОУИНА»,
   «АРЕНДА В ИСПАНИИ», «НЕВОЗВРАТНЫЙ БИЛЕТ», «ПОЧЕМУ ТАК». Строки в верхней полосе — не шире 640 px по центру.
3. Нижняя строка уходила под счётчик просмотров (слева внизу сетки) — «СВОБОДА?», «СЧЁТ ЗА СВЕТ?»,
   «ГЛАВНАЯ ОШИБКА». Низ любого текста — не ниже 1450.

Кадр 1080×1920. Сетка профиля Instagram и TikTok показывает 3:4 — примерно y 240–1680.
Всё сделано функциями: zones(img) → где голова и подбородок; plan(...) → куда ставить нижний блок и масштаб."""
import os, json
import numpy as np, cv2
from PIL import Image, ImageFilter, ImageEnhance

W, H = 1080, 1920
SAFE_TOP = 300        # выше режет сетка
SAFE_BOT = 1450       # ниже — счётчик просмотров и срез сетки
ICON_Y = 480          # полоса значка ролика Instagram (справа вверху сетки)
ICON_W = 600          # строки в этой полосе не шире, по центру (x 240–840; с плашкой до ~875)
GAP_HEAD = 25         # от низа надписи до макушки (волосы, кепка)
GAP_CHIN = 45         # от подбородка до верха нижнего блока
ZOOMS = (1.0,)        # уменьшение кадра (0.88, 0.78) выключено: даёт вид «окна» с размытыми краями, Евгений такое отклонял 22.10
D = os.path.dirname(os.path.abspath(__file__))


def _cascade():
    for p in (f'{D}/haar.xml', cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'):
        if os.path.exists(p):
            c = cv2.CascadeClassifier(p)
            if not c.empty(): return c
    return None


def zones(pil_img):
    """Лицо на кадре: dict(found, cx, head_top, chin, eye). head_top — макушка с волосами/кепкой, chin — низ подбородка."""
    g = cv2.cvtColor(np.array(pil_img.convert('RGB').resize((W, H))), cv2.COLOR_RGB2GRAY)
    fc = _cascade(); f = []
    if fc is not None:
        f = fc.detectMultiScale(g, 1.1, 5, minSize=(60, 60))
        if not len(f): f = fc.detectMultiScale(g, 1.05, 3, minSize=(40, 40))
        # ложные «лица» в листве мелкие и по краям — берём крупное ближе к центру
        f = [r for r in f if r[2] >= 70] or list(f)
    FJ = os.environ.get('FACE_JSON')   # лицо по всему ролику (montage.py) — отсекает ложные находки
    if FJ and os.path.exists(FJ):
        fj = json.load(open(FJ)); h_ = fj['HN'] * H; jx, jy = fj['CX'] * W, fj['EYE'] * H
        near = [r for r in f if abs(r[0] + r[2] / 2 - jx) < W * 0.2 and abs(r[1] + 0.42 * r[3] - jy) < H * 0.1]
        f = near or [(int(jx - h_ / 2), int(jy - 0.42 * h_), int(h_), int(h_))]
    if not len(f):
        return dict(found=False, cx=W / 2, head_top=int(H * 0.30), chin=int(H * 0.62), eye=int(H * 0.45))
    x, y, w, h = max(f, key=lambda r: r[2] * r[3] - abs(r[0] + r[2] / 2 - W / 2) * 40)
    chin = int(y + 1.15 * h)
    lbf = f'{D}/lbf.yaml'
    if os.path.exists(lbf):   # точный подбородок по точкам лица
        try:
            fm = cv2.face.createFacemarkLBF(); fm.loadModel(lbf)
            ok, lm = fm.fit(g, np.array([[x, y, w, h]]))
            if ok: chin = max(chin, int(lm[0][0][8][1]) + 10)
        except Exception:
            pass
    return dict(found=True, cx=x + w / 2, head_top=max(0, int(y - 0.45 * h)), chin=chin, eye=int(y + 0.42 * h))


def top_room(z):
    """Сколько места над головой для текста (от SAFE_TOP до макушки)."""
    return z['head_top'] - GAP_HEAD - SAFE_TOP


def plan(z, top_need, bot_need, min_scale=0.62):
    """top_need(s), bot_need(s) — высота верхнего и нижнего блока при масштабе шрифта s (0..1).
    Перебирает сдвиг картинки вниз (0–460 px) и два режима:
      'chest' — верх над головой, низ под подбородком;
      'above' — всё над головой одной стопкой.
    Берёт вариант с самым крупным шрифтом; при равенстве — без сдвига / с меньшим сдвигом.
    Возвращает dict(mode, s_top, s_bot, y_top, y_bot, shift)."""
    gap = 30 if top_need(1) else 0

    def best(need, room, lo=0.3):
        s = 1.0
        while s > lo and need(s) > room: s -= 0.03
        return s if need(s) <= room else 0.0

    cands = []
    # zm < 1 — картинка уменьшена и прижата к низу (по бокам размытый фон): только для очень крупного лица,
    # когда даже со сдвигом шрифт выходит мельче половины. Уменьшение 0.88 «стоит» 0.36 масштаба — включается редко.
    for zm in ZOOMS:
      if zm < 1 and cands and max(c[0] for c in cands) >= 0.55: break
      for d in range(0, 461, 20):
        tz = lambda y: int(y * zm + H * (1 - zm))
        ht, ch = tz(z['head_top']) + d, tz(z['chin']) + d
        if d and ch > 1640: break           # подбородок не уходит за низ сетки (видно до ~1680)
        room_top = ht - GAP_HEAD - SAFE_TOP; room_bot = SAFE_BOT - (ch + GAP_CHIN)
        st = best(top_need, room_top) if top_need(1) else 1.0
        sb = best(bot_need, room_bot) if bot_need(1) else 1.0
        if min(st, sb) > 0:
            y_top = max(SAFE_TOP, ht - GAP_HEAD - int(top_need(st))) if top_need(1) else SAFE_TOP
            cands.append((min(st, sb) - (1 - zm) * 3.0, -d, dict(mode='chest', s_top=st, s_bot=sb, y_top=y_top, y_bot=ch + GAP_CHIN, shift=d, zoom=zm)))
        both = lambda s: top_need(s) + gap + bot_need(s)
        sa = best(both, room_top)
        if sa > 0:
            y_top = max(SAFE_TOP, ht - GAP_HEAD - int(both(sa)))
            cands.append((sa - 0.02 - (1 - zm) * 3.0, -d, dict(mode='above', s_top=sa, s_bot=sa, y_top=y_top, y_bot=y_top + int(top_need(sa)) + gap, shift=d, zoom=zm)))
    def fallback():   # очень крупное лицо: сдвиг вниз до упора, весь текст над головой; если шрифт всё равно
        # мельче 0.5 — картинка чуть уменьшается (края дорисовываются отражением с размытием, без «окна»)
        both = lambda s: top_need(s) + gap + bot_need(s)
        for zm in (1.0, 0.9, 0.82, 0.75):
            tz = lambda y: int(y * zm + H * (1 - zm))
            d = max(0, min(460, 1640 - tz(z['chin'])))
            room = tz(z['head_top']) + d - GAP_HEAD - SAFE_TOP
            sa = best(both, room, 0.15) or 0.15
            if sa >= 0.5: break
        y_top = max(SAFE_TOP, tz(z['head_top']) + d - GAP_HEAD - int(both(sa)))
        print(f'cover_safe: ВНИМАНИЕ — лицо очень крупное (уменьшение {zm}); лучше кадр, где Евгений дальше от камеры')
        return sa, dict(mode='above', s_top=sa, s_bot=sa, y_top=y_top, y_bot=y_top + int(top_need(sa)) + gap, shift=d, zoom=zm)
    if not cands: return fallback()[1]
    # сдвиг — только если без него шрифт заметно мельче (каждые 100 px сдвига «стоят» 0.06 масштаба)
    ch = max(cands, key=lambda c: (round(min(c[0], 0.9) + c[1] / 100 * 0.06, 3), c[1]))
    if ch[0] < 0.5:
        fs, fp = fallback()
        if fs > ch[0] + 0.05: return fp
    return ch[2]


def prepare(src, top_need, bot_need):
    """Кадр → (кадр, лицо, план). Если иначе текст ляжет на лицо: картинка сдвигается вниз
    (верх дорисовывается размытием стены/неба) или, для очень крупного лица, чуть уменьшается."""
    src = src.convert('RGB').resize((W, H))
    z = zones(src); p = plan(z, top_need, bot_need)
    zm, d = p.get('zoom', 1.0), p.get('shift', 0)
    if zm < 1:
        sm = np.array(src.resize((int(W * zm), int(H * zm)), Image.LANCZOS))
        px = (W - sm.shape[1]) // 2; py = H - sm.shape[0]
        ext = cv2.copyMakeBorder(sm, py, 0, px, W - sm.shape[1] - px, cv2.BORDER_REPLICATE)  # 02.11: не REFLECT — зеркалило голову вверх «призраком»
        blur = cv2.GaussianBlur(ext, (0, 0), 25)
        m = np.zeros((H, W), np.float32); m[py:, px:px + sm.shape[1]] = 1
        m = cv2.GaussianBlur(m, (0, 0), 18)[..., None]           # мягкий переход, без рамки
        src = Image.fromarray((ext * m + blur * (1 - m)).astype(np.uint8))
        for k in ('head_top', 'chin', 'eye'): z[k] = int(z[k] * zm + H * (1 - zm))
    if d:
        top = src.crop((0, 0, W, 80)).resize((W, d + 80)).filter(ImageFilter.GaussianBlur(30))
        new = Image.new('RGB', (W, H)); new.paste(top, (0, 0)); new.paste(src.crop((0, 0, W, H - d)), (0, d))
        m = Image.linear_gradient('L').resize((W, 80))          # мягкий шов
        new.paste(src.crop((0, 0, W, 80)), (0, d), m)
        src = new
        for k in ('head_top', 'chin', 'eye'): z[k] += d
    p.setdefault('shift', 0); p.setdefault('zoom', 1.0)
    return src, z, p


def maxw_at(y, h, maxw):
    """Ширина строки с учётом значка Instagram справа вверху."""
    return min(maxw, ICON_W) if y < ICON_Y else maxw


def report(z, p, out):
    print(f"cover_safe: лицо {'найдено' if z['found'] else 'не найдено'}, макушка {z['head_top']}, подбородок {z['chin']}, "
          f"режим {p['mode']}, сдвиг {p['shift']}, уменьшение {p['zoom']}, масштаб верх {p['s_top']:.2f} низ {p['s_bot']:.2f} → {os.path.basename(out)}")
