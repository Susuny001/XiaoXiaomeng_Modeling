// Run with: NODE_PATH=/path/to/node_modules node tools/validate_glb.cjs
const fs=require('node:fs');
const path=require('node:path');
const validator=require('gltf-validator');
const root=path.resolve(__dirname,'..');
(async()=>{
 const report=await validator.validateBytes(new Uint8Array(fs.readFileSync(path.join(root,'models/xiaoxiaomeng.glb'))),{uri:'xiaoxiaomeng.glb',maxIssues:10000});
 fs.writeFileSync(path.join(root,'models/gltf-validation.json'),JSON.stringify(report,null,2));
 const codes={};for(const m of report.issues.messages){const k=`${m.severity}:${m.code}`;codes[k]=(codes[k]||0)+1;}
 console.log(JSON.stringify({errors:report.issues.numErrors,warnings:report.issues.numWarnings,infos:report.issues.numInfos,codes},null,2));
 if(report.issues.numErrors)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
