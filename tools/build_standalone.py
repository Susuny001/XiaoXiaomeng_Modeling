"""Bundle the viewer + GLB into one HTML file that opens without a web server."""
from pathlib import Path
import base64,re,sys
ROOT=Path(__file__).resolve().parents[1]
bundle=Path(sys.argv[1]).read_text()
html=(ROOT/'index.html').read_text()
html=html.replace('<link rel="stylesheet" href="viewer/style.css">','<style>'+(ROOT/'viewer'/'style.css').read_text()+'</style>')
html=re.sub(r'\s*<script type="importmap">.*?</script>','',html,flags=re.S)
embedded=base64.b64encode((ROOT/'models'/'xiaoxiaomeng.glb').read_bytes()).decode('ascii')
inline='<script>window.__EMBEDDED_GLB__="'+embedded+'";</script>\n<script>'+bundle.replace('</script','<\\/script')+'</script>'
html=html.replace('<script type="module" src="viewer/app.js"></script>',inline)
output=ROOT/'PREVIEW.html';output.write_text(html)
print('Standalone preview created:',output.stat().st_size,'bytes')
