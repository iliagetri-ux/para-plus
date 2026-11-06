import bpy,json,os,math
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));out=root+'/artifacts'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=out+'/GothicBlackKnight.glb')
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
report={'glb_reimport':True,'meshes':len(objects),'vertices':sum(len(o.data.vertices) for o in objects),'triangles':sum(len(o.data.polygons) for o in objects),'nonfinite_vertices':0,'degenerate_faces':0,'materials':len(bpy.data.materials),'uv_missing':[]}
for o in objects:
 report['nonfinite_vertices']+=sum(not all(math.isfinite(v) for v in p.co) for p in o.data.vertices)
 report['degenerate_faces']+=sum(p.area<1e-12 for p in o.data.polygons)
 if not o.data.uv_layers:report['uv_missing'].append(o.name)
with open(out+'/glb_import_check.json','w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
