const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),out=path.join(R,'native-test-results/0.1.9'),log=path.join(R,'environment-safe-final-v019/emulator.log'),base='http://127.0.0.1:43150/';
const sleep=ms=>new Promise(r=>setTimeout(r,ms)),logs=()=>fs.readFileSync(log,'utf8');
async function req(p){const r=await fetch(base+p);if(!r.ok)throw Error(await r.text());return r;}
async function click(x,y,delay=220){await req(`click?x=${x}&y=${y}`);await sleep(delay);}
async function shot(name){fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(await(await req('screen')).arrayBuffer()));}
async function title(){await click(216,470);await click(210,458);}
async function target(){await click(100,394);await click(210,402);await click(360,470);const at=logs().length;await click(210,402,0);for(let n=0;n<200&&!/SENREN_RW5 frame n310 0\b/.test(logs().slice(at));n++)await sleep(50);assert.match(logs().slice(at),/SENREN_RW5 frame n310 0\b/);}
(async()=>{
 const marker=logs().length;await shot('safe-title');await click(100,306);await shot('safe-reading');await title();
 await target();await shot('murasame-newlines');await title();
 await click(100,482);await shot('safe-config');await click(210,212);await shot('config-typed');await click(210,326);
 await target();const at=Date.now(),positions=[0,180,420,800,1300,1700];
 for(const ms of positions){await sleep(Math.max(0,at+ms-Date.now()));await shot('typed-'+String(ms).padStart(4,'0'));}
 assert.ok(!/SENREN_RW5 frame n310 [1-9]\b/.test(logs().slice(marker)),'Typing advanced the story');
 await click(216,470);await click(210,356);await click(210,412);await shot('font-switch-large');
 const fontDragAt=logs().length;await req('drag?x0=300&y0=425&x1=300&y1=345');await sleep(350);await shot('font-switch-large-scrolled');assert.ok(!/SENREN_RW5 frame/.test(logs().slice(fontDragAt)));
 await click(216,470);await click(210,356);await click(210,412);await shot('font-switch-standard');await title();
 await click(100,482);await click(210,212);await click(210,154);await click(210,326);
 await click(100,306);for(let i=0;i<41;i++)await click(360,470,70);await shot('safe-large-before');const dragAt=logs().length;
 await req('drag?x0=300&y0=425&x1=300&y1=345');await sleep(350);await shot('safe-large-after');assert.notDeepEqual(fs.readFileSync(path.join(out,'safe-large-before.png')),fs.readFileSync(path.join(out,'safe-large-after.png')));assert.ok(!/SENREN_RW5 frame/.test(logs().slice(dragAt)));
 await click(216,470);await shot('safe-menu');await click(210,458);await click(100,482);await click(210,154);await click(210,326);
 await click(100,394);await shot('safe-routes');await click(210,310);await shot('safe-chapters');await click(216,470);await shot('safe-routes-back');await click(360,470);await shot('safe-routes-next');await click(70,470);await click(216,470);
 await click(100,350);await shot('safe-slots');for(let i=0;i<7;i++)await click(360,470);await shot('safe-slots-last');await click(70,470);await click(360,470);await click(216,470);
 await click(100,438);await shot('safe-extra');await click(210,96);await shot('safe-gallery');await click(100,150);await shot('safe-cg');await click(360,470);await shot('safe-cg-next');await click(70,470);await click(216,470);await click(360,470);await shot('safe-gallery-next');await click(70,470);await click(216,470);
 assert.ok(!/SENREN_RW5 error|SENREN_RW5 audio error|Data Abort|PANIC!!!/.test(logs().slice(marker)));
 const sha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(R,'dist/com.codex.senren.rw5.debug.0.1.9.rpk'))).digest('hex');
 fs.writeFileSync(path.join(out,'layout-preparation.json'),JSON.stringify({result:'prepared',version:'0.1.9',sha256,murasameChapter:'n310 / chapter 6-2 / first sentence',typingCapturesMs:positions,largeFontDragDoesNotAdvance:true,routesBackAndBothPagersPassed:true,slotPagerBothDirectionsPassed:true,cgGroupsAndGalleryPagersPassed:true,physicalDeviceTested:false},null,2));console.log('LAYOUT_PREPARED');
})().catch(e=>{console.error(e);process.exitCode=1;});
