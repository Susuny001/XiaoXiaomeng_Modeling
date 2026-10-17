"""Round-trip acceptance test, executed with Blender background Python."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
reports=[]
for fmt in ['blend','glb','fbx']:
 if fmt=='blend':bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models'/'xiaoxiaomeng.blend'))
 else:
  bpy.ops.wm.read_factory_settings(use_empty=True)
  if fmt=='glb':bpy.ops.import_scene.gltf(filepath=str(ROOT/'models'/'xiaoxiaomeng.glb'))
  else:bpy.ops.import_scene.fbx(filepath=str(ROOT/'models'/'xiaoxiaomeng.fbx'))
 rigs=[ob for ob in bpy.context.scene.objects if ob.type=='ARMATURE']
 # Blender glTF importer creates a 2m Icosphere in glTF_not_exported for
 # pose-bone custom shapes. It is a UI widget, not a model mesh in the GLB.
 widgets={b.custom_shape for rig in rigs for b in rig.pose.bones if b.custom_shape}
 meshes=[ob for ob in bpy.context.scene.objects if ob.type=='MESH' and ob not in widgets and not ob.get('skip_export') and not any(c.name=='10_STUDIO' for c in ob.users_collection)]
 assert len(meshes)>300,(fmt,len(meshes))
 assert len(rigs)==1 and len(rigs[0].data.bones)>=30,(fmt,len(rigs))
 corners=[ob.matrix_world@Vector(corner) for ob in meshes for corner in ob.bound_box]
 size=[max(v[a] for v in corners)-min(v[a] for v in corners) for a in range(3)]
 assert .8<size[0]<1.2 and .15<size[1]<.6 and 1.7<size[2]<1.95,(fmt,size)
 assert all(math.isfinite(c) for v in corners for c in v)
 weights=sum(bool(ob.vertex_groups) for ob in meshes)
 assert weights==len(meshes),(fmt,weights,len(meshes))
 rig=rigs[0];knee=rig.pose.bones['shin.L'];knee.rotation_mode='XYZ'
 target=next(ob for ob in meshes if ob.name.startswith('Trouser leg') and ob.name.endswith('.L'))
 deps=bpy.context.evaluated_depsgraph_get()
 baseline=[v.co.copy() for v in target.evaluated_get(deps).data.vertices]
 knee.rotation_euler.x=.15;bpy.context.view_layer.update()
 changed=[v.co.copy() for v in target.evaluated_get(deps).data.vertices]
 displacement=max((a-b).length for a,b in zip(baseline,changed))
 assert displacement>.01,(fmt,'rig did not deform',displacement)
 knee.rotation_euler.x=0
 reports.append({'format':fmt,'passed':True,'mesh_objects':len(meshes),'bones':len(rig.data.bones),'bounds_metres':size,'weighted_meshes':weights,'knee_pose_displacement_metres':displacement})
(ROOT/'models'/'roundtrip-validation.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
print('ROUNDTRIP_VALIDATION_PASSED',json.dumps(reports))
