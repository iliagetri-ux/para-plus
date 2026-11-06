import bpy, math, os, random, json
from mathutils import Vector
from math import sin,cos,pi
random.seed(19)
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=ROOT+'/artifacts'; os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
parts=[]
def mat(name,col,metal,rough,noise=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*col,1); m.use_nodes=True
 n=m.node_tree.nodes; p=n.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*col,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 if noise:
  t=n.new('ShaderNodeTexNoise'); t.inputs['Scale'].default_value=noise; t.inputs['Detail'].default_value=3
  b=n.new('ShaderNodeBump'); b.inputs['Strength'].default_value=.22; b.inputs['Distance'].default_value=.0014
  m.node_tree.links.new(t.outputs['Fac'],b.inputs['Height']); m.node_tree.links.new(b.outputs['Normal'],p.inputs['Normal'])
 # Packed image maps survive glTF export; procedural fine bump is supplemental.
 size=256; pixels=[]; roughpixels=[]
 rng=random.Random(name)
 for yy in range(size):
  for xx in range(size):
   mottling=.85+.12*sin(xx*.17+sin(yy*.12))+.07*sin(yy*.29)+rng.uniform(-.08,.08)
   pixels.extend([min(1,c*mottling) for c in col]+[1])
   rr=max(.03,min(1,rough+.06*sin(xx*.17+yy*.11)+rng.uniform(-.045,.045)))
   roughpixels.extend((rr,rr,rr,1))
 for label,data,socket in [('Albedo',pixels,'Base Color'),('Roughness',roughpixels,'Roughness')]:
  im=bpy.data.images.new(name+' '+label,width=size,height=size);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(data);im.pack()
  tx=n.new('ShaderNodeTexImage');tx.image=im;m.node_tree.links.new(tx.outputs['Color'],p.inputs[socket])
 return m
steel=mat('01 | Blackened forged steel',(.038,.044,.052),.88,.44,180)
edge=mat('02 | Worn pewter edges',(.22,.195,.155),.83,.34,230)
dark=mat('03 | Recessed steel',(.012,.016,.021),.65,.46,150)
cloth=mat('04 | Charcoal woven wool',(.018,.014,.016),0,.94,320)
leather=mat('05 | Oxblood leather',(.035,.013,.012),0,.68,180)
ruby=mat('06 | Garnet',(.19,.005,.008),.45,.19)

def mesh(name,v,f,ma=steel,sub=0,thick=0):
 me=bpy.data.meshes.new(name); me.from_pydata(v,[],f); me.update(); ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); ob.data.materials.append(ma); parts.append(ob)
 for p in me.polygons:p.use_smooth=True
 if sub:
  md=ob.modifiers.new('Surface continuity','SUBSURF');md.levels=sub
 if thick:
  md=ob.modifiers.new('Forged wall thickness','SOLIDIFY');md.thickness=thick
 return ob

def line(name,pts,r=.002,ma=edge):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12;cu.bevel_depth=r;cu.bevel_resolution=0
 sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob);ob.data.materials.append(ma);parts.append(ob);return ob

def loft(name,rings,ma=steel,n=48,flute=0,cap=True):
 # Ring: center x,y,z and cross-section radii. Coherent quad surface.
 v=[]
 for x,y,z,rx,ry in rings:
  for j in range(n):
   a=2*pi*j/n; relief=1+flute*cos(8*a)
   v.append((x+rx*sin(a)*relief,y-ry*cos(a)*relief,z))
 f=[]
 for k in range(len(rings)-1):
  for j in range(n): a=k*n+j;b=k*n+(j+1)%n;f.append((a,b,b+n,a+n))
 if cap:f.extend([tuple(range(n-1,-1,-1)),tuple((len(rings)-1)*n+j for j in range(n))])
 return mesh(name,v,f,ma)

def limb(name,a,b,rads,ma=steel,flute=.035):
 d=Vector(b)-Vector(a);q=Vector((0,0,1)).rotation_difference(d.normalized())
 ob=loft(name,[(0,0,d.length*t,rx,ry) for t,rx,ry in rads],ma,32,flute)
 for v in ob.data.vertices:v.co=q@v.co+Vector(a)
 return ob

def rim(ob,indices,name='Rolled plate edge',r=.0025):line(name,[ob.data.vertices[i].co[:] for i in indices],r)
def ornament(ob,rows,n=48,front=True):
 # Repeating pointed-arch chased tracery follows surface; no floating ornaments.
 nr=len(ob.data.vertices)//n
 for j in range(0,n,4):
  if front and cos(j*2*pi/n)<-.3:continue
  pts=[]
  for k in range(nr):
   idx=k*n+(j+(1 if k%4==2 else 0))%n;p=ob.data.vertices[idx].co.copy();p.y-=.0015;pts.append(p)
  line('Chased longitudinal foliate rib',pts,.0012,edge)
 for k in rows:
  if k<nr:rim(ob,[k*n+j for j in range(n)]+[k*n],r=.002)

# Human scale: 1.94 m helmet top, crown 2.18 m. Feet planted; eight-head body.
loft('Padded arming torso',[(0,0,1.01,.15,.105),(0,0,1.12,.17,.11),(0,0,1.30,.20,.12),(0,0,1.49,.245,.125),(0,0,1.58,.17,.10)],dark)
cu=loft('Cuirass | continuous peascod breast and back',[(0,0,1.17,.145,.108),(0,0,1.20,.16,.12),(0,0,1.30,.185,.145),(0,0,1.42,.235,.154),(0,0,1.50,.24,.13),(0,0,1.56,.16,.099)],steel,64,.018)
ornament(cu,[0,5],64)
# Raised gothic arches on breast, following ellipsoidal breast surface.
for sign in [-1,1]:
 for band in range(3):
  pts=[]
  for i in range(33):
   t=i/32;x=sign*(.026+t*(.15-band*.024));z=1.24+band*.075+.10*sin(pi*t)
   y=-.147*math.sqrt(max(.12,1-(x/.235)**2))-.006
   pts.append((x,y,z))
  line('Breastplate ogival engraving',pts,.002)
for k in range(4):
 z=1.10+k*.034
 ob=loft('Overlapping articulated fauld %02d'%k,[(0,0,z,.185-k*.009,.125),(0,0,z+.045,.17-k*.008,.12)],steel,48,.018);ornament(ob,[0])
loft('Gorget',[(0,0,1.53,.14,.10),(0,0,1.58,.115,.09),(0,0,1.66,.085,.077)],steel,48,.025)
# Helmet: shaped full enclosure with actual narrow open visor band.
loft('Helmet | skull',[(0,0,1.775,.108,.099),(0,0,1.83,.111,.104),(0,.005,1.90,.09,.089),(0,.005,1.94,.04,.045),(0,.005,1.947,.006,.009)],steel,64,.025)
he=loft('Helmet | pointed bevor',[(0,-.024,1.625,.012,.036),(0,-.015,1.67,.065,.083),(0,-.005,1.72,.096,.107),(0,0,1.764,.109,.107)],steel,64,.025);ornament(he,[3],64)
loft('Shadow behind visor slit',[(0,.004,1.755,.098,.09),(0,.004,1.79,.098,.09)],dark,48)
# Brow and crown circlet
ob=loft('Crown | encircling band',[(0,0,1.855,.111,.106),(0,0,1.882,.109,.103)],dark,64);ornament(ob,[0,1],64,False)
for j in range(8):
 a=2*pi*j/8;x=.105*sin(a);y=-.105*cos(a);h=.19 if j%2==0 else .13
 ob=loft('Crown | tapered forged pinnacle %02d'%j,[(x,y,1.862,.029,.021),(x*1.10,y*1.10,1.91,.02,.015),(x*1.13,y*1.13,1.96,.010,.009),(x*1.17,y*1.17,1.88+h,.001,.001)],steel,16)
 ornament(ob,[0],16,False)
line('Helmet median ridge',[(0,-.065,1.63),(0,-.112,1.72),(0,-.111,1.762)],.003)
# Shaped pointed pauldrons using angular patches, each is a whole thick plate.
for s in [-1,1]:
 for layer in range(3):
  v=[];f=[];nr=9;nc=33
  for k in range(nr):
   t=k/(nr-1)
   for j in range(nc):
    a=-pi*.60+pi*1.20*j/(nc-1);w=.12+.035*t
    phi=.035+t*1.50; radius=.135-layer*.008
    x=s*(.255+layer*.018+radius*sin(phi)*cos(a));y=.14*sin(phi)*sin(a);z=1.51-layer*.057+.125*cos(phi)-.018*(1+cos(4*a))*t**5
    v.append((x,y,z))
  for k in range(nr-1):
   for j in range(nc-1):a=k*nc+j;f.append((a,a+1,a+nc+1,a+nc))
  if s>0:f=[tuple(reversed(face)) for face in f]
  ob=mesh(('Left' if s<0 else 'Right')+' pauldron lame '+str(layer),v,f,steel,1,.007)
  rim(ob,list(range((nr-1)*nc,nr*nc)),r=.0035);rim(ob,list(range(nc)),r=.003)
  for j in [4,10,16,22,28]:line('Pauldron chased arch',[v[k*nc+j] for k in range(nr)],.0018)
 # hanging left arm; right elbow bends outward toward sword
 sh=(s*.29,0,1.49);el=(s*.35,-.005,1.23);wr=(s*.36,-.055,1.02) if s<0 else (s*.61,-.10,1.34)
 limb('Sleeve',sh,el,[(0,.068,.07),(.5,.075,.072),(1,.06,.06)],dark)
 limb('Rerebrace',sh,el,[(.1,.082,.079),(.4,.077,.076),(.9,.062,.061)],steel)
 limb('Elbow couter',el,tuple(Vector(el)+Vector((0,0,.08))),[(0,.072,.07),(.35,.085,.08),(1,.065,.065)],steel)
 limb('Vambrace',el,wr,[(.12,.066,.066),(.4,.061,.06),(.85,.045,.047),(1,.051,.052)],steel)
 limb('Wrist cuff',el,wr,[(.89,.052,.054),(1.05,.057,.054)],edge)
 handend=Vector(wr)+Vector((0,-.012,-.085)) if s<0 else Vector(wr)+Vector((.02,-.03,.055))
 limb('Gauntlet metacarpal plate',wr,handend,[(0,.048,.035),(.45,.051,.034),(1,.043,.028)],steel)
 for finger in range(4):
  start=handend+Vector(((finger-1.5)*.023,0,0));end=start+Vector((.006,-.025,-.078 if s<0 else -.069))
  limb('Articulated individual finger',start,end,[(0,.010,.013),(.30,.011,.014),(.35,.012,.015),(.62,.010,.012),(.68,.011,.014),(1,.007,.009)],steel,0)
 start=Vector(wr)+Vector((-.043,0,-.02));end=start+Vector((-.025,-.032,-.043));limb('Opposable thumb',start,end,[(0,.015,.016),(.5,.014,.015),(1,.009,.012)],steel,0)
 # Legs, cuisses -> knee -> greaves, each fitted to anatomy.
 x=s*.115
 limb('Arming leg',(x,0,.98),(x,.012,.15),[(0,.087,.085),(.4,.07,.073),(.5,.064,.068),(.75,.055,.06),(1,.04,.045)],dark)
 ob=loft('Anatomical cuisse',[(x,0,.64,.074,.078),(x,0,.73,.08,.088),(x,0,.87,.089,.094),(x,0,.98,.087,.09)],steel,48,.045);ornament(ob,[0,3])
 for k in range(3):
  ob=loft('Hip tasset overlapping plate',[(x,-.015,.88+k*.061,.091,.092),(x,-.008,.95+k*.061,.092,.091)],steel,48,.015);ornament(ob,[0])
 ob=loft('Pointed poleyn',[(x,-.018,.53,.025,.05),(x,-.025,.57,.07,.08),(x,-.027,.62,.079,.09),(x,-.012,.67,.064,.073)],steel,48,.06);ornament(ob,[0,3])
 ob=loft('Greave | calf and tibial crest',[(x,0,.13,.044,.052),(x,0,.20,.045,.056),(x,.012,.35,.066,.072),(x,.012,.46,.061,.067),(x,0,.54,.051,.056)],steel,48,.075);ornament(ob,[0,4])
 # sabaton horizontal contour rings, layered toes in front
 ob=loft('Sabatons | shaped plated boot',[(x,-.06,.035,.072,.15),(x,-.065,.055,.075,.155),(x,-.06,.085,.066,.14),(x,-.015,.13,.048,.075),(x,0,.17,.045,.054)],steel,48,.012);ornament(ob,[0,2])
 for k in range(4):
  yy=-.19+k*.032;pts=[]
  for j in range(25):
   a=-pi/2+pi*j/24;pts.append((x+.064*sin(a),yy,.057+.042*cos(a)+.009*k))
  line('Sabatons transverse articulation',pts,.0025)
# Cape, a coherent draped mesh: shoulders to torn ground hem, folds evolve continuously.
v=[];f=[];nu=96;nv=100
for k in range(nv):
 t=k/(nv-1)
 for j in range(nu):
  u=j/(nu-1);a=-1.13+2.26*u;width=.23+.28*t
  x=sin(a)*width*1.45;y=.075+(.035+.22*t)*cos(a)+.028*sin(u*16*pi+1.7*t)*(0.3+t)+.025*sin(u*5*pi+2*t)*t
  z=(1.56-.04*abs(sin(a)))*(1-t)+.055*t + .035*sin(u*23*pi)*t**10+.025*sin(u*59*pi)*t**18
  v.append((x,y,z))
for k in range(nv-1):
 for j in range(nu-1):
  if k>nv-7 and ((j*17)%29<4) and k>nv-3-((j*13)%5):continue
  a=k*nu+j;f.append((a,a+1,a+nu+1,a+nu))
mesh('Cape | continuous woven drape with torn hem',v,f,cloth,1,.002)
# Asymmetric folded mantle across upper chest
for layer in range(3):
 v=[];f=[]
 for i in range(49):
  t=i/48
  for j in range(7):
   w=j/6; x=-.19+.47*t; y=-.145-.018*sin(pi*w)-.045*sin(pi*t);z=1.57-.15*sin(pi*t*.8)-layer*.035+w*.037
   v.append((x,y,z))
 for i in range(48):
  for j in range(6):a=i*7+j;f.append((a,a+1,a+8,a+7))
 mesh('Mantle folded band',v,f,cloth,1,.003)
# Split tabard front, tailored with folds and shredded hems
for s in [-1,1]:
 v=[];f=[]
 for k in range(65):
  t=k/64
  for j in range(25):
   u=j/24;x=s*(.014+u*.105+.015*t); y=-.13-.022*sin(u*4*pi+t*2);z=1.10-.76*t+.06*sin(pi*u)*t**9+.018*sin(u*31)*t**15
   v.append((x,y,z))
 for k in range(64):
  for j in range(24):a=k*25+j;f.append((a,a+1,a+26,a+25))
 mesh('Split heraldic tabard',v,f,cloth,1,.002)
 for j in [1,23]:line('Tabard embroidered border',[v[k*25+j] for k in range(65)],.0018,edge)
# Belt
ob=loft('Leather waist belt',[(0,0,1.12,.185,.137),(0,0,1.16,.181,.134)],leather,64);ornament(ob,[0,1],64,False)
# Rosette clasps made as continuous radial relief surfaces
def medallion(name,c,r):
 v=[(c[0],c[1]-.009,c[2])];f=[]
 for k in range(1,6):
  for j in range(48):
   a=2*pi*j/48;rr=r*k/5;v.append((c[0]+rr*sin(a),c[1]-.003*sin(k*pi/5)-.002*cos(8*a),c[2]+rr*cos(a)))
 for j in range(48):f.append((0,1+j,1+(j+1)%48))
 for k in range(4):
  for j in range(48):a=1+k*48+j;b=1+k*48+(j+1)%48;f.append((a,b,b+48,a+48))
 mesh(name,v,f,edge,0,.003)
 line('Rosette rim',[(c[0]+r*sin(2*pi*j/64),c[1],c[2]+r*cos(2*pi*j/64)) for j in range(65)],.0025)
medallion('Mantle clasp',(-.17,-.17,1.54),.033);medallion('Belt buckle',(0,-.145,1.14),.036)
# Sword, diamond-section blade with full tang, sculpted swept guard.
sx=.63;sy=-.12
loft('Greatsword | diamond section blade',[(sx,sy,.025,.001,.001),(sx,sy,.15,.025,.009),(sx,sy,.91,.038,.012),(sx,sy,1.00,.047,.014),(sx,sy,1.025,.031,.013)],edge,4)
loft('Greatsword | leather grip',[(sx,sy,1.04,.017,.017),(sx,sy,1.23,.014,.014),(sx,sy,1.28,.018,.018)],leather,24)
for i in range(13):
 z=1.05+i*.016;line('Grip spiral binding',[(sx+.017*sin(2*pi*j/32),sy-.017*cos(2*pi*j/32),z+.014*j/32) for j in range(33)],.0015,dark)
# guard uses outline extruded in depth, not a cylinder
outline=[(-.15,1.025),(-.12,1.06),(-.105,1.044),(-.045,1.044),(0,1.065),(.045,1.044),(.105,1.044),(.12,1.06),(.15,1.025),(.065,1.026),(0,.98),(-.065,1.026)]
v=[(sx+x,sy+y,z) for y in [-.019,.019] for x,z in outline];n=len(outline);f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
mesh('Greatsword | sculpted crossguard',v,f,steel,0,0)
line('Guard chased border',v[:n]+[v[0]],.0025,edge)
medallion('Guard garnet setting',(sx,sy-.022,1.031),.019)
loft('Greatsword | pommel',[(sx,sy,1.27,.017,.017),(sx,sy,1.30,.029,.026),(sx,sy,1.33,.022,.021),(sx,sy,1.345,.005,.005)],steel,24,.06)
# Fine foliate chasing projected onto actual plate surfaces.
from mathutils.bvhtree import BVHTree
for ob in list(parts):
 if ob.type!='MESH' or not any(word in ob.name for word in ['Cuirass','cuisse','Greave','pauldron','bevor','Vambrace','Rerebrace']):continue
 verts=[v.co.copy() for v in ob.data.vertices]; faces=[list(p.vertices) for p in ob.data.polygons]
 tree=BVHTree.FromPolygons(verts,faces)
 xmin=min(v.x for v in verts);xmax=max(v.x for v in verts);zmin=min(v.z for v in verts);zmax=max(v.z for v in verts)
 for ix in range(max(1,int((xmax-xmin)/.032))):
  for iz in range(max(1,int((zmax-zmin)/.043))):
   cx=xmin+.018+ix*.032;cz=zmin+.022+iz*.043
   for mirror in [-1,1]:
    pts=[]
    for j in range(27):
     t=j/26;ang=t*1.8*pi;rr=.014*(1-.78*t)
     x=cx+mirror*rr*sin(ang);z=cz+rr*cos(ang)
     hit,normal,idx,dist=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
     if hit is not None:pts.append(hit+normal*.00065)
    if len(pts)>5:line('Surface chased acanthus',pts,.00065,edge)
# Central pointed brow applique, following visor skull rather than an exposed round dome.
v=[(-.107,-.101,1.84),(-.055,-.114,1.82),(0,-.125,1.785),(.055,-.114,1.82),(.107,-.101,1.84),(.09,-.10,1.88),(0,-.109,1.91),(-.09,-.10,1.88)]
mesh('Helmet | pointed gothic brow',v,[tuple(range(8))],steel,0,.004)
line('Brow worn border',v+[v[0]],.002,edge)

# Consolidate decorative curve objects into one mesh for manageable asset hierarchy.
curves=[o for o in parts if o.type=='CURVE'];bpy.ops.object.select_all(action='DESELECT')
for o in curves:o.select_set(True)
bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();bpy.context.object.name='Chased tracery, rolled edges and bindings'
# UVs on all surfaces, export-compatible material factors; procedural microdetail remains in blend.
assets=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in assets:
 bpy.context.view_layer.objects.active=o;bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
# Studio staging excluded from exports
bpy.ops.object.select_all(action='DESELECT')
for o in assets:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT+'/GothicBlackKnight.glb',export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.export_scene.fbx(filepath=OUT+'/GothicBlackKnight.fbx',use_selection=True,apply_unit_scale=True,bake_anim=False,add_leaf_bones=False)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=False
scene.render.resolution_x=800;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.color=(.12,.12,.12)
ground=mat('Studio floor',(.027,.032,.04),.05,.72)
bpy.ops.mesh.primitive_plane_add(size=200);floor=bpy.context.object;floor.name='STUDIO floor';floor.location.z=.03;floor.data.materials.append(ground)
def area(name,loc,power,color,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1.1))-o.location).to_track_quat('-Z','Y').to_euler()
area('STUDIO softbox key',(-3,-4,5),650,(.78,.86,1),4)
area('STUDIO warm rim',(2,2,3.5),850,(1,.77,.52),3)
area('STUDIO front fill',(3,-2,2),300,(.76,.85,1),3)
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.55
scene.view_settings.view_transform='AgX'
views={'Front':(0,-5,1.45),'Back':(0,5,1.45),'Side':(-5,0,1.45),'Right':(5,0,1.45),'45':(3,-5,2.0)}
report={'asset_meshes':len(assets),'vertices_base':sum(len(o.data.vertices) for o in assets),'polygons_base':sum(len(o.data.polygons) for o in assets),'reference':'Compared front, back and 45-degree renders to the user reference; still stylized and below target fidelity','limitations':['Static posed mesh; no rig or LODs','Procedural micro-normal detail is Blender-only until baked; GLB contains packed albedo and roughness images plus metalness factors','No production retopology or collision clearance certification']}
with open(OUT+'/validation.json','w') as f:json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/GothicBlackKnight.blend')
for name,loc in views.items():
 cam.location=loc;cam.rotation_euler=(Vector((.08,0,1.08))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=OUT+'/Preview_'+name+'.png'
 bpy.ops.wm.save_as_mainfile(filepath=OUT+'/GothicBlackKnight.blend') if name=='45' else None
 bpy.ops.render.render(write_still=True)
print('BUILD_COMPLETE',json.dumps(report))
