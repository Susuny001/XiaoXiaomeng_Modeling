"""Portable exports from temporary baked copies; native quad meshes stay intact."""
import bpy,runpy
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
parts=[ob for ob in bpy.data.objects if ob.type=='MESH' and not ob.get('skip_export') and not any(c.name=='10_STUDIO' for c in ob.users_collection)]
rig=next(ob for ob in bpy.data.objects if ob.type=='ARMATURE')
export_col=bpy.data.collections.new('__PORTABLE_EXPORT__');bpy.context.scene.collection.children.link(export_col)
saved=[];copies=[]
bpy.ops.object.select_all(action='DESELECT')
for original in parts:
 name=original.name;world=original.matrix_world.copy()
 saved.append((original,name,original.hide_get(),original.hide_viewport))
 original.name='__NATIVE__'+name;original.hide_set(True);original.hide_viewport=True
 ob=original.copy();ob.data=original.data.copy();export_col.objects.link(ob)
 ob.name=name;ob.data.name=name;ob.hide_viewport=False;ob.hide_render=False;ob.hide_set(False)
 ob.data.transform(world);ob.parent=None;ob.matrix_world=Matrix.Identity(4)
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.show_viewport=False;mod.show_render=False
 copies.append(ob)
# Bake construction modifiers once, retaining interpolated vertex weights.
for ob in copies:
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 for mod in list(ob.modifiers):
  if mod.type!='ARMATURE':bpy.ops.object.modifier_apply(modifier=mod.name)
 tri=ob.modifiers.new('Portable triangulation','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
for ob in copies:
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.show_viewport=True;mod.show_render=True
bpy.ops.object.select_all(action='DESELECT')
for ob in copies:ob.select_set(True)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(ROOT/'models'/'xiaoxiaomeng.glb'),export_format='GLB',use_selection=True,export_apply=False,export_tangents=True,export_animations=False,export_skins=True,export_all_influences=False,export_def_bones=True,export_yup=True,export_materials='EXPORT',export_extras=True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/'models'/'xiaoxiaomeng.fbx'),use_selection=True,object_types={'MESH','ARMATURE'},use_mesh_modifiers=False,add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True,axis_forward='-Z',axis_up='Y',use_armature_deform_only=True)
for ob in copies:
 data=ob.data;bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(data)
bpy.data.collections.remove(export_col)
for ob,name,hidden,viewport_hidden in saved:
 ob.name=name;ob.hide_viewport=viewport_hidden;ob.hide_set(hidden)
runpy.run_path(str(ROOT/'tools'/'normalize_glb.py'))
print('PORTABLE_EXPORT_COMPLETE')
