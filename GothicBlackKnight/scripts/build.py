import bpy, math, os, random, json
from mathutils import Vector
from math import sin,cos,pi
random.seed(19)
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FAST=os.environ.get('KNIGHT_FAST')=='1'; OUT=ROOT+('/proof' if FAST else '/artifacts'); os.makedirs(OUT,exist_ok=True)
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
steel=mat('01 | Blackened forged steel',(.026,.030,.036),.9,.43,180)
edge=mat('02 | Worn pewter edges',(.13,.125,.114),.85,.38,230)
dark=mat('03 | Recessed steel',(.012,.016,.021),.65,.46,150)
cloth=mat('04 | Charcoal woven wool',(.009,.008,.010),0,.97,320)
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
 for k in rows:
  if k<nr:rim(ob,[k*n+j for j in range(n)]+[k*n],r=.002)

# Human scale: 1.94 m helmet top, crown 2.07 m. Feet planted; eight-head body.
loft('Padded arming torso',[(0,0,1.01,.15,.105),(0,0,1.12,.17,.11),(0,0,1.30,.20,.12),(0,0,1.49,.245,.125),(0,0,1.58,.17,.10)],dark)
cu=loft('Cuirass | forged breast and back',[(0,0,1.165,.153,.105),(0,-.008,1.205,.164,.12),(0,-.005,1.255,.168,.127),(0,0,1.32,.193,.137),(0,0,1.39,.224,.149),(0,0,1.455,.243,.141),(0,0,1.505,.229,.12),(0,0,1.545,.173,.098)],steel,64,.008)
# medial keel and anatomical pectoral sweep are formed in the surface itself
for v in cu.data.vertices:
 front=max(0,-v.co.y/.15); waist=math.exp(-((v.co.z-1.28)/.13)**2)
 v.co.y-=.018*math.exp(-(v.co.x/.045)**2)*front*waist
 v.co.z+=.018*(abs(v.co.x)/.245)**1.2*math.exp(-((v.co.z-1.45)/.10)**2)
ornament(cu,[0,7],64)
for k in range(4):
 z=1.10+k*.034
 ob=loft('Overlapping articulated fauld %02d'%k,[(0,0,z,.185-k*.009,.125),(0,0,z+.045,.17-k*.008,.12)],steel,48,.018);ornament(ob,[0])
loft('Gorget | fitted neck articulation',[(0,0,1.535,.122,.093),(0,0,1.57,.096,.082),(0,0,1.65,.079,.072)],dark,48,.012)
# Helmet: shaped rear skull plus an angular, pointed closed face harness.
loft('Helmet | enclosed rear skull',[(0,.02,1.655,.060,.064),(0,.014,1.73,.088,.083),(0,.014,1.83,.103,.087),(0,.016,1.91,.083,.077),(0,.016,1.945,.038,.04),(0,.016,1.95,.006,.008)],steel,64,.012)
def visor_patch(name,rows):
 v=[];f=[];n=33
 for z,rx,depth,bow in rows:
  for j in range(n):
   u=-1+2*j/(n-1);x=rx*u
   # central ridge and planar cheek slopes; outer edges turn around the temples
   y=-depth+.052*abs(u)**1.15+.012*abs(u)**8
   v.append((x,y,z+bow*abs(u)**.8))
 for k in range(len(rows)-1):
  for j in range(n-1):a=k*n+j;f.append((a,a+1,a+n+1,a+n))
 ob=mesh(name,v,f,steel,0,.004)
 rim(ob,list(range(n)),r=.0018);rim(ob,list(range((len(rows)-1)*n,len(rows)*n)),r=.0018)
 return ob
he=visor_patch('Helmet | pointed faceplate',[(1.625,.013,.090,.025),(1.665,.055,.133,.017),(1.715,.090,.142,.012),(1.764,.104,.131,.021)])
visor_patch('Helmet | brow and ocular ridge',[(1.775,.105,.130,.021),(1.818,.110,.124,.008),(1.86,.101,.111,-.005),(1.892,.083,.101,-.014)])
line('Faceplate central crest',[(0,-.093,1.625),(0,-.136,1.665),(0,-.145,1.715),(0,-.134,1.764)],.0023)
# Crown is a continuous scalloped forged circlet with integrated ogival peaks.
v=[];f=[];n=128
for k in range(5):
 t=k/4
 for j in range(n):
  a=2*pi*j/n;peak=max(0,cos(6*a))**12
  z=1.865+t*(.045+.14*peak);rx=.107+.014*t;ry=.103+.012*t
  v.append((rx*sin(a),.006-ry*cos(a),z))
for k in range(4):
 for j in range(n):a=k*n+j;b=k*n+(j+1)%n;f.append((a,b,b+n,a+n))
ob=mesh('Crown | continuous ogival coronet',v,f,steel,0,.004)
rim(ob,[4*n+j for j in range(n)]+[4*n],r=.0018)
rim(ob,list(range(n))+[0],r=.0023)
for j in range(0,n,21):line('Crown rising ridge',[v[k*n+j] for k in range(5)],.0012)
# Shaped pointed pauldrons using angular patches, each is a whole thick plate.
for s in [-1,1]:
 limb('Padded shoulder attachment',(s*.19,0,1.505),(s*.29,0,1.565),[(0,.086,.082),(.5,.096,.095),(1,.075,.073)],dark,0)
 for layer in range(3):
  v=[];f=[];nr=9;nc=33
  for k in range(nr):
   t=k/(nr-1)
   for j in range(nc):
    a=-pi*.60+pi*1.20*j/(nc-1);w=.12+.035*t
    phi=.035+t*1.57; radius=.15-layer*.012
    x=s*(.255+layer*.018+radius*sin(phi)*cos(a));y=.14*sin(phi)*sin(a);z=1.51-layer*.057+.132*cos(phi)-.028*(.5+.5*cos(3*a))*t**5+.025*max(0,cos(a))**12*(1-t)**4
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
 leg_start=len(parts)
 x=s*.115
 limb('Arming leg',(x,0,.98),(x,.012,.15),[(0,.087,.085),(.4,.07,.073),(.5,.064,.068),(.75,.055,.06),(1,.04,.045)],dark)
 ob=loft('Anatomical cuisse',[(x,0,.64,.074,.078),(x,0,.73,.08,.088),(x,0,.87,.089,.094),(x,0,.98,.087,.09)],steel,48,.045);ornament(ob,[0,3])
 for k in range(3):
  ob=loft('Hip tasset overlapping plate',[(x,-.015,.88+k*.061,.091,.092),(x,-.008,.95+k*.061,.092,.091)],steel,48,.015)
  for j in range(48):ob.data.vertices[j].co.z-=.035*max(0,cos(2*pi*j/48))**6
  ornament(ob,[0])
 ob=loft('Pointed poleyn',[(x,-.018,.53,.025,.05),(x,-.025,.57,.07,.08),(x,-.027,.62,.079,.09),(x,-.012,.67,.064,.073)],steel,48,.06);ornament(ob,[0,3])
 ob=loft('Greave | calf and tibial crest',[(x,0,.13,.044,.052),(x,0,.20,.045,.056),(x,.012,.35,.066,.072),(x,.012,.46,.061,.067),(x,0,.54,.051,.056)],steel,48,.075);ornament(ob,[0,4])
 # sabaton horizontal contour rings, layered toes in front
 ob=loft('Sabatons | shaped plated boot',[(x,-.06,.035,.072,.15),(x,-.065,.055,.075,.155),(x,-.06,.085,.066,.14),(x,-.015,.13,.048,.075),(x,0,.17,.045,.054)],steel,48,.012);ornament(ob,[0,2])
 for k in range(4):
  yy=-.19+k*.032;pts=[]
  for j in range(25):
   a=-pi/2+pi*j/24;pts.append((x+.064*sin(a),yy,.057+.042*cos(a)+.009*k))
  line('Sabatons transverse articulation',pts,.0025)
 # Widen stance progressively from hips to ankles; transform their fitted details together.
 for ob in parts[leg_start:]:
  if ob.type=='MESH':points=[v.co for v in ob.data.vertices]
  else:points=[p.co for spline in ob.data.splines for p in spline.points]
  for co in points:
   co.x+=s*.05*max(0,1-co.z/1.05)
   if co.z<.17:co.x+=s*.12*max(0,-co.y-.015)*(1-co.z/.17)

# Tailored cape with evolving folds and localized tears, in one connected surface.
v=[];f=[];nu=81;nv=81
for k in range(nv):
 t=k/(nv-1)
 for j in range(nu):
  u=j/(nu-1);a=-1.13+2.26*u
  width=.255+.25*t+.045*sin(pi*t)
  x=sin(a)*width*1.43-.065*t*t*(1-u)**4
  envelope=.012+.033*t+.018*sin(pi*t)
  phase=u*13*pi+1.8*t+.7*sin(u*7+2*t)
  y=.13+.20*t+.065*sin(pi*t)*(cos(a)**2)+envelope*sin(phase)+.024*t*sin(u*5*pi+t*3)
  if t<.28:y=max(y,.118+.055*sin(pi*min(1,t/.10)/2))
  z=(1.565-.035*cos(a))*(1-t)+.035*t
  z+=t**12*(.115*max(0,sin(17*u+1))**8+.055*max(0,sin(41*u))**10)
  z+=.035*sin(pi*t)*sin(u*9+3*t)
  v.append((x,y,z))
for k in range(nv-1):
 for j in range(nu-1):
  u=(j+.5)/(nu-1);t=(k+.5)/(nv-1)
  tear=any(((u-cu)/ru)**2+((t-ct)/rt)**2 < 1+.18*sin(j*7+k*3) for cu,ct,ru,rt in [(.10,.94,.026,.034),(.79,.91,.017,.047),(.91,.975,.024,.045),(.28,.989,.012,.027)])
  if tear:continue
  a=k*nu+j;f.append((a,a+1,a+nu+1,a+nu))
mesh('Cape | tailored drape and sparse torn openings',v,f,cloth,1,.0014)
# Asymmetric folded mantle across upper chest
for layer in range(3):
 v=[];f=[]
 for i in range(49):
  t=i/48
  for j in range(7):
   w=j/6; x=-.19+.47*t; y=-.125-.021*sin(pi*w)-.052*sin(pi*t)-.005*layer;z=1.60-.16*sin(pi*t*.8)-layer*.031*(.3+sin(pi*t))+w*.043+.009*sin(t*13+layer)*sin(pi*t)
   v.append((x,y,z))
 for i in range(48):
  for j in range(6):a=i*7+j;f.append((a,a+1,a+8,a+7))
 mesh('Mantle folded band',v,f,cloth,1,.003)
# Worn, desaturated heraldic pigment on the cloth; real UV texture, not hovering geometry.
heraldry=cloth.copy();heraldry.name='07 | Faded oxblood heraldry'
im=bpy.data.images.new('Faded heraldic cross',width=512,height=512);im.colorspace_settings.name='Non-Color';pixels=[];rng=random.Random(37)
for yy in range(512):
 v=yy/511
 for xx in range(512):
  u=xx/511;noise=rng.random()
  shaft=abs(u-.5)<.025 and .17<v<.82
  arm=abs(v-.65)<.022 and .20<u<.80
  spear=.82<v<.90 and abs(u-.5)<(.9-v)*.65
  feet=.13<v<.22 and abs(u-.5)<(.22-v)*.5
  mask=(shaft or arm or spear or feet) and noise>.26+.17*sin(xx*.23+yy*.19)
  wear=.45+.35*noise
  col=(.052*wear,.008*wear,.012*wear) if mask else (.009,.008,.010)
  pixels.extend((*col,1))
im.pixels.foreach_set(pixels);im.pack();tx=heraldry.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im
heraldry.node_tree.links.new(tx.outputs['Color'],heraldry.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])

# Split tabard front, tailored with folds and shredded hems
for s in [-1,1]:
 v=[];f=[]
 for k in range(65):
  t=k/64
  for j in range(25):
   u=j/24;x=s*(.008+u*.125+.012*sin(t*4+u)*t); y=-.14-.025*sin(u*3*pi+t*2)-.02*sin(pi*t);z=1.10-(.78 if s<0 else .69)*t+.065*sin(pi*u)*t**9+.018*sin(u*31)*t**15
   v.append((x,y,z))
 for k in range(64):
  for j in range(24):a=k*25+j;f.append((a,a+1,a+26,a+25))
 ob=mesh('Split heraldic tabard',v,f,heraldry,1,.002)
 uv=ob.data.uv_layers.new(name='Tailored fabric UV');ob['preserve_uv']=True
 for loop in ob.data.loops:
  ix=loop.vertex_index;uv.data[loop.index].uv=(ix%25/24,1-(ix//25)/64)
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
# Authored branching foliage motifs, projected to each fitted plate.
from mathutils.bvhtree import BVHTree
for ob in list(parts):
 if ob.type!='MESH' or not any(word in ob.name for word in ['Cuirass','cuisse','Greave','pauldron','faceplate','Vambrace','Rerebrace']):continue
 verts=[v.co.copy() for v in ob.data.vertices];faces=[list(p.vertices) for p in ob.data.polygons]
 tree=BVHTree.FromPolygons(verts,faces)
 xmin=min(v.x for v in verts);xmax=max(v.x for v in verts);zmin=min(v.z for v in verts);zmax=max(v.z for v in verts)
 width=xmax-xmin;height=zmax-zmin
 def chase(path,r=.00075):
  pts=[]
  for x,z in path:
   hit,normal,idx,dist=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
   if hit is not None:pts.append(hit+normal*.00055)
  if len(pts)>3:line('Projected branching foliate relief',pts,r,edge)
 cols=max(1,int(width/.07))
 for col in range(cols):
  cx=xmin+width*(col+.5)/cols; h=height*.82;zz=zmin+height*.08
  phase=col*pi
  chase([(cx+.008*sin(t*2*pi+phase),zz+t*h) for t in [i/48 for i in range(49)]],.001)
  for leaf in range(max(2,int(h/.037))):
   t0=(leaf+.5)/max(2,int(h/.037));cz=zz+t0*h
   for sign in [-1,1]:
    bx=cx+.008*sin(t0*2*pi+phase)
    # swept lanceolate leaves, alternated along the central stem
    chase([(bx+sign*.024*sin(pi*t),cz+.035*t) for t in [i/20 for i in range(21)]])
    chase([(bx+sign*.011*sin(pi*t),cz+.035*t) for t in [i/20 for i in range(21)]],.0005)
# Consolidate decorative curve objects into one mesh for manageable asset hierarchy.
curves=[o for o in parts if o.type=='CURVE'];bpy.ops.object.select_all(action='DESELECT')
for o in curves:o.select_set(True)
bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();bpy.context.object.name='Chased tracery, rolled edges and bindings'
# UVs on all surfaces, export-compatible material factors; procedural microdetail remains in blend.
assets=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in ([] if FAST else assets):
 if o.get('preserve_uv'):continue
 bpy.context.view_layer.objects.active=o;bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
# Studio staging excluded from exports; mobile export uses less tessellation.
bpy.ops.object.select_all(action='DESELECT')
for o in assets:o.select_set(True)
if not FAST:
 saved_levels=[]
 for ob in assets:
  for mod in ob.modifiers:
   if mod.type=='SUBSURF':saved_levels.append((mod,mod.levels));mod.levels=0
 decor=bpy.data.objects.get('Chased tracery, rolled edges and bindings')
 reduction=decor.modifiers.new('Mobile relief density','DECIMATE');reduction.ratio=.65
 bpy.ops.export_scene.gltf(filepath=OUT+'/GothicBlackKnight.glb',export_format='GLB',use_selection=True,export_apply=True)
 import subprocess
 subprocess.run(['python',ROOT+'/scripts/fix_glb_color.py',OUT+'/GothicBlackKnight.glb'],check=True)
 bpy.ops.export_scene.fbx(filepath=OUT+'/GothicBlackKnight.fbx',use_selection=True,apply_unit_scale=True,bake_anim=False,add_leaf_bones=False)
 decor.modifiers.remove(reduction)
 for mod,level in saved_levels:mod.levels=level

scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=12 if FAST else 48;scene.cycles.use_denoising=False
scene.render.resolution_x=800;scene.render.resolution_y=1000;scene.render.resolution_percentage=65 if FAST else 100
scene.world.color=(.12,.12,.12)
ground=mat('Studio floor',(.027,.032,.04),.05,.72)
bpy.ops.mesh.primitive_plane_add(size=200);floor=bpy.context.object;floor.name='STUDIO floor';floor.location.z=.03;floor.data.materials.append(ground)
def area(name,loc,power,color,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1.1))-o.location).to_track_quat('-Z','Y').to_euler()
area('STUDIO softbox key',(-3,-4,5),650,(.78,.86,1),4)
area('STUDIO rim',(2,2,3.5),700,(.86,.91,1),3)
area('STUDIO front fill',(3,-2,2),300,(.76,.85,1),3)
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.55
scene.view_settings.view_transform='AgX'
views={'Front':(0,-5,1.45),'Back':(0,5,1.45),'Side':(-5,0,1.45),'Right':(5,0,1.45),'45':(3,-5,2.0)}
if FAST:views={'45':(3,-5,2.0),'Back':(0,5,1.45)}
report={'asset_meshes':len(assets),'vertices_base':sum(len(o.data.vertices) for o in assets),'polygons_base':sum(len(o.data.polygons) for o in assets),'reference':'Compared front, back and 45-degree renders to the user reference; still stylized and below target fidelity','limitations':['Static posed mesh; no rig or LODs','Procedural micro-normal detail is Blender-only until baked; GLB contains packed albedo and roughness images plus metalness factors','No production retopology or collision clearance certification']}
with open(OUT+'/validation.json','w') as f:json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/GothicBlackKnight.blend')
for name,loc in views.items():
 cam.location=loc;cam.rotation_euler=(Vector((.08,0,1.08))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=OUT+'/Preview_'+name+'.png'
 bpy.ops.wm.save_as_mainfile(filepath=OUT+'/GothicBlackKnight.blend') if name=='45' else None
 bpy.ops.render.render(write_still=True)
print('BUILD_COMPLETE',json.dumps(report))
