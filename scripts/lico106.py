# 24.11.2026: 106 точек лица (2d106det.onnx из insightface buffalo_l) — глаза и рот для выбора кадра обложки.
import os, numpy as np, cv2
import onnxruntime as ort
M = os.environ.get("LM106") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "2d106det.onnx")
_S = ort.InferenceSession(M, providers=['CPUExecutionProvider']); _IN = _S.get_inputs()[0].name
def landmarks(img, box):
    """img — BGR, box — (x, y, w, h) лица в этих же координатах."""
    x, y, w, h = box; cx, cy = x + w / 2, y + h / 2; sc = 192 / (max(w, h) * 1.5)
    A = np.array([[sc, 0, 96 - cx * sc], [0, sc, 96 - cy * sc]], np.float32)
    a = cv2.warpAffine(img, A, (192, 192))
    b = cv2.dnn.blobFromImage(a, 1.0, (192, 192), (0, 0, 0), swapRB=True)
    p = (_S.run(None, {_IN: b})[0].reshape(-1, 2) + 1) * 96
    Ai = cv2.invertAffineTransform(A); return p @ Ai[:, :2].T + Ai[:, 2]
_d = lambda a, b: float(np.hypot(*(a - b)))
def metr(P):
    """(глаза мин, глаза ср, рот внутри, рот снаружи). Левый глаз 35/39 углы, 40-42 верх, 33/36/37 низ; правый 89/93, 94-96, 87/90/91;
    рот: углы 52/61, внутренние 66,62,70 / 54,60,57, наружные 71 / 53."""
    el = (_d(P[40], P[33]) + _d(P[41], P[36]) + _d(P[42], P[37])) / (3 * _d(P[35], P[39]))
    er = (_d(P[94], P[87]) + _d(P[95], P[90]) + _d(P[96], P[91])) / (3 * _d(P[89], P[93]))
    mw = _d(P[52], P[61])
    mi = (_d(P[62], P[60]) + _d(P[66], P[54]) + _d(P[70], P[57])) / (3 * mw)
    mo = _d(P[71], P[53]) / mw
    return min(el, er), (el + er) / 2, mi, mo
