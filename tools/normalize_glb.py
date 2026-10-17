"""Normalize exported tangent frames at UV poles, per glTF 2.0 requirements.

At a degenerate UV pole Blender can emit a zero tangent. The tangent there has
no unique UV direction; use a unit vector orthogonal to its vertex normal.
Existing nondegenerate tangents keep their direction and handedness.
"""
from pathlib import Path
import json,struct,math
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'models'/'xiaoxiaomeng.glb'
blob=bytearray(path.read_bytes());n=struct.unpack_from('<I',blob,12)[0]
doc=json.loads(blob[20:20+n]);binary_start=28+n
def location(index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
 return binary_start+v.get('byteOffset',0)+a.get('byteOffset',0),v.get('byteStride',16),a['count']
visited=set();fixed=0
for mesh in doc.get('meshes',[]):
 for prim in mesh['primitives']:
  attrs=prim['attributes']
  if 'TANGENT' not in attrs or attrs['TANGENT'] in visited:continue
  visited.add(attrs['TANGENT']);start,stride,count=location(attrs['TANGENT'])
  normal_start,normal_stride,_=location(attrs['NORMAL'])
  normal_stride=doc['bufferViews'][doc['accessors'][attrs['NORMAL']]['bufferView']].get('byteStride',12)
  for i in range(count):
   x,y,z,w=struct.unpack_from('<4f',blob,start+i*stride);length=math.sqrt(x*x+y*y+z*z)
   if length<1e-6:
    nx,ny,nz=struct.unpack_from('<3f',blob,normal_start+i*normal_stride)
    if abs(nz)<.9:x,y,z=-ny,nx,0.
    else:x,y,z=0.,-nz,ny
    length=math.sqrt(x*x+y*y+z*z);fixed+=1
   struct.pack_into('<4f',blob,start+i*stride,x/length,y/length,z/length,-1. if w<0 else 1.)
path.write_bytes(blob)
print('GLTF_TANGENT_POLES_NORMALIZED',fixed)
