import numpy as np,subprocess
def mo(src,crop,ss,n=1200):
    vf=(f'crop={crop},' if crop else '')+'scale=64:36,format=gray'
    b=subprocess.run(['ffmpeg','-v','error','-ss',str(ss),'-i',src,'-frames:v',str(n),'-vf',vf,'-f','rawvideo','-'],capture_output=True).stdout
    a=np.frombuffer(b,np.uint8).reshape(-1,36,64).astype(np.float32);return np.abs(np.diff(a,axis=0)).mean((1,2))
for ss in (300,1500,2300):
    A=mo('raw.mp4','632:436:1287:643',ss);B=mo('cam.mp4',None,ss)
    best=max(range(-30,31),key=lambda k:np.corrcoef(A[60:-60],B[60+k:len(B)-60+k])[0,1])
    print(ss,best,'frames (cam=raw +k)')
