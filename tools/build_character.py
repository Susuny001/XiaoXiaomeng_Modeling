"""Xiao Xiao Meng: editable, layered Blender character and portable exports.

Run: blender -b --factory-startup -t 4 --python tools/build_character.py
No downloaded character assets. Dimensions are metres; Z is up, front is -Y.
"""
import bpy, math, json, os, random, sys, time, runpy
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi, sqrt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'models'
RENDERS = ROOT / 'renders'
OUT.mkdir(exist_ok=True); RENDERS.mkdir(exist_ok=True)
random.seed(27)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.collections):
    if d.name != 'Collection': bpy.data.collections.remove(d)
base = bpy.data.collections.get('Collection'); base.name = 'XIAOXIAOMENG'
COLS = {}
for name in ['01_BODY', '02_FACE', '03_HAIR', '04_INNER', '05_JACKET', '06_TROUSERS', '07_SHOES', '08_HARDWARE', '09_RIG', '10_STUDIO']:
    c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); COLS[name] = c
PARTS = []; MATS = {}

def mat(name, color, rough=.55, metal=0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.diffuse_color = (*color, 1)
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    MATS[name]=m; return m

skin=mat('Skin • warm porcelain',(.82,.65,.48),.54)
blush=mat('Skin • blush',(.75,.40,.32),.7)
hair=mat('Hair • charcoal',(.027,.032,.033),.52)
hair2=mat('Hair • slate layers',(.045,.049,.049),.53)
hair3=mat('Hair • soft graphite',(.064,.069,.065),.54)
lime=mat('Accent • spring chartreuse',(.53,.77,.058),.42)
lime_light=mat('Accent • pale lime',(.69,.90,.14),.43)
yellow=mat('Accent • lemon',(.95,.73,.032),.4)
olive=mat('Accent • moss',(.25,.40,.035),.55)
white=mat('Jacket • ivory nylon',(.88,.89,.84),.61)
seam=mat('Jacket • seam shadow',(.65,.68,.64),.72)
lining=mat('Lining • charcoal twill',(.043,.049,.047),.8)
black=mat('T-shirt • washed black',(.061,.066,.063),.84)
pants=mat('Trousers • graphite canvas',(.043,.046,.043),.82)
pants_hi=mat('Trousers • panel',(.061,.063,.056),.8)
stitch=mat('Thread • dark olive',(.16,.18,.12),.83)
rubber=mat('Shoe • soft rubber',(.79,.81,.75),.8)
shoe=mat('Shoe • ivory leather',(.92,.93,.88),.47)
sole_dark=mat('Sole • graphite tread',(.10,.12,.10),.86)
gold=mat('Hardware • brushed pale gold',(.69,.57,.23),.3,.75)
steel=mat('Hardware • graphite metal',(.16,.19,.17),.3,.7)
ink=mat('Face • ink',(.016,.020,.019),.4)
sclera=mat('Eyes • ivory',(.94,.94,.83),.26)
iris=mat('Eyes • golden lime',(.63,.67,.055),.26)
iris_dark=mat('Eyes • olive rim',(.18,.23,.018),.3)
iris_light=mat('Eyes • iris fibers',(.90,.77,.12),.3)
glint=mat('Eyes • catchlight',(.99,1,.96),.15)
mouth=mat('Face • lip line',(.24,.11,.085),.6)

def move(obj, col, material=None, bone=None):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    COLS[col].objects.link(obj)
    if material: obj.data.materials.append(material)
    if bone: obj['rig_bone'] = bone
    if col != '10_STUDIO': PARTS.append(obj)
    return obj

def mesh(name, verts, faces, material, col, bone=None, sub=0):
    d=bpy.data.meshes.new(name); d.from_pydata(verts,[],faces); d.update()
    ob=bpy.data.objects.new(name,d); COLS[col].objects.link(ob)
    ob.data.materials.append(material)
    for p in d.polygons:p.use_smooth=True
    if bone: ob['rig_bone']=bone
    if sub:
        m=ob.modifiers.new('Tailored surface / editable subdivision','SUBSURF'); m.levels=sub; m.render_levels=sub
    PARTS.append(ob); return ob

def uv_sphere(name,loc,scale,material,col,bone=None,seg=32,rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
    ob=bpy.context.object; ob.name=name; ob.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in ob.data.polygons:p.use_smooth=True
    return move(ob,col,material,bone)

def cube(name,loc,scale,material,col,bone=None,bevel=.005):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob=bpy.context.object; ob.name=name; ob.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    move(ob,col,material,bone)
    if bevel:
        m=ob.modifiers.new('Rounded construction edges','BEVEL');m.width=bevel;m.segments=3
        m=ob.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return ob

def curve(name,pts,radius,material,col,bone=None,closed=False,res=3):
    d=bpy.data.curves.new(name,'CURVE'); d.dimensions='3D';d.resolution_u=12
    d.bevel_depth=radius;d.bevel_resolution=res
    sp=d.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
    for b,p in zip(sp.bezier_points,pts):
        b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
    sp.use_cyclic_u=closed
    ob=bpy.data.objects.new(name,d);COLS[col].objects.link(ob);d.materials.append(material)
    if bone:ob['rig_bone']=bone
    if col!='10_STUDIO':PARTS.append(ob)
    return ob

def torus(name,loc,major,minor,material,col,bone=None,rotation=(pi/2,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=8,location=loc,major_radius=major,minor_radius=minor,rotation=rotation)
    ob=bpy.context.object;ob.name=name
    for p in ob.data.polygons:p.use_smooth=True
    return move(ob,col,material,bone)

def catmull(points, values=None, steps=6):
    ps=[Vector(p) for p in points]; out=[]; vals=[]
    for i in range(len(ps)-1):
        a=ps[max(0,i-1)];b=ps[i];c=ps[i+1];d=ps[min(len(ps)-1,i+2)]
        for k in range(steps):
            t=k/steps
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
            if values:vals.append(values[i]*(1-t)+values[i+1]*t)
    out.append(ps[-1])
    if values:vals.append(values[-1])
    return out,vals

def sweep(name,points,widths,depths,material,col,bone=None,sides=12,steps=5,detail=0):
    path,ws=catmull(points,widths,steps);_,ds=catmull(points,depths,steps)
    vs=[];fs=[]
    for j,p in enumerate(path):
        tangent=(path[min(j+1,len(path)-1)]-path[max(0,j-1)]).normalized()
        ref=Vector((1,0,0))
        if abs(tangent.dot(ref))>.9:ref=Vector((0,1,0))
        u=(ref-tangent*tangent.dot(ref)).normalized();v=tangent.cross(u).normalized()
        for i in range(sides):
            t=2*pi*i/sides;wav=1+detail*sin(t*5+j*.8)
            vs.append(p+u*ws[j]*cos(t)*wav+v*ds[j]*sin(t)*wav)
    for j in range(len(path)-1):
        for i in range(sides):
            a=j*sides+i;b=j*sides+(i+1)%sides
            fs.append((a,b,b+sides,a+sides))
    fs.append(tuple(reversed(range(sides))))
    fs.append(tuple((len(path)-1)*sides+i for i in range(sides)))
    return mesh(name,vs,fs,material,col,bone)

def ring_mesh(name,rings,material,col,bone=None,n=64,fold=0,sub=1):
    vs=[];fs=[]
    for j,(cx,cy,z,rx,ry) in enumerate(rings):
        for i in range(n):
            t=2*pi*i/n
            r=1+fold*(sin(7*t+j*1.6)+.4*sin(11*t-j*.7))
            dz=0
            if name.startswith('Trouser leg'):
                ankle=math.exp(-((z-.27)/.085)**2)
                knee=math.exp(-((z-.57)/.075)**2)
                r+=.040*ankle*sin(3*t+j*1.9)+.025*knee*cos(3*t-j*1.5)
                dz=(.017*ankle*sin(3*t+j*1.7)+.009*knee*sin(2*t+j))*sin(pi*j/(len(rings)-1))
            vs.append((cx+rx*sin(t)*r,cy-ry*cos(t)*r,z+dz))
    for j in range(len(rings)-1):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
    fs.append(tuple(reversed(range(n))));fs.append(tuple((len(rings)-1)*n+i for i in range(n)))
    return mesh(name,vs,fs,material,col,bone,sub)

def strip(name,points,width,material,col,bone=None):
    # Woven flat ribbon, width along X, with actual shell thickness.
    vs=[];fs=[]
    path,_=catmull(points,steps=8)
    for p in path:vs.extend([p+Vector((-width/2,0,0)),p+Vector((width/2,0,0))])
    for i in range(len(path)-1):fs.append((2*i,2*i+1,2*i+3,2*i+2))
    ob=mesh(name,vs,fs,material,col,bone)
    so=ob.modifiers.new('Woven ribbon thickness','SOLIDIFY');so.thickness=.0015
    be=ob.modifiers.new('Soft ribbon edge','BEVEL');be.width=.0007;be.segments=2
    return ob

def text(name,value,loc,size,material,col,bone=None):
    d=bpy.data.curves.new(name,'FONT');d.body=value;d.size=size;d.align_x='CENTER';d.align_y='CENTER';d.extrude=.00025;d.bevel_depth=.00012
    ob=bpy.data.objects.new(name,d);COLS[col].objects.link(ob);ob.location=loc;ob.rotation_euler=(pi/2,0,0);d.materials.append(material)
    if bone:ob['rig_bone']=bone
    PARTS.append(ob);return ob

def stitch_line(name,points,material=seam,col='05_JACKET',bone='spine.02',radius=.00055):
    return curve(name,points,radius,material,col,bone,res=1)

# BODY: a shaped quad head, hidden torso and continuous fingers.
head_rings=[(0,.008,1.505,.025,.025),(0,.006,1.520,.047,.045),(0,.008,1.544,.074,.064),(0,.012,1.580,.100,.082),(0,.012,1.625,.117,.096),(0,.014,1.672,.123,.103),(0,.020,1.713,.115,.101),(0,.025,1.746,.093,.084),(0,.025,1.768,.055,.056),(0,.026,1.779,.008,.010)]
ring_mesh('Head / sculpted jaw and cheek loops',head_rings,skin,'01_BODY','head',n=80,sub=2)
ring_mesh('Neck',[(0,.015,1.367,.044,.044),(0,.012,1.39,.045,.041),(0,.015,1.48,.041,.039),(0,.02,1.53,.047,.044)],skin,'01_BODY','neck',sub=1)
ring_mesh('Body / under clothing',[(0,0,.91,.11,.08),(0,0,1.03,.125,.079),(0,0,1.20,.145,.087),(0,0,1.34,.17,.087),(0,0,1.40,.13,.075)],skin,'01_BODY','spine.02',sub=1)
for s,side in [(1,'L'),(-1,'R')]:
    uv_sphere('Ear.'+side,(s*.12,.010,1.626),(.022,.016,.034),skin,'01_BODY','head')
    uv_sphere('Ear concha.'+side,(s*.133,-.002,1.625),(.010,.009,.020),blush,'02_FACE','head')
    curve('Ear helix.'+side,[(s*.132,-.004,1.648),(s*.143,-.003,1.637),(s*.14,-.004,1.613),(s*.13,-.006,1.607)],.002,skin,'02_FACE','head')
    palm=uv_sphere('Hand palm.'+side,(s*.451,-.006,.925),(.031,.019,.050),skin,'01_BODY','hand.'+side)
    for i,off in enumerate([-.023,-.008,.008,.023]):
        x=s*(.45+off);length=[.052,.066,.062,.047][i]
        pts=[(x,-.009,.903),(x+s*off*.45,-.014,.882),(x+s*off*.65,-.015,.902-length)]
        sweep('Finger %d.%s'%(i+1,side),pts,[.0075,.007,.0045],[.007,.0065,.0045],skin,'01_BODY','finger%d.%s'%(i+1,side),sides=10,steps=6)
        tip=pts[-1]
        nail=uv_sphere('Nail %d.%s'%(i+1,side),(tip[0],tip[1]-.004,tip[2]+.006),(.0045,.0014,.0068),skin,'01_BODY','finger%d.%s'%(i+1,side),seg=16,rings=10)
    sweep('Thumb.'+side,[(s*.43,-.008,.935),(s*.413,-.018,.915),(s*.404,-.023,.895)],[.011,.009,.006],[.010,.008,.006],skin,'01_BODY','thumb.'+side,sides=12)

# FACE: curved almond whites, radial iris geometry, upper lids and ink details.
def face_y(x):return .011-.103*sqrt(max(.10,1-(x/.128)**2))
for s,side in [(1,'L'),(-1,'R')]:
    cx=s*.050;cz=1.648;vs=[(cx,face_y(cx)-.005,cz)];fs=[]
    border=[]
    for i in range(64):
        t=2*pi*i/64;dx=.039*cos(t);dz=(.013 if sin(t)>0 else .010)*sin(t)
        x=cx+dx;z=cz+dz+dx*s*.055;y=face_y(x)-.004
        vs.append((x,y,z));border.append((x,y-.001,z))
    for i in range(64):fs.append((0,i+1,(i+1)%64+1))
    mesh('Eye almond.'+side,vs,fs,sclera,'02_FACE','head')
    yc=face_y(cx)-.008
    uv_sphere('Iris limbal ring.'+side,(cx,yc,cz),(.0135,.002,.0127),iris_dark,'02_FACE','head',seg=48,rings=24)
    uv_sphere('Iris golden green.'+side,(cx,yc-.0019,cz),(.0115,.0015,.0115),iris,'02_FACE','head',seg=48,rings=24)
    for i in range(36):
        a=2*pi*i/36
        curve('Iris fiber %02d.%s'%(i,side),[(cx+.007*cos(a),yc-.0036,cz+.008*sin(a)),(cx+.0116*cos(a+.035),yc-.003,cz+.0134*sin(a+.035))],.00035,iris_light if i%3 else olive,'02_FACE','head',res=0)
    uv_sphere('Pupil.'+side,(cx,yc-.0042,cz+.001),(.0048,.001,.0086),ink,'02_FACE','head',seg=24,rings=16)
    uv_sphere('Eye catchlight.'+side,(cx-.0042,yc-.0052,cz+.0064),(.0033,.001,.0036),glint,'02_FACE','head',seg=20,rings=12)
    uv_sphere('Eye catchlight small.'+side,(cx+.0045,yc-.0045,cz-.006),(.0016,.0008,.0015),glint,'02_FACE','head',seg=12,rings=8)
    upper=[];lower=[]
    for i in range(17):
        t=pi*i/16;dx=.039*cos(t);x=cx+dx
        upper.append((x,face_y(x)-.006,cz+.013*sin(t)+dx*s*.055))
        lower.append((x,face_y(x)-.005,cz-.010*sin(t)+dx*s*.055))
    curve('Upper eyelid.'+side,upper,.0019,ink,'02_FACE','head')
    curve('Lower eyelid.'+side,lower,.00065,iris_dark,'02_FACE','head',res=1)
    curve('Brow.'+side,[(s*.019,face_y(s*.019)-.004,1.683),(s*.049,face_y(s*.049)-.004,1.688),(s*.082,face_y(s*.082)-.003,1.681)],.0028,hair,'02_FACE','head')
    curve('Eyelash outer.'+side,[(s*.083,face_y(s*.083)-.005,1.650),(s*.093,face_y(s*.093)-.006,1.654)],.0012,ink,'02_FACE','head')
uv_sphere('Nose / bridge',(0,-.092,1.614),(.005,.008,.018),skin,'02_FACE','head',seg=24)
uv_sphere('Nose / tip',(0,-.100,1.605),(.006,.006,.005),skin,'02_FACE','head',seg=24)
curve('Nose accent',[(.004,-.111,1.605),(.008,-.107,1.601)],.0007,mouth,'02_FACE','head',res=1)
curve('Mouth / neutral smile',[(-.017,-.083,1.566),(0,-.087,1.564),(.016,-.083,1.566)],.0011,mouth,'02_FACE','head')
curve('Lower lip highlight',[(-.009,-.085,1.559),(0,-.086,1.558),(.009,-.085,1.559)],.0008,skin,'02_FACE','head')

# INNER SHIRT: neckline and soft folds are real surfaces, not color-only decals.
ring_mesh('T-shirt / draped torso',[(0,0,.962,.125,.084),(0,0,.978,.139,.089),(0,0,1.06,.137,.084),(0,0,1.16,.153,.090),(0,0,1.29,.167,.095),(0,0,1.365,.183,.090),(0,0,1.39,.135,.078)],black,'04_INNER','spine.02',fold=.024,sub=1)
curve('T-shirt / collar binding',[(-.078,-.075,1.389),(-.049,-.090,1.372),(0,-.099,1.349),(.049,-.090,1.372),(.078,-.075,1.389)],.0025,lining,'04_INNER','spine.02')
for i in range(8):
    s=1 if i%2 else -1;x=s*(.015+.014*(i//2));z=1.05+.026*(i%3)
    curve('T-shirt / gathered fold %02d'%i,[(x*.55,-.088,z-.045),(x,-.094,z),(x*1.8,-.094,z+.12)],.0026,black,'04_INNER','spine.02')

# TROUSERS: asymmetric cargo pocket, belt loops, diagonal folds and pooled cuffs.
ring_mesh('Trousers / waistband',[(0,0,.91,.14,.098),(0,0,.985,.14,.093),(0,0,1.019,.131,.088),(0,0,1.028,.13,.089)],pants,'06_TROUSERS','pelvis',n=64,fold=.015)
curve('Waist / topstitch',[(.134*sin(t),-.093*cos(t),1.018) for t in [2*pi*i/48 for i in range(48)]],.0007,stitch,'06_TROUSERS','pelvis',closed=True,res=1)
for i in range(8):
    t=2*pi*i/8;x=.14*sin(t);y=-.096*cos(t)
    o=cube('Belt loop %02d'%i,(x,y,1.00),(.010,.007,.047),pants_hi,'06_TROUSERS','pelvis',.002)
curve('Fly seam',[(.012,-.099,1.012),(.018,-.104,.951),(.012,-.103,.885)],.0011,stitch,'06_TROUSERS','pelvis',res=1)
cube('Belt / buckle',(0,-.101,1.009),(.022,.009,.015),steel,'08_HARDWARE','pelvis',.002)
for s,side in [(1,'L'),(-1,'R')]:
    rings=[]
    specs=[(.19,.064,.060),(.215,.082,.074),(.25,.090,.076),(.29,.079,.070),(.34,.085,.071),(.40,.084,.074),(.47,.076,.075),(.53,.082,.083),(.57,.094,.086),(.61,.091,.079),(.69,.098,.087),(.77,.107,.093),(.86,.106,.092),(.93,.096,.085)]
    for j,(z,rx,ry) in enumerate(specs):
        cx=s*(.103+.014*sin(z*6));cy=.012+(.012 if .44<z<.64 else 0)
        rings.append((cx,cy,z,rx,ry))
    ring_mesh('Trouser leg / articulated cloth.'+side,rings,pants,'06_TROUSERS','leg.'+side,n=64,fold=.055,sub=1)
    # Side seam and stitched knee darts.
    curve('Outer seam.'+side,[(s*.185,.008,.88),(s*.209,.008,.73),(s*.204,.016,.58),(s*.183,.01,.40),(s*.188,.008,.245)],.0012,stitch,'06_TROUSERS','leg.'+side,res=1)
    for j in range(4):
        z=.235+j*.021
        pts=[(s*(.10-.061),-.048,z+.015),(s*.10,-.079,z),(s*(.10+.067),-.042,z+.023)]
        curve('Pooled cuff fold %02d.%s'%(j,side),pts,.008 if j%2 else .010,pants_hi if j==1 else pants,'06_TROUSERS','shin.'+side)
    for j in range(3):
        z=.54+j*.025
        curve('Knee tension fold %02d.%s'%(j,side),[(s*.044,-.05,z+.035),(s*.113,-.079,z),(s*.180,-.038,z-.009)],.0045,pants,'06_TROUSERS','leg.'+side)
    # Oblique hand pocket openings.
    curve('Hip pocket welt.'+side,[(s*.105,-.075,.988),(s*.151,-.077,.943),(s*.169,-.055,.884)],.003,lining,'06_TROUSERS','pelvis')
    curve('Hip pocket stitch.'+side,[(s*.110,-.080,.988),(s*.157,-.078,.941),(s*.177,-.053,.886)],.0007,stitch,'06_TROUSERS','pelvis',res=1)
# Right cargo pocket lies on -X, towards the front so it is visible in a front view.
pocket=cube('RIGHT cargo / gusset',(-.190,-.012,.785),(.037,.111,.181),lining,'06_TROUSERS','leg.R',.010)
cube('RIGHT cargo / pocket panel',(-.213,-.018,.785),(.012,.102,.165),pants_hi,'06_TROUSERS','leg.R',.008)
cube('RIGHT cargo / flap',(-.222,-.020,.872),(.014,.113,.040),pants,'06_TROUSERS','leg.R',.005)
for yy in [-.06,.025]:
    uv_sphere('Cargo snap',(-.232,yy,.867),(.002,.004,.004),steel,'08_HARDWARE','leg.R',seg=16,rings=10)
for yy in [-.061,.029]:
    curve('Cargo topstitch',[(-.224,yy,.850),(-.224,yy,.718)],.0007,stitch,'06_TROUSERS','leg.R',res=1)
strap_pts=[(-.194,-.078,.917),(-.218,-.080,.846),(-.228,-.082,.746),(-.257,-.068,.623),(-.253,-.082,.569)]
strip('RIGHT thigh / chartreuse webbing',strap_pts,.018,lime,'08_HARDWARE','leg.R')
strip('RIGHT thigh / yellow reverse',[(-.257,-.065,.643),(-.268,-.066,.582),(-.253,-.080,.567)],.017,yellow,'08_HARDWARE','leg.R')
cube('RIGHT webbing / loop hardware',(-.196,-.082,.918),(.030,.010,.024),steel,'08_HARDWARE','leg.R',.003)
cube('RIGHT webbing / strap over buckle',(-.196,-.089,.918),(.017,.003,.027),lime,'08_HARDWARE','leg.R',.001)

# JACKET: open quad shell, visible dark lining and constructed sleeves.
levels=[(.875,.196,.110),(.889,.207,.116),(.965,.196,.112),(1.05,.173,.101),(1.14,.174,.099),(1.25,.185,.102),(1.35,.206,.106),(1.394,.211,.100)]
vs=[];fs=[];n=80
for j,(z,rx,ry) in enumerate(levels):
    for i in range(n+1):
        t=.47+(2*pi-.94)*i/n
        wav=1+.018*sin(5*t+j*.7)+.009*sin(11*t-j)
        vs.append((rx*sin(t)*wav,-ry*cos(t)*wav,z+.005*sin(t*3+j)))
for j in range(len(levels)-1):
    for i in range(n):
        a=j*(n+1)+i;fs.append((a,a+1,a+n+2,a+n+1))
jacket=mesh('Jacket / tailored open shell',vs,fs,white,'05_JACKET','spine.02',sub=2)
jacket.data.materials.append(lining)
so=jacket.modifiers.new('Nylon shell and charcoal lining','SOLIDIFY');so.thickness=.007;so.offset=-1;so.material_offset=1;so.material_offset_rim=0
for s in [1,-1]:
    pts=[(s*rx*sin(.47),-ry*cos(.47)-.002,z) for z,rx,ry in levels]
    curve('Front opening / piping '+str(s),pts,.0025,white,'05_JACKET','spine.02')
    stitch_line('Front opening / stitch '+str(s),[(x+s*.007,y-.001,z) for x,y,z in pts])
    # Zipper teeth are individually modeled and sit on the edge of each open panel.
    for i in range(43):
        z=.905+i*.0107;frac=(z-.875)/(.52)
        rx=.19-.02*sin(frac*pi)
        cube('Zip tooth %s.%02d'%(s,i),(s*rx*sin(.47),-.101,z),(.003,.003,.004),gold,'08_HARDWARE','spine.02',.0006)
    torus('Hem press stud '+str(s),(s*.103,-.112,.894),.006,.0014,gold,'08_HARDWARE','spine.02')
    for back in [False,True]:
        angle=(pi-.82 if back else .82)*s
        pts=[(rx*sin(angle),-ry*cos(angle),z) for z,rx,ry in levels]
        stitch_line('Jacket / panel seam %s %s'%(s,back),pts,radius=.0008)
curve('Jacket / double hem',[((.205)*sin(t),-.117*cos(t),.888) for t in [.47+(2*pi-.94)*i/80 for i in range(81)]],.002,white,'05_JACKET','spine.02')
curve('Jacket / hem topstitch',[(.205*sin(t),-.118*cos(t),.901) for t in [.47+(2*pi-.94)*i/80 for i in range(81)]],.00065,seam,'05_JACKET','spine.02',res=1)
for s,side in [(1,'L'),(-1,'R')]:
    pts=[(s*.177,.008,1.357),(s*.237,.005,1.300),(s*.307,-.004,1.166),(s*.359,-.003,1.051),(s*.412,-.008,.969)]
    sweep('Jacket / generous sleeve.'+side,pts,[.073,.076,.068,.064,.064],[.073,.077,.067,.064,.060],white,'05_JACKET','arm.'+side,sides=40,steps=7,detail=.035)
    sweep('Jacket / cuff.'+side,[(s*.394,-.008,1.002),(s*.420,-.009,.961),(s*.427,-.010,.947)],[.066,.068,.066],[.064,.063,.060],white,'05_JACKET','forearm.'+side,sides=40,steps=4)
    # Inner cuff well and sleeve edge seam.
    sweep('Sleeve / black interior.'+side,[(s*.421,-.010,.954),(s*.434,-.010,.935)],[.054,.051],[.049,.045],lining,'05_JACKET','forearm.'+side,sides=32,steps=3)
    curve('Sleeve / underarm seam.'+side,[(s*.204,.067,1.32),(s*.292,.061,1.17),(s*.386,.046,.991)],.0011,seam,'05_JACKET','arm.'+side,res=1)
    for i in range(4):
        z=1.08+i*.025;x=s*(.35-i*.010)
        curve('Sleeve / elbow pleat %02d.%s'%(i,side),[(x-s*.032,-.050,z+.023),(x,-.067,z),(x+s*.035,-.030,z-.006)],.0035,white,'05_JACKET','forearm.'+side)
    # Raised, white stand collar, with angular cut tips.
    vv=[(s*.068,-.070,1.356),(s*.139,-.080,1.371),(s*.164,-.036,1.478),(s*.087,-.081,1.456)]
    ob=mesh('Jacket / stand collar.'+side,vv,[(0,1,2,3)],white,'05_JACKET','spine.02',sub=1)
    so=ob.modifiers.new('Collar thickness','SOLIDIFY');so.thickness=.006
    curve('Collar topstitch.'+side,[vv[0],vv[3],vv[2],vv[1]],.0008,seam,'05_JACKET','spine.02')
    torus('Collar eyelet.'+side,(s*.102,-.088,1.429),.004,.001,gold,'08_HARDWARE','spine.02')
    # Drawcord channel follows the open-front panel.
    pts=[(s*.131,-.105,1.434),(s*.143,-.115,1.342),(s*.130,-.119,1.235),(s*.126,-.118,1.161)]
    curve('Hood / drawcord.'+side,pts,.0023,yellow,'08_HARDWARE','spine.02')
    curve('Hood / cord loop.'+side,[(s*.126,-.118,1.187),(s*.134,-.124,1.153),(s*.128,-.125,1.143),(s*.122,-.121,1.160)],.0019,lime,'08_HARDWARE','spine.02')
    cube('Hood / metal aglet.'+side,(s*.128,-.125,1.148),(.0045,.0045,.017),gold,'08_HARDWARE','spine.02',.001)
# Hood drapes behind shoulders: shell has a shaped V-bottom and a separate dark inner rim.
hv=[];hf=[];nu=40;nv=16
for j in range(nv+1):
    u=j/nv
    for i in range(nu+1):
        t=-pi/2+pi*i/nu;x=.178*sin(t)*(1-.48*u)
        y=.045+.107*cos(t)+.021*sin(u*pi)
        z=1.484-.250*u*(cos(t)**.6)-.025*abs(sin(t))
        hv.append((x,y,z))
for j in range(nv):
    for i in range(nu):
        a=j*(nu+1)+i;hf.append((a,a+1,a+nu+2,a+nu+1))
ob=mesh('Hood / draped back shell',hv,hf,white,'05_JACKET','spine.02',sub=1)
ob.data.materials.append(lining);so=ob.modifiers.new('Hood lining thickness','SOLIDIFY');so.thickness=.007;so.material_offset=1
curve('Hood / rolled rim',[hv[i] for i in range(nu+1)],.005,white,'05_JACKET','spine.02')
stitch_line('Hood / center back seam',[(0,.153,1.482),(0,.174,1.37),(0,.153,1.24)])
stitch_line('Hood / lower rim',[hv[nv*(nu+1)+i] for i in range(nu+1)],radius=.0009)
# Single left sleeve patch, no duplicate patch on the right sleeve.
patch=cube('LEFT sleeve / woven green tab',(.268,-.062,1.324),(.026,.006,.057),lime,'05_JACKET','arm.L',.002)
patch.rotation_euler.y=-.32
stitch_line('LEFT sleeve patch / inner stitch',[(.257,-.066,1.347),(.252,-.066,1.304),(.274,-.066,1.300),(.281,-.066,1.342)],material=olive,bone='arm.L',radius=.0005)
# Grid print: slight film thickness, designed on the left front lower panel.
tiles=[('W',lining),('A',olive),('O',yellow),('◁',lime),('R',yellow),('▷',lime),('D',yellow),('L',lime),('E',yellow)]
for row in range(3):
    for col in range(3):
        char,ma=tiles[row*3+col];x=.107+col*.027;z=.997-row*.028
        cube('LEFT hem / print tile %d%d'%(row,col),(x,-.115,z),(.025,.0011,.025),ma,'05_JACKET','spine.01',.0018)
        text('LEFT hem / glyph %d%d'%(row,col),char,(x,-.1162,z),.019,white if ma in [lining,olive,lime] else lining,'05_JACKET','spine.01')

# HAIR: directional, individually editable tapered clumps and fine surface ridges.
# Cap has a raised front hairline, lower nape, and a non-spherical crown silhouette.
vs=[];fs=[];nr=22;nt=80
for j in range(nr+1):
    for i in range(nt):
        t=2*pi*i/nt
        end=1.68+.40*sin(t)  # front(-Y) above the eyes; nape lower.
        p=.025+(end-.025)*j/nr
        r=1+.022*cos(t*7+p*3)
        vs.append((.135*sin(p)*cos(t)*r,.024+.117*sin(p)*sin(t)*r,1.664+.151*cos(p)))
for j in range(nr):
    for i in range(nt):
        a=j*nt+i;b=j*nt+(i+1)%nt;fs.append((a,b,b+nt,a+nt))
mesh('Hair / fitted crown cap',vs,fs,hair,'03_HAIR','head',sub=1)
# Crown-to-fringe locks, with selected gray layers and chartreuse underlights.
bangs=[(-.114,1.612,.022),(-.090,1.648,.029),(-.064,1.673,.028),(-.034,1.676,.031),(-.003,1.679,.032),(.027,1.666,.028),(.055,1.676,.026),(.087,1.623,.025),(.112,1.565,.019)]
for i,(endx,endz,w) in enumerate(bangs):
    pts=[(endx*.24,-.018,1.812),(endx*.68,-.087,1.778),(endx*.95,-.119,1.715),(endx,-.112,endz)]
    ma=[hair2,hair,hair3,hair2,hair,hair2,hair,hair2,hair][i]
    sweep('Hair / fringe lock %02d'%i,pts,[.009,w*.80,w,w*.035],[.006,.010,.009,.001],ma,'03_HAIR','head',sides=14,steps=8)
    curve('Hair / fringe ridge %02d'%i,[(endx*.35,-.041,1.804),(endx*.73,-.100,1.767),(endx*.96,-.129,1.714),(endx,-.114,endz+.012)],.00065,hair3 if i%2 else hair2,'03_HAIR','head',res=1)
# Original asymmetrical lime face framing strands.
for s,side in [(1,'L'),(-1,'R')]:
    ex=s*(.101 if s==1 else .100);ez=1.534 if s==1 else 1.620
    pts=[(s*.079,-.054,1.789),(s*.105,-.103,1.734),(s*.101,-.120,1.652),(ex,-.091,ez)]
    sweep('Hair / lime face framing.'+side,pts,[.003,.009,.011,.0007],[.002,.004,.004,.0005],lime,'03_HAIR','head',sides=10,steps=8)
    sweep('Hair / lime glint.'+side,[(s*.085,-.059,1.784),(s*.106,-.108,1.731),(s*.104,-.124,1.650),(ex,-.094,ez+.009)],[.001,.0022,.002,.0003],[.001,.001,.001,.0002],lime_light,'03_HAIR','head',sides=8)
# Layered sides; lower locks curve away from cheeks.
for s,side in [(1,'L'),(-1,'R')]:
    for i in range(7):
        a=i/6;root=(s*(.057+.034*a),.024+.048*a,1.795-.025*a)
        tip=(s*(.123+.038*sin(a*pi)),.010+.13*a,1.550-.060*a)
        pts=[root,(s*(.123+.010*a),.012+.10*a,1.710),(s*(.143+.015*a),.010+.11*a,1.612),tip]
        sweep('Hair / side layer %02d.%s'%(i,side),pts,[.006,.022,.025,.0007],[.005,.010,.010,.0005],[hair,hair2,hair3][i%3],'03_HAIR','head',sides=12,steps=7)
    # Long back sections fall around the hood instead of through its center.
    for i in range(9):
        a=i/8;x=s*(.062+.084*a)
        pts=[(s*.072,.104,1.726),(s*(.106+.04*a),.139+.015*a,1.565),(s*(.136+.037*a),.175+.014*a,1.408),(s*(.139+.041*a),.157+.014*a,1.245),(s*(.130+.052*a),.117+.015*a,1.142+.088*sin(a*pi))]
        sweep('Hair / long back lock %02d.%s'%(i,side),pts,[.010,.019,.021,.017,.0008],[.006,.010,.010,.007,.0005],[hair,hair2,hair,hair3][i%4],'03_HAIR','hair.'+side,sides=12,steps=8)
        if i%2==0:
            curve('Hair / back filament %02d.%s'%(i,side),[(p[0]+s*.004,p[1]+.008,p[2]-.006) for p in pts[1:]],.0007,hair3,'03_HAIR','hair.'+side,res=1)
# Rear crown clumps and subtle tufts.
for i in range(13):
    a=pi*i/12;x=.116*cos(a);y=.024+.104*sin(a)
    pts=[(x*.3,.028+y*.25,1.814),(x*.88,y*.86,1.750),(x*1.10,y*1.04,1.662),(x*1.08+.009*sin(i),y,1.590+.020*sin(i*2))]
    sweep('Hair / occipital layer %02d'%i,pts,[.008,.024,.025,.001],[.005,.009,.010,.001],[hair,hair2,hair3][i%3],'03_HAIR','head',sides=12,steps=7)
# Two small golden crossed clips on the character's left fringe.
for z in [1.734,1.715]:
    curve('Hairpin / crossed A',[(.066,-.116,z+.008),(.081,-.112,z-.007)],.0014,gold,'08_HARDWARE','head')
    curve('Hairpin / crossed B',[(.066,-.116,z-.007),(.081,-.112,z+.008)],.0014,gold,'08_HARDWARE','head')
# Green side ribbon tied at left rear. Actual broad cloth loops, not thin wires.
uv_sphere('Ribbon / knot',(.133,.099,1.648),(.014,.012,.013),lime,'08_HARDWARE','head')
strip('Ribbon / outer loop',[(.135,.102,1.653),(.168,.098,1.668),(.188,.100,1.646),(.160,.108,1.638),(.136,.103,1.647)],.013,lime,'08_HARDWARE','head')
strip('Ribbon / inner loop',[(.133,.108,1.651),(.151,.137,1.670),(.165,.140,1.641),(.137,.110,1.647)],.012,olive,'08_HARDWARE','head')
strip('Ribbon / long tail',[(.137,.105,1.642),(.158,.118,1.602),(.183,.119,1.574),(.207,.103,1.577)],.018,lime,'08_HARDWARE','head')
strip('Ribbon / inner tail',[(.132,.108,1.643),(.148,.131,1.597),(.169,.128,1.571)],.014,lime_light,'08_HARDWARE','head')
curve('Ribbon / stitched edge',[(.141,.101,1.640),(.162,.113,1.605),(.188,.114,1.578),(.205,.102,1.580)],.0006,olive,'08_HARDWARE','head',res=1)

# SHOES: shaped lasted uppers, toe caps, separate cupsoles, individual laces and eyelets.
def shoe_ring(name,s,rings,material):
    vs=[];fs=[];n=64
    for z,w,length,cy in rings:
        for i in range(n):
            t=2*pi*i/n
            # Superellipse gives a rounded rectangular sneaker last.
            x=w*math.copysign(abs(cos(t))**.72,cos(t))
            y=length*math.copysign(abs(sin(t))**.82,sin(t))+cy
            vs.append((s*.108+x,y,z))
    for j in range(len(rings)-1):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
    fs.append(tuple(reversed(range(n))));fs.append(tuple((len(rings)-1)*n+i for i in range(n)))
    return mesh(name,vs,fs,material,'07_SHOES','foot.'+('L' if s==1 else 'R'),sub=1)
for s,side in [(1,'L'),(-1,'R')]:
    shoe_ring('Shoe / dark outsole.'+side,s,[(.022,.064,.137,-.047),(.031,.067,.141,-.047),(.043,.067,.141,-.047)],sole_dark)
    shoe_ring('Shoe / layered cupsole.'+side,s,[(.035,.066,.141,-.047),(.043,.068,.142,-.047),(.071,.067,.140,-.047),(.078,.064,.137,-.047)],rubber)
    shoe_ring('Shoe / stitched leather upper.'+side,s,[(.070,.063,.135,-.047),(.081,.064,.134,-.047),(.109,.060,.127,-.039),(.140,.051,.107,-.016),(.181,.044,.062,.022),(.208,.039,.048,.025)],shoe)
    # Collar socket and padded rim; trouser cuff overlaps top, leaving no floating gap.
    ring_mesh('Shoe / dark collar inset.'+side,[(s*.108,.026,.196,.036,.044),(s*.108,.026,.211,.039,.047)],lining,'07_SHOES','foot.'+side,n=48,sub=1)
    curve('Shoe / collar piping.'+side,[(s*.108+.041*cos(t),.025+.050*sin(t),.205+.006*sin(t)) for t in [2*pi*i/40 for i in range(40)]],.004,shoe,'07_SHOES','foot.'+side,closed=True)
    # Tongue lays along the sloping instep.
    sweep('Shoe / padded tongue.'+side,[(s*.108,-.135,.113),(s*.108,-.077,.151),(s*.108,-.010,.199),(s*.108,.004,.220)],[.030,.030,.028,.023],[.006,.007,.007,.004],shoe,'07_SHOES','foot.'+side,sides=16,steps=5)
    # Toe seam in a U around the vamp.
    toe=[]
    for i in range(33):
        a=pi+pi*i/32;toe.append((s*.108+.053*cos(a),-.069+.079*sin(a),.114-.018*abs(sin(a))))
    curve('Shoe / toe cap seam.'+side,toe,.0012,seam,'07_SHOES','foot.'+side,res=1)
    curve('Shoe / cupsole stitch.'+side,[(s*.108+.067*cos(t),-.047+.141*sin(t),.060) for t in [2*pi*i/64 for i in range(64)]],.0008,seam,'07_SHOES','foot.'+side,closed=True,res=1)
    # Both eyelet rows: six actual metal rings each, with cris-cross laces.
    for i in range(6):
        y=-.118+i*.020;z=.125+i*.0130;w=.025-i*.0009
        for e in [-1,1]:
            torus('Shoe eyelet %d %s.%s'%(i,e,side),(s*.108+e*w,y,z),.003,.00075,gold,'07_SHOES','foot.'+side,rotation=(.65,0,0))
        if i<5:
            for e in [-1,1]:
                curve('Lace crossing %d %s.%s'%(i,e,side),[(s*.108+e*w,y-.002,z+.002),(s*.108,y+.011,z+.013),(s*.108-e*(w-.0009),y+.020,z+.015)],.0017,lime_light if (i+e)%2 else yellow,'07_SHOES','foot.'+side)
    cx=s*.108
    curve('Lace bow left.'+side,[(cx,-.011,.208),(cx-.024,-.024,.218),(cx-.030,-.007,.213),(cx,-.011,.208)],.0018,lime,'07_SHOES','foot.'+side)
    curve('Lace bow right.'+side,[(cx,-.011,.208),(cx+.024,-.026,.218),(cx+.030,-.006,.214),(cx,-.011,.208)],.0018,yellow,'07_SHOES','foot.'+side)
    for e in [-1,1]:
        curve('Lace loose end %s.%s'%(e,side),[(cx,-.011,.208),(cx+e*.012,-.034,.186),(cx+e*.018,-.043,.175)],.0017,lime,'07_SHOES','foot.'+side)
        cube('Lace aglet %s.%s'%(e,side),(cx+e*.018,-.043,.174),(.003,.003,.007),gold,'07_SHOES','foot.'+side,.0007)
    # Quarter panel seam, heel tab and fine outsole tread blocks.
    for e in [-1,1]:
        curve('Shoe / quarter seam %s.%s'%(e,side),[(cx+e*.044,.074,.184),(cx+e*.056,.018,.122),(cx+e*.060,-.062,.093)],.0010,seam,'07_SHOES','foot.'+side,res=1)
    cube('Shoe / chartreuse heel tab.'+side,(cx,.081,.171),(.027,.009,.028),lime,'07_SHOES','foot.'+side,.003)
    for row in range(9):
        for col in [-1,1]:
            cube('Outsole tread %d %s.%s'%(row,col,side),(cx+col*.030,-.15+row*.028,.021),(.041,.017,.006),rubber,'07_SHOES','foot.'+side,.002)

# Final silhouette corrections: continuous cloth rather than tube-shaped folds,
# an appropriately short anime neck, and laces on top of the leather surface.
for ob in list(PARTS):
    if ob.name.startswith(('T-shirt / gathered fold','Pooled cuff fold','Knee tension fold')):
        PARTS.remove(ob);bpy.data.objects.remove(ob,do_unlink=True);continue
    if any(c.name in {'02_FACE','03_HAIR'} for c in ob.users_collection) or ob.name.startswith(('Head /','Ear.','Hairpin','Ribbon /')):
        ob.location.z-=.035
    if ob.name.startswith(('Lace','Shoe eyelet')):ob.location.z+=.027
    if ob.name.startswith('Shoe / padded tongue'):ob.location.z+=.025

# Pack an actual tileable micro-weave normal map; glTF gets the same PBR maps.
import numpy as np
N=256;yy,xx=np.mgrid[:N,:N]
height=(np.sin(xx*2*pi/16)*np.cos(yy*2*pi/16)*.28+np.sin(xx*2*pi/4)*.035+np.cos(yy*2*pi/4)*.035)
gx=np.roll(height,-1,1)-np.roll(height,1,1);gy=np.roll(height,-1,0)-np.roll(height,1,0)
arr=np.empty((N,N,4),dtype=np.float32);arr[:,:,0]=.5-gx*.20;arr[:,:,1]=.5-gy*.20;arr[:,:,2]=1;arr[:,:,3]=1
texdir=OUT/'textures';texdir.mkdir(exist_ok=True)
im=bpy.data.images.new('Tailored fabric • micro weave',width=N,height=N,alpha=True)
im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(arr.reshape(-1));im.filepath_raw=str(texdir/'fabric_weave_normal.png');im.file_format='PNG';im.save();im.pack()
for material,strength in [(white,.045),(black,.08),(pants,.08),(pants_hi,.075),(lining,.08)]:
    nodes=material.node_tree.nodes;links=material.node_tree.links
    tc=nodes.new('ShaderNodeTexCoord');mp=nodes.new('ShaderNodeMapping');mp.inputs['Scale'].default_value=(12,12,12)
    ti=nodes.new('ShaderNodeTexImage');ti.image=im;ti.extension='REPEAT'
    no=nodes.new('ShaderNodeNormalMap');no.inputs['Strength'].default_value=strength
    links.new(tc.outputs['UV'],mp.inputs['Vector']);links.new(mp.outputs['Vector'],ti.inputs['Vector']);links.new(ti.outputs['Color'],no.inputs['Color']);links.new(no.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])

# Convert seam/font geometry to real meshes for both rigging and FBX portability.
bpy.ops.object.select_all(action='DESELECT')
for ob in PARTS:
    if ob.type in {'CURVE','FONT'}:ob.select_set(True)
if bpy.context.selected_objects:
    bpy.context.view_layer.objects.active=bpy.context.selected_objects[0];bpy.ops.object.convert(target='MESH')
PARTS=[ob for c in COLS.values() if c.name!='10_STUDIO' for ob in c.objects if ob.type=='MESH']
for ob in PARTS:
    if not ob.data.uv_layers:
        uv=ob.data.uv_layers.new(name='UVMap')
        for poly in ob.data.polygons:
            n=poly.normal;axis=max(range(3),key=lambda i:abs(n[i]))
            axes=[i for i in range(3) if i!=axis]
            for li in poly.loop_indices:
                v=ob.matrix_world @ ob.data.vertices[ob.data.loops[li].vertex_index].co
                uv.data[li].uv=(v[axes[0]],v[axes[1]])

# BASIC DEFORMATION RIG. Smooth blends on sleeves, knees, torso and rear hair.
armdata=bpy.data.armatures.new('Xiaoxiaomeng • deformation skeleton')
rig=bpy.data.objects.new('RIG • Xiaoxiaomeng',armdata);COLS['09_RIG'].objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
def bone(name,head,tail,parent=None):
    b=armdata.edit_bones.new(name);b.head=head;b.tail=tail
    if parent:b.parent=armdata.edit_bones[parent]
bone('root',(0,0,.02),(0,0,.18))
bone('pelvis',(0,0,.89),(0,0,1.035),'root')
bone('spine.01',(0,0,1.035),(0,0,1.20),'pelvis')
bone('spine.02',(0,0,1.20),(0,0,1.385),'spine.01')
bone('neck',(0,0,1.385),(0,.012,1.475),'spine.02')
bone('head',(0,.012,1.475),(0,.023,1.735),'neck')
for s,side in [(1,'L'),(-1,'R')]:
    bone('clavicle.'+side,(s*.035,0,1.36),(s*.177,0,1.357),'spine.02')
    bone('arm.'+side,(s*.177,0,1.357),(s*.307,-.004,1.166),'clavicle.'+side)
    bone('forearm.'+side,(s*.307,-.004,1.166),(s*.427,-.010,.947),'arm.'+side)
    bone('hand.'+side,(s*.427,-.010,.947),(s*.451,-.01,.900),'forearm.'+side)
    for i,off in enumerate([-.023,-.008,.008,.023]):
        x=s*(.45+off);length=[.052,.066,.062,.047][i]
        bone('finger%d.%s'%(i+1,side),(x,-.009,.903),(x+s*off*.65,-.015,.902-length),'hand.'+side)
    bone('thumb.'+side,(s*.43,-.008,.935),(s*.404,-.023,.895),'hand.'+side)
    bone('leg.'+side,(s*.108,0,.94),(s*.108,.018,.56),'pelvis')
    bone('shin.'+side,(s*.108,.018,.56),(s*.108,.026,.21),'leg.'+side)
    bone('foot.'+side,(s*.108,.026,.21),(s*.108,-.14,.09),'shin.'+side)
    bone('hair.'+side,(s*.11,.13,1.555),(s*.15,.17,1.305),'head')
    bone('hair.tip.'+side,(s*.15,.17,1.305),(s*.16,.13,1.095),'hair.'+side)
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
rig['notes']='Basic FK deformation skeleton. No facial blendshapes, IK controls, physics, or production animation certification.'
def clamp(x):return max(0,min(1,x))
for ob in PARTS:
    name=ob.get('rig_bone','spine.02');groups={}
    def add(n,index,weight):
        if weight<=.00001:return
        if n not in groups:groups[n]=ob.vertex_groups.new(name=n)
        groups[n].add([index],weight,'REPLACE')
    for v in ob.data.vertices:
        p=ob.matrix_world@v.co;z=p.z
        if name.startswith('leg.'):
            side=name[-1];w=clamp((z-.49)/.14)
            add('leg.'+side,v.index,w);add('shin.'+side,v.index,1-w)
        elif name.startswith('arm.'):
            side=name[-1];w=clamp((z-1.09)/.15)
            add('arm.'+side,v.index,w);add('forearm.'+side,v.index,1-w)
        elif name.startswith('hair.'):
            side=name[-1];w=clamp((z-1.25)/.18)
            add('hair.'+side,v.index,w);add('hair.tip.'+side,v.index,1-w)
        elif name in ['spine.01','spine.02']:
            w=clamp((z-1.03)/.20);add('spine.02',v.index,w);add('spine.01',v.index,1-w)
        else:add(name,v.index,1)
    mod=ob.modifiers.new('Basic FK deformation','ARMATURE');mod.object=rig
    ob.parent=rig

runpy.run_path(str(ROOT/'tools'/'refine_cloth.py'))

# Studio, camera and soft portrait lighting remain editable in the .blend file.
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False
scene.render.resolution_x=1400;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.color=(.35,.35,.35)
world=scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.40,.43,.39,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.view_settings.view_transform='AgX'
studio_mat=mat('Studio • warm mist',(.32,.35,.30),.84)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.012));move(bpy.context.object,'10_STUDIO',studio_mat);bpy.context.object.name='Studio ground / not exported'
def area(name,loc,power,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    ob=bpy.data.objects.new(name,d);COLS['10_STUDIO'].objects.link(ob);ob.location=loc
    ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
area('Key / large softbox',(-3,-4,5),450,4,(1,.94,.82))
area('Fill / broad cool',(3,-2,3),300,3,(.79,.87,1))
area('Rim / hair separator',(1,3,4),650,3,(.87,1,.74))
camd=bpy.data.cameras.new('Portrait camera');cam=bpy.data.objects.new('Portrait camera',camd);COLS['10_STUDIO'].objects.link(cam);scene.camera=cam;camd.type='ORTHO';camd.ortho_scale=2.10
def view(loc,target=(0,0,.94)):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
view((2.7,-6,2.55))
scene['character']='小小萌 / Xiao Xiao Meng'
scene['reference']='Original character and supplied model sheet, Susuny001. Hidden surfaces are interpreted design extensions.'
scene['delivery']='Layered stylized model, UVs, packed fabric normal map, basic FK rig. Not a hand-sculpted likeness or animation-ready facial rig.'
# Keep references in the native project, packed, without exporting image planes.
ref=ROOT/'assets'/'xiaoxiaomeng-character-model-sheet.png'
if ref.exists():
    img=bpy.data.images.load(str(ref),check_existing=True);img.pack()

# Portable export selections exclude studio props and reference.
bpy.ops.object.select_all(action='DESELECT')
for ob in PARTS:ob.select_set(True)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'xiaoxiaomeng.blend'),compress=True)
runpy.run_path(str(ROOT/'tools'/'export_character.py'))

# Render three camera angles plus a close face image for visual validation.
for name,loc,target,scale in ([] if '--no-render' in sys.argv else [
    ('beauty',(2.7,-6,2.55),(0,0,.94),2.1),
    ('front',(0,-6,1.15),(0,0,.94),2.02),
    ('back',(-2.6,6,2.3),(0,0,.94),2.1),
    ('face',(.55,-4,1.86),(0,0,1.645),.54),
]):
    view(loc,target);camd.ortho_scale=scale;scene.render.filepath=str(RENDERS/(name+'.png'))
    if name=='face':scene.render.resolution_x=1200;scene.render.resolution_y=1200
    bpy.ops.render.render(write_still=True)
# Open the blend with an attractive useful camera, not the last detail view.
view((2.7,-6,2.55));camd.ortho_scale=2.1
scene.render.resolution_x=1400;scene.render.resolution_y=1600
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
runpy.run_path(str(ROOT/'tools'/'prepare_blend.py'))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'xiaoxiaomeng.blend'),compress=True)
stats={'name':'小小萌','version':'1.0.0','units':'metres','mesh_objects':len(PARTS),'base_vertices':sum(len(o.data.vertices) for o in PARTS),'base_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in PARTS),'bones':len(armdata.bones),'materials':len(MATS),'formats':['glb','fbx','blend'],'rig':'basic FK, no face shapes or physics','reference':'assets/xiaoxiaomeng-character-model-sheet.png'}
(OUT/'manifest.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
print('CHARACTER_BUILD_COMPLETE',json.dumps(stats,ensure_ascii=False))
