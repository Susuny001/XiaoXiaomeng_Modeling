"""Create the downloadable package only after all required checks have passed."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
validation=json.loads((ROOT/'models'/'roundtrip-validation.json').read_text())
assert len(validation)==3 and all(x['passed'] for x in validation)
gltf=json.loads((ROOT/'models'/'gltf-validation.json').read_text())
assert gltf['issues']['numErrors']==0
viewer=json.loads((ROOT/'viewer'/'acceptance.json').read_text());assert viewer['passed']
assert json.loads((ROOT/'viewer'/'offline-acceptance.json').read_text())['passed']
for name in ['beauty','front','back','face','viewer-desktop','viewer-mobile']:
 assert (ROOT/'renders'/(name+'.png')).is_file(),name
delivery=ROOT/'delivery';delivery.mkdir(exist_ok=True)
files=[ROOT/n for n in ['PREVIEW.html','index.html','README.md','DELIVERY.md','START_PREVIEW.py','START_PREVIEW.bat','START_PREVIEW.sh']]
for directory in ['models','renders','viewer','tools','assets']:
 files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.suffix in ['.blend1','.blend2','.pyc'])
checks=[]
for p in sorted(files):checks.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}')
(delivery/'SHA256SUMS.txt').write_text('\n'.join(checks)+'\n')
archive=delivery/'xiaoxiaomeng-model-and-viewer.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(files):z.write(p,'xiaoxiaomeng/'+str(p.relative_to(ROOT)))
 z.write(delivery/'SHA256SUMS.txt','xiaoxiaomeng/SHA256SUMS.txt')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
manifest={'archive':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':len(files)+1,'viewer':viewer['stats'],'gltf_errors':gltf['issues']['numErrors'],'gltf_warnings':gltf['issues']['numWarnings'],'roundtrip_formats':[x['format'] for x in validation]}
(delivery/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(manifest,ensure_ascii=False,indent=2))
