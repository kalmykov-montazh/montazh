import os, sys
src, out, name = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
data = open(src, 'rb').read(); CH, MASK = 23_000_000, 64
parts = [bytearray(data[i:i + CH]) for i in range(0, len(data), CH)]
for i in range(MASK): parts[0][i] ^= 0x5A
for k, p in enumerate(parts, 1): open(f'{out}/{name}.part{k}', 'wb').write(p)
open(f'{out}/{name}.parts', 'w').write(f'{len(parts)} {len(data)} {MASK}')
print(len(parts))
