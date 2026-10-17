"""Double-click/run this file with Python 3, then use the browser that opens."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
import webbrowser
root=Path(__file__).resolve().parent
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root)))
url=f'http://127.0.0.1:{server.server_address[1]}/'
print('小小萌 3D 预览器:',url,flush=True)
print('Keep this window open. Press Ctrl+C to stop.',flush=True)
webbrowser.open(url)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
