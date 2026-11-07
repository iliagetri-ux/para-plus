"""Resume studio views only when their GLB and PNG hashes match the last build."""
import bpy,os,json,time,hashlib
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT=ROOT+'/artifacts'
def digest(path):return hashlib.sha256(open(path,'rb').read()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=OUT+'/GothicBlackKnight.blend');s=bpy.context.scene
s.cycles.use_denoising=os.environ.get('KNIGHT_DENOISE')=='1';s.cycles.samples=48;s.render.resolution_percentage=100
views={'Front':(0,-5,1.45),'Back':(0,5,1.45),'Side':(-5,0,1.45),'Right':(5,0,1.45),'45':(-3.92,-4,1.45)}
report={'glb_sha256':digest(OUT+'/GothicBlackKnight.glb'),'views':{},'denoising':s.cycles.use_denoising}
previous=json.load(open(OUT+'/render_check.json')) if os.path.exists(OUT+'/render_check.json') else {}
for name,position in views.items():
 path=OUT+'/Preview_'+name+'.png';old=previous.get('views',{}).get(name,{})
 if previous.get('glb_sha256')==report['glb_sha256'] and previous.get('denoising')==report['denoising'] and os.path.exists(path) and old.get('sha256')==digest(path):
  report['views'][name]=old;continue
 s.camera.location=position;s.camera.rotation_euler=(Vector((.08,0,1.08))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=path
 start=time.time();bpy.ops.render.render(write_still=True);report['views'][name]={'rendered':True,'seconds':round(time.time()-start,2),'sha256':digest(path)}
 with open(OUT+'/render_check.json','w') as f:json.dump(report,f,indent=2)
s.camera.location=views['45'];s.camera.rotation_euler=(Vector((.08,0,1.08))-s.camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/GothicBlackKnight.blend',compress=True)
print('RENDER_RESUME_COMPLETE',json.dumps(report))
