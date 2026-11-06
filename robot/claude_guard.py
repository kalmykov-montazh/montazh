# Сторож приложения Claude (04.11.2026). Вызывается из publish.py каждые 10 минут.
# Причина: Claude (пакет Магазина) после своего обновления закрывается и сам не запускается
# (03.11 в 22:47 так и было — утром задачи не видели компьютер). Токены и лимит не тратит.
# Выключить сторожа: положить рядом файл «Claude не поднимать.txt» (содержимое любое). Убрать — снова работает.
import subprocess, time, ctypes
from pathlib import Path

HERE = Path(__file__).resolve().parent
OFF = HERE / 'Claude не поднимать.txt'
LOG = HERE / '_claude_сторож.txt'
NOWIN = 0x08000000                       # CREATE_NO_WINDOW
FALLBACK_AUMID = 'Claude_pzs8sxrjxfjjc!Claude'

def _note(s):
    try:
        old = LOG.read_text(encoding='utf-8').splitlines()[-200:] if LOG.exists() else []
        LOG.write_text('\n'.join(old + [f"{time.strftime('%Y-%m-%d %H:%M')} {s}"]) + '\n', encoding='utf-8')
    except Exception:
        pass

def _running():
    out = subprocess.run(['tasklist', '/fi', 'imagename eq claude.exe', '/nh', '/fo', 'csv'],
                         capture_output=True, text=True, creationflags=NOWIN, timeout=30).stdout
    return 'claude.exe' in out.lower()

def _aumid():
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-Command',
                              "(Get-StartApps | Where-Object { $_.AppID -like 'Claude_*!*' } | Select-Object -First 1).AppID"],
                             capture_output=True, text=True, creationflags=NOWIN, timeout=60).stdout.strip()
        return out or FALLBACK_AUMID
    except Exception:
        return FALLBACK_AUMID

def run():
    if OFF.exists():
        return
    if ctypes.windll.kernel32.GetTickCount64() < 5 * 60 * 1000:
        return                           # первые 5 минут после включения Claude поднимает автозагрузка
    if _running():
        return
    a = _aumid()
    subprocess.Popen(['explorer.exe', f'shell:AppsFolder\\{a}'], creationflags=NOWIN)
    _note(f'Claude был закрыт — запустил ({a})')
