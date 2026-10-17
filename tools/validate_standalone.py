"""Test the standalone HTML with every network request except itself blocked.

The managed Chromium in this environment blocks all file:// navigation by
administrator policy. Serve the single document to exercise its self-contained
code path without relying on any model, library or texture network requests.
"""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1440,'height':1080})
 blocked=[];errors=[]
 def route(r):
  if r.request.url=='http://127.0.0.1:8002/PREVIEW.html':r.continue_()
  else:blocked.append(r.request.url);r.abort()
 page.route('http://**',route)
 page.route('https://**',lambda r:(blocked.append(r.request.url),r.abort()))
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8002/PREVIEW.html',wait_until='load',timeout=120000)
 page.wait_for_function('window.__MODEL_READY__===true',timeout=120000)
 stats=page.evaluate('window.__MODEL_STATS__')
 assert 1.7<stats['bounds'][1]<1.95,stats
 page.locator('[data-view="front"]').click()
 page.locator('[data-layer="jacket"]').click()
 assert page.evaluate('window.__VIEWER__.meshes.filter(m=>m.userData.category==="jacket").every(m=>!m.visible)')
 page.locator('[data-layer="jacket"]').click();page.locator('#reset').click()
 page.screenshot(path=str(ROOT/'renders'/'viewer-offline.png'))
 assert not errors and not blocked,{'errors':errors,'network_requests':blocked}
 report={'passed':True,'single_document':True,'external_network_requests':blocked,'page_errors':errors,'stats':stats,'file_url_test':'Not run: managed browser policy blocks file:// navigation. Single-document test permits only the initial HTML request.'}
 (ROOT/'viewer'/'offline-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps(report,ensure_ascii=False,indent=2));browser.close()
