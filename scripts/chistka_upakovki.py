"""Обрезать в упаковках всё, начиная со строки «Обложка:». Аргументы: папка mode(check|fix)"""
import os, re, sys
root, mode = sys.argv[1], sys.argv[2]
if mode in ('links-check', 'links-fix'):
    # 25.10.2026: убрать из упаковок строки со ссылками и отсылками к ним («Полное видео…», «Монтаж делал в приложении…»)
    bad = re.compile(r'https?://|ссылк|в шапке профиля|в описании|полное видео|полном видео|монтаж делал в приложени', re.I)
    changed, lines_out = [], []
    for d, _, fs in os.walk(root):
        for f in fs:
            if f != 'упаковка.txt':
                continue
            p = os.path.join(d, f); t = open(p, encoding='utf-8-sig', errors='replace').read()
            ls = t.split('\n'); keep = [ls[0]] + [l for l in ls[1:] if not bad.search(l)]
            if keep != ls:
                rel = os.path.relpath(p, root); changed.append(rel)
                lines_out += [f'{rel.split("/")[-2][:40]}: {l.strip()[:70]}' for l in ls[1:] if bad.search(l)]
                if mode == 'links-fix':
                    open(p, 'w', encoding='utf-8').write('\n'.join(keep))
    open('changed.txt', 'w', encoding='utf-8').write('\n'.join(changed))
    print(f'::notice::Упаковок со ссылками: {len(changed)}')
    txt = ' | '.join(lines_out)
    for i in range(0, min(len(txt), 24000), 3000):
        print('::notice::' + txt[i:i + 3000])
    sys.exit(0)
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
