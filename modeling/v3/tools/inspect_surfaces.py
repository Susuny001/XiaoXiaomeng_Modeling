"""Inspect connected garment/anatomy control surfaces; not visual approval."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reports=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or not ob.name.startswith(('Jacket /','Trousers /','Hand /')):continue
 data=ob.data;adj=[[] for _ in data.vertices]
 for e in data.edges:
  a,b=e.vertices;adj[a].append(b);adj[b].append(a)
 seen=set();components=[]
 for v in data.vertices:
  if v.index in seen:continue
  todo=[v.index];seen.add(v.index);count=0
  while todo:
   a=todo.pop();count+=1
   for b in adj[a]:
    if b not in seen:seen.add(b);todo.append(b)
  components.append(count)
 used={vi for p in data.polygons for vi in p.vertices}
 reports.append({'name':ob.name,'vertices':len(data.vertices),'polygons':len(data.polygons),'quad_fraction':sum(len(p.vertices)==4 for p in data.polygons)/len(data.polygons),'connected_components':len(components),'isolated_vertices':len(data.vertices)-len(used),'component_sizes':components})
 assert len(components)==1,(ob.name,components)
 assert len(used)==len(data.vertices),(ob.name,'unused control vertices')
(ROOT/'models'/'surface-inspection.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
print('CONTROL_SURFACE_INSPECTION',json.dumps(reports,ensure_ascii=False))
