"""Guided heavy-cloth study. Artistic floor pins retain the spread of a static cape."""
import bpy,os,json,math
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT=ROOT+'/cloth-study';os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=ROOT+'/proof/GothicBlackKnight.blend');s=bpy.context.scene
cape=next(o for o in s.objects if o.type=='MESH' and o.name.startswith('Cape |'))
uv={loop.vertex_index:cape.data.uv_layers.active.data[loop.index].uv.copy()/8 for loop in cape.data.loops}
vg=cape.vertex_groups.new(name='Shoulder seam and artistic train anchors')
for vertex in cape.data.vertices:
 u,t=uv[vertex.index];z=vertex.co.z
 if t>.72:
  f=(t-.72)/.28;vertex.co.z=max(.043,z-.24*f)
  vertex.co.y+=.28*f*f
  vertex.co.z+=.012*f*math.sin(u*47)**2
 if t<.026:vg.add([vertex.index],1.0,'REPLACE')
 elif t<.05:vg.add([vertex.index],.35,'REPLACE')
 elif t>.975 and (u<.10 or u>.94):vg.add([vertex.index],.8,'REPLACE')
for mod in cape.modifiers:mod.show_viewport=False;mod.show_render=False
cloth=cape.modifiers.new('Guided heavy wool','CLOTH');q=cloth.settings;q.quality=6;q.mass=.35;q.air_damping=8;q.tension_stiffness=20;q.compression_stiffness=18;q.shear_stiffness=12;q.bending_stiffness=.06;q.vertex_group_mass=vg.name;q.pin_stiffness=1
cloth.collision_settings.use_collision=True;cloth.collision_settings.distance_min=.004;cloth.collision_settings.collision_quality=3;cloth.collision_settings.use_self_collision=True;cloth.collision_settings.self_distance_min=.004
cloth.point_cache.frame_start=1;cloth.point_cache.frame_end=50
colliders=[]
for ob in s.objects:
 if ob.type=='MESH' and any(ob.name.startswith(p) for p in ['Padded arming torso','Sleeve','Rerebrace','Arming leg','STUDIO floor']):
  mod=ob.modifiers.new('Cloth clearance','COLLISION');ob.collision.thickness_outer=.005;colliders.append((ob,mod))
for frame in range(1,51):
 s.frame_set(frame);bpy.context.view_layer.update();ob=cape.evaluated_get(bpy.context.evaluated_depsgraph_get());ob.to_mesh();ob.to_mesh_clear();print('FRAME',frame,flush=True)
graph=bpy.context.evaluated_depsgraph_get();deformed=bpy.data.meshes.new_from_object(cape.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph);cape.modifiers.remove(cloth);cape.data=deformed
for mod in cape.modifiers:mod.show_viewport=True;mod.show_render=True
for ob,mod in colliders:ob.modifiers.remove(mod)
s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_percentage=65
for name,loc in {'45':(-3.92,-4,1.45),'Back':(0,5,1.45)}.items():
 s.camera.location=loc;s.camera.rotation_euler=(Vector((.08,0,1.08))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=OUT+'/Guided_'+name+'.png';bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/GuidedCape.blend',compress=True)
print('GUIDED_CLOTH_COMPLETE',len(deformed.vertices))
