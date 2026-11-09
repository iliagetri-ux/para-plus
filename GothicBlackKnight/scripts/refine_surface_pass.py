"""Second continuation: open the actual 4526999 source and refine its surfaces.

Keep checkpoints/4526999.blend from that commit for deterministic iteration.
KNIGHT_PROOF=1 writes ignored proofs; the default replaces artifacts/refined.
"""
import bpy,bmesh,math,os,json,hashlib,subprocess
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from math import sin,cos,pi
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'checkpoints/4526999.blend'
if not BASE.exists():
    saved=subprocess.run(['git','show','4526999d0d75787b148da734cb5ee2e97313a39a:GothicBlackKnight/artifacts/refined/Gothic_Black_Knight.blend'],cwd=ROOT.parent,capture_output=True,check=True)
    BASE.parent.mkdir(parents=True,exist_ok=True);BASE.write_bytes(saved.stdout)
assert hashlib.sha256(BASE.read_bytes()).hexdigest()=='06ba4a0efa1a57774e041ea448553c7d33080cfa25238d452b524a52aba89085'
PROOF=os.environ.get('KNIGHT_PROOF')=='1'
OUT=ROOT/('proof/surface-pass' if PROOF else 'artifacts/refined');OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE));scene=bpy.context.scene
archive=bpy.data.collections.new('ARCHIVE | first refinement surfaces')
scene.collection.children.link(archive);archive.hide_viewport=True;archive.hide_render=True
steel=bpy.data.materials['01 | Blackened forged steel'];plate=bpy.data.materials['11 | Black plate, localized wear']
gold=bpy.data.materials['08 | Aged warm brass inlay'];dark=bpy.data.materials['03 | Recessed steel']
cut=bpy.data.materials['09 | Engraved recess'];silver=bpy.data.materials['10 | Honed steel bevel']
cloth=bpy.data.materials['04 | Charcoal woven wool'];new=[]

def preserve(ob,copy=False):
    if copy:
        old=ob.copy();old.data=ob.data.copy();archive.objects.link(old)
    else:
        old=ob
        for c in list(ob.users_collection):c.objects.unlink(ob)
        archive.objects.link(old)
    old.hide_render=True;old.hide_set(True)

def material(name,color,metal=0,rough=.8):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    m.diffuse_color=(*color,1);return m
fiber=material('12 | Exposed charcoal fibres',(.022,.019,.017),0,.94)
seam_mat=material('13 | Waxed black linen stitching',(.014,.012,.01),0,.9)
leather=material('14 | Weathered sword leather',(.014,.006,.003),0,.72)

def mesh(name,v,f,mat=plate,thick=0):
    me=bpy.data.meshes.new('D2 '+name);me.from_pydata(v,[],f);me.update()
    ob=bpy.data.objects.new('D2 | '+name,me);scene.collection.objects.link(ob);me.materials.append(mat);new.append(ob)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    for p in me.polygons:p.use_smooth=True
    if thick:m=ob.modifiers.new('Forged plate thickness','SOLIDIFY');m.thickness=thick;m.offset=-1
    return ob

def uvgrid(ob,nr,nc):
    uv=ob.data.uv_layers.new(name='Surface coordinates')
    for l in ob.data.loops:uv.data[l.index].uv=(l.vertex_index%nc/(nc-1),l.vertex_index//nc/(nr-1))

def wire(name,points,r=.0007,mat=gold):
    if len(points)<2:return
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=1
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new('D2 | '+name,cu);scene.collection.objects.link(ob);cu.materials.append(mat);new.append(ob);return ob

def stud(name,co,normal,r=.003):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1,location=co)
    o=bpy.context.object;o.name='D2 | '+name;o.scale=(r,r,r*.38)
    o.rotation_euler=Vector(normal).to_track_quat('Z','Y').to_euler();o.data.materials.append(gold);new.append(o)
    for p in o.data.polygons:p.use_smooth=True

# The old broad projected relief has jagged, foil-like margins in close-up.
# Archive that layer; fitted armor and its edge articulation remain in place.
for ob in list(scene.objects):
    if not ob.hide_render and ob.name.startswith('Repousse acanthus |'):
        preserve(ob)
    if ob.type=='MESH' and ob.name.startswith('Wrist cuff'):
        ob.data.materials.clear();ob.data.materials.append(plate)
    if ob.type=='MESH' and ob.name.startswith('Greatsword | leather grip'):
        ob.data.materials.clear();ob.data.materials.append(leather)
    if ob.type=='MESH' and ob.name.startswith('Sleeve'):
        # The old padding intersects the upper-arm shell at mid-length.
        # Inset its radial rings while keeping shoulder/elbow centers fixed.
        for start in range(0,len(ob.data.vertices),32):
            ring=list(ob.data.vertices[start:start+32])
            center=sum((v.co for v in ring),Vector())/len(ring)
            for vertex in ring:vertex.co=center+(vertex.co-center)*.90

# Remove only the legacy hairline acanthus components from their merged mesh.
# Their tube cross sections are below 0.9 mm radius; substantial rolled edges,
# sword binding and belt chain remain. Preserve the exact original mesh first.
decor=bpy.data.objects.get('Preserved body chasing and bindings')
if decor:
    preserve(decor,copy=True);bm=bmesh.new();bm.from_mesh(decor.data);unseen=set(bm.verts);remove=[]
    while unseen:
        a=unseen.pop();component=[a];stack=[a];edges=set()
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                edges.add(e);other=e.other_vert(v)
                if other in unseen:unseen.remove(other);component.append(other);stack.append(other)
        lengths=sorted(e.calc_length() for e in edges)
        if lengths and lengths[len(lengths)//4]<.00130:remove.extend(component)
    bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(decor.data);bm.free()

# UV-authored etching stays on each plate and cannot bridge armor gaps.
plain_plate=plate;plate=plain_plate.copy();plate.name='16 | Chased black steel, seated microrelief'
dim=768;vv,uu=np.mgrid[0:dim,0:dim]/(dim-1);etch=np.zeros((dim,dim))
for k in range(3):
    for side in [-1,1]:
        for j in range(70):
            t=j/69;x=.5+side*(.05+.27*sin(t*pi*.70));y=.15+k*.22+.22*t
            d=((uu-x)/.003)**2+((vv-y)/.004)**2
            etch=np.maximum(etch,np.exp(-d*1.5))
stem=.5+.025*np.sin(vv*2*pi)
etch=np.maximum(etch,np.exp(-((uu-stem)/.0025)**2)*((vv>.12)&(vv<.88)))
height=-.20*etch
gx=np.roll(height,1,1)-np.roll(height,-1,1);gy=np.roll(height,1,0)-np.roll(height,-1,0)
for node in plate.node_tree.nodes:
    if node.type!='TEX_IMAGE' or not node.image:continue
    original=node.image;px=np.array(original.pixels[:],dtype=np.float32).reshape(dim,dim,4)
    if 'Albedo' in original.name:px[:,:,:3]+=etch[:,:,None]*np.array([.008,.005,.002])
    elif 'Roughness' in original.name:px[:,:,:3]=np.clip(px[:,:,:3]+etch[:,:,None]*.05,0,1)
    elif 'Normal' in original.name:
        normal=px[:,:,:3]*2-1;normal[:,:,0]+=gx;normal[:,:,1]+=gy
        normal/=np.linalg.norm(normal,axis=-1,keepdims=True);px[:,:,:3]=normal*.5+.5
    im=bpy.data.images.new('D2 '+original.name,width=dim,height=dim);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(px.ravel());im.pack();node.image=im
for ob in scene.objects:
    if ob.hide_render or ob.type!='MESH':continue
    for slot in range(len(ob.data.materials)):
        if ob.data.materials[slot]==plain_plate:ob.data.materials[slot]=plate

# Close the smooth, featureless side/rear skull with fitted angular shell panels.
for s in [-1,1]:
    nr,nc=25,25;v=[];f=[]
    for i in range(nr):
        t=i/(nr-1);z=1.737+.19*t
        rx=.077+.024*sin(pi*t)**.65;ry=.074+.012*sin(pi*t)
        for j in range(nc):
            u=j/(nc-1);a=.16*pi+.73*pi*u
            zz=z+.014*sin(pi*u)*sin(pi*t)-.018*u*(1-t)
            radius=.0028+.0022*sin(pi*t)*max(0,cos(u*4*pi))**8
            v.append((s*(rx+radius)*sin(a),.014-(ry+radius)*cos(a),zz))
    for i in range(nr-1):
        for j in range(nc-1):
            a=i*nc+j;f.append((a,a+1,a+nc+1,a+nc))
    if s<0:f=[tuple(reversed(face)) for face in f]
    ob=mesh('Helmet | fitted temple and occipital plate',v,f,plate,.003);uvgrid(ob,nr,nc)
    for row in [0,nr-1]:wire('Helmet | rolled occipital seam',[v[row*nc+j] for j in range(nc)],.0012)
    for col in [0,nc-1,12]:wire('Helmet | temple reinforcement',[v[i*nc+col] for i in range(nr)],.00085)
    for row,col in [(8,2),(19,20)]:
        p=Vector(v[row*nc+col]);normal=Vector((s*.8,.3,0)).normalized();stud('Helmet | hinge pin',p+normal*.001,normal,.004)
    for k in range(3):
        row=6+k*3
        wire('Helmet | temple vent',[Vector(v[row*nc+j])+Vector((s*.001,0,0)) for j in range(4,9)],.0010,cut)

# Continuous brow foundation under the existing raised lancets.
nr,nc=29,33;v=[];f=[]
for i in range(nr):
    t=i/(nr-1);rx=.108*(1-.62*t**3);depth=.139-.076*t**1.4
    for j in range(nc):
        u=-1+2*j/(nc-1)
        v.append((rx*u,-depth+.068*abs(u)**1.25,1.819+.134*t+.010*abs(u)*(1-t)-.036*abs(u)*t**3))
for i in range(nr-1):
    for j in range(nc-1):a=i*nc+j;f.append((a,a+1,a+nc+1,a+nc))
ob=mesh('Helmet | continuous forged brow',v,f,plate,.003);uvgrid(ob,nr,nc)
wire('Helmet | ocular upper rim',[v[j] for j in range(nc)],.001,gold)

# Three real overlapping plates per finger, using the original curved finger
# surface and its posed transform. The underlying articulated fingers survive.
for ob in list(scene.objects):
    if ob.hide_render or ob.type!='MESH' or not ob.name.startswith('Gauntlet | curled articulated finger'):continue
    n=12;rings=len(ob.data.vertices)//n
    if rings<16:continue
    for slot in range(len(ob.data.materials)):
        if 'Patinated warm' in ob.data.materials[slot].name:ob.data.materials[slot]=dark
    for section,(lo,hi) in enumerate([(1,5),(6,10),(11,15)]):
        v=[];f=[];nc=7
        for row in range(lo,min(hi,rings-1)+1):
            for j in range(7):
                vertex=ob.data.vertices[row*n+j]
                p=vertex.co+vertex.normal*.0015
                v.append(ob.matrix_world@p)
        nr=len(v)//nc
        for i in range(nr-1):
            for j in range(nc-1):
                a=i*nc+j;f.append((a,a+1,a+nc+1,a+nc))
        cap=mesh('Gauntlet | articulated phalanx cap',v,f,plate,.0008);uvgrid(cap,nr,nc)
        wire('Gauntlet | phalanx rolled lip',[v[j] for j in range(nc)],.00065,silver)
        stud('Gauntlet | articulation pin',v[(nr//2)*nc+1],(ob.matrix_world.to_3x3()@Vector((0,-1,0))).normalized(),.0016)

# A pointed rear central plate joins the temple shells rather than leaving a
# wide blank strip between them. Its profile follows the saved skull rings.
nr,nc=29,17;v=[];f=[]
for i in range(nr):
    t=i/(nr-1);z=1.735+.20*t;w=.015+.031*sin(pi*t)**.6
    rx=float(np.interp(z,[1.735,1.775,1.861,1.930,1.946],[.074,.088,.103,.083,.038]))
    ry=float(np.interp(z,[1.735,1.775,1.861,1.930,1.946],[.073,.083,.087,.077,.04]))
    for j in range(nc):
        u=-1+2*j/(nc-1);x=w*u;y=.014+ry*math.sqrt(max(.01,1-(x/rx)**2))+.005+.003*(1-abs(u))*sin(pi*t)
        v.append((x,y,z+.012*abs(u)*(1-t)**4))
for i in range(nr-1):
    for j in range(nc-1):a=i*nc+j;f.append((a,a+nc,a+nc+1,a+1))
ob=mesh('Helmet | central occipital keel',v,f,plate,.0025);uvgrid(ob,nr,nc)
for j in [0,nc-1]:wire('Helmet | rear keel seam',[v[i*nc+j] for i in range(nr)],.0009)

# Cloth: keep the saved connected cape, sewn UVs, silhouette and attachment.
# Evolving creases and narrow irregular tears replace the pristine surface.
cape=bpy.data.objects.get('Cape | tailored drape and sparse torn openings');preserve(cape,copy=True)
uvs={l.vertex_index:cape.data.uv_layers.active.data[l.index].uv.copy()/8 for l in cape.data.loops}
for vertex in cape.data.vertices:
    u,t=uvs[vertex.index];mask=sin(pi*max(0,min(1,t)))
    vertex.co.y+=.012*sin(21*t+13*u+sin(11*u))*mask
    vertex.co.y+=.006*sin(79*t+13*sin(6*u))*math.exp(-((t-.24)/.23)**2)*sin(pi*u)**2
    vertex.co.x+=.018*sin(15*t+7*u)*t*t
    if t>.86:
        a=-1.13+2.26*u
        hem=(1.59+.11*cos(a)**4)*(1-t)+.025*t
        hem+=t**14*(.052*max(0,sin(u*61+.6))**5+.024*max(0,sin(u*143))**4)
        blend=((t-.86)/.14)**2;vertex.co.z=vertex.co.z*(1-blend)+hem*blend
for l in cape.data.loops:cape.data.uv_layers.active.data[l.index].uv/=8
tears=[(.16,.88,.012,.080),(.72,.91,.011,.075),(.90,.83,.008,.065),(.37,.97,.008,.042)]
def tear_mask(u,t):
    for a,b,ru,rt in tears:
        x=(u-a-.003*sin(56*t))/ru;y=(t-b)/rt
        if x*x+y*y<1+.20*sin(90*t+35*u)+.12*sin(171*t):return True
    return False
bm=bmesh.new();bm.from_mesh(cape.data);bm.verts.ensure_lookup_table()
uvlayer=bm.loops.layers.uv.active
remove=[]
for f in bm.faces:
    u=sum(l[uvlayer].uv.x for l in f.loops)/len(f.loops);t=sum(l[uvlayer].uv.y for l in f.loops)/len(f.loops)
    if tear_mask(u,t):remove.append(f)
bmesh.ops.delete(bm,geom=remove,context='FACES')
for v in list(bm.verts):
    if not v.link_faces:bm.verts.remove(v)
boundary=[(e.verts[0].co.copy(),e.verts[1].co.copy()) for e in bm.edges if e.is_boundary and min(v.co.z for v in e.verts)<.52]
bm.to_mesh(cape.data);bm.free();cape.data.update()

# A unique full-cape PBR texture carries weathering, weave and hem abrasion.
cm=material('15 | Weathered woven cloak',(.01,.009,.008),0,.94)
n=1024;tt,uu=np.mgrid[0:n,0:n]/(n-1);rng=np.random.default_rng(190911)
grain=rng.random((n,n));cloud=(np.sin(uu*19+np.sin(tt*9))+np.sin(tt*23+uu*11))*.5
hem=np.clip((tt-.64)/.36,0,1)**2
fade=.6+.4*np.sin(uu*25+tt*17)**2
color=np.array([.008,.0085,.009])[None,None,:]*(1+.20*cloud[:,:,None]+.1*(grain[:,:,None]-.5))
color+=hem[:,:,None]*fade[:,:,None]*np.array([.012,.009,.005])
for a,b,ru,rt in tears:
    dist=((uu-a)/ru)**2+((tt-b)/rt)**2
    abrasion=np.exp(-((dist-1)/.8)**2)*(.2+.8*grain)
    color+=abrasion[:,:,None]*np.array([.014,.010,.006])
rough=np.clip(.93+.035*cloud+.02*grain,.83,.99)
weave=np.sin(uu*2*pi*230)*np.sin(tt*2*pi*270)*.02+(grain-.5)*.04
nx=np.roll(weave,1,1)-np.roll(weave,-1,1);ny=np.roll(weave,1,0)-np.roll(weave,-1,0)
normal=np.stack((nx,ny,np.ones_like(nx)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
p=cm.node_tree.nodes.get('Principled BSDF');p.inputs['Sheen Weight'].default_value=.18
for label,pixels,socket in [('Albedo',color,'Base Color'),('Roughness',np.repeat(rough[:,:,None],3,2),'Roughness'),('Normal',normal*.5+.5,'Normal')]:
    im=bpy.data.images.new('Cloak unique '+label,width=n,height=n);im.colorspace_settings.name='Non-Color'
    rgba=np.concatenate((pixels,np.ones((n,n,1))),axis=-1).astype(np.float32);im.pixels.foreach_set(rgba.ravel());im.pack()
    tx=cm.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im
    if socket=='Normal':
        nm=cm.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.5
        cm.node_tree.links.new(tx.outputs['Color'],nm.inputs['Color']);cm.node_tree.links.new(nm.outputs['Normal'],p.inputs['Normal'])
    else:cm.node_tree.links.new(tx.outputs['Color'],p.inputs[socket])
cape.data.materials.clear();cape.data.materials.append(cm)
for ob in scene.objects:
    if not ob.hide_render and ob.type=='MESH' and ob.name.startswith('Cloth | folded torn hip hanging'):
        for l in ob.data.uv_layers.active.data:l.uv.x/=3;l.uv.y/=6
        ob.data.materials.clear();ob.data.materials.append(cm)
# The native/glTF material use the same portable inputs; no Blender-only sheen.
p.inputs['Sheen Weight'].default_value=0
for i,(a,b) in enumerate(boundary):
    if i%2:continue
    length=(b-a).length
    if length>.06:continue
    q=(a+b)*.5;rand=np.random.default_rng(i+81)
    for k in range(2):
        offset=(b-a)*rand.uniform(-.4,.4);start=q+offset
        end=start+Vector((rand.uniform(-.005,.005),rand.uniform(-.002,.002),-rand.uniform(.003,.016)))
        wire('Cape | frayed warp strand',[start,(start+end)*.5+Vector((.001,0,0)),end],.00016,fiber)

# Stitch a quiet central back seam onto the actual deformed cape surface.
v=[x.co.copy() for x in cape.data.vertices];f=[list(p.vertices) for p in cape.data.polygons];cloth_tree=BVHTree.FromPolygons(v,f)
for i in range(90):
    z=.25+i*.014;x=-.025-.045*(1.65-z)
    a,normal,_,_=cloth_tree.ray_cast(Vector((x,1,z)),Vector((0,-1,0)))
    b,_,_,_=cloth_tree.ray_cast(Vector((x+.003,1,z+.006)),Vector((0,-1,0)))
    if a is not None and b is not None:wire('Cape | hand stitched back seam',[a+Vector((0,.001,0)),b+Vector((0,.001,0))],.00045,seam_mat)

# Better packed roughness on the small silhouette horns, without new geometry.
for ob in scene.objects:
    if ob.type=='MESH' and not ob.hide_render and any(k in ob.name for k in ['swept temple blade','rear swept tine','high swept blade','lateral spear','rear defensive thorn']):
        if ob.data.materials and ob.data.materials[0]==steel:ob.data.materials[0]=plate

for ob in list(new):
    if ob.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
for ob in new:
    if ob.type!='MESH' or ob.data.uv_layers:continue
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')

scene['continuation_base']='4526999d0d75787b148da734cb5ee2e97313a39a'
scene['surface_pass']='Fitted helmet panels, phalanx plates, engraved armor and weathered torn cloak'
scene.cycles.samples=20 if PROOF else 64;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='CUDA'
    scene.cycles.device='GPU' if any(d.type=='CUDA' for d in prefs.devices) else 'CPU'
except Exception:scene.cycles.device='CPU'
scene.render.resolution_x=1280;scene.render.resolution_y=1440;scene.render.resolution_percentage=45 if PROOF else 100
cam=scene.camera;cam.data.ortho_scale=2.75;target=Vector((.24,0,1.08))
views={'front':(0,-5,1.48),'back':(0,5,1.48),'side':(-5,0,1.48),'perspective':(-3.4,-5.2,2.35)}
def setview(name):cam.location=views[name];cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
setview('perspective');bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Gothic_Black_Knight.blend'),compress=True)
assets=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
if not PROOF:
    for ob in assets:ob.select_set(True)
    # Batch static pieces only in the transient export scene. Keep native
    # objects editable and use render subdivision for source/export parity.
    for ob in assets:
        for mod in ob.modifiers:
            if mod.type=='SUBSURF':mod.levels=mod.render_levels
    bpy.context.view_layer.objects.active=bpy.data.objects['Cuirass | forged breast and back']
    bpy.ops.object.convert(target='MESH')
    for ob in bpy.context.selected_objects:
        if ob.type!='MESH':continue
        uv=ob.data.uv_layers.active
        if uv:
            for other in list(ob.data.uv_layers):
                if other!=uv:ob.data.uv_layers.remove(other)
            uv.name='UVMap'
    bpy.ops.object.join();hero=bpy.context.object;hero.name='Gothic Black Knight | static material batches'
    hero.modifiers.new('Export triangulation','TRIANGULATE')
    bpy.ops.export_scene.gltf(filepath=str(OUT/'Gothic_Black_Knight.glb'),export_format='GLB',use_selection=True,export_apply=True,export_tangents=True,export_cameras=False,export_lights=False)
    for script in ['fix_glb_color.py','repair_tangents.py']:
        subprocess.run([os.environ.get('KNIGHT_PYTHON','python'),str(ROOT/'scripts'/script),str(OUT/'Gothic_Black_Knight.glb')],check=True)
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'Gothic_Black_Knight.blend'));scene=bpy.context.scene;cam=scene.camera
report={'base_commit':scene['continuation_base'],'source_meshes':len(assets),'new_objects':len(new),'resolution':[int(1280*scene.render.resolution_percentage/100),int(1440*scene.render.resolution_percentage/100)],'samples':scene.cycles.samples,'views':{}}
for name in os.environ.get('KNIGHT_VIEWS',','.join(views)).split(','):
    setview(name);scene.render.filepath=str(OUT/('preview_'+name+'.png'));bpy.ops.render.render(write_still=True)
    report['views'][name]=hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest();(OUT/'refinement_check.json').write_text(json.dumps(report,indent=2))
print('SURFACE_PASS_COMPLETE',json.dumps(report))
