# 14.11.2026 (решение Евгения): в описаниях объявлений (карусели, рилсы — аренда и продажа) ссылки на
# Telegram-канал НЕТ ни в одной сети. Канал — только первым комментарием («Больше объектов… + ссылка»).
# Строки со ссылкой t.me (и любой другой) из текста вырезаем; в Telegram-группах это правило не действует.
import re

_URL = re.compile(r'(https?://\S+|www\.\S+|t\.me/\S+|wa\.me/\S+)', re.I)


def bez_ssylok(text):
    out = []
    for line in (text or '').split('\n'):
        if not _URL.search(line):
            out.append(line); continue
        if 't.me/' in line.lower():
            continue                              # строка про канал целиком уходит — канал ставим комментарием
        rest = _URL.sub('', line).rstrip(' :—-–👉📲📱').rstrip()
        if rest.strip():
            out.append(rest)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip()
