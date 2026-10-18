# Step 4: rebuilds the FBX2glTF output into a PBR glTF that references KTX2 textures (KHR_texture_basisu),
# removes the baked camera/sun (the showcase adds its own lights) and keeps the string-light wind animation.
import json,os,sys
from PIL import Image
B=os.environ.get('BISTRO_WORK','/tmp/bistro')
g=json.load(open(f'{B}/ext/bistro_out/bistro.gltf'))
g['buffers'][0]['uri']='../ext/bistro_out/buffer.bin'
ktx=set(os.path.splitext(f)[0] for f in os.listdir(f'{B}/ktx'))
images=[];textures=[];index={}
def tex(name):
    if name not in ktx: return None
    if name not in index:
        images.append({'uri':f'../ktx/{name}.ktx2','mimeType':'image/ktx2'})
        textures.append({'sampler':0,'extensions':{'KHR_texture_basisu':{'source':len(images)-1}}})
        index[name]=len(textures)-1
    return {'index':index[name]}
def has_alpha(name):
    p=f'{B}/tex/{name}.png'
    if not os.path.exists(p): return False
    im=Image.open(p)
    if im.mode!='RGBA': return False
    lo,hi=im.getchannel('A').getextrema(); return lo<250
def strength(n):
    if 'StringLights' in n: return 80.0
    if 'Shopsign' in n: return 25.0
    if 'Lantern' in n or 'StreetLight' in n or 'Spotlight' in n: return 50.0
    return 20.0
used=set(['KHR_texture_basisu'])
for m in g['materials']:
    name=m['name']; base=name.replace('.DoubleSided','')
    m.pop('extras',None)
    if name.endswith('.DoubleSided') or base.startswith('Foliage'): m['doubleSided']=True
    pbr=m.setdefault('pbrMetallicRoughness',{})
    bc=tex(base+'_BaseColor')
    if bc: pbr['baseColorTexture']=bc; pbr['baseColorFactor']=[1,1,1,1]
    sp=tex(base+'_Specular')
    if sp:
        pbr['metallicRoughnessTexture']=sp; pbr['metallicFactor']=1.0; pbr['roughnessFactor']=1.0
        m['occlusionTexture']=dict(sp)
    else:
        pbr['metallicFactor']=0.0; pbr['roughnessFactor']=0.6
    nm=tex(base+'_Normal')
    if nm: m['normalTexture']=nm
    em=tex(base+'_Emissive')
    if em:
        m['emissiveTexture']=em; m['emissiveFactor']=[1,1,1]
        m.setdefault('extensions',{})['KHR_materials_emissive_strength']={'emissiveStrength':strength(base)}
        used.add('KHR_materials_emissive_strength')
    elif 'emissiveFactor' in m and 'Emissive' in base:
        m.setdefault('extensions',{})['KHR_materials_emissive_strength']={'emissiveStrength':strength(base)}
        used.add('KHR_materials_emissive_strength')
    else: m.pop('emissiveFactor',None)
    if 'Glass' in base and 'MASKED' not in base and 'Glass_Dirty' not in base:
        m['alphaMode']='BLEND'
    elif bc and has_alpha(base+'_BaseColor'):
        m['alphaMode']='MASK'; m['alphaCutoff']=0.5
    else: m['alphaMode']='OPAQUE'
g['images']=images; g['textures']=textures
g['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}]
# drop camera & sun (lights are added by the application), keep animations
for n in g['nodes']:
    n.pop('camera',None)
    if 'extensions' in n: n['extensions'].pop('KHR_lights_punctual',None); 
    if n.get('extensions')=={}: n.pop('extensions')
g.pop('cameras',None); g.pop('extensions',None)
g['extensionsUsed']=sorted(used); g['extensionsRequired']=['KHR_texture_basisu']
os.makedirs(f'{B}/fixed',exist_ok=True)
json.dump(g,open(f'{B}/fixed/bistro.gltf','w'))
print('materials',len(g['materials']),'textures',len(textures))
