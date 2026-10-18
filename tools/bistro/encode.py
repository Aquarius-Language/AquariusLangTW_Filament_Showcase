# Step 3: encodes the PNG textures used by the exterior materials to KTX2/ETC1S (BasisU), resumable.
import os,subprocess,time,sys
t0=time.time(); budget=float(sys.argv[1]) if len(sys.argv)>1 else 160
B=os.environ.get('BISTRO_WORK','/tmp/bistro'); src=B+'/tex'; dst=B+'/ktx'; os.makedirs(dst,exist_ok=True)
# Texture names follow the Bistro convention <Material>_{BaseColor,Normal,Specular,Emissive}.
import json
_g=json.load(open(B+'/ext/bistro_out/bistro.gltf'))
wanted=sorted({f"{m['name'].replace('.DoubleSided','')}_{k}" for m in _g['materials'] for k in ('BaseColor','Normal','Specular','Emissive')})
have=set(os.path.splitext(f)[0] for f in os.listdir(src))
todo=[w for w in wanted if w in have and not os.path.exists(f'{dst}/{w}.ktx2')]
print('todo',len(todo),flush=True)
for w in todo:
    if time.time()-t0>budget: break
    kind=w.rsplit('_',1)[-1]
    args=[os.environ.get('BASISU','basisu'),'-ktx2','-mipmap','-comp_level','1','-q','128' if kind!='Normal' else '200']
    if kind in ('Normal','Specular'): args+=['-linear']
    args+=[f'{src}/{w}.png','-output_file',f'{dst}/{w}.ktx2.tmp']
    r=subprocess.run(args,capture_output=True)
    if r.returncode==0: os.replace(f'{dst}/{w}.ktx2.tmp',f'{dst}/{w}.ktx2')
    else: print('FAIL',w,r.stdout[-300:],r.stderr[-300:],flush=True)
left=[w for w in wanted if w in have and not os.path.exists(f'{dst}/{w}.ktx2')]
print('left',len(left),flush=True)
