@echo off
chcp 65001 >nul
schtasks /create /f /tn "Montazh skleika" /sc minute /mo 3 /tr "wscript.exe \"%~dp0join.vbs\""
if errorlevel 1 (
  echo.
  echo Не получилось. Сфотографируй это окно и отправь Claude.
) else (
  echo.
  echo Готово. Склейщик будет проверять папку Готовые! каждые 3 минуты.
  wscript.exe "%~dp0join.vbs"
)
echo.
pause
