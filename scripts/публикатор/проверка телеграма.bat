@echo off
cd /d "%~dp0"
py -c "import common; common.tg('\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0441\u0432\u044f\u0437\u0438, \u0440\u043e\u0431\u043e\u0442 \u043d\u0430 \u043c\u0435\u0441\u0442\u0435'); print('OK - check Telegram')"
pause
