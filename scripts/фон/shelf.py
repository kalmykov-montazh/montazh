import numpy as np, cv2, random
random.seed(7); np.random.seed(7)
W, H = 1264, 772
img = np.zeros((H, W, 3), np.float32)
# стена: тёплая тёмная, с мягким градиентом и лёгким шумом
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
base = np.array([46, 58, 72], np.float32) / 255  # BGR тёплый серо-коричневый
vign = 1.0 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2) - 0.25 * ((yy / H) ** 1.5)
img[:] = base * vign[..., None]
img += np.random.normal(0, 0.006, img.shape).astype(np.float32)

def rect(x0, y0, x1, y1, col, shade=True):
    x0, x1 = int(max(0, x0)), int(min(W, x1)); y0, y1 = int(max(0, y0)), int(min(H, y1))
    if x1 <= x0 or y1 <= y0: return
    c = np.array(col, np.float32)[::-1] / 255
    blk = np.ones((y1 - y0, x1 - x0, 3), np.float32) * c
    if shade:
        g = np.linspace(0.75, 1.05, x1 - x0)[None, :, None]
        blk *= g
    img[y0:y1, x0:x1] = blk

shelves = [250, 480, 710]   # y верхней кромки полки
WOOD = (120, 84, 52)
PAL = [(38, 52, 84), (110, 36, 40), (88, 96, 58), (196, 180, 150), (70, 50, 38), (150, 110, 60), (30, 30, 34), (120, 130, 140), (160, 70, 50)]
def books(x0, x1, ybot):
    x = x0
    while x < x1:
        w = random.randint(14, 34); h = random.randint(110, 175)
        if random.random() < 0.12:  # промежуток
            x += random.randint(20, 50); continue
        col = random.choice(PAL)
        rect(x, ybot - h, x + w, ybot, col)
        # корешок: полоски
        c2 = tuple(min(255, int(v * 1.5) + 30) for v in col)
        for k in range(random.randint(1, 2)):
            yb = ybot - h + random.randint(15, h - 20)
            rect(x + 2, yb, x + w - 2, yb + 4, c2, False)
        x += w + 1

def globe(cx, ybot, r):
    cy = ybot - r - 18
    cv2.circle(img, (cx, cy), r, (0.45, 0.42, 0.20), -1, cv2.LINE_AA)
    for a in range(-2, 3):
        cv2.ellipse(img, (cx, cy), (int(r * abs(a) / 3) + 2, r), 0, 0, 360, (0.30, 0.32, 0.18), 2, cv2.LINE_AA)
    cv2.ellipse(img, (cx + r // 4, cy - r // 5), (r // 3, r // 4), 20, 0, 360, (0.25, 0.45, 0.35), -1, cv2.LINE_AA)
    cv2.line(img, (cx, ybot - 18), (cx, ybot), (0.15, 0.2, 0.28), 4)
    rect(cx - 22, ybot - 6, cx + 22, ybot, (60, 45, 30))

def bull(x, ybot, s):
    c = (0.12, 0.22, 0.30)  # бронза BGR
    cv2.ellipse(img, (x, ybot - int(28 * s)), (int(38 * s), int(20 * s)), 0, 0, 360, c, -1, cv2.LINE_AA)
    cv2.circle(img, (x + int(40 * s), ybot - int(36 * s)), int(13 * s), c, -1, cv2.LINE_AA)
    cv2.line(img, (x + int(44 * s), ybot - int(46 * s)), (x + int(56 * s), ybot - int(58 * s)), c, max(2, int(4 * s)), cv2.LINE_AA)
    for dx in (-26, -12, 14, 28):
        cv2.line(img, (x + int(dx * s), ybot - int(15 * s)), (x + int(dx * s), ybot), c, max(3, int(6 * s)), cv2.LINE_AA)
    rect(x - 45 * s, ybot - 5, x + 60 * s, ybot, (40, 34, 30))

def plant(cx, ybot):
    rect(cx - 26, ybot - 50, cx + 26, ybot, (180, 170, 160))
    for k in range(14):
        a = random.uniform(-2.6, -0.5); L = random.randint(50, 95)
        x2 = int(cx + np.cos(a) * L); y2 = int(ybot - 50 + np.sin(a) * L)
        cv2.ellipse(img, ((cx + x2) // 2, (ybot - 50 + y2) // 2), (L // 2, 9), np.degrees(a), 0, 360, (0.22, 0.42 + random.uniform(-.05, .05), 0.20), -1, cv2.LINE_AA)

def vase(cx, ybot):
    cv2.ellipse(img, (cx, ybot - 45), (24, 45), 0, 0, 360, (0.82, 0.84, 0.86), -1, cv2.LINE_AA)
    rect(cx - 8, ybot - 105, cx + 8, ybot - 80, (215, 212, 205))

# стеллаж: боковины и полки
for ys in shelves:
    rect(0, ys, W, ys + 16, WOOD)
for xs in (0, 410, 850, W - 18):
    rect(xs, 0, xs + 18, H, (100, 70, 44))
# наполнение (центр всё равно закрыт человеком)
books(30, 230, shelves[0]); globe(320, shelves[0], 48)
books(870, 1020, shelves[0]); bull(1120, shelves[0], 1.1)
plant(110, shelves[1]); books(200, 390, shelves[1])
books(870, 960, shelves[1]); vase(1010, shelves[1]); books(1060, 1240, shelves[1])
books(30, 180, shelves[2]); bull(300, shelves[2], 0.9)
books(880, 1240, shelves[2])
books(440, 830, shelves[0]); books(440, 600, shelves[1]); plant(720, shelves[1])

# тёплая LED-подсветка под каждой полкой
light = np.zeros((H, W), np.float32)
for ys in shelves[:2] + [0]:
    yl = ys + 16 if ys else 6
    for x in range(0, W):
        pass
    band = np.zeros((H, W), np.float32)
    band[yl:yl + 3, 20:W - 20] = 1
    light += cv2.GaussianBlur(band, (0, 0), 45) * 18
light = np.clip(light, 0, 1.2)
warm = np.array([0.45, 0.72, 1.0], np.float32)
img = img * (1 + 0.9 * light[..., None]) + warm * light[..., None] * 0.18
for ys in shelves[:2]:
    img[ys + 16:ys + 19, 20:W - 20] = np.array([0.75, 0.92, 1.0])
img = np.clip(img, 0, 1)
cv2.imwrite('shelf_sharp.png', (img * 255).astype(np.uint8))
# мягкий фокус как у камеры на человеке
bl = cv2.GaussianBlur(img, (0, 0), 7)
cv2.imwrite('shelf.png', (np.clip(bl, 0, 1) * 255).astype(np.uint8))
print('ok')
