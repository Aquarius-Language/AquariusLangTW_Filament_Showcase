# Step 1 helper: computes node world transforms of the converted Bistro glTF (used by gen_lights.py).
import json,numpy as np,collections
g=json.load(open('bistro.gltf'))
def mat(n):
    if 'matrix' in n: return np.array(n['matrix']).reshape(4,4).T
    t=np.array(n.get('translation',[0,0,0])); r=n.get('rotation',[0,0,0,1]); s=np.array(n.get('scale',[1,1,1]))
    x,y,z,w=r
    R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    M=np.eye(4); M[:3,:3]=R*s; M[:3,3]=t; return M
world={}
def walk(i,P):
    W=P@mat(g['nodes'][i]); world[i]=W
    for c in g['nodes'][i].get('children',[]): walk(c,W)
for r in g['scenes'][0]['nodes']: walk(r,np.eye(4))
mats=[m['name'] for m in g['materials']]
hits=collections.defaultdict(list)
for ni,n in enumerate(g['nodes']):
    if 'mesh' not in n: continue
    for p in g['meshes'][n['mesh']]['primitives']:
        mn=mats[p['material']]
        if any(k in mn for k in ['Emissive','Lantern','Light_Bulb','StringLights','Spotlight','Streetlight_Support']):
            a=g['accessors'][p['attributes']['POSITION']]
            lo=np.array(a['min']);hi=np.array(a['max'])
            corners=np.array([[x,y,z,1] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
            wc=(world[ni]@corners.T).T[:,:3]
            hits[mn].append((n.get('name'),wc.min(0),wc.max(0)))
for k,v in hits.items():
    print(k,len(v))
    for name,lo,hi in v[:40]: print('   ',name,np.round((lo+hi)/2,2),np.round(hi-lo,2))
# scene bounds
allc=[]
for ni,n in enumerate(g['nodes']):
    if 'mesh' in n:
        for p in g['meshes'][n['mesh']]['primitives']:
            a=g['accessors'][p['attributes']['POSITION']]; allc.append(world[ni][:3,:3]@np.array(a['min'])+world[ni][:3,3])
print('bounds',np.min(allc,0),np.max(allc,0))
print('cam',world[[i for i,n in enumerate(g['nodes']) if n.get('name')=='Camera'][0]].round(2))
