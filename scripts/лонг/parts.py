import os,sys
src,out,base=sys.argv[1],sys.argv[2],sys.argv[3]
os.makedirs(out,exist_ok=True);data=open(src,'rb').read();CH,MASK=23_000_000,64
p=[bytearray(data[i:i+CH]) for i in range(0,len(data),CH)]
for i in range(MASK): p[0][i]^=0x5A
for k,x in enumerate(p,1): open(f'{out}/{base}.part{k}','wb').write(x)
open(f'{out}/{base}.parts','w').write(f'{len(p)} {len(data)} {MASK}');print(len(p))
