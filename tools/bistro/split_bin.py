# Splits a glTF's single binary buffer into GitHub-friendly (< limit) parts at bufferView boundaries.
import json,os,sys
path=sys.argv[1]; limit=int(float(sys.argv[2])*1024*1024) if len(sys.argv)>2 else 40*1024*1024
d=os.path.dirname(path); g=json.load(open(path))
real=[i for i,b in enumerate(g['buffers']) if 'uri' in b]
assert len(real)==1, real
bi=real[0]; uri=g['buffers'][bi]['uri']; data=open(os.path.join(d,uri),'rb').read()
refs=[]  # (holder dict, offset key)
for v in g['bufferViews']:
    e=v.get('extensions',{}).get('EXT_meshopt_compression')
    if e and e['buffer']==bi: refs.append(e)
    elif v['buffer']==bi: refs.append(v)
refs.sort(key=lambda r:r.get('byteOffset',0))
parts=[];cur=bytearray();stem=os.path.splitext(uri)[0]
newbuf=[]
for r in refs:
    off=r.get('byteOffset',0); ln=r['byteLength']; chunk=data[off:off+ln]
    if len(cur)+ln>limit and cur: parts.append(cur); cur=bytearray()
    while len(cur)%4: cur.append(0)
    r['_part']=len(parts); r['byteOffset']=len(cur); cur+=chunk
parts.append(cur)
base=len(g['buffers'])
names=[]
for i,p in enumerate(parts):
    n=f'{stem}_{i:02d}.bin'; open(os.path.join(d,n),'wb').write(p); names.append(n)
    g['buffers'].append({'uri':n,'byteLength':len(p)})
for r in refs:
    k=base+r.pop('_part')
    if 'buffer' in r: r['buffer']=k
# old buffer becomes unused: replace with smallest stub to keep indices valid
g['buffers'][bi]={'byteLength':0} if False else g['buffers'][bi]
# remove original buffer entry by remapping indices
old=bi
def remap(i): return i-1 if i>old else i
del g['buffers'][old]
for v in g['bufferViews']:
    v['buffer']=remap(v['buffer'])
    e=v.get('extensions',{}).get('EXT_meshopt_compression')
    if e: e['buffer']=remap(e['buffer'])
os.remove(os.path.join(d,uri))
json.dump(g,open(path,'w'),separators=(',',':'))
print('parts',[(n,len(p)//1024//1024) for n,p in zip(names,parts)])
