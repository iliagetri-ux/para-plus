import bpy,os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=ROOT+'/proof/GothicBlackKnight.blend')
s=bpy.context.scene;s.camera.location=(.95,-1.4,1.52);s.camera.rotation_euler=(Vector((.62,-.12,1.35))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=.28;s.render.resolution_x=600;s.render.resolution_y=600;s.render.resolution_percentage=100;s.cycles.samples=24;s.render.filepath=ROOT+'/proof/Hand_Closeup.png';bpy.ops.render.render(write_still=True)
