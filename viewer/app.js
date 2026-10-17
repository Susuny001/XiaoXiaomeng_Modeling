import * as THREE from 'three';
import {OrbitControls} from './vendor/controls/OrbitControls.js';
import {GLTFLoader} from './vendor/loaders/GLTFLoader.js';

const $=s=>document.querySelector(s);
const mount=$('#canvas-container');
const scene=new THREE.Scene();
const perspective=new THREE.PerspectiveCamera(32,1,.01,100);
const ortho=new THREE.OrthographicCamera(-1,1,1,-1,.01,100);
let camera=perspective,model=null,skeletonHelper=null,mode='material',ready=false,redraw=true;
let renderer;
try{
 renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true,powerPreference:'high-performance'});
}catch(error){
 $('#load-title').textContent='当前浏览器未能启用 WebGL';$('#progress').textContent='请启用硬件加速，或从左侧下载模型文件。';throw error;
}
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
renderer.outputColorSpace=THREE.SRGBColorSpace;mount.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);
controls.addEventListener('change',()=>{redraw=true;});
controls.enableDamping=true;controls.dampingFactor=.07;controls.minDistance=.40;controls.maxDistance=8;
controls.maxPolarAngle=Math.PI*.90;controls.target.set(0,.95,0);controls.autoRotateSpeed=.75;
scene.add(new THREE.HemisphereLight(0xdfe6cf,0x313b28,2.1));
const key=new THREE.DirectionalLight(0xffefdd,3.2);key.position.set(-3,4,5);key.castShadow=true;
key.shadow.mapSize.set(2048,2048);key.shadow.camera.left=-1.6;key.shadow.camera.right=1.6;key.shadow.camera.top=2.5;key.shadow.camera.bottom=-1;
key.shadow.bias=-.0002;key.shadow.normalBias=.015;key.shadow.radius=4;scene.add(key);
const fill=new THREE.DirectionalLight(0xd0ddff,1.8);fill.position.set(3,2,2);scene.add(fill);
const rim=new THREE.DirectionalLight(0xd0f9a5,3);rim.position.set(1,3,-3);scene.add(rim);
const ground=new THREE.Mesh(new THREE.CircleGeometry(.90,96),new THREE.MeshStandardMaterial({color:0x263121,roughness:1}));
ground.rotation.x=-Math.PI/2;ground.receiveShadow=true;ground.position.y=.011;scene.add(ground);
const ring=new THREE.Mesh(new THREE.RingGeometry(.87,.873,128),new THREE.MeshBasicMaterial({color:0x899c69,transparent:true,opacity:.14,side:THREE.DoubleSide}));ring.rotation.x=-Math.PI/2;ring.position.y=.012;scene.add(ring);
const meshes=[];const layerState={hair:true,jacket:true,accessories:true,shoes:true};
function category(name){
 if(/^Hair\b/i.test(name))return 'hair';
 if(/^(Shoe|Lace|Outsole)/i.test(name))return 'shoes';
 if(/^(Jacket|Sleeve|Hood|Collar|LEFT hem|LEFT sleeve|Front opening)/i.test(name))return 'jacket';
 if(/^(Ribbon|Hairpin|RIGHT webbing|RIGHT thigh|Cargo snap|Zip tooth|Hem press)/i.test(name))return 'accessories';
 return 'body';
}
function size(){
 redraw=true;
 const w=mount.clientWidth,h=mount.clientHeight;renderer.setSize(w,h,false);perspective.aspect=w/h;perspective.updateProjectionMatrix();
 const s=1.10;ortho.left=-s*w/h;ortho.right=s*w/h;ortho.top=s;ortho.bottom=-s;ortho.updateProjectionMatrix();
}
new ResizeObserver(size).observe(mount);
const views={front:[0,1.02,3.8],left:[3.8,1.02,0],back:[0,1.02,-3.8],right:[-3.8,1.02,0],home:[2.1,1.48,3.7]};
function setView(name){
 controls.target.set(0,.94,0);camera.position.fromArray(views[name]||views.home);camera.zoom=1;camera.updateProjectionMatrix();controls.update();
 document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===name));
}
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
$('#reset').addEventListener('click',()=>setView('home'));
$('#rotate').addEventListener('change',e=>{controls.autoRotate=e.target.checked;});
$('#ortho').addEventListener('change',e=>{
 const next=e.target.checked?ortho:perspective;next.position.copy(camera.position);next.quaternion.copy(camera.quaternion);next.zoom=1;camera=next;controls.object=camera;camera.updateProjectionMatrix();controls.update();
});
$('#skeleton').addEventListener('change',e=>{if(skeletonHelper)skeletonHelper.visible=e.target.checked;redraw=true;});
function applyMode(value){
 redraw=true;
 mode=value;
 for(const m of meshes){
  const materials=Array.isArray(m.material)?m.material:[m.material];
  materials.forEach(ma=>{const original=ma.userData.original;ma.wireframe=value==='wire';ma.color.copy(value==='clay'?new THREE.Color(0xc2c6b6):original.color);ma.metalness=value==='clay'?0:original.metalness;ma.roughness=value==='clay'?.75:original.roughness;ma.needsUpdate=true;});
 }
 document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===value));
}
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>applyMode(b.dataset.mode)));
document.querySelectorAll('[data-layer]').forEach(b=>b.addEventListener('click',()=>{
 const layer=b.dataset.layer;layerState[layer]=!layerState[layer];b.setAttribute('aria-pressed',String(layerState[layer]));
 redraw=true;
 meshes.forEach(m=>{if(m.userData.category===layer)m.visible=layerState[layer];});
}));
$('#screenshot').addEventListener('click',()=>{
 if(!ready)return;renderer.render(scene,camera);
 renderer.domElement.toBlob(blob=>{if(!blob)return;const a=document.createElement('a');a.download='xiaoxiaomeng-view.png';a.href=URL.createObjectURL(blob);a.click();setTimeout(()=>URL.revokeObjectURL(a.href),5000);},'image/png');
});
setView('home');size();
function loadModel(onLoad,onProgress,onError){
 const loader=new GLTFLoader();
 if(window.__EMBEDDED_GLB__){
  try{const decoded=atob(window.__EMBEDDED_GLB__);const bytes=new Uint8Array(decoded.length);for(let i=0;i<decoded.length;i++)bytes[i]=decoded.charCodeAt(i);loader.parse(bytes.buffer,'',onLoad,onError);}
  catch(error){onError(error);}
 }else loader.load('./models/xiaoxiaomeng.glb',onLoad,onProgress,onError);
}
loadModel(gltf=>{
 model=gltf.scene;scene.add(model);let triangles=0,vertices=0;
 model.traverse(object=>{
  if(!object.isMesh)return;meshes.push(object);object.castShadow=true;object.receiveShadow=true;object.frustumCulled=false;
  object.userData.category=category(object.name.replaceAll('_',' '));
  const mats=Array.isArray(object.material)?object.material:[object.material];
  const clones=mats.map(m=>{const ma=m.clone();ma.side=THREE.DoubleSide;ma.userData.original={color:ma.color.clone(),metalness:ma.metalness,roughness:ma.roughness};return ma;});object.material=Array.isArray(object.material)?clones:clones[0];
  vertices+=object.geometry.attributes.position.count;triangles+=(object.geometry.index?object.geometry.index.count:object.geometry.attributes.position.count)/3;
 });
 skeletonHelper=new THREE.SkeletonHelper(model);skeletonHelper.visible=false;skeletonHelper.material.depthTest=false;skeletonHelper.material.transparent=true;skeletonHelper.material.opacity=.75;skeletonHelper.renderOrder=10;scene.add(skeletonHelper);
 const bones=[];model.traverse(o=>{if(o.isBone)bones.push(o);});
 $('#stats').textContent=`${Math.round(triangles).toLocaleString()} 三角面 · ${meshes.length} 部件 · ${bones.length} 骨骼`;
 $('#model-status').textContent='模型已就绪';$('#progress-bar').style.width='100%';$('#loading').classList.add('done');
 const bounds=new THREE.Box3().setFromObject(model).getSize(new THREE.Vector3());
 ready=true;redraw=true;window.__MODEL_READY__=true;window.__MODEL_STATS__={triangles,vertices,meshes:meshes.length,bones:bones.length,bounds:[bounds.x,bounds.y,bounds.z]};window.__VIEWER__={scene,model,meshes,controls,renderer,getCamera:()=>camera};
},event=>{
 const ratio=event.total?event.loaded/event.total:0;$('#progress').textContent=event.total?`${Math.round(ratio*100)}% · 读取模型与材质`:`已读取 ${(event.loaded/1024/1024).toFixed(1)} MB`;
 $('#progress-bar').style.width=`${event.total?ratio*95:Math.min(85,event.loaded/200000)}%`;
},error=>{
 console.error('Model load failed',error);$('#model-status').textContent='载入失败';$('#load-title').textContent='模型未能载入';
 $('#progress').textContent=location.protocol==='file:'?'请运行 START_PREVIEW 启动器，通过本地服务器打开。':'请检查 models/xiaoxiaomeng.glb 是否存在，然后刷新。';window.__MODEL_ERROR__=String(error);
});
renderer.setAnimationLoop(()=>{controls.update();if(redraw||controls.autoRotate){renderer.render(scene,camera);redraw=false;}});
