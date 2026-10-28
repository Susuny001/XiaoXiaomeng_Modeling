"""Remove construction vertices left inside garment and orbital openings."""
import bpy,bmesh
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(ob.data);loose=[v for v in bm.verts if not v.link_faces]
 if loose:
  bmesh.ops.delete(bm,geom=loose,context='VERTS');bm.to_mesh(ob.data)
  print('Construction vertices removed:',ob.name,len(loose))
 bm.free()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
