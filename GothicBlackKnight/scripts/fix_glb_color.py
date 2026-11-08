"""Encode the generator's linear Non-Color albedo images as glTF-mandated sRGB.
Idempotent. Roughness/metallic data images remain linear. Geometry is unchanged.
"""
import struct,json,io,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.deps'))
from PIL import Image
p=Path(sys.argv[1]);raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);binary=raw[28+n:]
if g.get('asset',{}).get('extras',{}).get('linearAlbedoConvertedToSRGB'):print('Already corrected');sys.exit(0)
base=set();data=set()
for m in g['materials']:
 q=m.get('pbrMetallicRoughness',{})
 if 'baseColorTexture' in q:base.add(g['textures'][q['baseColorTexture']['index']]['source'])
 if 'metallicRoughnessTexture' in q:data.add(g['textures'][q['metallicRoughnessTexture']['index']]['source'])
assert not base.intersection(data)
lut=[round(255*(12.92*(x/255) if x/255<=.0031308 else 1.055*(x/255)**(1/2.4)-.055)) for x in range(256)]
replacements={}
for i in base:
 view=g['images'][i]['bufferView'];v=g['bufferViews'][view];im=Image.open(io.BytesIO(binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).convert('RGBA')
 r,green,b,a=im.split();im=Image.merge('RGBA',(r.point(lut),green.point(lut),b.point(lut),a));buf=io.BytesIO();im.save(buf,format='PNG',optimize=True);replacements[view]=buf.getvalue()
new=bytearray()
for i,v in enumerate(g['bufferViews']):
 payload=replacements.get(i,binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);new.extend(b'\0'*((-len(new))%4));v['byteOffset']=len(new);v['byteLength']=len(payload);new.extend(payload)
g['buffers'][0]['byteLength']=len(new);new.extend(b'\0'*((-len(new))%4));g['asset'].setdefault('extras',{})['linearAlbedoConvertedToSRGB']=True
text=json.dumps(g,separators=(',',':')).encode();text+=b' '*((-len(text))%4);result=struct.pack('<III',0x46546c67,2,28+len(text)+len(new))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(new),0x004e4942)+new;p.write_bytes(result)
print(json.dumps({'converted_albedo_images':len(base),'bytes':len(result),'geometry_changed':False}))
