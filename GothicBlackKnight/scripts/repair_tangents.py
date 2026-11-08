"""Repair zero tangent frames at generated bevel/UV corner singularities.

Positions, normals, indices, UVs and textures are unchanged. An orthonormal
fallback is used only where Blender exported an undefined zero tangent.
"""
import json,struct,math,sys,hashlib
from pathlib import Path
p=Path(sys.argv[1]);raw=bytearray(p.read_bytes());before=hashlib.sha256(raw).hexdigest()
length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length]);bin_start=28+length
def at(accessor,index):
    a=g['accessors'][accessor];v=g['bufferViews'][a['bufferView']]
    assert a['componentType']==5126
    n={'VEC3':3,'VEC4':4}[a['type']]
    return bin_start+v.get('byteOffset',0)+a.get('byteOffset',0)+index*v.get('byteStride',n*4)
fixed=0;seen=set()
for mesh in g['meshes']:
    for primitive in mesh['primitives']:
        attrs=primitive['attributes']
        if 'TANGENT' not in attrs:continue
        ti=attrs['TANGENT'];ni=attrs['NORMAL']
        if ti in seen:continue
        seen.add(ti)
        for i in range(g['accessors'][ti]['count']):
            off=at(ti,i);x,y,z,w=struct.unpack_from('<4f',raw,off)
            norm=math.sqrt(x*x+y*y+z*z)
            if norm>.5:continue
            nx,ny,nz=struct.unpack_from('<3f',raw,at(ni,i))
            # Cross the normal with the least aligned cardinal direction.
            axis=min(range(3),key=lambda k:abs((nx,ny,nz)[k]))
            x,y,z=[(0,nz,-ny),(-nz,0,nx),(ny,-nx,0)][axis]
            norm=math.sqrt(x*x+y*y+z*z);assert norm>1e-8
            struct.pack_into('<4f',raw,off,x/norm,y/norm,z/norm,1 if w>=0 else -1)
            fixed+=1
p.write_bytes(raw)
report={'repaired_zero_tangents':fixed,'geometry_uv_textures_unchanged':True,'before_sha256':before,'after_sha256':hashlib.sha256(raw).hexdigest()}
(p.parent/'tangent_repair.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
