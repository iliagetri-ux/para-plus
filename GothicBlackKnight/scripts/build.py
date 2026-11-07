import bpy, math, os, random, json, hashlib, time
import numpy as np
from mathutils import Vector
from math import sin,cos,pi
random.seed(19)
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FAST=os.environ.get('KNIGHT_FAST')=='1'; OUT=ROOT+('/proof' if FAST else '/artifacts'); os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
parts=[]
def mat(name,col,metal,rough,noise=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*col,1); m.use_nodes=True
 n=m.node_tree.nodes; p=n.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*col,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 # Packed color, roughness and tangent normal maps survive glTF export.
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
 if noise:
  # Tileable tangent normals, shared by Blender/glTF/USDZ rather than Blender-only noise.
  dim=256;rg=np.random.default_rng(sum((i+1)*ord(c) for i,c in enumerate(name)))
  yy,xx=np.mgrid[0:dim,0:dim]/dim
  if 'woven' in name:
   height=.16*(np.sin(2*pi*xx*64)+np.sin(2*pi*yy*64))+rg.standard_normal((dim,dim))*.025
  else:
   height=rg.standard_normal((dim,dim))*.10+.025*np.sin(2*pi*(xx*47+yy*19))
  nx=(np.roll(height,1,axis=1)-np.roll(height,-1,axis=1))*.65
  ny=(np.roll(height,1,axis=0)-np.roll(height,-1,axis=0))*.65
  nz=np.ones_like(nx);length=np.sqrt(nx*nx+ny*ny+nz*nz)
  pixels=np.stack((nx/length*.5+.5,ny/length*.5+.5,nz/length*.5+.5,np.ones_like(nx)),axis=-1).astype(np.float32)
  normal_image=bpy.data.images.new(name+' Tangent normal',width=dim,height=dim);normal_image.colorspace_settings.name='Non-Color';normal_image.pixels.foreach_set(pixels.ravel());normal_image.pack()
  tx=n.new('ShaderNodeTexImage');tx.image=normal_image
  normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.55 if metal>.5 else .28
  m.node_tree.links.new(tx.outputs['Color'],normal.inputs['Color']);m.node_tree.links.new(normal.outputs['Normal'],p.inputs['Normal'])
 return m
steel=mat('01 | Blackened forged steel',(.026,.030,.036),.9,.43,180)
edge=mat('02 | Worn pewter edges',(.13,.125,.114),.85,.38,230)
dark=mat('03 | Recessed steel',(.012,.016,.021),.65,.46,150)
cloth=mat('04 | Charcoal woven wool',(.009,.008,.010),0,.97,320)
leather=mat('05 | Oxblood leather',(.035,.013,.012),0,.68,180)
ruby=mat('06 | Garnet',(.19,.005,.008),0,.19)

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

def digit(name,control,length_scale=1):
 # A curved articulated finger is one swept quad surface, with knuckle ridges.
 centers=[]
 for k in range(len(control)-1):
  a=Vector(control[max(0,k-1)]);b=Vector(control[k]);c=Vector(control[k+1]);d=Vector(control[min(len(control)-1,k+2)])
  for j in range(4):
   t=j/4;centers.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 centers.append(Vector(control[-1]));v=[];f=[];n=12
 for k,center in enumerate(centers):
  t=k/(len(centers)-1);tangent=(centers[min(k+1,len(centers)-1)]-centers[max(0,k-1)]).normalized()
  side=Vector((1,0,0));side=(side-tangent*side.dot(tangent)).normalized();up=tangent.cross(side).normalized()
  radius=(.0105-.003*t)*length_scale*(1+.17*math.exp(-((t-.27)/.045)**2)+.15*math.exp(-((t-.63)/.045)**2))
  for j in range(n):
   angle=2*pi*j/n;v.append(center+side*(radius*cos(angle))+up*(radius*1.1*sin(angle)))
 for k in range(len(centers)-1):
  for j in range(n):a=k*n+j;b=k*n+(j+1)%n;f.append((a,b,b+n,a+n))
 f.extend([tuple(range(n-1,-1,-1)),tuple((len(centers)-1)*n+j for j in range(n))])
 ob=mesh(name,v,f,steel);ob.data.materials.append(dark);ob.data.materials.append(edge)
 for face in ob.data.polygons:
  if face.index<(len(centers)-1)*n:
   t=(face.index//n+.5)/(len(centers)-1)
   if abs(t-.32)<.035 or abs(t-.68)<.035:face.material_index=1
   elif abs(t-.27)<.035 or abs(t-.63)<.035:face.material_index=2
 return ob

def rim(ob,indices,name='Rolled plate edge',r=.0025):line(name,[ob.data.vertices[i].co[:] for i in indices],r)
def ornament(ob,rows,n=48,front=True):
 # Repeating pointed-arch chased tracery follows surface; no floating ornaments.
 nr=len(ob.data.vertices)//n
 for k in rows:
  if k<nr:rim(ob,[k*n+j for j in range(n)]+[k*n],r=.002)

# Human scale: 1.975 m helmet top, crown 2.05 m. Feet planted; eight-head body.
loft('Padded arming torso',[(0,0,1.01,.15,.105),(0,0,1.12,.17,.11),(0,0,1.30,.20,.12),(0,0,1.57,.245,.125),(0,0,1.65,.17,.10)],dark)
cu=loft('Cuirass | forged breast and back',[(0,0,1.165,.153,.105),(0,-.008,1.205,.164,.12),(0,-.005,1.255,.168,.127),(0,0,1.32,.193,.137),(0,0,1.39,.224,.149),(0,0,1.455,.243,.141),(0,0,1.505,.229,.12),(0,0,1.545,.173,.098)],steel,64,.008)
# medial keel and anatomical pectoral sweep are formed in the surface itself
for v in cu.data.vertices:
 front=max(0,-v.co.y/.15); waist=math.exp(-((v.co.z-1.28)/.13)**2)
 v.co.y-=.018*math.exp(-(v.co.x/.045)**2)*front*waist
 v.co.z+=.018*(abs(v.co.x)/.245)**1.2*math.exp(-((v.co.z-1.45)/.10)**2)
for v in cu.data.vertices:v.co.z+=.08*min(1,max(0,(v.co.z-1.18)/.36))
ornament(cu,[0,7],64)
# Two fitted plackart leaves: shaped sheet metal with a pointed upper seam and a medial keel.
from mathutils.bvhtree import BVHTree
chest_tree=BVHTree.FromPolygons([v.co.copy() for v in cu.data.vertices],[list(p.vertices) for p in cu.data.polygons])
for side in [-1,1]:
 vertices=[];faces=[];resolution=25
 for row in range(resolution):
  t=row/(resolution-1)
  for col in range(resolution):
   u=col/(resolution-1);x=side*(.003+.178*u)*(.85+.15*t)
   lower=1.205+.045*u;upper=1.39+.085*(1-u)**2+.03*sin(pi*u)
   z=lower*(1-t)+upper*t
   hit,normal,idx,distance=chest_tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
   assert hit is not None, 'Plackart outside breastplate'
   ridge=.008+.010*sin(pi*u)**2*sin(pi*t)+.004*max(0,cos(u*5*pi))**6*sin(pi*t)
   vertices.append((x,hit.y-ridge,z))
 for row in range(resolution-1):
  for col in range(resolution-1):
   a=row*resolution+col;face=(a,a+1,a+resolution+1,a+resolution)
   faces.append(face if side>0 else tuple(reversed(face)))
 plackart=mesh('Plackart | pointed fitted breast leaf',vertices,faces,steel,0,.004)
 for row in [0,resolution-1]:rim(plackart,[row*resolution+j for j in range(resolution)],r=.0023)
 for col in [0,resolution-1]:rim(plackart,[j*resolution+col for j in range(resolution)],r=.0018)

for k in range(4):
 z=1.10+k*.034
 ob=loft('Overlapping articulated fauld %02d'%k,[(0,0,z,.185-k*.009,.125),(0,0,z+.045,.17-k*.008,.12)],steel,48,.018);ornament(ob,[0])
neck=loft('Gorget | fitted neck articulation',[(0,0,1.61,.122,.093),(0,0,1.655,.096,.082),(0,0,1.70,.079,.072)],dark,48,.012);ornament(neck,[0,1,2])
loft('Mantle | fitted neck wrap',[(0,0,1.62,.13,.105),(0,0,1.645,.12,.10),(0,0,1.665,.108,.092),(0,0,1.69,.105,.09),(0,0,1.695,.095,.086),(0,0,1.702,.087,.082),(0,0,1.71,.083,.080)],cloth,48,.02)
helmet_start=len(parts)
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
# Correct helmet-to-body proportion while preserving crown height.
for ob in parts[helmet_start:]:
 points=[v.co for v in ob.data.vertices] if ob.type=='MESH' else [p.co for spline in ob.data.splines for p in spline.points]
 for co in points:co.z=2.05-.86*(2.05-co.z)

# Shaped pointed pauldrons using angular patches, each is a whole thick plate.
for s in [-1,1]:
 limb('Padded shoulder attachment',(s*.19,0,1.585),(s*.29,0,1.645),[(0,.086,.082),(.5,.096,.095),(1,.075,.073)],dark,0)
 for layer in range(3):
  v=[];f=[];nr=9;nc=33
  for k in range(nr):
   t=k/(nr-1)
   for j in range(nc):
    a=-pi*.60+pi*1.20*j/(nc-1);w=.12+.035*t
    phi=.035+t*1.57; radius=.15-layer*.012
    x=s*(.255+layer*.018+radius*sin(phi)*cos(a));y=.14*sin(phi)*sin(a);z=1.59-layer*.057+.132*cos(phi)-.028*(.5+.5*cos(3*a))*t**5+.025*max(0,cos(a))**12*(1-t)**4
    v.append((x,y,z))
  for k in range(nr-1):
   for j in range(nc-1):a=k*nc+j;f.append((a,a+1,a+nc+1,a+nc))
  if s>0:f=[tuple(reversed(face)) for face in f]
  ob=mesh(('Left' if s<0 else 'Right')+' pauldron lame '+str(layer),v,f,steel,1,.007)
  rim(ob,list(range((nr-1)*nc,nr*nc)),r=.0035);rim(ob,list(range(nc)),r=.003)
  for j in [4,10,16,22,28]:line('Pauldron chased arch',[v[k*nc+j] for k in range(nr)],.0018)
 # hanging left arm; right elbow bends outward toward sword
 sh=(s*.29,0,1.57);el=(s*.35,-.005,1.23);wr=(s*.36,-.055,1.02) if s<0 else (s*.61,-.10,1.34)
 limb('Sleeve',sh,el,[(0,.068,.07),(.5,.075,.072),(1,.06,.06)],dark)
 limb('Rerebrace',sh,el,[(.1,.082,.079),(.4,.077,.076),(.9,.062,.061)],steel)
 elbow=limb('Elbow couter',tuple(Vector(el)+Vector((0,0,-.035))),tuple(Vector(el)+Vector((0,0,.085))),[(0,.035,.048),(.28,.065,.074),(.52,.079,.085),(.76,.069,.073),(1,.05,.058)],steel,0)
 for vertex in elbow.data.vertices:
  a=2*pi*(vertex.index%32)/32;ridge=max(0,cos(a))**10
  vertex.co.y-=.018*ridge;vertex.co.x+=s*.028*max(0,s*sin(a))**8
 ornament(elbow,[0,4],32)
 limb('Vambrace',el,wr,[(.12,.064,.062),(.28,.068,.061),(.6,.053,.052),(.85,.043,.046),(1,.049,.051)],steel)
 limb('Wrist cuff',el,wr,[(.89,.052,.054),(1.05,.057,.054)],edge)
 handend=Vector(wr)+Vector((0,-.012,-.085)) if s<0 else Vector(wr)+Vector((.02,-.03,.055))
 limb('Gauntlet metacarpal plate',wr,handend,[(0,.048,.035),(.45,.051,.034),(1,.043,.028)],steel)
 for finger in range(4):
  start=handend+Vector(((finger-1.5)*.022,0,.004))
  if s<0:
   length=[.074,.084,.079,.061][finger]
   points=[start,start+Vector((0,-.004,-length*.28)),start+Vector((0,-.012,-length*.58)),start+Vector((.002,-.021,-length*.85)),start+Vector((.003,-.030,-length))]
  else:
   length=[.94,1.0,.96,.80][finger]
   points=[start,start+Vector((0,-.023,-.015))*length,start+Vector((0,-.033,-.040))*length,start+Vector((0,-.022,-.063))*length,start+Vector((0,-.003,-.070))*length]
  digit('Gauntlet | curled articulated finger',points,.86 if finger==3 else 1)
 if s<0:
  start=Vector(wr)+Vector((.039,-.01,-.037));points=[start,start+Vector((.012,-.015,-.020)),start+Vector((.006,-.025,-.042)),start+Vector((-.004,-.026,-.049))]
 else:
  start=Vector(wr)+Vector((-.034,.012,.015));points=[start,Vector((.585,-.112,1.342)),Vector((.60,-.145,1.337)),Vector((.62,-.15,1.348))]
 digit('Gauntlet | opposed thumb',points,1.25)
 # Legs, cuisses -> knee -> greaves, each fitted to anatomy.
 leg_start=len(parts)
 x=s*.115
 limb('Arming leg',(x,0,.98),(x,.012,.15),[(0,.087,.085),(.4,.07,.073),(.5,.064,.068),(.75,.055,.06),(1,.04,.045)],dark)
 ob=loft('Anatomical cuisse',[(x,0,.64,.074,.078),(x,0,.73,.08,.088),(x,0,.87,.089,.094),(x,0,.98,.087,.09)],steel,48,.045);ornament(ob,[0,3])
 for k in range(3):
  ob=loft('Hip tasset overlapping plate',[(x,-.015,.88+k*.061,.091,.092),(x,-.008,.95+k*.061,.092,.091)],steel,48,.015)
  for j in range(48):ob.data.vertices[j].co.z-=.035*max(0,cos(2*pi*j/48))**6
  ornament(ob,[0])
 ob=loft('Pointed poleyn',[(x,-.018,.52,.027,.049),(x,-.025,.57,.065,.077),(x,-.027,.615,.074,.087),(x,-.012,.66,.059,.069),(x,0,.685,.04,.053)],steel,48,0)
 for vertex in ob.data.vertices:
  a=2*pi*(vertex.index%48)/48;front=max(0,cos(a))
  vertex.co.y-=.022*front**12
  if vertex.index<48:vertex.co.z-=.028*front**8
  if vertex.index>=4*48:vertex.co.z+=.028*front**8
  vertex.co.x+=s*.025*max(0,s*sin(a))**10*sin(pi*(vertex.index//48)/4)
 ornament(ob,[0,4])
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
  x=sin(a)*width*1.35-.075*t*t-.035*t*t*(1-u)**4
  envelope=(.012+.033*t+.018*sin(pi*t))*(.75+.25*sin(u*9+1)**2)
  phase=u*13*pi+2.1*sin(2*t+3*u)+.45*sin(u*19+t*4)
  y=.085+.052*abs(sin(a))*(1-t)**3+.10*(1-math.exp(-t*20))+.14*t+.035*sin(pi*t)*cos(a)**2+envelope*sin(phase)+.024*t*sin(u*5*pi+t*3)
  z=(1.59+.11*cos(a)**4)*(1-t)+.035*t
  z+=t**12*(.10*max(0,sin(17*u+1))**8+.055*max(0,sin(41*u))**10+.025*max(0,sin(97*u+1))**4+.015*max(0,sin(177*u))**4)
  z+=.035*sin(pi*t)*sin(u*9+3*t)
  v.append((x,y,z))
for k in range(nv-1):
 for j in range(nu-1):
  u=(j+.5)/(nu-1);t=(k+.5)/(nv-1)
  tear=any(((u-cu)/ru)**2+((t-ct)/rt)**2 < 1+.18*sin(j*7+k*3) for cu,ct,ru,rt in [(.10,.94,.026,.034),(.79,.91,.017,.047),(.91,.975,.024,.045),(.28,.989,.012,.027)])
  if tear:continue
  a=k*nu+j;f.append((a,a+1,a+nu+1,a+nu))
cape_ob=mesh('Cape | tailored drape and sparse torn openings',v,f,cloth,1,.0014)
import bmesh
bm=bmesh.new();bm.from_mesh(cape_ob.data)
for vertex in list(bm.verts):
 if not vertex.link_faces:bm.verts.remove(vertex)
bm.to_mesh(cape_ob.data);bm.free()
# Asymmetric folded mantle across upper chest
for layer in range(3):
 v=[];f=[]
 for i in range(49):
  t=i/48
  for j in range(7):
   w=j/6; x=-.19+.47*t; y=-.10-.021*sin(pi*w)-.022*sin(pi*t)-.005*layer;z=1.63+.10*t-.04*sin(pi*t)-layer*.026*(.4+sin(pi*t))+w*.035+.006*sin(t*13+layer)*sin(pi*t)
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
 mesh(name,v,[tuple(reversed(face)) for face in f],dark if name.startswith('Crown') else edge,0,.003)
 line('Rosette rim',[(c[0]+r*sin(2*pi*j/64),c[1],c[2]+r*cos(2*pi*j/64)) for j in range(65)],.0025)
medallion('Mantle clasp',(-.17,-.135,1.64),.033);medallion('Belt buckle',(0,-.145,1.14),.036)
medallion('Crown | central heraldic seal',(0,-.113,1.9253),.025)
# A short suspension chain follows a catenary between two actual belt attachment points.
for link in range(25):
 t=link/24;x=-.10+.26*t;z=1.14-.13*sin(pi*t)
 ya=-.137*math.sqrt(1-(.10/.185)**2)-.004;yb=-.137*math.sqrt(1-(.16/.185)**2)-.004
 y=ya*(1-t)+yb*t-.07*sin(pi*t)
 tangent=Vector((.26,yb-ya-.07*pi*cos(pi*t),-.13*pi*cos(pi*t))).normalized()
 side=Vector((0,-1,0));side=(side-tangent*side.dot(tangent)).normalized()
 if link%2:side=tangent.cross(side)
 center=Vector((x,y,z))
 line('Belt suspension chain',[(center+tangent*(.010*cos(2*pi*j/20))+side*(.004*sin(2*pi*j/20))) for j in range(21)],.001,edge)

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
# Faceted garnet, set within the guard rosette.
gv=[(sx,sy-.027,1.049),(sx+.010,sy-.027,1.031),(sx,sy-.027,1.013),(sx-.010,sy-.027,1.031),(sx,sy-.038,1.041),(sx+.004,sy-.038,1.031),(sx,sy-.038,1.021),(sx-.004,sy-.038,1.031),(sx,sy-.021,1.031)]
gf=[(4,5,6,7)]+[(j,(j+1)%4,(j+1)%4+4,j+4) for j in range(4)]+[(8,(j+1)%4,j) for j in range(4)]
gem=mesh('Greatsword | faceted garnet',gv,gf,ruby)
for face in gem.data.polygons:face.use_smooth=False
bm=bmesh.new();bm.from_mesh(gem.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(gem.data);bm.free()
loft('Greatsword | pommel',[(sx,sy,1.27,.017,.017),(sx,sy,1.30,.029,.026),(sx,sy,1.33,.022,.021),(sx,sy,1.345,.005,.005)],steel,24,.06)
# Authored branching foliage motifs, projected to each fitted plate.
from mathutils.bvhtree import BVHTree
for ob in list(parts):
 if ob.type!='MESH' or not any(word in ob.name for word in ['Cuirass','Plackart','cuisse','Greave','pauldron','faceplate','Vambrace','Rerebrace']):continue
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
  phase=col*pi+.55*sin(col*2.7+height*5)
  chase([(cx+.008*sin(t*2*pi+phase),zz+t*h) for t in [i/48 for i in range(49)]],.001)
  for leaf in range(max(2,int(h/.037))):
   t0=(leaf+.5)/max(2,int(h/.037));cz=zz+t0*h
   for sign in [-1,1]:
    bx=cx+.008*sin(t0*2*pi+phase)
    # swept lanceolate leaves, alternated along the central stem
    chase([(bx+sign*(.017+.007*sin(leaf*1.7+col)**2)*sin(pi*t),cz+.035*t) for t in [i/20 for i in range(21)]])
    chase([(bx+sign*(.008+.004*sin(leaf*1.7+col)**2)*sin(pi*t),cz+.035*t) for t in [i/20 for i in range(21)]],.0005)
# Individually seated, hand-peened rivets; one consolidated mesh.
rv=[];rf=[]
for plate in list(parts):
 if plate.type!='MESH' or 'pauldron lame' not in plate.name:continue
 for index in [8*33+4,8*33+28]:
  vert=plate.data.vertices[index];normal=vert.normal.normalized();center=vert.co+normal*.0005
  axis=Vector((0,0,1));side=normal.cross(axis)
  if side.length<.01:side=normal.cross(Vector((1,0,0)))
  side.normalize();up=normal.cross(side);base=len(rv);rv.append(center+normal*.0014)
  for ring in [pi/4,pi/2]:
   for j in range(8):
    a=2*pi*j/8;rv.append(center+side*(.003*sin(ring)*cos(a))+up*(.003*sin(ring)*sin(a))+normal*(.0014*cos(ring)))
  for j in range(8):
   rf.append((base,base+1+j,base+1+(j+1)%8));rf.append((base+1+j,base+9+j,base+9+(j+1)%8,base+1+(j+1)%8))
  rf.append(tuple(base+9+j for j in range(7,-1,-1)))
mesh('Pauldron | seated steel rivets',rv,rf,edge)

# Consolidate decorative curve objects into one mesh for manageable asset hierarchy.
curves=[o for o in parts if o.type=='CURVE'];bpy.ops.object.select_all(action='DESELECT')
for o in curves:o.select_set(True)
bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();bpy.context.object.name='Chased tracery, rolled edges and bindings'
# UVs on all surfaces and portable image-based PBR microdetail.
assets=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in ([] if FAST else assets):
 if o.get('preserve_uv'):continue
 bpy.context.view_layer.objects.active=o;bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
# Studio staging excluded from exports; mobile export uses less tessellation.
bpy.ops.object.select_all(action='DESELECT')
for o in assets:o.select_set(True)
if not FAST:
 import sys
 sys.path.insert(0,ROOT+'/scripts')
 from export_meshes import export_assets
 export_assets(assets,OUT,ROOT)

scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=16 if FAST else 48;scene.cycles.use_denoising=os.environ.get('KNIGHT_DENOISE')=='1'
scene.render.resolution_x=1024;scene.render.resolution_y=1280;scene.render.resolution_percentage=52 if FAST else 100
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
views={'Front':(0,-5,1.45),'Back':(0,5,1.45),'Side':(-5,0,1.45),'Right':(5,0,1.45),'45':(-3.92,-4,1.45)}
if FAST:views={name:views[name] for name in os.environ.get('KNIGHT_FAST_VIEWS','Front,45,Back').split(',')}
report={'asset_meshes':len(assets),'vertices_base':sum(len(o.data.vertices) for o in assets),'polygons_base':sum(len(o.data.polygons) for o in assets),'reference':'docs/Reference.jpg; artistic review recorded separately in docs/ART_REVIEW.md','limitations':['Static posed mesh; no rig or LODs','PBR albedo, roughness and tangent normal maps are embedded; game-specific atlas baking is still pending','No production retopology or collision clearance certification']}
with open(OUT+'/validation.json','w') as f:json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/GothicBlackKnight.blend',compress=True)
render_report={'glb_sha256':hashlib.sha256(open(OUT+'/GothicBlackKnight.glb','rb').read()).hexdigest() if not FAST else None,'denoising':scene.cycles.use_denoising,'views':{}}
for name,loc in views.items():
 cam.location=loc;cam.rotation_euler=(Vector((.08,0,1.08))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=OUT+'/Preview_'+name+'.png'
 bpy.ops.wm.save_as_mainfile(filepath=OUT+'/GothicBlackKnight.blend',compress=True) if name=='45' else None
 start=time.time();bpy.ops.render.render(write_still=True)
 render_report['views'][name]={'rendered':True,'seconds':round(time.time()-start,2),'sha256':hashlib.sha256(open(scene.render.filepath,'rb').read()).hexdigest()}
 with open(OUT+'/render_check.json','w') as f:json.dump(render_report,f,indent=2)
print('BUILD_COMPLETE',json.dumps(report))
