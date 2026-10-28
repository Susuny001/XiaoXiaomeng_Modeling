"""Image-guided anime head with a sculpted control surface and open eye loops.
No primitive head/face assembly. All visible skin is a connected surface.
"""
import bpy,bmesh,math,json,sys,runpy
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,sqrt,exp
ROOT=Path(__file__).resolve().parents[1]
(ROOT/'models').mkdir(exist_ok=True);(ROOT/'renders').mkdir(exist_ok=True)
reference_path=ROOT/'assets'/'character-sheet.png'
if not reference_path.exists():
 import shutil
 canonical=ROOT.parents[1]/'assets'/'xiaoxiaomeng-character-model-sheet.png'
 if not canonical.exists():raise FileNotFoundError('Place the character sheet at assets/character-sheet.png before building.')
 reference_path.parent.mkdir(exist_ok=True);shutil.copy2(canonical,reference_path)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
 if c.name!='Collection':bpy.data.collections.remove(c)
COL=bpy.data.collections.get('Collection');COL.name='HEAD_CONTROL_SURFACES'
CHIN=1.487
def srgb(hexcode):
 c=[int(hexcode[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in c)
def material(name,color,rough=.75):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*srgb(color),1)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=rough
 return m
SKIN=material('Skin / warm porcelain','F7E5D4')
LID=material('Eyelid waterline','B78774')
INK=material('Eyelash / soft charcoal','282923')
WHITE=material('Eye white / warm ivory','FFFAE9')
EAR=material('Ear fold shadow','D7AA93')
LIP=material('Mouth closure','8E6657')
def mesh(name,vs,fs,mat,sub=0):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update()
 ob=bpy.data.objects.new(name,d);COL.objects.link(ob);d.materials.append(mat)
 for p in d.polygons:p.use_smooth=True
 if sub:
  s=ob.modifiers.new('Sculpt surface subdivision','SUBSURF');s.levels=sub;s.render_levels=sub
 return ob
def mix(a,b,t):return a*(1-t)+b*t
PROFILE=[(0,.006,.038,.025),(.010,.024,.048,.037),(.025,.048,.059,.049),(.047,.073,.072,.062),(.072,.090,.080,.075),(.099,.102,.083,.089),(.130,.111,.087,.098),(.168,.115,.095,.103),(.208,.107,.092,.096),(.242,.084,.076,.077),(.265,.046,.045,.046),(.277,.003,.005,.005)]
def profile(z):
 z=max(0,min(.277,z))
 for i in range(len(PROFILE)-1):
  a=PROFILE[i];b=PROFILE[i+1]
  if a[0]<=z<=b[0]:
   h=b[0]-a[0];t=(z-a[0])/h
   def slope(k,j):
    if k==0:return (PROFILE[1][j]-PROFILE[0][j])/(PROFILE[1][0]-PROFILE[0][0])
    if k==len(PROFILE)-1:return (PROFILE[-1][j]-PROFILE[-2][j])/(PROFILE[-1][0]-PROFILE[-2][0])
    h0=PROFILE[k][0]-PROFILE[k-1][0];h1=PROFILE[k+1][0]-PROFILE[k][0]
    d0=(PROFILE[k][j]-PROFILE[k-1][j])/h0;d1=(PROFILE[k+1][j]-PROFILE[k][j])/h1
    if d0*d1<=0:return 0.
    return (3*(h0+h1))/((2*h1+h0)/d0+(h1+2*h0)/d1)
   return tuple(max(.001,(2*t**3-3*t*t+1)*a[j]+(t**3-2*t*t+t)*h*slope(i,j)+(-2*t**3+3*t*t)*b[j]+(t**3-t*t)*h*slope(i+1,j)) for j in range(1,4))
 return PROFILE[-1][1:]
def gaussian(x,z,cx,cz,wx,wz):return exp(-((x-cx)/wx)**2-((z-cz)/wz)**2)
def relief(x,z):
 # Connected craniofacial sculpt: eye socket, brow, cheek, nose and lips.
 ax=abs(x);d=0
 d+=.0050*gaussian(ax,z,.045,.100,.031,.020)   # shallow anime orbital hollow
 d-=.0030*gaussian(ax,z,.045,.123,.033,.013)   # supraorbital ridge
 d-=.0035*gaussian(ax,z,.064,.075,.035,.023)   # malar plane
 d+=.0025*gaussian(ax,z,.084,.126,.025,.035)   # temple hollow
 d-=.0020*gaussian(x,z,0,.100,.010,.030)       # narrow bridge
 d-=.0055*gaussian(x,z,0,.065,.009,.010)       # small drawn-profile nasal tip
 d-=.0007*gaussian(ax,z,.008,.060,.004,.006)   # alar transition
 d+=.0012*gaussian(x,z,0,.048,.005,.009)       # philtrum
 d-=.0005*gaussian(x,z,0,.039,.012,.004)       # restrained lip roll
 d+=.0005*gaussian(x,z,0,.0355,.012,.0015)     # mouth closure recess
 d-=.0006*gaussian(x,z,0,.031,.011,.0045)      # lower lip
 d-=.0025*gaussian(x,z,0,.015,.025,.012)       # chin pad
 return d
def front_y(x,z):
 rx,rf,rb=profile(z);c=sqrt(max(.001,1-(x/max(rx,.001))**2))
 return .013-rf*(c**.70)+relief(x,z)*(c**2)

# Structured head control mesh. Eye openings are real holes, with four
# sculpted annuli linking the facial surface to the inner eyelid rim.
N=160;R=128;VS=[];FS=[]
EYES=[{'s':1,'l':86,'r':100},{'s':-1,'l':60,'r':74}]
RL=43;RH=51
def eyelid(c,eye):
 u=(c-eye['l'])/(eye['r']-eye['l'])
 if eye['s']==1:x=.021+.053*u;v=u
 else:x=-.074+.053*u;v=1-u
 centre=.101+.0017*v
 upper=centre+.0090*sin(pi*u)**.65+.0009
 lower=centre-.0140*sin(pi*u)**.8-.0009
 return x,lower,upper
def surface(r,c):
 z=.277*r/R;t=-pi+2*pi*c/N;rx,rf,rb=profile(z);x=rx*sin(t)
 for eye in EYES:
  if eye['l']-5<=c<=eye['r']+5 and RL-9<=r<=RH+9:
   cc=max(eye['l'],min(eye['r'],c));ex,lo,hi=eyelid(cc,eye)
   wu=1-max(0,eye['l']-c,c-eye['r'])/5
   if RL<=r<=RH:zz=mix(lo,hi,(r-RL)/(RH-RL));wz=1
   elif r<RL:
    wz=(r-(RL-9))/9;zz=mix(z,lo,wz)
   else:
    wz=1-(r-RH)/9;zz=mix(z,hi,wz)
   x=mix(x,ex,wu*wz);z=mix(z,zz,wu)
   rx,rf,rb=profile(z)
 if cos(t)>=0:y=front_y(x,z)
 else:y=.013+rb*(-cos(t))**.9
 return x,y,z+CHIN
for r in range(R+1):
 for c in range(N):VS.append(surface(r,c))
def idx(r,c):return r*N+(c%N)
for r in range(R):
 for c in range(N):
  if any(RL<=r<RH and e['l']<=c<e['r'] for e in EYES):continue
  FS.append((idx(r,c),idx(r,c+1),idx(r+1,c+1),idx(r+1,c)))
FS.append(tuple(reversed([idx(0,c) for c in range(N)])))
FS.append(tuple(idx(R,c) for c in range(N)))
LID_INNER=[]
for eye in EYES:
 l,r=eye['l'],eye['r']
 outer=[idx(RH,c) for c in range(l,r+1)]+[idx(row,r) for row in range(RH-1,RL-1,-1)]+[idx(RL,c) for c in range(r-1,l-1,-1)]+[idx(row,l) for row in range(RL+1,RH)]
 previous=outer;cx=eye['s']*.0475;cz=.1017
 for k in range(1,5):
  ring=[];a=k/4
  for vi in outer:
   x,y,zw=VS[vi];z=zw-CHIN
   xx=cx+(x-cx)*(1-.075*a);zz=cz+(z-cz)*(1-.10*a)
   # Upper eyelid has a soft edge roll; lower lid stays fine.
   roll=(.0017 if z>cz else .0007)*sin(pi*a)
   yy=front_y(xx,zz)-roll-.0005*a
   ring.append(len(VS));VS.append((xx,yy,zz+CHIN))
  for j in range(len(ring)):FS.append((previous[j],previous[(j+1)%len(ring)],ring[(j+1)%len(ring)],ring[j]))
  previous=ring
 LID_INNER.append((eye,previous))
head=mesh('HEAD / sculpted connected face and orbital loops',VS,FS,SKIN,sub=1)
bm=bmesh.new();bm.from_mesh(head.data)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.000015)
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(head.data);bm.free()
head['workflow']='Shaped cranial/jaw control surface with orbital holes and connected eyelid loops; nasal and lip relief are part of the face surface.'

# Iris painting is on the eyeball surface, avoiding protruding button-like eyes.
import numpy as np
T=512;yy,xx=np.mgrid[:T,:T];u=(xx/(T-1)-.5)*2;v=(yy/(T-1)-.5)*2
rad=np.sqrt((u/.40)**2+(v/.84)**2);ang=np.arctan2(v,u)
pixels=np.empty((T,T,4),np.float32);pixels[:,:,:3]=srgb('FFFAEB');pixels[:,:,3]=1
inside=rad<=1
base=np.zeros((T,T,3),np.float32)
shade=np.clip((v+.9)/1.8,0,1)
top=np.array(srgb('504B11'));bottom=np.array(srgb('F5D52F'))
for j in range(3):base[:,:,j]=bottom[j]*(1-shade)+top[j]*shade
edge=np.clip((rad-.87)/.13,0,1)
for j,c in enumerate(srgb('4F4E19')):base[:,:,j]=base[:,:,j]*(1-edge)+c*edge
fiber=(np.sin(ang*45+rad*7)*.5+.5)*.025
base+=fiber[:,:,None]
pixels[inside,:3]=base[inside]
pupil=((u/.125)**2+((v-.07)/.52)**2)<=1
pixels[pupil,:3]=srgb('353412')
for cx,cy,rx,ry in [(-.13,.43,.085,.13),(.14,-.39,.033,.05)]:
 mask=((u-cx)/rx)**2+((v-cy)/ry)**2<1;pixels[mask,:3]=srgb('FFFFF5')
image=bpy.data.images.new('Eye paint / gold-chartreuse',width=T,height=T,alpha=True)
image.colorspace_settings.name='Linear Rec.709';image.pixels.foreach_set(pixels.reshape(-1))
image.filepath_raw=str(ROOT/'models'/'eye-paint.png');image.file_format='PNG';image.save();image.pack()
eye_mat=material('Eyes / painted iris','FFFFFF',.6)
node=eye_mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
eye_mat.node_tree.links.new(node.outputs['Color'],eye_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
def ribbon(name,points,widths,mat):
 # A tapered polygon strip, rather than a round tube.
 vs=[];fs=[]
 for (x,y,z),w in zip(points,widths):vs.extend([(x,y,z-w*.5),(x,y-.0001,z+w*.5)])
 for i in range(len(points)-1):fs.append((i*2,i*2+1,i*2+3,i*2+2))
 return mesh(name,vs,fs,mat)
for eye in EYES:
 s=eye['s'];cx=s*.0475;cz=.1017
 vs=[(cx,front_y(cx,cz)-.0010,cz+CHIN)];fs=[];uvs=[(.5,.5)]
 steps=64;layers=12
 for j in range(1,layers+1):
  a=j/layers
  for i in range(steps):
   t=2*pi*i/steps;ux=(cos(t)+1)/2
   x0,lo,hi=eyelid(mix(eye['l'],eye['r'],ux),eye)
   x=cx+(x0-cx)*a*.925
   zz=cz+((hi if sin(t)>=0 else lo)-cz)*abs(sin(t))*a*.90
   y=front_y(x,zz)-.0012*(1-a*a)+.00015
   vs.append((x,y,zz+CHIN));uvs.append(((x-cx)/.053+.5,(zz-cz)/.026+.5))
 for i in range(steps):fs.append((0,1+i,1+(i+1)%steps))
 for j in range(layers-1):
  a=1+j*steps;b=a+steps
  for i in range(steps):fs.append((a+i,a+(i+1)%steps,b+(i+1)%steps,b+i))
 ob=mesh('EYE surface '+str(s),vs,fs,eye_mat)
 uv=ob.data.uv_layers.new(name='Iris UV')
 for loop in ob.data.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
 upper=[];lower=[];brow=[]
 for i in range(41):
  c=mix(eye['l'],eye['r'],i/40);x,lo,hi=eyelid(c,eye)
  x=cx+(x-cx)*.925;hi=cz+(hi-cz)*.90;lo=cz+(lo-cz)*.90
  upper.append((x,front_y(x,hi)-.0010,hi+CHIN))
  lower.append((x,front_y(x,lo)-.0004,lo+CHIN))
  bz=.125+.0015*sin(pi*i/40)
  brow.append((x*.95,front_y(x*.95,bz)-.0008,bz+CHIN))
 ribbon('Upper lashes / tapered '+str(s),upper,[.0004+.0043*sin(pi*i/40)**.6 for i in range(41)],INK)
 ribbon('Lower lid / fine '+str(s),lower,[.00018+.00035*sin(pi*i/40) for i in range(41)],LID)
 ribbon('Brow / soft arch '+str(s),brow,[.0003+.0018*sin(pi*i/40)**.8 for i in range(41)],INK)

# Closed lips and tiny nostril accents follow the sculpted surface.
mouth=[]
for i in range(31):
 x=-.008+.016*i/30;z=.0357+.00015*(x/.008)**2
 mouth.append((x,front_y(x,z)-.0009,z+CHIN))
ribbon('Mouth closure',mouth,[.0001+.00055*sin(pi*i/30) for i in range(31)],LIP)
pts=[]
for i in range(10):
 x=-.0015+.002*i/9;z=.063-.002*i/9
 pts.append((x,front_y(x,z)-.0004,z+CHIN))
ribbon('Nostril crease / single fine nose accent',pts,[.00015+.00025*sin(pi*i/9) for i in range(10)],LIP)

# Ears are sculpted concha/helix surfaces, sized to sit under the hair.
for s in [-1,1]:
 vs=[];fs=[];num=48
 for j in range(9):
  r=j/8
  for i in range(num):
   t=2*pi*i/num
   y=.011+.015*cos(t)*r;z=CHIN+.091+.025*sin(t)*r
   x=s*(.104+.010*sin(pi*r)*(.6+.4*sin(t))-.004*(1-r))
   vs.append((x,y,z))
 for j in range(8):
  for i in range(num):
   a=j*num+i;b=j*num+(i+1)%num;fs.append((a,b,b+num,a+num))
 ear=mesh('EAR / helix and concha '+str(s),vs,fs,SKIN)
 so=ear.modifiers.new('Auricle thickness','SOLIDIFY');so.thickness=.0015

# Neck with sternomastoid planes, widening into the shoulder base.
vs=[];fs=[];nr=28;nc=64
for j in range(nr+1):
 z=1.36+.18*j/nr;a=j/nr;rx=.037+.032*(1-a)**4;ry=.033+.015*(1-a)**4
 for i in range(nc):
  t=2*pi*i/nc;bulge=.0014*sin(t*2)**2*sin(pi*a)
  vs.append(((rx+bulge)*sin(t),.018-(ry+bulge)*cos(t),z))
for j in range(nr):
 for i in range(nc):
  a=j*nc+i;b=j*nc+(i+1)%nc;fs.append((a,b,b+nc,a+nc))
mesh('NECK / shaped transition',vs,fs,SKIN)

if '--with-hair' in sys.argv:
 runpy.run_path(str(ROOT/'tools'/'build_hair.py'))

# Keep view-matched references inside the native modeling scene.
reference=bpy.data.images.load(str(ROOT/'assets'/'character-sheet.png'));reference.pack()
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.75,.75,.75,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.render.film_transparent=False
def area(name,loc,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
 ob=bpy.data.objects.new(name,d);scene.collection.objects.link(ob);ob.location=loc
 ob.rotation_euler=(Vector((0,0,1.62))-ob.location).to_track_quat('-Z','Y').to_euler()
area('Broad key',(-1,-2,3),25,2);area('Fill',(1,-1,2),8,2)
d=bpy.data.cameras.new('Head review camera');cam=bpy.data.objects.new('Head review camera',d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=.43
head_views=[] if '--skip-head-renders' in sys.argv else [('head-front',(0,-3,1.64)),('head-side',(3,0,1.64)),('head-three-quarter',(1.9,-3,1.74))]
for name,loc in head_views:
 cam.location=loc;cam.rotation_euler=(Vector((0,0,1.62))-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(ROOT/'renders'/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models'/'head-work.blend'),compress=True)
print('HEAD_CONTROL_SURFACE_BUILT',len(head.data.vertices),len(head.data.polygons))
