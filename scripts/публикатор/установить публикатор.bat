@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Установка публикатора. Окно не закрывайте до конца.
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo Ставлю Python...
  winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
  echo.
  echo Python установлен. ЗАКРОЙТЕ это окно и запустите этот файл ещё раз.
  pause
  exit /b
)
py -m pip install --upgrade playwright
if errorlevel 1 goto fail
schtasks /create /f /tn "Publikator" /sc minute /mo 10 /tr "wscript.exe \"%~dp0publish.vbs\""
if errorlevel 1 goto fail
echo.
echo Готово. Теперь запустите «войти в соцсети.bat».
pause
exit /b
:fail
echo.
echo Не получилось. Сфотографируйте это окно и отправьте Claude.
pause
