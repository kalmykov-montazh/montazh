@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Откроется окно Chrome для робота. Войдите в нём в Facebook (остальные вкладки пока можно пропустить), потом закройте окно.
py publish.py login
