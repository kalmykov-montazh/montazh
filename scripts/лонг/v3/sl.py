import numpy as np,subprocess
# 4 fps, slide zone = left part above camera row + top band
b=subprocess.run(['ffmpeg','-v','error','-i','raw.mp4','-vf','fps=4,crop=1280:1080:0:0,scale=160:135,format=gray','-f','rawvideo','-'],capture_output=True).stdout
a=np.frombuffer(b,np.uint8).reshape(-1,135,160).astype(np.float32)
d=np.abs(np.diff(a,axis=0)).mean((1,2))
ch=[(i+1)/4 for i in np.where(d>6)[0]]
out=[]
for t in ch:
    if not out or t-out[-1]>2: out.append(t)
print(len(out));print(' '.join(f'{t:.1f}' for t in out))
np.save('sld.npy',d)
