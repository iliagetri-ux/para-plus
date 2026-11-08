"""Continue the saved 92c98ee asset; never regenerate or overwrite the baseline.

Blender 4.5: blender -b --python-exit-code 1 --python scripts/refine_saved.py
KNIGHT_PROOF=1 produces small art proofs; default writes the reviewed deliverables.
"""
import bpy, bmesh, math, os, sys, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi

ROOT = Path(__file__).resolve().parents[1]
PROOF = os.environ.get('KNIGHT_PROOF') == '1'
OUT = ROOT / ('proof/refinement' if PROOF else 'artifacts/refined')
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'artifacts/GothicBlackKnight.blend'))
scene = bpy.context.scene
baseline = list(scene.objects)
archive = bpy.data.collections.new('ARCHIVE | previous forms, excluded from delivery')
scene.collection.children.link(archive)
archive.hide_render = True
archive.hide_viewport = True

def preserve(ob):
    for col in list(ob.users_collection): col.objects.unlink(ob)
    archive.objects.link(ob)
    ob.hide_render = True
    ob.hide_set(True)

steel = bpy.data.materials['01 | Blackened forged steel']
edge = bpy.data.materials['02 | Worn pewter edges']
dark = bpy.data.materials['03 | Recessed steel']
cloth = bpy.data.materials['04 | Charcoal woven wool']
new_objects = []

def material(name, color, metal, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*color, 1)
    return m

gold = material('08 | Aged warm brass inlay', (.17,.095,.035), .88, .38)
cut = material('09 | Engraved recess', (.004,.005,.007), .7, .5)
polished = material('10 | Honed steel bevel', (.19,.20,.21), .96, .27)

def plate_finish():
    """Portable PBR finish: edge wear, mottled patina and sparse fine scratches."""
    m=material('11 | Black plate, localized wear',(.023,.027,.032),.94,.37)
    n=768;yy,xx=np.mgrid[0:n,0:n]/(n-1);rng=np.random.default_rng(1909)
    grain=rng.random((n,n));patina=(np.sin(23*xx+2*np.sin(13*yy))+np.sin(39*yy+np.sin(17*xx)))*.5
    border=np.minimum.reduce([xx,1-xx,yy,1-yy])
    worn=np.exp(-border*160)*(.3+.7*grain)*(grain>.31)
    scratches=np.zeros((n,n))
    for k in range(100):
        x,y=rng.uniform(.07,.93,2);length=rng.uniform(.006,.06);slope=rng.uniform(-1.8,1.8)
        line=np.maximum(0,1-np.abs(xx-x-slope*(yy-y))/.0011)
        line*=np.maximum(0,1-np.abs(yy-y)/length)
        scratches=np.maximum(scratches,line*rng.uniform(.1,.7))
    base=np.array([.017,.021,.027])[None,None,:]*(1+.12*patina[:,:,None]+.05*(grain[:,:,None]-.5))
    base+=worn[:,:,None]*np.array([.075,.064,.044])+scratches[:,:,None]*.025
    rough=np.clip(.36+.055*patina+.028*(grain-.5)-.10*worn-.06*scratches,.20,.52)
    height=(grain-.5)*.014+patina*.009-scratches*.09
    nx=(np.roll(height,1,1)-np.roll(height,-1,1))*1.5
    ny=(np.roll(height,1,0)-np.roll(height,-1,0))*1.5
    normals=np.stack((nx,ny,np.ones_like(nx)),axis=-1);normals/=np.linalg.norm(normals,axis=-1,keepdims=True)
    p=m.node_tree.nodes.get('Principled BSDF')
    for name,data,socket in [('Albedo',base,'Base Color'),('Roughness',np.repeat(rough[:,:,None],3,2),'Roughness'),('Normal',normals*.5+.5,'Normal')]:
        im=bpy.data.images.new('Refined plate '+name,width=n,height=n);im.colorspace_settings.name='Non-Color'
        rgba=np.concatenate((data,np.ones((n,n,1))),axis=-1).astype(np.float32)
        im.pixels.foreach_set(rgba.ravel());im.pack()
        tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im
        if socket=='Normal':
            nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.4
            m.node_tree.links.new(tx.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],p.inputs['Normal'])
        else:m.node_tree.links.new(tx.outputs['Color'],p.inputs[socket])
    return m
plate_steel=plate_finish()

# Reduce the coarse hammered finish; preserve all packed source maps.
for m in [steel, dark]:
    for node in m.node_tree.nodes:
        if node.type == 'NORMAL_MAP': node.inputs['Strength'].default_value = .18
for node in edge.node_tree.nodes:
    if node.type == 'TEX_IMAGE' and node.image and 'Albedo' in node.image.name:
        px = np.array(node.image.pixels[:], dtype=np.float32).reshape(-1,4)
        px[:,:3] *= [1.0,.71,.38]
        node.image.pixels.foreach_set(px.ravel()); node.image.pack()
edge.name = '02 | Patinated warm metal edges'

def mesh(name, verts, faces, mat=steel, thick=0, bevel=0):
    me=bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob=bpy.data.objects.new(name,me); scene.collection.objects.link(ob)
    me.materials.append(mat); new_objects.append(ob)
    bm=bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth=True
    if thick:
        m=ob.modifiers.new('Forged wall', 'SOLIDIFY'); m.thickness=thick; m.offset=-1
    if bevel:
        m=ob.modifiers.new('Hand softened edges', 'BEVEL'); m.width=bevel; m.segments=3
    return ob

def wire(name, pts, radius=.0011, mat=gold):
    if len(pts)<2:return
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=radius;c.bevel_resolution=2
    sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,co in zip(sp.points,pts):p.co=(*co,1)
    ob=bpy.data.objects.new(name,c);scene.collection.objects.link(ob);ob.data.materials.append(mat)
    new_objects.append(ob);return ob

def bezier(control,t):
    a,b,c,d=[Vector(p) for p in control]
    return a*(1-t)**3+3*b*t*(1-t)**2+3*c*t*t*(1-t)+d*t**3

def blade_leaf(name, control, width, depth=.008, mat=steel, trim=True):
    """Broad swept armor leaf with taper, central keel and forged edge thickness."""
    nr,nc=33,13;v=[];f=[]
    for i in range(nr):
        t=i/(nr-1);p=bezier(control,t)
        tangent=bezier(control,min(1,t+.002))-bezier(control,max(0,t-.002))
        side=Vector((tangent.z,0,-tangent.x)).normalized()
        w=width*(.022+.978*sin(pi*t)**.65)*(1-.27*t)
        for j in range(nc):
            u=-1+2*j/(nc-1)
            co=p+side*w*u
            co.y-=depth*(1-abs(u))*(.35+.65*sin(pi*t))
            co.y+=.0013*sin(t*18+u*4)*sin(pi*t)*(1-u*u)
            v.append(co)
    for i in range(nr-1):
        for j in range(nc-1):
            a=i*nc+j;f.append((a,a+1,a+nc+1,a+nc))
    ob=mesh(name,v,f,plate_steel if mat==steel else mat,.003,.0007)
    uv=ob.data.uv_layers.new(name='Authored plate coordinates')
    for l in ob.data.loops:uv.data[l.index].uv=(l.vertex_index%nc/(nc-1),l.vertex_index//nc/(nr-1))
    if trim:
        for j in [0,nc-1]:wire(name+' | chased margin',[v[i*nc+j]+Vector((0,-.0009,0)) for i in range(nr)],.0009)
        wire(name+' | raised keel',[v[i*nc+nc//2]+Vector((0,-.0006,0)) for i in range(nr)],.00065)
    # Fine paired incisions running beside the ridge, built into the relief surface.
    for j in [4,8]:
        wire(name+' | incised line',[v[i*nc+j]+Vector((0,-.0005,0)) for i in range(4,nr-4)],.00055,cut)
    if name.startswith(('Breast','Pauldron | overlapping','Plackart','Tasset')):
        # Curving etched branches, interpolated directly on this plate surface.
        def on_surface(t,u):
            a=max(0,min(nr-1.001,t*(nr-1)));b=max(0,min(nc-1.001,(u+1)*.5*(nc-1)))
            i,j=int(a),int(b);ft,fu=a-i,b-j
            return ((v[i*nc+j]*(1-fu)+v[i*nc+j+1]*fu)*(1-ft)+(v[(i+1)*nc+j]*(1-fu)+v[(i+1)*nc+j+1]*fu)*ft)+Vector((0,-.0007,0))
        for k in range(3):
            t0=.22+k*.18
            for side in [-1,1]:
                pts=[on_surface(t0+.19*a/24,side*(.18+.53*sin(pi*a/48))) for a in range(25)]
                wire(name+' | engraved branching scroll',pts,.0006,cut)
                wire(name+' | inlaid scroll lip',[p+Vector((.0007,-.0002,0)) for p in pts],.00028,gold)
    return ob

def horn(name, controls, width, flatten=.48):
    v=[];f=[];nr=33;nc=12
    for i in range(nr):
        t=i/(nr-1);center=bezier(controls,t)
        tangent=(bezier(controls,min(1,t+.002))-bezier(controls,max(0,t-.002))).normalized()
        a=tangent.cross(Vector((0,1,0))).normalized();b=tangent.cross(a).normalized()
        r=width*(1-t)**1.18+.0003
        for j in range(nc):
            angle=2*pi*j/nc
            v.append(center+a*(r*cos(angle))+b*(r*flatten*sin(angle)))
    for i in range(nr-1):
        for j in range(nc):
            a=i*nc+j;b=i*nc+(j+1)%nc;f.append((a,b,b+nc,a+nc))
    f += [tuple(range(nc-1,-1,-1)),tuple((nr-1)*nc+j for j in range(nc))]
    # The swept surface is already smooth. A bevel at its submillimetre tip
    # creates collapsed sliver triangles; leave the watertight taper intact.
    ob=mesh(name,v,f,steel,0,0)
    for j in [0,3,6]:wire(name+' | forged ridge',[v[i*nc+j] for i in range(nr)],.0007)
    return ob

def rivet(name, position, radius=.0035, mat=gold):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1,location=position)
    ob=bpy.context.object;ob.name=name;ob.scale=(radius,radius*.45,radius)
    ob.data.materials.append(mat);new_objects.append(ob)
    for p in ob.data.polygons:p.use_smooth=True
    return ob

# Store superseded crown/mantle rather than delete editable work.
for ob in baseline:
    if ob.name == 'STUDIO floor':
        bpy.data.objects.remove(ob,do_unlink=True)
    elif ob.name.startswith(('Crown |','Repousse acanthus | Crown','Mantle folded band','Mantle clasp')):
        preserve(ob)

# Old crown outlines belong to one merged ornament mesh. Keep the original in
# archive, and remove only crown/mantle-clasp components from a delivery copy.
old=bpy.data.objects.get('Chased tracery, rolled edges and bindings')
if old:
    decor=old.copy();decor.data=old.data.copy();scene.collection.objects.link(decor)
    decor.name='Preserved body chasing and bindings';preserve(old)
    bm=bmesh.new();bm.from_mesh(decor.data)
    remove=[v for v in bm.verts if (v.co.z>1.87 and abs(v.co.x)<.15) or
            ((v.co-Vector((-.17,-.135,1.64))).length<.041)]
    bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(decor.data);bm.free()

# Integrated helmet crown: broad rearward swept blades, pointed cheek wings.
for s in [-1,1]:
    horn('Crown | swept temple blade',[(s*.075,.016,1.86),(s*.12,.025,1.95),(s*.14,.035,2.04),(s*.154,.025,2.11)],.046,.48)
    horn('Crown | rear swept tine',[(s*.074,.079,1.87),(s*.103,.115,1.94),(s*.11,.13,2.035),(s*.096,.12,2.10)],.031,.5)
    blade_leaf('Helmet | angular cheek wing',[(s*.035,-.129,1.70),(s*.092,-.121,1.76),(s*.107,-.082,1.84),(s*.125,-.045,1.93)],.025,.013)
    blade_leaf('Helmet | scowling brow',[(s*.003,-.136,1.803),(s*.035,-.146,1.825),(s*.084,-.121,1.837),(s*.104,-.079,1.865)],.017,.005)
    blade_leaf('Helmet | forehead lancet',[(s*.012,-.122,1.823),(s*.042,-.128,1.875),(s*.04,-.105,1.925),(s*.02,-.06,1.975)],.026,.011)
    # Narrow cheek ventilation slits seated along the closed mask.
    for k in range(3):
        x=s*(.041+k*.014)
        wire('Helmet | recessed breathing slit',[(x,-.127+k*.008,1.734+k*.007),(x+s*.008,-.122+k*.008,1.764+k*.008)],.0013,cut)
horn('Helmet | central swept crest',[(0,.03,1.91),(0,.023,1.975),(0,.015,2.025),(0,.015,2.06)],.041,.6)

# Reference-like spiked shoulder shells, seated over original articulated lames.
for s in [-1,1]:
    lift=.045 if s<0 else 0
    horn('Pauldron | high swept blade',[(s*.295,.002,1.70),(s*.355,.006,1.765),(s*.402,.012,1.84+lift),(s*.414,.016,1.90+lift)],.069,.7)
    horn('Pauldron | lateral spear',[(s*.37,-.005,1.635),(s*.43,-.009,1.65),(s*.50,-.01,1.67),(s*.565,-.015,1.71)],.058,.58)
    horn('Pauldron | rear defensive thorn',[(s*.32,.10,1.65),(s*.36,.155,1.70),(s*.40,.18,1.75),(s*.415,.20,1.80)],.044,.7)
    for layer in range(3):
        z=1.68-layer*.065
        blade_leaf('Pauldron | overlapping flared face',[(s*.235,-.085,z+.04),(s*.31,-.15,z+.035),(s*.41,-.151,z-.03),(s*.455,-.10,z-.105)],.053-layer*.005,.013)
        for x,dz in [(.276,.012),(.379,-.024)]:rivet('Pauldron | bronze hinge rivet',(s*x,-.156,z+dz),.003)

# New broad breastplates overlap the usable cuirass; shaped chevrons follow the
# pectoral volume and converge into a lower medial point, as in the reference.
for s in [-1,1]:
    blade_leaf('Breast | upper clavicle plate',[(s*.157,-.104,1.646),(s*.12,-.143,1.645),(s*.055,-.164,1.58),(s*.005,-.181,1.545)],.026,.009)
    for k in range(3):
        z=1.59-k*.086
        blade_leaf('Breast | swept articulated chevron',[(s*.205,-.114,z+.018),(s*.165,-.176,z+.028),(s*.075,-.193,z-.01),(s*.007,-.178,z-.113)],.046-k*.003,.014)
    blade_leaf('Plackart | long pointed waist flange',[(s*.165,-.117,1.38),(s*.123,-.162,1.34),(s*.059,-.174,1.25),(s*.008,-.148,1.18)],.037,.012)
    blade_leaf('Gorget | standing collar fin',[(s*.01,-.100,1.60),(s*.065,-.104,1.645),(s*.10,-.059,1.689),(s*.12,-.011,1.72)],.020,.006)
    # Fanned tassets give the hips the layered, angular shape of the reference.
    for k in range(3):
        blade_leaf('Tasset | fanned hip lame',[(s*(.08+k*.035),-.139,1.165-k*.021),(s*(.15+k*.033),-.16,1.12-k*.034),(s*(.21+k*.027),-.135,1.015-k*.045),(s*(.20+k*.037),-.10,.935-k*.04)],.046,.010)
    # Thorns are flattened blade forms, rooted in the forearm rather than cones.
    if s<0:
        for k in range(2):horn('Vambrace | defensive blade',[(-.385,-.028,1.12+k*.065),(-.421,-.028,1.17+k*.066),(-.454,-.024,1.205+k*.071),(-.47,-.018,1.24+k*.07)],.030,.4)
    blade_leaf('Poleyn | side wing',[(s*.171,-.088,.56),(s*.215,-.085,.59),(s*.244,-.061,.64),(s*.224,-.016,.70)],.029,.009)

# Replace no fabric: reshape the original connected cape mesh and its sewn UVs.
cape=bpy.data.objects.get('Cape | tailored drape and sparse torn openings')
for v in cape.data.vertices:
    t=max(0,min(1,(1.69-v.co.z)/1.65))
    u=(v.co.x+.075*t*t)/(.505*1.35)
    v.co.x += .12*t**2*sin(u*1.5)+.025*t*sin(7*u+3*t)
    v.co.y += .055*t*t*sin(6*u+2*t)
    v.co.z += .024*t**8*sin(17*u+.5)+.012*t**12*sin(49*u)
    v.co.z=max(.018,v.co.z)

# A pair of trailing side panels: broad folds rather than a cylindrical skirt.
for s in [-1,1]:
    nr,nc=65,33;v=[];f=[]
    for i in range(nr):
        t=i/(nr-1)
        for j in range(nc):
            u=j/(nc-1)
            x=s*(.145+.15*u+.09*t+.15*u*t*t)
            y=-.07+.19*u-.052*sin(3*pi*u+.8*t)*(.4+t)+.045*t*t
            z=1.12*(1-t)+(.09+.08*u+.05*sin(u*17)**4)*t
            z+=.07*t**10*max(0,sin(23*u+.7))**6
            v.append((x,y,z))
    for i in range(nr-1):
        for j in range(nc-1):
            a=i*nc+j;f.append((a,a+1,a+nc+1,a+nc))
    ob=mesh('Cloth | folded torn hip hanging',v,f,cloth,.0015)
    uv=ob.data.uv_layers.new(name='Woven panel UV')
    for l in ob.data.loops:uv.data[l.index].uv=(l.vertex_index%nc/(nc-1)*3,l.vertex_index//nc/(nr-1)*6)
    for j in [1,nc-2]:wire('Cloth | dark stitched selvage',[v[i*nc+j] for i in range(nr)],.0008,dark)

# Sword: preserve position and hand contact, broaden blade and accentuate bevels.
sword=bpy.data.objects.get('Greatsword | diamond section blade')
for v in sword.data.vertices:v.co.x=.63+(v.co.x-.63)*1.65
sword.data.materials.clear();sword.data.materials.append(steel);sword.data.materials.append(polished)
for p in sword.data.polygons:p.material_index=p.index%2
for s in [-1,1]:
    wire('Greatsword | inset fuller edge',[(.63+s*.014,-.133,.20),(.63+s*.023,-.137,.89),(.63+s*.029,-.139,.96)],.001,cut)

# Visible mantle clasps and back suspension straps anchor the surviving cloak.
for s in [-1,1]:
    blade_leaf('Cape | leaf clasp',[(s*.14,-.094,1.61),(s*.19,-.114,1.65),(s*.225,-.104,1.686),(s*.238,-.061,1.71)],.018,.006,gold,False)
    rivet('Cape | clasp pin',(s*.193,-.124,1.657),.005,polished)

# Lower the existing articulated forearm and carry the sword diagonally. The
# fingers, opposed thumb and forearm chasing follow the same rigid transform.
elbow=Vector((.35,-.005,1.23));grasp=Vector((.63,-.12,1.35))
arm_transform=Matrix.Translation(elbow)@Matrix.Rotation(math.radians(50),4,'Y')@Matrix.Translation(-elbow)
new_grasp=arm_transform@grasp
sword_transform=Matrix.Translation(new_grasp)@Matrix.Rotation(math.radians(-38),4,'Y')@Matrix.Translation(-grasp)@Matrix.Translation((0,0,.12))
for ob in list(scene.objects):
    if archive in ob.users_collection or ob==decor:continue
    if ob.name.startswith(('Greatsword |','Guard garnet setting')):
        ob.matrix_world=sword_transform@ob.matrix_world
    elif ob.type=='MESH' and any(n in ob.name for n in ['Vambrace','Wrist cuff','Gauntlet']):
        center=sum((ob.matrix_world@Vector(c) for c in ob.bound_box),Vector())/8
        if center.x>.40:ob.matrix_world=arm_transform@ob.matrix_world
if old:
    bm=bmesh.new();bm.from_mesh(decor.data);unseen=set(bm.verts)
    while unseen:
        start=unseen.pop()
        # Traverse connected ornament components, not arbitrary vertex boxes.
        frontier=[start];component=[start]
        while frontier:
            current=frontier.pop()
            for e in current.link_edges:
                other=e.other_vert(current)
                if other in unseen:unseen.remove(other);component.append(other);frontier.append(other)
        c=sum((v.co for v in component),Vector())/len(component)
        is_weapon=(c.x>.46 and c.z<1.15) or (c.x>.57 and c.z<1.28)
        transform=sword_transform if is_weapon else arm_transform if c.x>.39 and 1.18<c.z<1.47 else None
        if transform:
            for v in component:v.co=transform@v.co
    bm.to_mesh(decor.data);bm.free()

# Convert only newly made curves, unwrap added armor and preserve existing UVs.
for ob in list(new_objects):
    if ob.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
        bpy.ops.object.convert(target='MESH')
for ob in new_objects:
    if ob.type!='MESH' or ob.data.uv_layers:continue
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')

assets=[o for o in scene.objects if o.type=='MESH' and archive not in o.users_collection and not o.hide_render]
scene.render.engine='CYCLES';scene.cycles.samples=16 if PROOF else 48;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='CUDA';prefs.get_devices()
    cuda=[d for d in prefs.devices if d.type=='CUDA']
    for d in prefs.devices:d.use=d.type=='CUDA'
    if cuda:scene.cycles.device='GPU'
    print('RENDER_DEVICE',[(d.name,d.type,d.use) for d in prefs.devices],flush=True)
except Exception as exc:
    print('CUDA unavailable, using CPU',str(exc),flush=True);scene.cycles.device='CPU'
scene.render.resolution_x=800 if PROOF else 1280;scene.render.resolution_y=900 if PROOF else 1440
scene.render.resolution_percentage=65 if PROOF else 100
scene.render.film_transparent=True
scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.11,.13,.16,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.4
scene.view_settings.view_transform='AgX'
for o in scene.objects:
    if o.type=='LIGHT':
        o.data.color=(1,.91,.8) if 'key' in o.name else (.78,.85,1)
        o.data.energy*=1.2
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=2.75
target=Vector((.24,0,1.08))
views={'front':(0,-5,1.48),'back':(0,5,1.48),'side':(-5,0,1.48),'perspective':(-3.4,-5.2,2.35)}
def view(name):
    cam.location=views[name];cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
view('perspective')
scene['continuation_base']='92c98eefedf760f42ad7a9bf96388e32fc80c7df'
scene['art_status']='Reference silhouette refinement; static study, not certified production character'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Gothic_Black_Knight.blend'),compress=True)
if not PROOF:
    bpy.ops.object.select_all(action='DESELECT')
    for ob in assets:ob.select_set(True)
    temporary=[]
    for ob in assets:
        m=ob.modifiers.new('Export triangulation','TRIANGULATE');temporary.append((ob,m))
    bpy.ops.export_scene.gltf(filepath=str(OUT/'Gothic_Black_Knight.glb'),export_format='GLB',use_selection=True,export_apply=True,export_tangents=True,export_cameras=False,export_lights=False)
    for ob,m in temporary:ob.modifiers.remove(m)
    # Existing packed albedo images were authored as linear Non-Color. Encode
    # them to sRGB with the same tested correction used in the original pipeline.
    import subprocess
    subprocess.run([os.environ.get('KNIGHT_PYTHON','python'), str(ROOT/'scripts/fix_glb_color.py'),str(OUT/'Gothic_Black_Knight.glb')],check=True)
    subprocess.run([os.environ.get('KNIGHT_PYTHON','python'), str(ROOT/'scripts/repair_tangents.py'),str(OUT/'Gothic_Black_Knight.glb')],check=True)
report={'base_commit':scene['continuation_base'],'source_meshes':len(assets),'archive_objects':len(archive.objects),'new_objects':len(new_objects),'resolution':[round(scene.render.resolution_x*scene.render.resolution_percentage/100),round(scene.render.resolution_y*scene.render.resolution_percentage/100)],'samples':scene.cycles.samples,'views':{}}
for name in os.environ.get('KNIGHT_VIEWS',','.join(views)).split(','):
    view(name);scene.render.filepath=str(OUT/('preview_'+name+'.png'));bpy.ops.render.render(write_still=True)
    report['views'][name]=hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest()
    (OUT/'refinement_check.json').write_text(json.dumps(report,indent=2))
print('REFINEMENT_COMPLETE',json.dumps(report))
