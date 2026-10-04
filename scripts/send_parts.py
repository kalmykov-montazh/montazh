#!/usr/bin/env python3
"""Готовит видео к записи на Диск кусками: python3 send_parts.py видео.mp4 папка_вывода
Куски по 23 МБ: видео.mp4.part1..N, первые 64 байта первого куска XOR 0x5A (иначе передача портит mp4),
и маркер видео.mp4.parts = "N размер 64". Записывать на Диск по stagedPath: сначала все куски, маркер ПОСЛЕДНИМ.
Склейщик на компьютере (скрипты/join.ps1, задача «Montazh skleika», раз в 3 мин) соберёт видео.mp4 и удалит куски."""
import os, sys
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
data = open(src, 'rb').read()
CH, MASK = 23_000_000, 64
parts = [bytearray(data[i:i + CH]) for i in range(0, len(data), CH)]
for i in range(MASK): parts[0][i] ^= 0x5A
for k, p in enumerate(parts, 1):
    open(f'{out}/видео.mp4.part{k}', 'wb').write(p)
open(f'{out}/видео.mp4.parts', 'w').write(f'{len(parts)} {len(data)} {MASK}')
print(len(parts), 'кусков,', len(data), 'байт')
