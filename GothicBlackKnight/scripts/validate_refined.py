"""Reopen the delivered native source and independently import/render the GLB."""
import bpy,json,math,hashlib,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/refined'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Gothic_Black_Knight.blend'))
visible=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
report={'blend_reopened':True,'blend_visible_meshes':len(visible),'base_commit':bpy.context.scene.get('continuation_base')}
camera_target=tuple(bpy.context.scene.get('review_camera_target',(.24,0,1.08)))
camera_scale=float(bpy.context.scene.get('review_camera_scale',2.75))
assert not any('STUDIO floor'==o.name for o in bpy.context.scene.objects)
lights=[(o.name,tuple(o.location),tuple(o.rotation_euler),o.data.energy,tuple(o.data.color),o.data.size) for o in bpy.context.scene.objects if o.type=='LIGHT']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'Gothic_Black_Knight.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
report.update(glb_reopened=True,glb_meshes=len(meshes),triangles=sum(len(o.data.polygons) for o in meshes),nonfinite_vertices=0,degenerate_faces=0,degenerate_meshes={},uv_missing=[],textures_missing=[],bounds=[])
points=[]
for o in meshes:
    report['nonfinite_vertices']+=sum(not all(math.isfinite(c) for c in v.co) for v in o.data.vertices)
    report['degenerate_faces']+=sum(p.area<1e-12 for p in o.data.polygons)
    bad=sum(p.area<1e-12 for p in o.data.polygons)
    if bad:report['degenerate_meshes'][o.name]=bad
    if not o.data.uv_layers:report['uv_missing'].append(o.name)
    # A joined mesh can retain the cuirass rotation. Transform actual vertices,
    # not local bounding-box corners, to avoid inflated world-space extents.
    points.extend([o.matrix_world@v.co for v in o.data.vertices])
report['bounds']=[[min(v[i] for v in points),max(v[i] for v in points)] for i in range(3)]
report['materials']=[m.name for m in bpy.data.materials]
for m in bpy.data.materials:
    if not m.use_nodes:continue
    for n in m.node_tree.nodes:
        if n.type=='TEX_IMAGE':
            if n.image:
                # Packed glTF images are loaded lazily; force pixel decoding.
                try:sample=n.image.pixels[0]
                except Exception:pass
            if not n.image or not n.image.has_data:report['textures_missing'].append(m.name)
(OUT/'validation_refined.json').write_text(json.dumps(report,indent=2))
assert report['nonfinite_vertices']==0
assert report['degenerate_faces']==0,report['degenerate_faces']
assert not report['uv_missing'],report['uv_missing']
assert not report['textures_missing'],report['textures_missing']
assert report['bounds'][2][1]>2.0 and report['bounds'][2][1]<2.25
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
try:
    p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='CUDA';p.get_devices()
    for d in p.devices:d.use=d.type=='CUDA'
    if any(d.type=='CUDA' for d in p.devices):s.cycles.device='GPU'
except Exception:pass
s.world=bpy.data.worlds.new('Neutral studio lighting');s.world.use_nodes=True
s.world.node_tree.nodes.get('Background').inputs[0].default_value=(.11,.13,.16,1)
s.world.node_tree.nodes.get('Background').inputs[1].default_value=.4
for name,loc,rot,power,color,size in lights:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.rotation_euler=rot;o.data.energy=power;o.data.color=color;o.data.size=size;o.data.shape='DISK'
bpy.ops.object.camera_add(location=(-3.4,-5.2,2.35));c=bpy.context.object
c.rotation_euler=(Vector(camera_target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=camera_scale;s.camera=c
s.view_settings.view_transform='AgX';s.render.film_transparent=True
s.render.resolution_x=800;s.render.resolution_y=900;s.render.resolution_percentage=100
s.render.filepath=str(OUT/'preview_glb_reimport.png');bpy.ops.render.render(write_still=True)
report['independent_render']=True
report['sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.suffix in ['.blend','.glb'] or p.name=='preview_glb_reimport.png'}
(OUT/'validation_refined.json').write_text(json.dumps(report,indent=2))
print('INDEPENDENT_VALIDATION_COMPLETE',json.dumps(report))
