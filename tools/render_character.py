"""Re-render an existing project without repeating geometry creation/export."""
import bpy,json,runpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
scene=bpy.context.scene;cam=scene.camera;scene.render.engine='CYCLES'
scene.cycles.samples=48;scene.cycles.use_denoising=False
for name,loc,target,scale in [
 ('beauty',(2.7,-6,2.55),(0,0,.94),2.1),
 ('front',(0,-6,1.15),(0,0,.94),2.02),
 ('back',(-2.6,6,2.3),(0,0,.94),2.1),
 ('face',(.55,-4,1.86),(0,0,1.645),.54),
]:
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 scene.render.resolution_x=1100 if name=='face' else (1400 if name=='beauty' else 1050)
 scene.render.resolution_y=1100 if name=='face' else (1600 if name=='beauty' else 1200)
 scene.cycles.samples=64 if name=='face' else (48 if name=='beauty' else 32)
 scene.render.filepath=str(ROOT/'renders'/(name+'.png'));bpy.ops.render.render(write_still=True)
cam.location=(2.7,-6,2.55);cam.rotation_euler=(Vector((0,0,.94))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.1
scene.render.resolution_x=1400;scene.render.resolution_y=1600
runpy.run_path(str(ROOT/'tools'/'prepare_blend.py'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models'/'xiaoxiaomeng.blend'),compress=True)
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not any(c.name=='10_STUDIO' for c in o.users_collection)]
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
stats={'name':'小小萌','version':'1.0.0','units':'metres','mesh_objects':len(meshes),'base_vertices':sum(len(o.data.vertices) for o in meshes),'base_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'bones':len(rig.data.bones),'materials':len(bpy.data.materials),'formats':['glb','fbx','blend'],'rig':'basic FK, no face shapes or physics','reference':'assets/xiaoxiaomeng-character-model-sheet.png'}
(ROOT/'models'/'manifest.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
print('RENDER_COMPLETE',json.dumps(stats,ensure_ascii=False))
