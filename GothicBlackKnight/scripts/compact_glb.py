"""Store normals/tangents as normalized signed 16-bit vectors using KHR_mesh_quantization.
Positions, indices, UVs and images are unchanged. Maximum component error is 1/65534.
"""
from pathlib import Path
import struct,json,sys
path=Path(sys.argv[1]);raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+size]);binary=raw[28+size:]
if g.get('asset',{}).get('extras',{}).get('compactVectorFrames'):print('Already compacted');sys.exit(0)
indices=set()
for mesh in g['meshes']:
 for primitive in mesh['primitives']:
  for semantic in ('NORMAL','TANGENT'):
   if semantic in primitive['attributes']:indices.add(primitive['attributes'][semantic])
replacements={};worst=0
for index in indices:
 a=g['accessors'][index];v=g['bufferViews'][a['bufferView']]
 assert a['componentType']==5126 and not a.get('normalized') and not a.get('sparse')
 assert sum(x.get('bufferView')==a['bufferView'] for x in g['accessors'])==1
 count={'VEC3':3,'VEC4':4}[a['type']];stride=v.get('byteStride',count*4);offset=v.get('byteOffset',0)+a.get('byteOffset',0);payload=bytearray()
 for i in range(a['count']):
  row=struct.unpack_from('<'+'f'*count,binary,offset+i*stride);q=[round(max(-1,min(1,x))*32767) for x in row]
  worst=max(worst,max(abs(x-y/32767) for x,y in zip(row,q)))
  payload.extend(struct.pack('<'+'h'*count,*q));payload.extend(b'\0'*((-len(payload))%4))
 a['componentType']=5122;a['normalized']=True;a['byteOffset']=0
 a.pop('min',None);a.pop('max',None);v['byteStride']=8;replacements[a['bufferView']]=bytes(payload)
new=bytearray()
for i,v in enumerate(g['bufferViews']):
 payload=replacements.get(i,binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);new.extend(b'\0'*((-len(new))%4));v['byteOffset']=len(new);v['byteLength']=len(payload);new.extend(payload)
for key in ['extensionsUsed','extensionsRequired']:
 g.setdefault(key,[])
 if 'KHR_mesh_quantization' not in g[key]:g[key].append('KHR_mesh_quantization')
g['buffers'][0]['byteLength']=len(new);new.extend(b'\0'*((-len(new))%4));g['asset'].setdefault('extras',{})['compactVectorFrames']={'maximum_component_error':worst,'positions_changed':False}
text=json.dumps(g,separators=(',',':')).encode();text+=b' '*((-len(text))%4)
result=struct.pack('<III',0x46546c67,2,28+len(text)+len(new))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(new),0x004e4942)+new;path.write_bytes(result)
print(json.dumps({'before':len(raw),'after':len(result),'maximum_component_error':worst}))
