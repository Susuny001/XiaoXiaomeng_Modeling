"""Real mesh toon review: controlled normal ramps and inverted-hull outlines.
Uses native painted eye surfaces and real garment geometry, no image card.
"""
import bpy,bmesh,math,hashlib,json,shutil
from datetime import datetime,timezone
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for directory in ('models','renders','previews'):
 (ROOT/directory).mkdir(parents=True,exist_ok=True)
def srgb(h):
 c=[int(h[i:i+2],16)/255 for i in [0,2,4]]
 return [x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in c]
def toon(name,base,shade):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*srgb(base),1)
 n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 geom=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(-.27,-.80,.53)
 l.new(geom.outputs['Normal'],dot.inputs[0]);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE'
 ramp.color_ramp.elements[0].position=.35;ramp.color_ramp.elements[0].color=(*srgb(shade),1)
 ramp.color_ramp.elements[1].position=.66;ramp.color_ramp.elements[1].color=(*srgb(base),1)
 l.new(dot.outputs['Value'],ramp.inputs[0]);e=n.new('ShaderNodeEmission');l.new(ramp.outputs['Color'],e.inputs['Color']);o=n.new('ShaderNodeOutputMaterial');l.new(e.outputs[0],o.inputs[0]);return m
SKIN=toon('Toon / porcelain','F4E0CD','DCBCA4');WHITE=toon('Toon / ivory nylon','F5F5F0','B9C1B8');BLACK=toon('Toon / canvas','424641','282D28')
HAIR=toon('Toon / graphite locks','555952','2C322C');HAIR2=toon('Toon / deeper hair','454A44','252B25');LIME=toon('Toon / lime','B4D833','748F22');GOLD=toon('Toon / gold','C4A531','84741F')
# Refine individual lock tips and their silhouette, preserving their root flow.
for ob in list(bpy.context.scene.objects):
 if ob.type!='MESH':continue
 if ob.name=='Fringe / right clipped plane':
  for v in ob.data.vertices:
   t=max(0,min(1,(1.75-v.co.z)/.18))**2;v.co.x+=.017*t;v.co.z+=.025*t
 if ob.name=='Fringe / left broad curved plane':
  for v in ob.data.vertices:
   t=max(0,min(1,(1.75-v.co.z)/.17))**2;v.co.x-=.007*t
 # Restore a compact hair mass instead of broad plate-like nape straps.
 if ob.name.startswith('Long rear /'):
  s=-1 if '.-' in ob.name or '/ -1' in ob.name else 1
  for v in ob.data.vertices:
   a=math.exp(-((v.co.z-1.31)/.18)**2);v.co.y+=.006*a;v.co.x+=s*.004*a
 name=ob.name
 if name.startswith('EYE surface'):
  old=ob.data.materials[0];image=next(n.image for n in old.node_tree.nodes if n.type=='TEX_IMAGE')
  eye=bpy.data.materials.new('Toon / painted eye');eye.use_nodes=True;ns=eye.node_tree.nodes;ns.clear();tx=ns.new('ShaderNodeTexImage');tx.image=image;em=ns.new('ShaderNodeEmission');out=ns.new('ShaderNodeOutputMaterial');eye.node_tree.links.new(tx.outputs['Color'],em.inputs['Color']);eye.node_tree.links.new(em.outputs[0],out.inputs[0]);ob.data.materials.clear();ob.data.materials.append(eye);continue
 if name.startswith(('Upper lashes','Brow /','Mouth closure','Nostril crease','Lower lid')):continue
 if any(c.name.startswith('HAIR') for c in ob.users_collection):
  ma=LIME if name.startswith(('Lime /','Ribbon /')) else GOLD if name.startswith('Hair clip') else HAIR2 if name.startswith(('Long rear','Occipital','Crown')) else HAIR
 elif name.startswith(('HEAD /','EAR /','NECK /','Hand /')):ma=SKIN
 elif name.startswith(('Trousers /','T-shirt /','RIGHT / cargo')):ma=BLACK
 elif name.startswith('RIGHT / long woven'):ma=LIME
 else:ma=WHITE
 ob.data.materials.clear();ob.data.materials.append(ma)
 if name.startswith(('Jacket /','Collar /','Hood /')):
  ob.data.materials.append(BLACK)
  for mod in ob.modifiers:
   if mod.type=='SOLIDIFY':mod.material_offset=1;mod.material_offset_rim=0
for ob in bpy.context.scene.objects:
 if ob.type=='CURVE':
  ob.data.materials.clear();ob.data.materials.append(GOLD)

# The exact supplied nine-tile motif is mapped only onto the garment panel.
# It remains a flat print; the rest of the jacket uses its own toon material.
ref_path=ROOT/'assets'/'character-sheet.png'
if not ref_path.exists():ref_path=ROOT.parents[1]/'assets'/'xiaoxiaomeng-character-model-sheet.png'
ref=bpy.data.images.get('Design reference') or bpy.data.images.load(str(ref_path));ref.name='Design reference';ref.pack()
mat=bpy.data.materials.new('Hem print / source motif');mat.use_nodes=True;ns=mat.node_tree.nodes;ns.clear();tx=ns.new('ShaderNodeTexImage');tx.image=ref;em=ns.new('ShaderNodeEmission');out=ns.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(tx.outputs['Color'],em.inputs[0]);mat.node_tree.links.new(em.outputs[0],out.inputs[0])
from mathutils.bvhtree import BVHTree
deps=bpy.context.evaluated_depsgraph_get()
jacket=next(o for o in bpy.context.scene.objects if o.name.startswith('Jacket /'))
jacket_eval=jacket.evaluated_get(deps);jacket_data=bpy.data.meshes.new_from_object(jacket_eval,depsgraph=deps)
tree=BVHTree.FromPolygons([jacket.matrix_world@v.co for v in jacket_data.vertices],[tuple(p.vertices) for p in jacket_data.polygons])
S=1.78/537;vs=[];fs=[];uvs=[];NU=10;NV=12
for j in range(NV+1):
 py=321+(376-321)*j/NV
 for i in range(NU+1):
  px=208+(250-208)*i/NU;x=(px-185)*S;z=(613-py)*S
  # Fit the print to the front surface of the flared left coat panel.
  rx=.21 if z<.91 else .18;dep=.117
  hit,normal,index,distance=tree.ray_cast(Vector((x,-2,z)),Vector((0,1,0)),4)
  y=hit.y-.0007 if hit is not None else -dep*math.sqrt(max(.05,1-(x/rx)**2))-.004
  vs.append((x,y,z));uvs.append((px/1086,1-py/1448))
for j in range(NV):
 for i in range(NU):a=j*(NU+1)+i;fs.append((a,a+1,a+NU+2,a+NU+1))
d=bpy.data.meshes.new('Hem print');d.from_pydata(vs,[],fs);d.materials.append(mat);ob=bpy.data.objects.new('Hem print / conforming ink',d);bpy.context.scene.collection.objects.link(ob)
uv=d.uv_layers.new(name='Print UV')
for loop in d.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
bpy.data.meshes.remove(jacket_data)

# Inverted hulls provide geometric outlines in the native camera render.
outline=bpy.data.materials.new('Outline / camera-facing cull');outline.use_nodes=True;ns=outline.node_tree.nodes;ns.clear();l=outline.node_tree.links
g=ns.new('ShaderNodeNewGeometry');e=ns.new('ShaderNodeEmission');e.inputs['Color'].default_value=(*srgb('282C27'),1);t=ns.new('ShaderNodeBsdfTransparent');mix=ns.new('ShaderNodeMixShader');l.new(e.outputs[0],mix.inputs[1]);l.new(t.outputs[0],mix.inputs[2]);l.new(g.outputs['Backfacing'],mix.inputs[0]);o=ns.new('ShaderNodeOutputMaterial');l.new(mix.outputs[0],o.inputs[0])
deps=bpy.context.evaluated_depsgraph_get()
snapshots=[]
for original in list(bpy.context.scene.objects):
 if original.type!='MESH' or original.name.startswith(('EYE','Upper lashes','Lower lid','Brow','Mouth','Nostril','Hem print')):continue
 evaluated=original.evaluated_get(deps);data=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=deps)
 snapshots.append((original.name,original.matrix_world.copy(),data,.0006 if any(c.name.startswith('HAIR') for c in original.users_collection) else .0008))
oc=bpy.data.collections.new('RENDER / silhouette outlines');bpy.context.scene.collection.children.link(oc)
for name,world,data,amount in snapshots:
 # Cache normals before changing coordinates; reading normals after each
 # coordinate edit would repeatedly invalidate and recompute the whole mesh.
 normals=[v.normal.copy() for v in data.vertices]
 for v,normal in zip(data.vertices,normals):v.co+=normal*amount
 bm=bmesh.new();bm.from_mesh(data);bmesh.ops.reverse_faces(bm,faces=bm.faces);bm.to_mesh(data);bm.free()
 data.materials.clear();data.materials.append(outline);ob=bpy.data.objects.new('Outline / '+name,data);oc.objects.link(ob);ob.matrix_world=world;ob['render_outline']=True
print('TOON_OUTLINE_GEOMETRY_READY',len(snapshots),flush=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.cycles.transparent_max_bounces=32
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.565,.565,.565,1)
for ob in scene.objects:
 if ob.type=='LIGHT':ob.hide_render=True
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=1.96
scene.render.resolution_x=900;scene.render.resolution_y=1100
for name,pos in [('toon-front',(0,-5,.90)),('toon-back',(0,5,.90)),('toon-quarter',(2.6,-5,1.20))]:
 cam.location=pos;cam.rotation_euler=(Vector((0,0,.90))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ROOT/'renders'/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models'/'character-toon-work.blend'),compress=True)

# Keep the README previews tied to the same native scene as this render run.
source=ROOT/'models'/'character-toon-work.blend'
snapshot={'renderer':'Blender '+bpy.app.version_string,'source':source.name,
          'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'rendered_at_utc':datetime.now(timezone.utc).isoformat(),
          'resolution':[scene.render.resolution_x,scene.render.resolution_y],'views':[]}
for view in ('front','quarter','back'):
 src=ROOT/'renders'/('toon-'+view+'.png');dst=ROOT/'previews'/(view+'.png')
 shutil.copy2(src,dst)
 snapshot['views'].append({'file':dst.name,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
(ROOT/'previews'/'snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('README_PREVIEWS_UPDATED',str(ROOT/'previews'),flush=True)
