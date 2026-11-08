"""Surface-seated acanthus relief: broad lobed leaves and curved stems, composed per plate."""
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from math import sin,cos,pi

def decorate(parts,mesh,line,steel,edge):
 for ob in list(parts):
  if ob.type!='MESH' or not any(w in ob.name for w in ['Cuirass','Plackart','cuisse','Greave','pauldron','faceplate','Vambrace','Rerebrace','brow and ocular','continuous ogival']):continue
  source=[v.co.copy() for v in ob.data.vertices]
  tree=BVHTree.FromPolygons(source,[list(p.vertices) for p in ob.data.polygons])
  xmin=min(v.x for v in source);xmax=max(v.x for v in source);zmin=min(v.z for v in source);zmax=max(v.z for v in source)
  width=xmax-xmin;height=zmax-zmin
  if 'Cuirass' in ob.name:zmin=1.475;height=zmax-zmin
  if height<.025:continue
  vertices=[];faces=[]
  def project(x,z,lift):
   hit,normal,idx,distance=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
   return hit+normal*lift if hit is not None else None
  def stem(path,r=.00065):
   pts=[]
   for x,z in path:
    hit=project(x,z,.00065)
    if hit is not None:pts.append(hit)
    elif pts:
     if len(pts)>2:line('Acanthus | seated stem',pts,r,edge)
     pts=[]
   if len(pts)>2:line('Acanthus | seated stem',pts,r,edge)
  def leaf(control,span,lift=.002):
   a,b,c,d=[Vector(p) for p in control];ids={};centers=[];n=16;m=6
   for row in range(n+1):
    t=row/n;center=a*(1-t)**3+3*b*t*(1-t)**2+3*c*t*t*(1-t)+d*t**3
    tangent=3*(b-a)*(1-t)**2+6*(c-b)*t*(1-t)+3*(d-c)*t*t
    if tangent.length<1e-8:continue
    tangent.normalize();side=Vector((-tangent.y,tangent.x))
    # Lobed margins and a tapering center rib are modeled in the surface.
    radius=span*(.025+sin(pi*t)**.85)*(.72+.28*abs(sin(pi*t*4.5)))
    for col in range(m+1):
     u=-1+2*col/m;p=center+side*(radius*u)
     elevation=.00025+lift*sin(pi*t)**.6*(1-abs(u))**.7
     elevation+=.00035*sin(t*8*pi+abs(u)*4*pi)*sin(pi*t)*(1-u*u)
     hit=project(p.x,p.y,elevation)
     if hit is not None:ids[(row,col)]=len(vertices);vertices.append(hit)
    centers.append((center.x,center.y))
   for row in range(n):
    for col in range(m):
     corners=[(row,col),(row,col+1),(row+1,col+1),(row+1,col)]
     if all(k in ids for k in corners):faces.append(tuple(ids[k] for k in corners))
   # Fine vein follows the high point of the relief rather than a separate floating contour.
   points=[]
   for row,(x,z) in enumerate(centers):
    t=row/n;hit=project(x,z,.0007+lift*sin(pi*t)**.6)
    if hit is not None:points.append(hit)
   if len(points)>2:line('Acanthus | worn center vein',points,.00035,edge)
  columns=2 if 'Cuirass' in ob.name else 1
  if 'pauldron' in ob.name:columns=2
  for column in range(columns):
   cx=xmin+width*(column+.5)/columns;w=width/columns*.83;h=height*.85;z0=zmin+height*.07
   bends=.13*w;phase=column*pi
   spine=lambda t:(cx+bends*sin(t*1.5*pi+phase),z0+h*t)
   stem([spine(i/48) for i in range(49)],.0009)
   levels=5 if h>.20 else 3
   for level in range(levels):
    t=.09+level*.78/levels;root=Vector(spine(t));span=w*(.095+.025*sin(level*1.6+column)**2)
    for side in [-1,1]:
     reach=w*(.40-.07*(level%2));rise=min(h*.33,.07+.01*(level%2))
     end=root+Vector((side*reach,rise))
     control=[root,root+Vector((side*reach*.72,-rise*.12)),end+Vector((side*reach*.36,-rise*.48)),end]
     leaf(control,span,.0018 if 'faceplate' in ob.name else .0027)
   top=Vector(spine(.76));leaf([top,top+Vector((-.13*w,.09*h)),top+Vector((.12*w,.20*h)),Vector((cx,z0+h))],w*.12)
  if faces:
   detail=mesh('Repousse acanthus | '+ob.name,vertices,faces,steel)
   # Projected tangent patches can be mirrored: orient them toward the viewing side.
   import bmesh
   bm=bmesh.new();bm.from_mesh(detail.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
   for face in bm.faces:
    if face.normal.y>0:face.normal_flip()
   bm.to_mesh(detail.data);bm.free()
