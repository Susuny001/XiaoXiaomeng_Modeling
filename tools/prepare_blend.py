"""Frame the editable character on opening Blender; studio stays renderable."""
import bpy,sys
from mathutils import Vector
from pathlib import Path
scene=bpy.context.scene
for ob in bpy.data.objects:
 if any(c.name=='10_STUDIO' for c in ob.users_collection):
  ob.hide_set(True);ob.hide_select=True
 if ob.type=='ARMATURE':ob.show_in_front=False
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   space=area.spaces.active;space.clip_start=.01;space.clip_end=100
   space.shading.type='SOLID';space.shading.color_type='MATERIAL';space.shading.show_shadows=True;space.shading.show_cavity=True
   space.overlay.show_floor=False
   r=space.region_3d;r.view_location=Vector((0,0,.94));r.view_distance=2.9;r.view_perspective='PERSP'
   r.view_rotation=scene.camera.rotation_euler.to_quaternion()
if '--save-layout' in sys.argv:
 path=Path(__file__).resolve().parents[1]/'models'/'xiaoxiaomeng.blend'
 bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
