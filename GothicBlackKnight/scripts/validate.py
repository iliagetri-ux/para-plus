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
assert report['nonfinite_vertices']==0, 'Non-finite coordinates'
assert report['degenerate_faces']==0, 'Degenerate faces'
assert not report['uv_missing'], 'Missing UV layers'
# Independent render of the imported GLB, without relying on the source scene.
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=os.environ.get('KNIGHT_DENOISE')=='1'
s.render.resolution_x=400;s.render.resolution_y=520;s.render.resolution_percentage=100;s.world.color=(.2,.2,.2)
bpy.ops.object.camera_add(location=(-3.92,-4,1.45));c=bpy.context.object;c.rotation_euler=(Vector((.05,0,1.08))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=2.5;s.camera=c
for pos,power in [((-3,-4,4),600),((3,1,4),900)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=4;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=out+'/GLB_Import_Preview.png';bpy.ops.render.render(write_still=True)
