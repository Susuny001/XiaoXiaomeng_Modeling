"""Continue the sculpted head into image-guided, connected character surfaces.
All primary shapes are authored profiles and quad patches, not primitive props.
"""
import bpy,bmesh,math,runpy,sys
from mathutils import Vector,Matrix
from math import sin,cos,pi,sqrt,exp,atan2
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];S=1.78/537
COLS={}
for name in ['BODY / continuous hands','CLOTH / connected garments','SHOES / constructed uppers','DETAILS / fastenings']:
 c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);COLS[name.split(' /')[0]]=c
def material(name,rgb):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.8
 return m
WHITE=material('Ivory cloth',(.85,.86,.83));BLACK=material('Black canvas',(.045,.049,.047));SKIN=material('Hand skin',(.88,.75,.62));YELLOW=material('Cord yellow',(.80,.60,.025));GREEN=material('Webbing lime',(.48,.68,.04));GOLD=material('Brass fastenings',(.52,.40,.08))
def mesh(name,vs,fs,ma=WHITE,col='CLOTH',sub=0,solid=0):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update()
 bm=bmesh.new();bm.from_mesh(d);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.00001)
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(d);bm.free()
 ob=bpy.data.objects.new(name,d);COLS[col].objects.link(ob);d.materials.append(ma)
 for p in d.polygons:p.use_smooth=True
 if sub:
  mod=ob.modifiers.new('Surface refinement','SUBSURF');mod.levels=sub;mod.render_levels=sub
 if solid:
  mod=ob.modifiers.new('Fabric thickness','SOLIDIFY');mod.thickness=solid;mod.offset=-1
 return ob
def interp(rows,z):
 if z<=rows[0][0]:return rows[0][1:]
 if z>=rows[-1][0]:return rows[-1][1:]
 for a,b in zip(rows,rows[1:]):
  if a[0]<=z<=b[0]:
   t=(z-a[0])/(b[0]-a[0]);return [a[j]*(1-t)+b[j]*t for j in range(1,len(a))]
def px(x,y,depth):return Vector(((x-185)*S,depth,(613-y)*S))
def curve(name,points,r,ma,col='DETAILS'):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=12;d.bevel_depth=r;d.bevel_resolution=3
 spl=d.splines.new('BEZIER');spl.bezier_points.add(len(points)-1)
 for b,p in zip(spl.bezier_points,points):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 ob=bpy.data.objects.new(name,d);COLS[col].objects.link(ob);d.materials.append(ma);ob['texture_mode']='solid';return ob

# Correct the facial mask width and view direction without changing the
# front-traced asymmetrical hair silhouettes.
rot=Matrix.Rotation(math.radians(-13),4,'Z');pivot=Vector((0,.018,1.52))
for ob in list(bpy.context.scene.objects):
 if ob.type!='MESH':continue
 if ob.name.startswith(('HEAD /','EYE surface','Upper lashes','Lower lid','Brow /','Mouth closure','Nostril crease','EAR /')):
  for v in ob.data.vertices:
   w=1-min(1,max(0,(v.co.z-1.64)/.07));v.co.x*=1-.08*w
   v.co=pivot+rot@(v.co-pivot);v.co.z+=.002

# The T-shirt has a real neckline opening and a shaped waist, behind the coat.
vs=[];fs=[];N=80;R=40
for j in range(R+1):
 u=j/R;z=1.105+.315*u
 rx,ry=interp([(1.105,.127,.075),(1.18,.145,.085),(1.29,.165,.090),(1.36,.178,.092),(1.42,.070,.047)],z)
 for i in range(N):
  t=2*pi*i/N;zz=z
  if j>R-4:zz-=.045*max(cos(t),0)*(j-(R-4))/4
  # Local tension ridges converge toward the tucked-in waist.
  fold=.0025*exp(-((z-1.15)/.07)**2)*sin(4*t+z*10)
  x=(rx+fold)*sin(t);y=-(ry+fold)*cos(t)
  if cos(t)>0:
   for anchor,slope in [(-.095,-.30),(-.034,-.12),(.035,.17),(.092,.38)]:
    distance=x-(anchor+slope*(z-1.11));fade=exp(-((z-1.13)/.105)**2)
    y-=.0055*exp(-(distance/.006)**2)*fade
    y+=.0028*exp(-((distance-.009)/.006)**2)*fade
  vs.append((x,y,zz))
for j in range(R):
 for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
shirt=mesh('T-shirt / neckline and draped torso',vs,fs,BLACK,sub=1,solid=.002)

# Connected trouser legs, crotch gusset and pelvis. Axial silhouette controls
# come from the front view; localized folds create physical cloth volume.
LEFT=[(350,148,190),(385,137,180),(410,140,177),(435,142,174),(460,142,170),(485,136,169),(510,128,168),(522,127,170),(533,132,164),(543,129,166),(554,136,162),(565,133,161),(574,138,158)]
RIGHT=[(350,190,225),(385,197,233),(410,200,237),(435,202,239),(460,208,238),(485,211,242),(510,212,248),(522,214,252),(534,211,249),(545,216,254),(556,213,248),(567,219,251),(575,218,245)]
def leg_profile(s,z):
 controls=LEFT if s<0 else RIGHT;rows=[]
 for y,a,b in controls:rows.append(((613-y)*S,(a+b)*.5,(b-a)*.5))
 c,w=interp(sorted(rows),z)
 return (c-185)*S,w*S
PV=[];PF=[];leg_tops={};nn=64;rr=104
for s in [-1,1]:
 off=len(PV)
 for j in range(rr+1):
  u=j/rr;z=.13+.81*u;cx,rx=leg_profile(s,z)
  ry=interp([(.13,.047),(.23,.058),(.38,.053),(.58,.055),(.76,.068),(.94,.083)],z)[0]
  for i in range(nn):
   t=2*pi*i/nn;zv=z
   if j>rr-8:zv+=.035*sin(t)*s*(j-(rr-8))/8
   # Individually placed, directional cuff and knee fold planes.
   d=0
   for z0,a,phase,span in [(.18,.009,.4,.60),(.235,.011,-.9,.85),(.292,.007,1.6,.65),(.56,.004,-.5,.50)]:
    line=z0+.025*sin(t*1.35+phase*s)
    angle=atan2(sin(t-phase),cos(t-phase))
    local=exp(-(angle/span)**2)
    d+=a*exp(-((z-line)/.009)**2)*local-.004*exp(-((z-line-.013)/.009)**2)*local
   PV.append((cx+(rx+d)*sin(t),.008-(ry+d)*cos(t),zv))
 for j in range(rr):
  for i in range(nn):a=off+j*nn+i;b=off+j*nn+(i+1)%nn;PF.append((a,b,b+nn,a+nn))
 leg_tops[s]=[off+rr*nn+i for i in range(nn)]
# Join the two inner upper half-loops across the crotch.
lt=leg_tops[-1];rt=leg_tops[1]
for i in range(nn//2):
 a=lt[i];b=lt[(i+1)%nn];c=rt[(nn-i-1)%nn];d=rt[(nn-i)%nn];PF.append((a,b,c,d))
# Outer leg halves form the lower boundary of the pelvic shell.
boundary=[lt[i] for i in range(nn//2,nn)]+[lt[0]]+[rt[i] for i in range(nn//2+1)];previous=boundary
for j in range(1,17):
 u=j/16;ring=[]
 for index in boundary:
  p=Vector(PV[index]);t=atan2(p.x/.205,-p.y/.084)
  target=Vector((.137*sin(t),-.089*cos(t),1.113))
  q=p.lerp(target,u);ring.append(len(PV));PV.append(q)
 for i in range(len(ring)):PF.append((previous[i],previous[(i+1)%len(ring)],ring[(i+1)%len(ring)],ring[i]))
 previous=ring
pants=mesh('Trousers / continuous pelvis legs and sculpted folds',PV,PF,BLACK,sub=1,solid=.0025)
v=[];f=[]
for j in range(7):
 z=1.088+.034*j/6
 for i in range(64):
  t=2*pi*i/64;v.append((.139*sin(t),-.092*cos(t),z))
for j in range(6):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;f.append((a,b,b+64,a+64))
mesh('Trousers / sewn waistband',v,f,BLACK,sub=1,solid=.003)

# Open jacket bodice. The sleeve surfaces share the actual armhole vertices.
vs=[];fs=[];NC=96;NR=60;t0=.26;t1=2*pi-.29
ZROWS=[(.770,.218,.115,.121),(.795,.224,.118,.123),(.91,.204,.113,.121),(1.04,.177,.105,.115),(1.11,.174,.104,.108),(1.24,.181,.104,.110),(1.35,.199,.104,.111),(1.415,.194,.091,.102)]
for j in range(NR+1):
 z=.770+(.645)*j/NR;rx,front,back=interp(ZROWS,z)
 for i in range(NC+1):
  t=t0+(t1-t0)*i/NC;x=rx*sin(t);y=-(front if cos(t)>0 else back)*cos(t);zz=z
  if j>NR-4:zz+=.012*cos(2*t)*(j-(NR-4))/4
  if abs(t-pi)<.8:zz-=.006*sin(j/NR*pi)
  # Front panel folds are local to the waist and lower hem.
  frontw=max(cos(t),0)**4
  y-=frontw*(.004*exp(-((z-(.87+.09*abs(x)/.22))/.025)**2))
  vs.append((x,y,zz))
HOLES=[]
for s,theta in [(1,pi/2),(-1,3*pi/2)]:
 centre=round((theta-t0)/(t1-t0)*NC);lo=centre-7;hi=centre+7;low=47;high=59
 HOLES.append((s,lo,hi,low,high))
def ci(r,c):return r*(NC+1)+c
for j in range(NR):
 for i in range(NC):
  if any(lo<=i<hi and low<=j<high for _,lo,hi,low,high in HOLES):continue
  a=ci(j,i);fs.append((a,a+1,a+NC+2,a+NC+1))
for s,lo,hi,low,high in HOLES:
 edge=[ci(high,c) for c in range(lo,hi+1)]+[ci(r,hi) for r in range(high-1,low-1,-1)]+[ci(low,c) for c in range(hi-1,lo-1,-1)]+[ci(r,lo) for r in range(low+1,high)]
 centre=sum((Vector(vs[k]) for k in edge),Vector())/len(edge)
 tangent=Vector((s*.57,0,-.82)).normalized();front=Vector((0,-1,0));up=Vector((s*.82,0,.57)).normalized()
 angles=[atan2((Vector(vs[k])-centre).dot(up),(Vector(vs[k])-centre).dot(front)) for k in edge]
 controls=[(0,centre.x,centre.z,.068,.075),(.16,s*.241,1.300,.075,.078),(.40,s*.313,1.174,.066,.069),(.68,s*.382,1.048,.070,.071),(1,s*.441,.944,.064,.067)]
 previous=edge
 for row in range(1,37):
  u=row/36;cx,cz,ry,rv=interp(controls,u);c=Vector((cx,-.006,cz));ring=[]
  for k,a in enumerate(angles):
   p=c+front*(ry*cos(a))+up*(rv*sin(a))
   if row<5:p=Vector(vs[edge[k]]).lerp(p,row/5)
   # Elbow gathers: two partial diagonal folds, fading before side seams.
   p+=front*(.004*exp(-((u-.51-.04*sin(a))/.045)**2)*max(cos(a),0)**3)
   p+=up*(.003*exp(-((u-.58+.04*cos(a))/.04)**2)*max(sin(a),0)**3)
   ring.append(len(vs));vs.append(p)
  for k in range(len(ring)):fs.append((previous[k],previous[(k+1)%len(ring)],ring[(k+1)%len(ring)],ring[k]))
  previous=ring
 # Folded cuff is a real continuation turning back over the sleeve.
 for row in range(1,9):
  u=row/8;ring=[];c=Vector((s*.441,-.006,.944))+tangent*(-.047*u)
  for a in angles:
   p=c+front*((.066+.003*sin(pi*u))*cos(a))+up*((.069+.003*sin(pi*u))*sin(a));ring.append(len(vs));vs.append(p)
  for k in range(len(ring)):fs.append((previous[k],previous[(k+1)%len(ring)],ring[(k+1)%len(ring)],ring[k]))
  previous=ring
jacket=mesh('Jacket / joined bodice armholes sleeves and cuffs',vs,fs,WHITE,sub=1,solid=.004)

# Folded collar pieces, fitted to the coat rather than floating wire outlines.
def folded_panel(name,points):
 points=[Vector(p) for p in points];c=sum(points,Vector())/len(points)
 vs=points+[c];fs=[]
 for i in range(len(points)):fs.append((i,(i+1)%len(points),len(points)))
 return mesh(name,vs,fs,WHITE,solid=.004)
folded_panel('Collar / right folded stand',[px(138,164,.005),px(172,173,-.066),px(173,215,-.119),px(157,196,-.128),px(135,190,-.028)])
folded_panel('Collar / left folded stand',[px(234,159,.018),px(202,174,-.068),px(201,216,-.119),px(220,194,-.125),px(244,187,.014)])
# Hood has a connected rim-to-tip surface with continuous fabric thickness.
vs=[];fs=[];U=48;V=30
for j in range(V+1):
 v=j/V
 for i in range(U+1):
  u=-1+2*i/U;x=.195*u*(1-.77*v);y=.090+.057*(1-u*u)+.015*sin(pi*v);z=1.496-.226*v*(1-.17*abs(u))-.034*abs(u)
  vs.append((x,y,z))
for j in range(V):
 for i in range(U):a=j*(U+1)+i;fs.append((a,a+1,a+U+2,a+U+1))
hood=mesh('Hood / shaped back shell',vs,fs,WHITE,sub=1,solid=.004)

# Continuous hand surfaces: palm grid, four welded finger ports and thumb port.
for s,side in [(-1,'R'),(1,'L')]:
 v=[];f=[];rows=7;columns=4
 for back in [False,True]:
  for j in range(rows+1):
   u=j/rows;z=.938-.067*u;cx=s*(.451+.017*u);w=.020+.011*sin(pi*u/2);th=.0115-.002*u
   for i in range(columns+1):
    x=cx+(i/columns-.5)*w*2;y=-.011+(th if back else -th)*(1-.12*abs(i/columns-.5));v.append((x,y,z))
 layer=(rows+1)*(columns+1)
 for back in [False,True]:
  off=layer if back else 0
  for j in range(rows):
   for i in range(columns):a=off+j*(columns+1)+i;q=(a,a+1,a+columns+2,a+columns+1);f.append(tuple(reversed(q)) if back else q)
 for j in range(rows):
  for i in [0,columns]:
   if j==3 and i==(0 if s>0 else columns):continue
   a=j*(columns+1)+i;b=a+columns+1;f.append((a,b,b+layer,a+layer))
 for i in range(columns):
  port=[rows*(columns+1)+i,rows*(columns+1)+i+1,layer+rows*(columns+1)+i+1,layer+rows*(columns+1)+i]
  c=sum((Vector(v[k]) for k in port),Vector())/4
  lengths=[.054,.064,.060,.045];length=lengths[i if s>0 else 3-i];angle=(i-1.5)*.11
  previous=port
  for j in range(1,13):
   u=j/12;tip=c+Vector((sin(angle)*length*u,-.003*sin(pi*u),-length*u));scale=(1-.48*u)*(.96+.05*cos(u*pi*3))
   ring=[]
   for k in port:
    q=Vector(v[k])-c;q.z=0;p=tip+q*scale;ring.append(len(v));v.append(p)
   for k in range(4):f.append((previous[k],previous[(k+1)%4],ring[(k+1)%4],ring[k]))
   previous=ring
  f.append(tuple(reversed(previous)))
 # Thumb emerges from the side opening of the palm.
 i=0 if s>0 else columns;a=3*(columns+1)+i;b=a+columns+1;port=[a,b,b+layer,a+layer]
 c=sum((Vector(v[k]) for k in port),Vector())/4;previous=port
 for j in range(1,13):
  u=j/12;centre=c+Vector((-s*.038*u,-.006*u,-.031*u));ring=[]
  for k in port:
   delta=Vector(v[k])-c;p=centre+delta*(1-.5*u);ring.append(len(v));v.append(p)
  for k in range(4):f.append((previous[k],previous[(k+1)%4],ring[(k+1)%4],ring[k]))
  previous=ring
 f.append(tuple(reversed(previous)))
 hand=mesh('Hand / welded palm fingers thumb.'+side,v,f,SKIN,col='BODY',sub=2);hand['texture_mode']='solid'

# Footwear last, cupsole and upper: authored outline with a low toe and ankle.
OUTLINE=[(0,.065),(.042,.060),(.053,.028),(.060,-.060),(.061,-.145),(.051,-.207),(.031,-.228),(0,-.234),(-.033,-.228),(-.054,-.207),(-.063,-.144),(-.063,-.060),(-.052,.028),(-.042,.060)]
def shoe_ring(name,s,sections):
 vs=[];fs=[];n=70;angle=s*math.radians(15);c=Vector((s*.145,0,0));rot=Matrix.Rotation(angle,4,'Z')
 for z,wx,front,back in sections:
  for i in range(n):
   t=i/n*len(OUTLINE);k=int(t);u=t-k;a=Vector(OUTLINE[k%len(OUTLINE)]);b=Vector(OUTLINE[(k+1)%len(OUTLINE)]);q=a.lerp(b,u)
   x=q.x*wx;y=q.y*(front if q.y<0 else back)
   p=c+rot@Vector((x,y,z));vs.append(p)
 for j in range(len(sections)-1):
  for i in range(n):a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
 fs.append(tuple(reversed(range(n))));fs.append(tuple((len(sections)-1)*n+i for i in range(n)))
 return mesh(name,vs,fs,WHITE,col='SHOES',sub=1)
for s,side in [(-1,'R'),(1,'L')]:
 shoe_ring('Shoe / shaped layered cupsole.'+side,s,[(.011,.98,.99,.98),(.017,1.03,1.01,1.01),(.045,1.03,1.01,1.01),(.054,1.,1.,1.)])
 shoe_ring('Shoe / sculpted leather upper.'+side,s,[(.051,.96,.99,.99),(.066,.97,.98,.98),(.085,.95,.94,.96),(.107,.87,.77,.91),(.132,.76,.44,.85),(.160,.65,.07,.78),(.169,.63,.03,.77)])
 rot=Matrix.Rotation(s*math.radians(15),4,'Z');centre=Vector((s*.145,0,0))
 def sp(x,y,z):return centre+rot@Vector((x,y,z))
 # Shoe tongue and actual raised lacing follow the instep height.
 tongue=[];tf=[]
 for j in range(21):
  u=j/20;y=-.164+.165*u;z=.109+.065*u
  for x in [-.023,.023]:tongue.append(sp(x,y,z))
 for j in range(20):a=j*2;tf.append((a,a+1,a+3,a+2))
 mesh('Shoe / tongue.'+side,tongue,tf,WHITE,col='SHOES',sub=1,solid=.002)
 for j in range(6):
  y=-.159+.024*j;z=.112+.010*j;w=.025-.001*j
  for e in [-1,1]:
   if j<5:curve('Lace / crossing %s %s %s'%(side,j,e),[sp(e*w,y,z),sp(0,y+.013,z+.009),sp(-e*(w-.001),y+.024,z+.010)],.0015,YELLOW)
 curve('Lace / bow A.'+side,[sp(0,-.018,.175),sp(-.023,-.030,.184),sp(-.025,-.009,.184),sp(0,-.018,.175)],.0015,YELLOW)
 curve('Lace / bow B.'+side,[sp(0,-.018,.175),sp(.023,-.030,.184),sp(.026,-.008,.184),sp(0,-.018,.175)],.0015,YELLOW)

# Functional cords and the asymmetric right-side webbing have real thickness.
for x in [148,215]:
 curve('Hood cord '+str(x),[px(x,187,-.127),px(x,217,-.135),px(x-1,246,-.132),px(x-1,270,-.133)],.0018,YELLOW)
 curve('Hood cord loop '+str(x),[px(x-1,261,-.133),px(x+1,272,-.137),px(x-1,276,-.136),px(x-3,271,-.134),px(x-1,261,-.133)],.0018,YELLOW)
strip=[px(129,392,-.082),px(121,423,-.088),px(111,466,-.075),px(110,495,-.087),px(115,505,-.085)]
vv=[];ff=[]
for p in strip:vv.extend([p-Vector((.008,0,0)),p+Vector((.008,0,0))])
for i in range(len(strip)-1):ff.append((i*2,i*2+1,i*2+3,i*2+2))
ob=mesh('RIGHT / long woven strap',vv,ff,GREEN,col='DETAILS',solid=.0015);ob['texture_mode']='solid'
# Cargo pocket is a shaped, gusseted sewn shell, attached to the right thigh.
vs=[px(125,390,-.043),px(135,392,-.086),px(139,448,-.092),px(126,452,-.062),px(122,392,.026),px(123,451,.022)]
mesh('RIGHT / cargo gusset and flap',vs,[(0,1,2,3),(0,3,5,4),(0,4,1),(3,2,5)],BLACK,solid=.002)

# Store a native, editable working scene before the albedo alignment pass.
scene=bpy.context.scene;scene['production_stage']='Connected garment and anatomy surfaces; reference-albedo alignment in progress.'
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=1.94
cam.location=(0,-5,.91);cam.rotation_euler=(Vector((0,0,.91))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1100;scene.render.resolution_y=1300
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models'/'character-geometry.blend'),compress=True)
print('CONNECTED_CHARACTER_SURFACES_BUILT',len(vs))
