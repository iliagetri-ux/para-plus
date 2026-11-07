"""Convert the validated static GLB into an Apple Quick Look USDZ using OpenUSD.
Dependency: python -m pip install --target .deps usd-core==26.11
No Blender USD support required. Geometry and packed PBR maps come from the GLB.
"""
from pathlib import Path
import sys,json,struct,zipfile,math
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'.deps'))
from PIL import Image
from pxr import Usd,UsdGeom,UsdShade,UsdUtils,Sdf,Gf,Vt,Kind,UsdValidation
OUT=ROOT/'artifacts';WORK=ROOT/'usd_work';WORK.mkdir(exist_ok=True);(WORK/'textures').mkdir(exist_ok=True)
data=(OUT/'GothicBlackKnight.glb').read_bytes();pos=12
while pos<len(data):
 size,kind=struct.unpack_from('<II',data,pos);chunk=data[pos+8:pos+8+size]
 if kind==0x4e4f534a:g=json.loads(chunk)
 elif kind==0x004e4942:binary=chunk
 pos+=size+8

def access(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0)
 assert not a.get('sparse'), 'Sparse attributes are not supported'
 count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];fmt={5126:'f',5125:'I',5123:'H',5121:'B',5122:'h'}[a['componentType']]
 item=struct.Struct('<'+fmt*count);stride=v.get('byteStride',item.size)
 values=[item.unpack_from(binary,offset+k*stride) for k in range(a['count'])]
 if a.get('normalized'):
  assert a['componentType']==5122, 'Unsupported normalized attribute'
  values=[tuple(max(-1,x/32767) for x in row) for row in values]
 return [x[0] for x in values] if count==1 else values
for i,im in enumerate(g.get('images',[])):
 v=g['bufferViews'][im['bufferView']];offset=v.get('byteOffset',0)
 assert im['mimeType']=='image/png'
 (WORK/'textures'/f'image_{i:03d}.png').write_bytes(binary[offset:offset+v['byteLength']])
stage=Usd.Stage.CreateNew(str(WORK/'GothicBlackKnight.usdc'));UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.y);UsdGeom.SetStageMetersPerUnit(stage,1.0)
root=UsdGeom.Xform.Define(stage,'/Knight');stage.SetDefaultPrim(root.GetPrim());Usd.ModelAPI(root).SetKind(Kind.Tokens.component)
# Explicit hierarchy preserves the up-axis root transform in Blender's USD importer.
UsdGeom.Xform.Define(stage,'/Knight/Geometry');UsdGeom.Scope.Define(stage,'/Knight/Materials')
materials=[]
for i,source in enumerate(g['materials']):
 path=f'/Knight/Materials/Material_{i:02d}';m=UsdShade.Material.Define(stage,path)
 shader=UsdShade.Shader.Define(stage,path+'/Surface');shader.CreateIdAttr('UsdPreviewSurface')
 shader.CreateOutput('surface',Sdf.ValueTypeNames.Token);m.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
 reader=UsdShade.Shader.Define(stage,path+'/UV');reader.CreateIdAttr('UsdPrimvarReader_float2');reader.CreateInput('varname',Sdf.ValueTypeNames.String).Set('st');reader.CreateOutput('result',Sdf.ValueTypeNames.Float2)
 p=source.get('pbrMetallicRoughness',{});factor=p.get('baseColorFactor',[1,1,1,1]);metal=p.get('metallicFactor',1);rough=p.get('roughnessFactor',1)
 shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*factor[:3]));shader.CreateInput('metallic',Sdf.ValueTypeNames.Float).Set(metal);shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(rough)
 def tex(key,label,color_space,scale):
  image_index=g['textures'][p[key]['index']]['source'];t=UsdShade.Shader.Define(stage,path+'/'+label);t.CreateIdAttr('UsdUVTexture')
  t.CreateInput('file',Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(f'textures/image_{image_index:03d}.png'))
  t.CreateInput('sourceColorSpace',Sdf.ValueTypeNames.Token).Set(color_space);t.CreateInput('wrapS',Sdf.ValueTypeNames.Token).Set('repeat');t.CreateInput('wrapT',Sdf.ValueTypeNames.Token).Set('repeat')
  t.CreateInput('scale',Sdf.ValueTypeNames.Float4).Set(Gf.Vec4f(*scale));t.CreateInput('st',Sdf.ValueTypeNames.Float2).ConnectToSource(reader.ConnectableAPI(),'result')
  for channel in ['r','g','b']:t.CreateOutput(channel,Sdf.ValueTypeNames.Float)
  t.CreateOutput('rgb',Sdf.ValueTypeNames.Float3);return t
 if 'baseColorTexture' in p:shader.GetInput('diffuseColor').ConnectToSource(tex('baseColorTexture','Color','sRGB',factor).ConnectableAPI(),'rgb')
 if 'metallicRoughnessTexture' in p:
  t=tex('metallicRoughnessTexture','SurfaceMap','raw',[1,rough,metal,1]);shader.GetInput('metallic').ConnectToSource(t.ConnectableAPI(),'b');shader.GetInput('roughness').ConnectToSource(t.ConnectableAPI(),'g')
 if 'normalTexture' in source:
  q=source['normalTexture'];image_index=g['textures'][q['index']]['source'];scale=q.get('scale',1)
  t=UsdShade.Shader.Define(stage,path+'/NormalMap');t.CreateIdAttr('UsdUVTexture')
  normal_name=f'image_{image_index:03d}_normal_{round(scale*1000)}.png'
  source_image=Image.open(WORK/'textures'/f'image_{image_index:03d}.png').convert('RGB');pixels=[]
  for r,gc,b in source_image.get_flattened_data():
   nx=(r/255*2-1)*scale;ny=(gc/255*2-1)*scale;nz=b/255*2-1;length=math.sqrt(nx*nx+ny*ny+nz*nz)
   pixels.append(tuple(round(255*(c/length*.5+.5)) for c in (nx,ny,nz)))
  source_image.putdata(pixels);source_image.save(WORK/'textures'/normal_name)
  t.CreateInput('file',Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath('textures/'+normal_name))
  t.CreateInput('sourceColorSpace',Sdf.ValueTypeNames.Token).Set('raw');t.CreateInput('scale',Sdf.ValueTypeNames.Float4).Set(Gf.Vec4f(2,2,2,1));t.CreateInput('bias',Sdf.ValueTypeNames.Float4).Set(Gf.Vec4f(-1,-1,-1,0))
  t.CreateInput('st',Sdf.ValueTypeNames.Float2).ConnectToSource(reader.ConnectableAPI(),'result');t.CreateOutput('rgb',Sdf.ValueTypeNames.Float3)
  shader.CreateInput('normal',Sdf.ValueTypeNames.Normal3f).ConnectToSource(t.ConnectableAPI(),'rgb')
 materials.append(m)
count=0;triangles=0
for ni,node in enumerate(g['nodes']):
 if 'mesh' not in node:continue
 # This pipeline exports posed world-space vertices; reject unexpected transforms rather than silently drop them.
 assert not any(key in node for key in ['matrix','translation','rotation','scale','children']), 'Unexpected transformed node'
 for pi,p in enumerate(g['meshes'][node['mesh']]['primitives']):
  assert p.get('mode',4)==4
  ob=UsdGeom.Mesh.Define(stage,f'/Knight/Geometry/Mesh_{ni:03d}_{pi}');ob.GetPrim().SetDisplayName(node.get('name',f'Mesh {ni}'))
  positions=access(p['attributes']['POSITION']);indices=access(p['indices']);normals=access(p['attributes']['NORMAL']);uvs=access(p['attributes']['TEXCOORD_0'])
  ob.CreatePointsAttr(Vt.Vec3fArray(positions));ob.CreateFaceVertexIndicesAttr(Vt.IntArray(indices));ob.CreateFaceVertexCountsAttr(Vt.IntArray([3]*(len(indices)//3)))
  ob.CreateNormalsAttr(Vt.Vec3fArray(normals));ob.SetNormalsInterpolation(UsdGeom.Tokens.vertex);ob.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none);ob.CreateDoubleSidedAttr(True)
  # USD and glTF use opposite conventions for the vertical image coordinate.
  UsdGeom.PrimvarsAPI(ob).CreatePrimvar('st',Sdf.ValueTypeNames.TexCoord2fArray,UsdGeom.Tokens.vertex).Set(Vt.Vec2fArray([(u,1-v) for u,v in uvs]))
  UsdShade.MaterialBindingAPI.Apply(ob.GetPrim()).Bind(materials[p['material']]);count+=1;triangles+=len(indices)//3
stage.GetRootLayer().Save();destination=OUT/'GothicBlackKnight.usdz'
if destination.exists():destination.unlink()
assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(WORK/'GothicBlackKnight.usdc')),str(destination))
reopened=Usd.Stage.Open(str(destination));assert reopened and reopened.GetDefaultPrim()
report={'usd_version':Usd.GetVersion(),'usdz_reopened':True,'mesh_count':count,'triangles':triangles,'bytes':destination.stat().st_size,'physical_iphone_test':False}
with zipfile.ZipFile(destination) as archive:
 report['package_files']=len(archive.infolist());report['all_entries_uncompressed']=all(i.compress_type==zipfile.ZIP_STORED for i in archive.infolist())
 with destination.open('rb') as f:
  align=[]
  for info in archive.infolist():
   f.seek(info.header_offset+26);name_len,extra_len=struct.unpack('<HH',f.read(4));align.append((info.header_offset+30+name_len+extra_len)%64==0)
 report['all_entries_64_byte_aligned']=all(align)
registry=UsdValidation.ValidationRegistry()
context=UsdValidation.ValidationContext(registry.GetOrLoadAllValidators())
issues=context.Validate(reopened)
report['validation_engine']='OpenUSD 26.11 UsdValidation, all registered validators'
report['validation_issues']=[e.GetErrorAsString() for e in issues]
report['all_texture_assets_resolved']=all(bool(UsdShade.Shader(p).GetInput('file').Get().resolvedPath) for p in reopened.Traverse() if p.IsA(UsdShade.Shader) and UsdShade.Shader(p).GetIdAttr().Get()=='UsdUVTexture')
(OUT/'usdz_check.json').write_text(json.dumps(report,indent=2,default=str)+'\n');print(json.dumps(report,indent=2,default=str))
assert not issues and report['all_texture_assets_resolved'], 'USDZ validation failed'
