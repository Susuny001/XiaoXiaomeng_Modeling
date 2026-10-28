"""Designed volume hair patches, traced main silhouettes and variable thickness."""
import bpy,bmesh,math
from math import sin,cos,pi,sqrt
from mathutils import Vector
HAIRCOL=bpy.data.collections.new('HAIR / designed layered locks');bpy.context.scene.collection.children.link(HAIRCOL)
def linear(h):
 c=[int(h[i:i+2],16)/255 for i in [0,2,4]]
 return [x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in c]
def material(name,c):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*linear(c),1)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=.85;p.inputs['Specular IOR Level'].default_value=.08
 return m
CHAR=material('Hair / deep graphite','424641');MID=material('Hair / graphite planes','4B4F4A');LIGHT=material('Hair / upper soft planes','555953')
GREEN=material('Hair / lime painted section','B2D934');GREEN2=material('Ribbon / bright side','ABD02D');GREENBACK=material('Ribbon / shaded side','6F901C')
GOLD=material('Clips / yellow brass','B7A239')
def mesh(name,vs,fs,ma):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update()
 bm=bmesh.new();bm.from_mesh(d);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.00002);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(d);bm.free()
 o=bpy.data.objects.new(name,d);HAIRCOL.objects.link(o);d.materials.append(ma)
 for p in d.polygons:p.use_smooth=True
 return o
def sample(points,t):
 p=t*(len(points)-1);i=min(len(points)-2,int(p));u=p-i
 a=Vector(points[max(0,i-1)]);b=Vector(points[i]);c=Vector(points[i+1]);d=Vector(points[min(len(points)-1,i+2)])
 return .5*(2*b+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
def hair_y(x,z):
 t=max(0,min(1,(1.784-z)/.134))
 return .010-.113*sqrt(max(.08,1-(x/.155)**2))*sin(pi*.5*t)
S=1.78/537
def xyz(p,bias=0):
 x=(p[0]-185)*S;z=(613-p[1])*S
 return Vector((x,hair_y(x,z)+bias,z))
def patch(name,left,right,ma=CHAR,depth=.010,bias=0):
 # Two artist-controlled silhouette splines and a sculpted lenticular section.
 l=[xyz(p,bias) for p in left];r=[xyz(p,bias) for p in right]
 vs=[];fs=[];rows=48;cols=12
 for back in [False,True]:
  for j in range(rows+1):
   t=j/rows;a=sample(l,t);b=sample(r,t)
   thickness=depth*(.35+.65*sin(pi*t)**.5)*(1-.85*t**9)
   for i in range(cols+1):
    u=i/cols;p=a.lerp(b,u)
    p.y+=((.40 if back else -1)*thickness*sin(pi*u)**.70)
    # A single soft crest on the broad locks, no repeated thin ridges.
    if not back:p.y-=.0013*sin(pi*u)*sin(pi*t)
    vs.append(p)
 layer=(rows+1)*(cols+1)
 for back in [False,True]:
  off=layer if back else 0
  for j in range(rows):
   for i in range(cols):
    a=off+j*(cols+1)+i
    face=(a,a+1,a+cols+2,a+cols+1)
    fs.append(tuple(reversed(face)) if back else face)
 for j in range(rows):
  a=j*(cols+1);b=(j+1)*(cols+1);fs.append((a,b,b+layer,a+layer))
  a+=cols;b+=cols;fs.append((a,a+layer,b+layer,b))
 for i in range(cols):
  a=i;fs.append((a,a+layer,a+layer+1,a+1))
  a=rows*(cols+1)+i;fs.append((a,a+1,a+layer+1,a+layer))
 return mesh(name,vs,fs,ma)

# An integrated crown mass. Main silhouette is not a bundle of radial tubes.
vs=[];fs=[];nr=36;nt=96
for j in range(nr+1):
 for i in range(nt):
  a=2*pi*i/nt;end=1.08+.74*(1+sin(a))/2
  p=.001+(end-.001)*j/nr
  x=.137*sin(p)*cos(a);y=.014+.116*sin(p)*sin(a);z=1.630+.146*cos(p)
  # Offset the part and soften asymmetry in the crown.
  x+=.003*sin(p)*sin(a*2);z+=.0015*sin(a*3)*sin(p)
  vs.append((x,y,z))
for j in range(nr):
 for i in range(nt):
  a=j*nt+i;b=j*nt+(i+1)%nt;fs.append((a,b,b+nt,a+nt))
mesh('Crown / continuous scalp volume',vs,fs,MID)

patch('Fringe / central sweeping point',[(181,81),(175,92),(174,108),(179,121),(184,130)],[(188,82),(189,95),(188,111),(186,122),(184,130)],MID,.011,-.001)
patch('Fringe / short inset point',[(188,87),(188,102),(186,116),(189,128)],[(198,89),(196,105),(194,120),(189,128)],CHAR,.007,-.003)
patch('Fringe / left broad curved plane',[(175,85),(164,97),(159,111),(158,125),(164,135)],[(183,85),(175,101),(172,116),(167,129),(164,135)],LIGHT,.012,-.001)
patch('Fringe / outer sweep 01',[(168,89),(157,101),(149,112),(136,119)],[(177,87),(168,105),(153,118),(136,119)],MID,.009,.004)
patch('Fringe / outer sweep 02',[(157,107),(147,120),(140,127),(133,130)],[(167,104),(161,120),(147,132),(133,130)],CHAR,.009,-.001)
patch('Temple / left cheek framing',[(151,120),(145,134),(150,147),(163,157)],[(159,116),(158,133),(160,146),(163,157)],CHAR,.009,.003)
patch('Fringe / right clipped plane',[(196,84),(200,102),(198,118),(196,131),(203,139)],[(206,90),(215,109),(211,126),(207,135),(203,139)],MID,.013,.001)
patch('Temple / long right silhouette',[(207,93),(215,112),(214,135),(210,154),(206,170)],[(216,101),(226,122),(226,146),(220,164),(206,170)],CHAR,.013,.004)
patch('Temple / lower left sweep',[(147,129),(143,141),(148,152),(162,159)],[(155,125),(155,139),(159,150),(162,159)],MID,.008,.008)
# Colored regions follow specific locks rather than floating green tubes.
patch('Lime / left curved underlight',[(167,96),(160,110),(155,124),(157,136)],[(169,95),(164,111),(161,127),(157,136)],GREEN,.0015,-.011)
patch('Lime / long right face framing',[(216,122),(215,137),(212,155),(206,168)],[(218,119),(220,139),(217,156),(206,168)],GREEN,.0018,-.010)

def free_lock(name,centres,widths,depths,ma=CHAR):
 # A flattened solid mesh patch with a controlled center spine and tapered tip.
 vs=[];fs=[];rows=48;cols=10;pts=[Vector(p) for p in centres]
 for back in [False,True]:
  for j in range(rows+1):
   t=j/rows;p=sample(pts,t)
   k=min(len(widths)-2,int(t*(len(widths)-1)));u=t*(len(widths)-1)-k
   w=widths[k]*(1-u)+widths[k+1]*u;d=depths[k]*(1-u)+depths[k+1]*u
   for i in range(cols+1):
    a=i/cols;x=p.x+(a-.5)*w*2;y=p.y+(1 if back else -1)*d*sin(pi*a)**.8
    vs.append((x,y,p.z))
 layer=(rows+1)*(cols+1)
 for back in [False,True]:
  off=layer if back else 0
  for j in range(rows):
   for i in range(cols):
    a=off+j*(cols+1)+i;f=(a,a+1,a+cols+2,a+cols+1);fs.append(tuple(reversed(f)) if back else f)
 for j in range(rows):
  a=j*(cols+1);b=(j+1)*(cols+1);fs.append((a,b,b+layer,a+layer));a+=cols;b+=cols;fs.append((a,a+layer,b+layer,b))
 return mesh(name,vs,fs,ma)
# Side bob planes cover the ears and tuck under the main fringe.
for s in [-1,1]:
 for i in range(4):
  f=i/3
  free_lock('Side bob / %s.%s'%(s,i),[(s*.072,.027+f*.055,1.744),(s*(.120+.012*f),.013+.067*f,1.660),(s*(.130+.018*f),.005+.075*f,1.568),(s*(.111+.028*f),-.003+.085*f,1.536+.015*f)],[.013,.025,.025,.0004],[.006,.010,.010,.0005],[CHAR,MID,CHAR,LIGHT][i])
 # Three broad rear locks per side, with distinct bends and uneven tips.
 for i in range(3):
  f=i/2
  free_lock('Long rear / %s.%s'%(s,i),[(s*(.070+.012*f),.093,1.681),(s*(.105+.022*f),.129,1.547),(s*(.137+.022*f),.161,1.387),(s*(.143+.020*f),.138,1.228),(s*(.127+.032*f),.104,1.153+.057*f)],[.013,.030,.032,.026,.0005],[.008,.014,.015,.012,.0005],[CHAR,MID,CHAR][i])
for i in range(5):
 x=-.083+i*.0415
 free_lock('Occipital / broad nape plane '+str(i),[(x*.35,.069,1.745),(x*.9,.112,1.671),(x*1.10,.114,1.595),(x*1.20,.096,1.562+.012*sin(i*1.7))],[.018,.029,.028,.0005],[.006,.008,.009,.0004],[MID,CHAR,LIGHT,CHAR,MID][i])

def strip3d(name,points,width,ma,closed=False):
 pts=[Vector(p) for p in points];vs=[];fs=[];n=64
 for i in range(n+1):
  t=i/n;p=sample(pts,t)
  q=sample(pts,max(0,min(1,t+.001)))-sample(pts,max(0,min(1,t-.001)))
  # Ribbon width lies in the screen XZ plane, not a wire cross section.
  u=Vector((-q.z,0,q.x)).normalized()
  vs.extend([p-u*width*.5,p+u*width*.5])
 for i in range(n):fs.append((i*2,i*2+1,i*2+3,i*2+2))
 ob=mesh(name,vs,fs,ma);so=ob.modifiers.new('Woven cloth thickness','SOLIDIFY');so.thickness=.001
 return ob
K=Vector((.130,.066,1.639))
strip3d('Ribbon / loop',[K,(.157,.068,1.610),(.184,.070,1.582),(.163,.082,1.584),K],.012,GREEN2,True)
strip3d('Ribbon / tail one',[K,(.160,.078,1.574),(.192,.080,1.551),(.213,.072,1.553)],.014,GREEN2)
strip3d('Ribbon / tail two',[K,(.148,.094,1.578),(.169,.099,1.537)],.013,GREENBACK)
strip3d('Ribbon / knot wrap',[(.124,.057,1.647),(.137,.057,1.644),(.136,.056,1.632),(.124,.056,1.634)],.009,GREEN2)
# Clips conform to the front hair plane and have angular, flat metal sections.
for row in range(2):
 z=1.678-row*.020;x=.062
 for tilt in [-1,1]:
  p=[(x-.008,hair_y(x-.008,z)-.014,z+tilt*.006),(x+.008,hair_y(x+.008,z)-.014,z-tilt*.006)]
  strip3d('Hair clip %d %d'%(row,tilt),p,.0028,GOLD)
print('DESIGNED_HAIR_SURFACES_CREATED')
