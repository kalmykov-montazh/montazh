"""Обрезать в упаковках всё, начиная со строки «Обложка:». Аргументы: папка mode(check|fix)"""
import os, re, sys
root, mode = sys.argv[1], sys.argv[2]
pat = re.compile(r'^\s*обложк[аи]\s*:?', re.I | re.M)
changed, bad = [], []
for d, _, fs in os.walk(root):
    for f in fs:
        if not f.lower().endswith('.txt'):
            continue
        p = os.path.join(d, f)
        t = open(p, encoding='utf-8-sig', errors='replace').read()
        m = pat.search(t)
        if not m:
            continue
        new = t[:m.start()].rstrip()
        last = new.splitlines()[-1].strip() if new else ''
        rel = os.path.relpath(p, root)
        changed.append(rel)
        if not last.startswith('#'):
            bad.append(f'{rel} [конец: {last[:40]}]')
        if mode == 'fix':
            open(p, 'w', encoding='utf-8').write(new + '\n')
open('changed.txt', 'w', encoding='utf-8').write('\n'.join(changed))
print(f'::notice::Найдено {len(changed)} файлов с блоком обложки')
print('::notice::Не хэштеги в конце: ' + (' | '.join(bad) if bad else 'нет'))
print('::notice::' + ' | '.join(changed)[:2500])
