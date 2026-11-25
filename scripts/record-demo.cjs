// Records the real localhost UI with the code-generated fictional resume only.
// Never load a personal PDF, browser profile, or credentials into this recording.
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const root=path.resolve(__dirname,'..');
const output=path.join(root,'private','demo');
const media=path.join(root,'docs','media');
const inspect=process.argv.includes('--inspect');
fs.mkdirSync(output,{recursive:true});fs.mkdirSync(media,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let server,browser,context;
async function main(){
 server=spawn(process.env.PYTHON||'python3',['run.py','serve','--port','0'],{cwd:root,stdio:['ignore','pipe','pipe']});
 const url=await new Promise((resolve,reject)=>{let buffer='';const timer=setTimeout(()=>reject(Error('Local server startup timed out')),15000);server.stdout.on('data',x=>{buffer+=x;const m=buffer.match(/http:\/\/127\.0\.0\.1:\d+\/#token=[A-Za-z0-9_-]+/);if(m){clearTimeout(timer);resolve(m[0])}});server.on('exit',()=>reject(Error('Local server stopped')))});
 browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
 context=await browser.newContext({viewport:{width:1440,height:1080},deviceScaleFactor:1,locale:'zh-CN',acceptDownloads:true,...(!inspect?{recordVideo:{dir:path.join(output,'raw'),size:{width:1440,height:1080}}}:{})});
 const page=await context.newPage();const errors=[];const external=[];const checkRequest=request=>{if(!request.url().startsWith('http://127.0.0.1:')&&!request.url().startsWith('blob:'))external.push(request.url().split('?')[0]);};context.on('request',checkRequest);page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.waitForSelector('#demo');
 if(inspect)await page.screenshot({path:path.join(output,'empty-desktop.png')});
 if(!inspect){
  await page.evaluate(()=>{
   const style=document.createElement('style');style.textContent=`body{padding-top:62px;--demo-offset:62px}#demo-hud{position:fixed;inset:0 0 auto;height:62px;background:#153b32;color:white;z-index:9000;display:flex;align-items:center;justify-content:space-between;padding:0 30px;font-family:system-ui}#demo-hud b{font-size:18px}#demo-hud small{font-size:12px;color:#c4dfd0}#demo-cursor{position:fixed;width:22px;height:28px;pointer-events:none;z-index:9999;left:100px;top:100px;filter:drop-shadow(0 1px 2px #0005)}.demo-ripple{position:fixed;width:36px;height:36px;border:3px solid #29916c;border-radius:50%;pointer-events:none;z-index:9998;animation:demo-click .6s ease-out forwards}@keyframes demo-click{from{transform:translate(-50%,-50%) scale(.3);opacity:1}to{transform:translate(-50%,-50%) scale(1.4);opacity:0}}`;
   document.head.append(style);const hud=document.createElement('div');hud.id='demo-hud';hud.innerHTML='<b id="demo-caption"></b><small>CleanCV · 完全虚构示例 · 本机处理</small>';document.body.append(hud);
   const cursor=document.createElement('div');cursor.id='demo-cursor';cursor.innerHTML='<svg viewBox="0 0 24 30"><path d="M2 2v23l6-6 5 9 4-2-5-9h9Z" fill="#163d32" stroke="white" stroke-width="1.5"/></svg>';document.body.append(cursor);
   window.addEventListener('pointermove',e=>{cursor.style.left=e.clientX+'px';cursor.style.top=e.clientY+'px'});
   window.addEventListener('pointerdown',e=>{const r=document.createElement('div');r.className='demo-ripple';r.style.left=e.clientX+'px';r.style.top=e.clientY+'px';document.body.append(r);setTimeout(()=>r.remove(),650)});
  });
 }
 async function caption(text,hold=700){if(!inspect)await page.locator('#demo-caption').evaluate((el,t)=>el.textContent=t,text);await sleep(hold)}
 async function click(locator){await locator.scrollIntoViewIfNeeded();const b=await locator.boundingBox();await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:35});await sleep(260);await page.mouse.click(b.x+b.width/2,b.y+b.height/2);await sleep(450)}
 async function ready(){await page.waitForFunction(()=>!busy && document.querySelector('#sheet-1 img')?.complete && document.querySelector('#sheet-1 img')?.naturalWidth>0)}
 await caption('01  打开简历：先用虚构示例体验完整流程',1300);
 await click(page.locator('#demo'));await ready();
 if(inspect){
  await page.screenshot({path:path.join(output,'inspect.png')});
  const layouts=[];
  for(const [width,height] of [[1440,900],[1024,768],[801,900],[800,900],[390,844]]){
   await page.setViewportSize({width,height});
   if(width<=800)await page.locator('#tab-preview').click();
   await page.waitForTimeout(150);
   if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Horizontal overflow at '+width);
   if(await page.evaluate(()=>document.documentElement.scrollHeight>innerHeight+1))throw Error('Workspace must fit viewport at '+width);
   await page.screenshot({path:path.join(output,'layout-'+width+'.png')});
   await page.locator('#zoom-in').click();if(await page.locator('#zoom-value').textContent()!=='125%')throw Error('Zoom in failed');await page.locator('#zoom-out').click();
   if(width<=800)await page.locator('#tab-editor').click();
   await page.locator('[data-kind="email"]').click();
   await page.waitForSelector('.region.focused');
   if(width<=800)await page.locator('#tab-editor').click();
   await page.locator('#terms').fill('demo_profile');await page.locator('#detect').click();await page.waitForFunction(()=>!busy);
   if(!await page.evaluate(()=>regions.some(r=>r.kind==='extra')))throw Error('Extra term failed');
   if(width<=800)await page.screenshot({path:path.join(output,'editor-'+width+'.png')});
   layouts.push({width,height,noHorizontalOverflow:true,workspaceFitsViewport:true,zoom:true,candidateNavigation:true});
  }
  await page.setViewportSize({width:390,height:844});await page.reload();
  if(!await page.locator('#landing').isVisible())throw Error('Landing should open on reload');
  await page.screenshot({path:path.join(output,'home-mobile.png'),fullPage:true});
  await page.locator('#help').click();if(!await page.locator('#guide').isVisible())throw Error('Help did not open');await page.keyboard.press('Escape');if(await page.locator('#guide').isVisible())throw Error('Help did not close');
  await page.locator('#demo').click();await ready();if(await page.locator('#draw').getAttribute('aria-pressed')!=='false')throw Error('Mobile must start in browse mode');
  await page.locator('#tab-editor').click();await page.locator('#reviewed').check();
  const downloadPromise=page.waitForEvent('download');await page.locator('#export').click();await downloadPromise;await ready();
  if(await page.locator('body').getAttribute('data-mobile')!=='preview')throw Error('Mobile export should reveal preview');
  await page.screenshot({path:path.join(output,'result-mobile.png')});
  await page.locator('#tab-editor').click();if(!await page.locator('#result-panel').isVisible())throw Error('Result panel missing');
  const again=page.waitForEvent('download');await page.locator('#redownload').click();await again;
  await page.locator('#return-edit').click();await ready();await page.locator('#tab-preview').click();if(!await page.locator('.region').count())throw Error('Editing overlays not restored');
  await page.locator('#clear').click();await page.waitForFunction(()=>!busy&&!current);if(!await page.locator('#landing').isVisible())throw Error('Clear did not restore landing');
  const fixture=execFileSync(process.env.PYTHON||'python3',['-c','import sys; sys.path.insert(0, "src"); from cleancv.demo import create_demo_pdf; sys.stdout.buffer.write(create_demo_pdf())'],{cwd:root});
  const transfer=await page.evaluateHandle(bytes=>{const transfer=new DataTransfer();transfer.items.add(new File([new Uint8Array(bytes)],'synthetic-resume.pdf',{type:'application/pdf'}));return transfer;},Array.from(fixture));
  await page.locator('#pick').dispatchEvent('drop',{dataTransfer:transfer});await ready();await transfer.dispose();
  if(await page.locator('#filename').textContent()!=='synthetic-resume.pdf')throw Error('Drop import failed');
  const multi=execFileSync(process.env.PYTHON||'python3',['-c','import sys; sys.path.insert(0, "src"); import pymupdf as fitz; from cleancv.demo import create_demo_pdf; a=fitz.open(stream=create_demo_pdf(),filetype="pdf"); b=fitz.open(); b.insert_pdf(a); b.insert_pdf(a); sys.stdout.buffer.write(b.tobytes())'],{cwd:root});
  await page.locator('#file').setInputFiles({name:'synthetic-multipage.pdf',mimeType:'application/pdf',buffer:multi});await ready();
  await page.waitForFunction(()=>document.querySelectorAll('.page').length===2 && [...document.querySelectorAll('.sheet img')].every(img=>img.complete&&img.naturalWidth>0));
  await page.locator('#page-select').selectOption('2');await page.waitForFunction(()=>activePage===2);
  if(await page.locator('#filename').textContent()!=='synthetic-multipage.pdf')throw Error('File picker import failed');
  await page.setViewportSize({width:1440,height:900});await page.locator('.thumbnail').first().click();await page.waitForFunction(()=>activePage===1);await page.locator('.thumbnail').nth(1).click();await page.waitForFunction(()=>activePage===2);
  await page.screenshot({path:path.join(output,'multipage-desktop.png')});
  if(await page.locator('#draw').getAttribute('aria-pressed')!=='true')await page.locator('#draw').click();
  await page.locator('#zoom-in').click();
  const box=await page.locator('#sheet-2').boundingBox();
  await page.mouse.move(box.x+40/595*box.width,box.y+143/842*box.height);await page.mouse.down();await page.mouse.move(box.x+140/595*box.width,box.y+162/842*box.height,{steps:12});await page.mouse.up();
  if(!await page.evaluate(()=>regions.some(r=>r.kind==='manual'&&r.page===2&&r.rect.every((value,i)=>Math.abs(value-[40,143,140,162][i])<2))))throw Error('Zoomed manual coordinates are wrong');
  await page.locator('#zoom-out').click();
  await page.setViewportSize({width:390,height:844});await page.locator('#tab-preview').press('ArrowRight');if(await page.locator('#tab-editor').getAttribute('aria-selected')!=='true')throw Error('Keyboard tabs failed');
  if(errors.length||external.length)throw Error('Browser errors or external requests detected');
  fs.writeFileSync(path.join(output,'layout-checks.json'),JSON.stringify({syntheticOnly:true,layouts,mobileExport:true,redownload:true,clear:true,help:true,keyboardTabs:true,dropImport:true,filePickerImport:true,multiPageNavigation:true,zoomedManualCoordinates:true,externalRequests:external,pageErrors:errors},null,2));
  console.log('Landing, desktop/mobile workspace, imports, zoom, candidate/page navigation, export and local-only checks passed.');return;
 }
 await caption('02  核查自动候选：姓名、邮箱、电话、政治身份和照片',2300);
 const kinds=await page.evaluate(()=>regions.map(r=>r.kind));for(const k of ['name','email','phone','politics','photo'])if(!kinds.includes(k))throw Error('Missing automatic candidate '+k);
 await click(page.locator('[data-kind="photo"]'));await sleep(1100);
 await caption('03  撤销误报：正文里的“群众”不属于个人身份');
 const falseIndex=await page.evaluate(()=>regions.findIndex(r=>r.kind==='politics' && r.rect[1]>200));if(falseIndex<0)throw Error('Expected synthetic false positive');
 await click(page.locator('.region:not(.drag)').nth(falseIndex).locator('button'));await sleep(1500);
 await caption('04  补充关联信息：填写额外词并重新识别');
 await click(page.locator('#terms'));await page.locator('#terms').pressSequentially('demo_profile',{delay:95});await sleep(500);await click(page.locator('#detect'));await ready();
 if(await page.evaluate(()=>regions.some(r=>r.kind==='politics' && r.rect[1]>200)))throw Error('Dismissed candidate returned');
 if(!await page.evaluate(()=>regions.some(r=>r.kind==='extra')))throw Error('Extra term was not detected');
 await sleep(1500);
 await caption('05  手动补框：拖动选中还想移除的所在地');
 const sheet=await page.locator('#sheet-1').boundingBox();
 const from={x:sheet.x+39/595*sheet.width,y:sheet.y+143/842*sheet.height};
 const to={x:sheet.x+143/595*sheet.width,y:sheet.y+162/842*sheet.height};
 await page.mouse.move(from.x,from.y,{steps:30});await sleep(350);await page.mouse.down();
 for(let i=1;i<=35;i++){await page.mouse.move(from.x+(to.x-from.x)*i/35,from.y+(to.y-from.y)*i/35);await sleep(25)}
 await page.mouse.up();await sleep(1500);
 if(!await page.evaluate(()=>regions.some(r=>r.kind==='manual')))throw Error('Manual box not recorded');
 await caption('06  确认已逐页核查，再生成脱敏 PDF');
 await click(page.locator('#reviewed'));if(!await page.locator('#export').isEnabled())throw Error('Export should be enabled');
 const downloadPromise=page.waitForEvent('download');await click(page.locator('#export'));const download=await downloadPromise;await download.saveAs(path.join(output,'result.pdf'));await ready();
 await page.waitForFunction(()=>showingResult===true);
 if(await page.locator('.region').count())throw Error('Result preview still has editing overlays');
 await caption('07  核查导出结果：再把处理后的 PDF 交给 AI',3500);
 await page.screenshot({path:path.join(output,'result-preview.png')});
 if(errors.length||external.length)throw Error('Browser errors or external requests detected');
 const video=page.video();await page.close();await context.close();context=null;
 await video.saveAs(path.join(output,'walkthrough.webm'));
 // Capture the poster in a separate unrecorded context, so the video never jumps layout.
 const posterContext=await browser.newContext({viewport:{width:1440,height:1080},locale:'zh-CN'});
 posterContext.on('request',checkRequest);
 const poster=await posterContext.newPage();poster.on('pageerror',e=>errors.push(e.message));
 await poster.goto(url);await poster.screenshot({path:path.join(media,'cleancv-home.png'),fullPage:true});await poster.locator('#demo').click();
 await poster.waitForFunction(()=>!busy && document.querySelector('#sheet-1 img')?.complete && document.querySelector('#sheet-1 img')?.naturalWidth>0);
 await poster.screenshot({path:path.join(media,'cleancv-poster.png'),fullPage:true});await posterContext.close();
 if(errors.length||external.length)throw Error('Browser errors or external requests detected');

 fs.writeFileSync(path.join(output,'recording-checks.json'),JSON.stringify({fixture:'cleancv.demo.create_demo_pdf',syntheticOnly:true,automaticFields:true,dismissalPreserved:true,extraTerm:true,manualRegion:true,download:true,resultPreview:true,pageErrors:errors,externalRequests:external},null,2));
 console.log('Recorded actual UI workflow with synthetic data; interaction checks passed.');
}
main().catch(e=>{console.error(e.message);process.exitCode=1}).finally(async()=>{if(context)await context.close().catch(()=>{});if(browser)await browser.close().catch(()=>{});if(server)server.kill('SIGINT')});
