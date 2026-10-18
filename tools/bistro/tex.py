# Step 2: decode the Bistro DDS textures, resize to <= 1024 px and convert DirectX normal maps to OpenGL
# convention (Filament/glTF). Resumable: existing PNGs are skipped.
#   python3 tex.py /path/to/Bistro_v5_2/Textures [max_size]
import os,glob,sys
import numpy as np
from PIL import Image
src=sys.argv[1] if len(sys.argv)>1 else os.path.expanduser('~/Bistro_v5_2/Textures')
B=os.environ.get('BISTRO_WORK','/tmp/bistro'); dst=os.path.join(B,'tex'); os.makedirs(dst,exist_ok=True)
MAX=int(sys.argv[2]) if len(sys.argv)>2 else 1024
for f in sorted(glob.glob(src+'/*')):
    base=os.path.splitext(os.path.basename(f))[0]
    out=os.path.join(dst,base+'.png')
    if os.path.exists(out): continue
    try:
        im=Image.open(f); im.load()
    except Exception as e:
        print('ERR',f,e,flush=True); continue
    w,h=im.size; s=min(1.0,MAX/max(w,h))
    kind=base.rsplit('_',1)[-1].lower()
    if kind=='normal':
        im=im.convert('RGB')
        if s<1: im=im.resize((max(1,int(w*s)),max(1,int(h*s))),Image.LANCZOS)
        a=np.asarray(im).astype(np.float32)/127.5-1.0
        x=a[...,0]; y=-a[...,1]   # DirectX -> OpenGL
        z=np.sqrt(np.clip(1-x*x-y*y,0,1))
        n=np.stack([x,y,z],-1); n/=np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-6)
        im=Image.fromarray(np.clip((n+1)*127.5+0.5,0,255).astype(np.uint8),'RGB')
    else:
        if kind=='basecolor':
            im=im.convert('RGBA')
            if im.getextrema()[3][0]==255: im=im.convert('RGB')
        else: im=im.convert('RGB')
        if s<1: im=im.resize((max(1,int(w*s)),max(1,int(h*s))),Image.LANCZOS)
    tmp=out+'.tmp.png'; im.save(tmp,compress_level=1); os.replace(tmp,out)
    print('ok',base,im.size,flush=True)
print('DONE',flush=True)
