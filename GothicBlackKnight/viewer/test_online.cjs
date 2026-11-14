const { chromium }=require('playwright');
const fs=require('fs');
const path=require('path');
const root=path.resolve(__dirname,'..');
fs.mkdirSync(path.join(root,'proof'),{recursive:true});
(async()=>{
 const model='https://raw.githubusercontent.com/iliagetri-ux/para-plus/92c98eefedf760f42ad7a9bf96388e32fc80c7df/GothicBlackKnight/artifacts/GothicBlackKnight.glb';
 // Babylon Sandbox expects the literal asset URL here, not a percent-encoded value.
 const url='https://sandbox.babylonjs.com/?assetUrl='+model;
 const proxy=process.env.HTTPS_PROXY||process.env.HTTP_PROXY;
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_BIN||'/usr/bin/chromium',headless:true,proxy:proxy?{server:proxy}:undefined,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:430,height:932},isMobile:true,hasTouch:true});
  const errors=[],responses=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.url()===model)responses.push({url:r.url(),status:r.status()})});
  await page.goto(url,{waitUntil:'domcontentloaded',timeout:60000});
  let readiness='';try{await page.waitForFunction(()=>window.BABYLON?.Engine?.Instances?.some(e=>e.scenes.some(s=>s.isReady()&&s.meshes.some(m=>m.getTotalVertices?.()>1000))),null,{timeout:60000});readiness='mesh loaded';}catch(e){readiness=e.message;}
  await page.waitForTimeout(3500);
  await page.screenshot({path:path.join(root,'proof/Online_Viewer.png'),timeout:30000});
  const result={url,readiness,responses,errors,browser:'Chromium/SwiftShader at 430x932; not a physical iPhone',body:(await page.locator('body').innerText()).slice(0,3000),scene:await page.evaluate(()=>window.BABYLON?.Engine?.Instances?.map(e=>e.scenes.map(s=>({meshes:s.meshes.length,vertices:s.meshes.reduce((a,m)=>a+(m.getTotalVertices?.()||0),0)}))))};
  fs.writeFileSync(path.join(root,'proof/online_check.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));if(readiness!=='mesh loaded'||errors.length||!responses.some(r=>r.status===200))process.exitCode=1;
 }finally{await browser.close()}
})().catch(e=>{console.error(e.message);process.exitCode=1});
