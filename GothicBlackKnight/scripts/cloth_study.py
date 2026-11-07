"""Physical cape drape study; preserves published source and exports."""
import bpy,os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT=ROOT+'/cloth-study';os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=ROOT+'/artifacts/GothicBlackKnight.blend')
s=bpy.context.scene;s.frame_start=1;s.frame_end=90
cape=next(o for o in s.objects if o.type=='MESH' and o.name.startswith('Cape |'))
for vertex in cape.data.vertices:
 t=(vertex.index//81)/80
 vertex.co.z=max(.045,vertex.co.z-.14*t**1.3)
 vertex.co.y+=.22*max(0,(t-.72)/.28)**2
for mod in cape.modifiers:mod.show_viewport=False;mod.show_render=False
vg=cape.vertex_groups.new(name='Shoulder seam pinning')
# The generated mesh has 81 vertices across each of its 81 rows.
vg.add(list(range(81)),1.0,'REPLACE');vg.add(list(range(81,162)),.65,'REPLACE');vg.add(list(range(162,243)),.15,'REPLACE')
cloth=cape.modifiers.new('Physical wool drape','CLOTH');q=cloth.settings;q.quality=8;q.mass=.22;q.air_damping=4;q.tension_stiffness=18;q.compression_stiffness=18;q.shear_stiffness=12;q.bending_stiffness=1.2;q.vertex_group_mass=vg.name;q.pin_stiffness=1
cloth.collision_settings.use_collision=True;cloth.collision_settings.distance_min=.005;cloth.collision_settings.collision_quality=3
cloth.collision_settings.use_self_collision=True;cloth.collision_settings.self_distance_min=.006;cloth.point_cache.frame_start=1;cloth.point_cache.frame_end=90
colliders=[]
for ob in s.objects:
 if ob.type=='MESH' and any(ob.name.startswith(prefix) for prefix in ['Padded arming torso','Sleeve','Rerebrace','Arming leg','STUDIO floor']):
  mod=ob.modifiers.new('Cloth clearance','COLLISION');ob.collision.thickness_outer=.006;colliders.append((ob,mod))
bpy.ops.object.effector_add(type='WIND',location=(2,1,1));wind=bpy.context.object;wind.field.strength=.18;wind.rotation_euler=Vector((-.8,.3,.1)).to_track_quat('Z','Y').to_euler()
for frame in range(1,91):
 s.frame_set(frame);bpy.context.view_layer.update();evaluated=cape.evaluated_get(bpy.context.evaluated_depsgraph_get());evaluated.to_mesh();evaluated.to_mesh_clear();print('CLOTH_FRAME',frame,flush=True)
eval_ob=cape.evaluated_get(bpy.context.evaluated_depsgraph_get());deformed=bpy.data.meshes.new_from_object(eval_ob,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());cape.modifiers.remove(cloth);cape.data=deformed
for mod in cape.modifiers:mod.show_viewport=True;mod.show_render=True
for ob,mod in colliders:ob.modifiers.remove(mod)
bpy.data.objects.remove(wind,do_unlink=True)
s.cycles.samples=12;s.render.resolution_percentage=65;s.render.filepath=OUT+'/Cape_45.png';bpy.ops.wm.save_as_mainfile(filepath=OUT+'/CapeStudy.blend');bpy.ops.render.render(write_still=True)
