"""Independent FBX geometry smoke check; material appearance is not certified."""
import bpy,json,math,os
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));out=root+'/artifacts'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=out+'/GothicBlackKnight.fbx')
bpy.context.view_layer.update();objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
points=[o.matrix_world @ Vector(p) for o in objects for p in o.bound_box]
bounds=[(min(p[i] for p in points),max(p[i] for p in points)) for i in range(3)]
report={'fbx_reimport':True,'meshes':len(objects),'vertices':sum(len(o.data.vertices) for o in objects),'nonfinite_vertices':sum(not all(math.isfinite(v) for v in p.co) for o in objects for p in o.data.vertices),'uv_missing':[o.name for o in objects if not o.data.uv_layers],'world_bounds':bounds,'material_appearance_certified':False}
assert objects and report['nonfinite_vertices']==0 and not report['uv_missing']
assert 1.9<bounds[2][1]-bounds[2][0]<2.2
with open(out+'/fbx_import_check.json','w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
