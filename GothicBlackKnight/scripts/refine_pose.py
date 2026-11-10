"""Repose the saved 29494cd character, retaining its fitted armor and materials.

Rigid joint transforms preserve armor; only padding and hanging cloth deform.
KNIGHT_PROOF=1 writes review images and a source under proof/pose.
"""
import bpy,bmesh,os,math,json,hashlib,subprocess
from pathlib import Path
from collections import Counter
from mathutils import Vector,Matrix,Quaternion
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1]
COMMIT='29494cdf6b974546e7c70f7745b0da94514f83d6'
BASE=ROOT/'checkpoints/29494cd.blend'
if not BASE.exists():
    saved=subprocess.run(['git','show',COMMIT+':GothicBlackKnight/artifacts/refined/Gothic_Black_Knight.blend'],cwd=ROOT.parent,capture_output=True,check=True)
    BASE.parent.mkdir(parents=True,exist_ok=True);BASE.write_bytes(saved.stdout)
assert hashlib.sha256(BASE.read_bytes()).hexdigest()=='8e5a89b7be7aebf711d4ceed16a6febbde1ec4800908aa7513ce018deb4f23ed'
PROOF=os.environ.get('KNIGHT_PROOF')=='1'
OUT=ROOT/('proof/pose' if PROOF else 'artifacts/refined');OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE));scene=bpy.context.scene
assets=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
original={o.name:o.matrix_world.copy() for o in assets}
def V(v):return Vector(v)
def R(axis,degrees):return Matrix.Rotation(math.radians(degrees),4,axis)
def pivot(p,rotation):return Matrix.Translation(p)@rotation@Matrix.Translation(-p)
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def joint(old,new,rotation):return Matrix.Translation(new)@rotation.to_4x4()@Matrix.Translation(-old)
def align(a,b,c,d):return joint(a,c,(b-a).rotation_difference(d-c).to_matrix())
pelvis=Matrix.Translation(V((-.065,.012,-.006)))@pivot(V((0,0,1.10)),R('Z',-5.5)@R('Y',3))
waist=pelvis@V((0,0,1.16))
torso=pivot(waist,R('Z',13)@R('Y',-4))@pelvis
neck=torso@V((0,0,1.685))
head=pivot(neck,R('Z',-12)@R('X',4))@torso
mat={'pelvis':pelvis,'torso':torso,'head':head}
joints={}

# Arms bend forward at the elbows, rather than pointing sideways in one plane.
old_arm=Matrix.Translation(V((.35,-.005,1.23)))@R('Y',50)@Matrix.Translation(-V((.35,-.005,1.23)))
for side in [-1,1]:
    key='L' if side<0 else 'R'
    sh=V((side*.29,0,1.57));el=V((side*.35,-.005,1.23))
    wr=V((-.36,-.055,1.02)) if side<0 else old_arm@V((.61,-.10,1.34))
    ns=torso@sh
    if side>0:ns+=V((0,0,-.012))
    desired_el=V((-.405,-.025,1.22)) if side<0 else V((.285,-.055,1.235))
    ne=ns+(desired_el-ns).normalized()*(el-sh).length
    desired_wr=V((-.425,-.115,.99)) if side<0 else V((.42,-.24,1.06))
    nw=ne+(desired_wr-ne).normalized()*(wr-el).length
    upper=align(sh,el,ns,ne);lower=align(el,wr,ne,nw)
    axis=(nw-ne).normalized()
    if side<0:
        roll=math.radians(-48)
    else:
        # Preserve hand/sword contact while rotating the whole forearm about
        # its anatomical axis. No independent sword translation or wrist kink.
        old_blade=R('Y',-38).to_3x3()@V((0,0,-1))
        current=lower.to_3x3()@old_blade;desired=V((.60,-.12,-.791)).normalized()
        a=(current-axis*current.dot(axis)).normalized();b=(desired-axis*desired.dot(axis)).normalized()
        roll=math.atan2(axis.dot(a.cross(b)),a.dot(b))
    lower=pivot(ne,Quaternion(axis,roll).to_matrix().to_4x4())@lower
    mat[key+'upper']=upper;mat[key+'lower']=lower;mat[key+'hand']=lower
    mat[key+'elbow']=joint(el,ne,upper.to_quaternion().slerp(lower.to_quaternion(),.30).to_matrix())
    # Shoulder shells follow the chest, with a restrained articulation toward
    # the changed upper arm. Their layered silhouettes remain intact.
    shell_q=torso.to_quaternion().slerp(upper.to_quaternion(),.30)
    mat[key+'shoulder']=joint(sh,ns,shell_q.to_matrix())
    joints[key+'arm']={'shoulder':list(ns),'elbow':list(ne),'wrist':list(nw)}
# A small wrist adjustment aims the heavy blade clear of the feet. Rotate the
# circular grip about its own axis to retain a useful edge alignment in hand.
old_blade=R('Y',-38).to_3x3()@V((0,0,-1))
blade_axis=V((.60,-.12,-.791)).normalized()
current_axis=mat['Rlower'].to_3x3()@old_blade
wrist_adjust=current_axis.rotation_difference(blade_axis)
assert math.degrees(wrist_adjust.angle)<15
mat['Rhand']=pivot(V(joints['Rarm']['wrist']),wrist_adjust.to_matrix().to_4x4())@mat['Rlower']
grip=bpy.data.objects['Greatsword | leather grip']
grip_center=sum((original[grip.name]@V(c) for c in grip.bound_box),V((0,0,0)))/8
old_normal=mat['Rhand'].to_3x3()@V((0,-1,0));desired_normal=V((0,-1,0))
a=(old_normal-blade_axis*old_normal.dot(blade_axis)).normalized()
b=(desired_normal-blade_axis*desired_normal.dot(blade_axis)).normalized()
edge_roll=math.atan2(blade_axis.dot(a.cross(b)),a.dot(b))
mat['weapon']=pivot(mat['Rhand']@grip_center,Quaternion(blade_axis,edge_roll).to_matrix().to_4x4())@mat['Rhand']

# Two-bone leg solve: the left leg supports the shifted pelvis. The right foot
# is advanced, turned out and lightly raised at the heel, with a relaxed knee.
for side in [-1,1]:
    key='L' if side<0 else 'R'
    hip=V((side*.115,0,1.01));knee=V((side*.137,.005,.60));ankle=V((side*.16,0,.14))
    nh=pelvis@hip
    na=V((-.18,.04,.14)) if side<0 else V((.18,-.105,.166))
    rotation=R('Z',-9 if side<0 else 18)@R('X',0 if side<0 else 8)
    foot=joint(ankle,na,rotation.to_3x3())
    boot=next(o for o in assets if o.name.startswith('Sabatons | shaped') and (sum((o.matrix_world@V(c)).x for c in o.bound_box)<0)==(side<0))
    points=[boot.matrix_world@v.co for v in boot.data.vertices]
    correction=min(p.z for p in points)-min((foot@p).z for p in points)
    na.z+=correction;foot=Matrix.Translation(V((0,0,correction)))@foot
    l1=(knee-hip).length;l2=(ankle-knee).length;axis=(na-nh).normalized();d=(na-nh).length
    assert abs(l1-l2)<d<l1+l2,(key,d,l1+l2)
    along=(l1*l1-l2*l2+d*d)/(2*d);height=math.sqrt(max(0,l1*l1-along*along))
    pole=V((side*.1,-1,0));pole=(pole-axis*pole.dot(axis)).normalized()
    nk=nh+axis*along+pole*height
    thigh=align(hip,knee,nh,nk);shin=align(knee,ankle,nk,na)
    mat[key+'thigh']=thigh;mat[key+'shin']=shin;mat[key+'foot']=foot
    mat[key+'knee']=joint(knee,nk,thigh.to_quaternion().slerp(shin.to_quaternion(),.50).to_matrix())
    joints[key+'leg']={'hip':list(nh),'knee':list(nk),'ankle':list(na),'foot_plane':min((foot@p).z for p in points),'knee_bend_degrees':math.degrees((nk-nh).angle(na-nk))}

def center(o):return sum((original[o.name]@V(c) for c in o.bound_box),V((0,0,0)))/8
def role(o):
    name=o.name;c=center(o);side='L' if c.x<0 else 'R'
    if name=='Preserved body chasing and bindings':return 'decor'
    if name.startswith(('Greatsword','Guard garnet')):return 'weapon'
    if 'Helmet' in name or name.startswith('Crown'):return 'head'
    if 'Gauntlet' in name:return side+'hand'
    if name.startswith(('Wrist cuff','Vambrace')):return side+'lower'
    if name.startswith(('Sleeve','Rerebrace')):return side+'upper'
    if name.startswith('Elbow couter'):return side+'elbow'
    if 'pauldron' in name.lower() or name.startswith('Padded shoulder attachment'):return side+'shoulder'
    if name.startswith('Arming leg'):return side+'padding'
    if name.startswith('Anatomical cuisse'):return side+'thigh'
    if name.startswith('Hip tasset overlapping'):return side+'thigh'
    if name.startswith(('Pointed poleyn','Poleyn')):return side+'knee'
    if name.startswith('Greave'):return side+'shin'
    if name.startswith('Sabatons'):return side+'foot'
    if name.startswith('Tasset'):return side+'tasset'
    if name.startswith(('Cloth','Split heraldic')):return 'skirt'
    if 'Cape' in name and not any(k in name for k in ['clasp','pin']):return 'cape'
    if name.startswith(('Leather waist','Belt buckle','Overlapping articulated fauld')):return 'pelvis'
    if name.startswith('Padded arming torso'):return 'padding_torso'
    return 'torso'
roles={o.name:role(o) for o in assets}

# Match disconnected legacy trim to the actual piece it sits on, before any
# geometry moves. Component-wide assignment keeps each trim ring intact.
samples=[];sample_roles=[]
for o in assets:
    if roles[o.name]=='decor':continue
    if any(k in o.name for k in ['frayed warp strand','hand stitched back seam']):continue
    if any(k in o.name for k in ['chased margin','raised keel','incised line','engraved branching','inlaid scroll','forged ridge']):continue
    for v in o.data.vertices:
        samples.append(original[o.name]@v.co);sample_roles.append(roles[o.name])
tree=KDTree(len(samples))
for i,p in enumerate(samples):tree.insert(p,i)
tree.balance()

def deform(p,kind):
    if kind in mat:return mat[kind]@p
    if kind.endswith('padding'):
        s=kind[0];a=mat[s+'shin']@p;b=mat[s+'thigh']@p;return a.lerp(b,smooth(.54,.68,p.z))
    if kind.endswith('tasset'):
        s=kind[0];return (mat[s+'thigh']@p).lerp(pelvis@p,smooth(.98,1.17,p.z))
    if kind=='padding_torso':return (pelvis@p).lerp(torso@p,smooth(1.08,1.30,p.z))
    if kind in ['cape','skirt']:
        top=torso if kind=='cape' else pelvis
        t=smooth(.12,1.67 if kind=='cape' else 1.12,p.z)
        delta=top@p-p
        q=p+V((delta.x*t-.025*(1-t),delta.y*t,delta.z*t))
        # Hanging panels follow gravity; the free knee pushes fabric forward.
        if kind=='skirt' and p.y<-.02:
            knee=V(joints['Rleg']['knee']);w=math.exp(-((q.x-knee.x)/.14)**2-((q.z-knee.z)/.26)**2)
            q.y-=.14*w
        q.z=max(.018,q.z)
        return q
    raise ValueError(kind)

counts=Counter()
for o in assets:
    kind=roles[o.name];counts[kind]+=1;o['pose_region']=kind
    if kind=='decor':
        bm=bmesh.new();bm.from_mesh(o.data);unseen=set(bm.verts);inverse=original[o.name].inverted()
        while unseen:
            start=unseen.pop();component=[start];stack=[start]
            while stack:
                v=stack.pop()
                for e in v.link_edges:
                    other=e.other_vert(v)
                    if other in unseen:unseen.remove(other);component.append(other);stack.append(other)
            votes=[]
            for v in component[::max(1,len(component)//24)]:
                _,index,_=tree.find(original[o.name]@v.co);votes.append(sample_roles[index])
            target=Counter(votes).most_common(1)[0][0]
            points=[original[o.name]@v.co for v in component]
            low=[min(p[i] for p in points) for i in range(3)]
            high=[max(p[i] for p in points) for i in range(3)]
            # The top toe articulation lies closer to a greave vertex than
            # to the sparse boot rings. It must turn with the foot, not shin.
            if high[2]<.19 and high[0]-low[0]<.19 and high[1]<.11 and max(abs(low[0]),abs(high[0]))<.28:
                target=('L' if low[0]+high[0]<0 else 'R')+'foot'
            for v in component:v.co=inverse@deform(original[o.name]@v.co,target)
        bm.to_mesh(o.data);bm.free()
    elif kind in mat:o.matrix_world=mat[kind]@original[o.name]
    else:
        inverse=original[o.name].inverted()
        for v in o.data.vertices:v.co=inverse@deform(original[o.name]@v.co,kind)

scene['continuation_base']=COMMIT
scene['pose_pass']='Weight on left leg; advanced relaxed right foot; counterturned torso; lowered forward sword arm'
scene['art_status']='Intermediate static character study; pose revised, reference sculptural target remains unmet'
scene.render.engine='CYCLES';scene.cycles.samples=20 if PROOF else 64;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='CUDA'
    scene.cycles.device='GPU' if any(d.type=='CUDA' for d in prefs.devices) else 'CPU'
except Exception:scene.cycles.device='CPU'
scene.render.resolution_x=1280;scene.render.resolution_y=1440;scene.render.resolution_percentage=55 if PROOF else 100
cam=scene.camera;cam.data.ortho_scale=2.65;target=V((.10,0,1.075))
views={'front':(0,-5,1.48),'back':(0,5,1.48),'side':(-5,0,1.48),'perspective':(-3.4,-5.2,2.35)}
def setview(name):cam.location=views[name];cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
setview('perspective');bpy.ops.object.select_all(action='DESELECT')
scene['review_camera_target']=list(target);scene['review_camera_scale']=cam.data.ortho_scale
bpy.context.view_layer.update()
depsgraph=bpy.context.evaluated_depsgraph_get()
def evaluated_points(ob):
    evaluated=ob.evaluated_get(depsgraph);mesh=evaluated.to_mesh()
    points=[evaluated.matrix_world@v.co for v in mesh.vertices];evaluated.to_mesh_clear();return points
foot_minima=[min(p.z for p in evaluated_points(o)) for o in assets if o.name.startswith('Sabatons | shaped')]
blade_points=evaluated_points(bpy.data.objects['Greatsword | diamond section blade'])
blade_min=min(p.z for p in blade_points)
assert abs(foot_minima[0]-foot_minima[1])<.003,foot_minima
assert blade_min>max(foot_minima)+.01,(blade_min,foot_minima)
assert all(abs(m.to_3x3().determinant()-1)<.0001 for m in mat.values())
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Gothic_Black_Knight.blend'),compress=True)
pose_check={'base_commit':COMMIT,'native_sha256':hashlib.sha256((OUT/'Gothic_Black_Knight.blend').read_bytes()).hexdigest(),'visible_meshes_retained':len(assets),'foot_contact_heights':foot_minima,'blade_minimum_height':blade_min,'blade_clearance_above_foot_plane':blade_min-max(foot_minima),'wrist_adjustment_degrees':math.degrees(wrist_adjust.angle),'joints':joints,'rigid_armor_transform_determinants_valid':True,'scope':'Static pose; mathematical checks and rendered review, not a rig or physical balance simulation'}
(OUT/'pose_check.json').write_text(json.dumps(pose_check,indent=2))
if not PROOF:
    for ob in assets:
        ob.select_set(True)
        for modifier in ob.modifiers:
            if modifier.type=='SUBSURF':modifier.levels=modifier.render_levels
    bpy.context.view_layer.objects.active=bpy.data.objects['Cuirass | forged breast and back']
    bpy.ops.object.convert(target='MESH')
    for ob in bpy.context.selected_objects:
        if ob.type!='MESH':continue
        uv=ob.data.uv_layers.active
        if uv:
            for other in list(ob.data.uv_layers):
                if other!=uv:ob.data.uv_layers.remove(other)
            uv.name='UVMap'
    bpy.ops.object.join();hero=bpy.context.object;hero.name='Gothic Black Knight | posed static material batches'
    hero.modifiers.new('Export triangulation','TRIANGULATE')
    bpy.ops.export_scene.gltf(filepath=str(OUT/'Gothic_Black_Knight.glb'),export_format='GLB',use_selection=True,export_apply=True,export_tangents=True,export_cameras=False,export_lights=False)
    for script in ['fix_glb_color.py','repair_tangents.py']:
        subprocess.run([os.environ.get('KNIGHT_PYTHON','python'),str(ROOT/'scripts'/script),str(OUT/'Gothic_Black_Knight.glb')],check=True)
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'Gothic_Black_Knight.blend'));scene=bpy.context.scene;cam=scene.camera
report={'base_commit':COMMIT,'source_meshes':len(assets),'resolution':[round(scene.render.resolution_x*scene.render.resolution_percentage/100),round(scene.render.resolution_y*scene.render.resolution_percentage/100)],'samples':scene.cycles.samples,'views':{},'pose_regions':dict(counts),'joints':joints}
for name in os.environ.get('KNIGHT_VIEWS',','.join(views)).split(','):
    setview(name);scene.render.filepath=str(OUT/('preview_'+name+'.png'));bpy.ops.render.render(write_still=True)
    report['views'][name]=hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest();(OUT/'refinement_check.json').write_text(json.dumps(report,indent=2))
print('POSE_PASS_COMPLETE',json.dumps(report))
