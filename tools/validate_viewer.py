"""Browser acceptance checks for a running local viewer; screenshots for review."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1440,'height':1080},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 response=page.goto('http://127.0.0.1:8002/',wait_until='load')
 assert response.status==200
 page.wait_for_function('window.__MODEL_READY__ === true',timeout=120000)
 stats=page.evaluate('window.__MODEL_STATS__')
 assert stats['meshes']>200 and stats['triangles']>100000 and stats['bones']>=30,stats
 assert .8<stats['bounds'][0]<1.2 and 1.7<stats['bounds'][1]<1.95 and .15<stats['bounds'][2]<.6,stats
 page.screenshot(path=str(ROOT/'renders'/'viewer-desktop.png'))
 page.locator('[data-view="back"]').click()
 assert page.evaluate('window.__VIEWER__.getCamera().position.z')<0
 page.locator('[data-view="front"]').click()
 page.locator('[data-mode="wire"]').click()
 assert page.evaluate('window.__VIEWER__.meshes.every(o=>(Array.isArray(o.material)?o.material:[o.material]).every(m=>m.wireframe))')
 page.locator('[data-mode="clay"]').click()
 assert page.locator('[data-mode="clay"]').get_attribute('class')=='active'
 page.locator('[data-mode="material"]').click()
 assert not page.evaluate('window.__VIEWER__.meshes[0].material.wireframe')
 cats=page.evaluate('window.__VIEWER__.meshes.reduce((a,m)=>(a[m.userData.category]=(a[m.userData.category]||0)+1,a),{})')
 assert cats.get('hair',0)>20 and cats.get('jacket',0)>10 and cats.get('shoes',0)>20,cats
 page.locator('[data-layer="hair"]').click()
 assert page.evaluate('window.__VIEWER__.meshes.filter(m=>m.userData.category==="hair").every(m=>!m.visible)')
 page.locator('[data-layer="hair"]').click()
 page.locator('#ortho').check()
 assert page.evaluate('window.__VIEWER__.getCamera().isOrthographicCamera')
 page.locator('#skeleton').check();page.locator('#skeleton').uncheck()
 page.locator('#rotate').check();assert page.evaluate('window.__VIEWER__.controls.autoRotate')
 page.locator('#rotate').uncheck();page.locator('#ortho').uncheck();page.locator('#reset').click()
 with page.expect_download() as download:page.locator('#screenshot').click()
 assert download.value.suggested_filename.endswith('.png')
 for fmt in ['glb','fbx','blend']:
  r=page.request.get('http://127.0.0.1:8002/models/xiaoxiaomeng.'+fmt)
  assert r.status==200 and len(r.body())>100000
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(500)
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.screenshot(path=str(ROOT/'renders'/'viewer-mobile.png'))
 assert not errors,errors
 report={'passed':True,'stats':stats,'categories':cats,'page_errors':errors,'checks':['model load','geometry and rig','camera views','wireframe','clay','materials','layers','orthographic','skeleton','turntable','screenshot export','three file downloads','mobile layout']}
 (ROOT/'viewer'/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps(report,ensure_ascii=False,indent=2))
 browser.close()
