@echo off
chcp 65001 >nul
schtasks /query /tn "Montazh skleika" /v /fo LIST > "%~dp0zadacha.txt" 2>&1
wscript.exe "%~dp0join.vbs"
echo Готово, можно закрыть окно и написать Claude.
pause
