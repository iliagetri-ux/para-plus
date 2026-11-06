import bpy,os
from mathutils import Vector
p=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=p+'/artifacts/GothicBlackKnight.blend')
s=bpy.context.scene;s.camera.location=(0,5,1.45);s.camera.rotation_euler=(Vector((.08,0,1.08))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.cycles.samples=8;s.render.resolution_percentage=50;s.render.filepath=p+'/artifacts/QA_Back.png';bpy.ops.render.render(write_still=True)
