# Step 6: generates data/bistro_lights.aqua from the emissive fixtures of the converted Bistro glTF.
#   python3 gen_lights.py  (run next to bistro.gltf produced by FBX2glTF)
import json,numpy as np
import os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'analyze.py')).read().split("mats=[m['name']")[0])  # reuse world transform code
mats=[m['name'] for m in g['materials']]
def boxes(names):
    out=[]
    for ni,n in enumerate(g['nodes']):
        if 'mesh' not in n: continue
        for p in g['meshes'][n['mesh']]['primitives']:
            if mats[p['material']] in names:
                a=g['accessors'][p['attributes']['POSITION']]
                lo=np.array(a['min']);hi=np.array(a['max'])
                cs=np.array([[x,y,z,1] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
                wc=(world[ni]@cs.T).T[:,:3]
                out.append((n.get('name',''),wc.min(0),wc.max(0)))
    return out
def small(b,lim=1.5): return [x for x in b if (x[2]-x[1]).max()<lim]
lights=[]
# street lamps (glass globes) -> warm point lights
for name,lo,hi in small(boxes({'Emissive_StreetLight'})):
    c=(lo+hi)/2
    if 'Lantern' in name: lights.append(('point',c,[1.0,0.62,0.32],900,7.0,None))
    elif 'StreetLight' in name or 'Streetlight' in name: lights.append(('point',c,[1.0,0.72,0.42],3500,16.0,None))
    else: lights.append(('spot',c+[0,-0.15,0],[1.0,0.78,0.5],2500,9.0,'down'))
# wall lamps / small spots on buildings
for name,lo,hi in small(boxes({'Spotlight_Glass_Emissive'})):
    c=(lo+hi)/2
    if 'Spotlights' in name: continue
    lights.append(('spot',c+[0,-0.1,0],[1.0,0.82,0.6],1800,8.0,'down'))
# big facade spotlights
for name,lo,hi in small(boxes({'Spotlight_Emissive'}),2.0):
    c=(lo+hi)/2
    lights.append(('spot',c+[0,-0.2,0],[0.75,0.85,1.0],12000,30.0,'facade'))
# string lights: colored glow points along each wire segment
cols={'Orange':[1,0.45,0.1],'Blue':[0.2,0.4,1],'White':[1,0.95,0.85],'Pink':[1,0.3,0.8],'Red':[1,0.1,0.08],'Green':[0.2,1,0.3]}
for k,col in cols.items():
    for name,lo,hi in boxes({f'Paris_StringLights_01_{k}_Color_Emissive'}):
        if (hi-lo).max()>3:  # whole wire: put a light at its centre
            lights.append(('point',(lo+hi)/2,col,600,6.0,None))
print(len(lights), {t:sum(1 for l in lights if l[0]==t) for t in ('point','spot')})
def fmt(v): return '['+','.join(f'{x:.3f}d' for x in v)+']'
rows=[]
for t,c,col,lm,fall,d in lights:
    direction={'down':[0,-1,0.0],'facade':[0.35,-0.55,0.75],None:[0,-1,0]}[d]
    rows.append(f'    ["{t}", {fmt(c)}, {fmt(col)}, {lm}, {fall:.1f}d, {fmt(direction)}]')
src='''# Generated from the Bistro exterior's emissive fixtures (street lamps, lanterns, wall lamps, facade
# spotlights and string lights) / 由 Bistro 外景的發光燈具自動產生。
# [type 類型, position 位置, color 顏色, lumens 流明, falloff 衰減距離, direction 方向]
變數 Lights = [
'''+',\n'.join(rows)+'''
];
變數 光源列表 = Lights;
'''
open('bistro_lights.aqua','w').write(src)
