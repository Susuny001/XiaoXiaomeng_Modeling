"""Continuous cloth folds, preserved as editable quad geometry and subdivision."""
import bpy,math
from pathlib import Path
from math import sin,cos,atan2,exp,pi
for ob in list(bpy.data.objects):
 if ob.name.startswith('Outer seam.'):
  ob.hide_render=True;ob.hide_viewport=True;ob['skip_export']=True
 if not ob.name.startswith('Trouser leg /') or ob.get('cloth_refined'):continue
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 sub=next(m for m in ob.modifiers if m.type=='SUBSURF');sub.levels=2
 bpy.ops.object.modifier_apply(modifier=sub.name)
 sign=1 if ob.name.endswith('.L') else -1
 for v in ob.data.vertices:
  x,y,z=v.co;cx=sign*(.103+.014*sin(z*6));cy=.012+.012*exp(-((z-.54)/.09)**4)
  dx=x-cx;dy=y-cy;t=atan2(dy,dx)
  ankle=exp(-((z-.275)/.074)**2);knee=exp(-((z-.56)/.072)**2)
  wave=.115*ankle*sin(z*145+2.2*t)+.050*knee*sin(z*103-1.8*t)+.016*exp(-((z-.78)/.14)**2)*sin(z*54+3*t)
  v.co.x=cx+dx*(1+wave);v.co.y=cy+dy*(1+wave)
 sub=ob.modifiers.new('Soft sculpted cloth / subdivision','SUBSURF');sub.levels=1;sub.render_levels=1
 bpy.ops.object.modifier_move_up(modifier=sub.name)
 ob['cloth_refined']=True
if '--save-refinement' in __import__('sys').argv:
 root=Path(__file__).resolve().parents[1]
 bpy.ops.wm.save_as_mainfile(filepath=str(root/'models'/'xiaoxiaomeng.blend'),compress=True)
print('CONTINUOUS_CLOTH_REFINEMENT_COMPLETE')
