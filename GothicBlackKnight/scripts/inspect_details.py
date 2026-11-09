import bpy, os, json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
source=Path(os.environ.get('KNIGHT_SOURCE',str(root/'artifacts/refined/Gothic_Black_Knight.blend')))
out=Path(os.environ.get('KNIGHT_DETAILS_OUT',str(root/'proof/details')));out.mkdir(parents=True,exist_ok=True)
prefix=os.environ.get('KNIGHT_DETAIL_PREFIX','')
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene
s.render.resolution_x=1000;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.cycles.samples=24;s.cycles.use_denoising=True
try:
 p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='CUDA';p.get_devices()
 for d in p.devices:d.use=d.type=='CUDA'
 if any(d.type=='CUDA' for d in p.devices):s.cycles.device='GPU'
except Exception:s.cycles.device='CPU'
for name,pos,target,scale in [('armor',(-2.2,-4,2.3),(0,0,1.58),1.10),('hand',(1.5,-3,1.5),(.61,-.10,1.10),.44),('rear',(2,4,2.2),(0,.1,1.76),.85)]:
 s.camera.location=pos;s.camera.rotation_euler=(Vector(target)-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=scale
 s.render.filepath=str(out/(prefix+name+'.png'));bpy.ops.render.render(write_still=True)
report=[]
for o in s.objects:
 if o.type=='MESH' and not o.hide_render:
  if any(k in o.name for k in ['Helmet','Gauntlet','Cape','Cloth','tabard']):
   b=[o.matrix_world@Vector(c) for c in o.bound_box]
   report.append({'name':o.name,'vertices':len(o.data.vertices),'bounds':[[min(c[i] for c in b),max(c[i] for c in b)] for i in range(3)]})
(out/(prefix+'objects.json')).write_text(json.dumps(report,indent=2))
