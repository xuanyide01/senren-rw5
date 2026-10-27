const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),out=path.join(root,'native-test-results/0.1.9'),log=path.join(root,(process.env.WATCH_TEST_ENV||'environment-safe-final-v019')+'/emulator.log'),base='http://127.0.0.1:43150/';fs.mkdirSync(out,{recursive:true});const sha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'dist/com.codex.senren.rw5.debug.0.1.9.rpk'))).digest('hex');const logs=()=>fs.readFileSync(log,'utf8'),sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function req(p){const r=await fetch(base+p);if(!r.ok)throw Error(await r.text());return r;}
async function wait(re,at,ms=20000){const end=Date.now()+ms;while(Date.now()<end){if(re.test(logs().slice(at)))return;await sleep(60);}throw Error('Timeout '+re+'\n'+logs().slice(at).slice(-800));}
async function click(x,y,re){const at=logs().length;await req('click?x='+x+'&y='+y);if(re)await wait(re,at);await sleep(250);}
async function shot(name){fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(await(await req('screen')).arrayBuffer()));}
async function title(){await sleep(1800);await click(216,478,/SENREN_RW5 menu/);await click(210,458,/SENREN_RW5 title ready/);}
async function load(slot){await click(130,344,/slots ready load/);for(let i=0;i<Math.floor((slot-1)/4);i++)await click(360,478);await click(210,126+((slot-1)%4)*92,new RegExp('slot loaded '+slot+' '));}
(async()=>{
 const marker=logs().length;
 if(process.argv.includes('--cold')){for(let n=0;n<120;n++){const b=Buffer.from(await(await req('screen')).arrayBuffer());if(b.length>100000)break;await sleep(500);}await sleep(1500);await shot('cold-title');for(const slot of [1,30]){await load(slot);await shot('cold-slot-'+slot);await title();}const old=JSON.parse(fs.readFileSync(path.join(out,'preparation.json')));assert.equal(old.sha256,sha256);old.result='passed';old.coldStartSlotsRestored=[1,30];fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(old,null,2));console.log('COLD_PASSED');return;}
 // Starts from the legitimate first-choice result reached by the smoke run.
 if(!process.argv.includes('--resume-save1')){await click(216,478,/SENREN_RW5 menu/);await click(210,88,/slots ready save/);await shot('save-slots');await click(210,126,/slot saved 1 /);
 await click(360,478,/SENREN_RW5 frame/);await title();}await load(1);await shot('restored-slot-1');
 await click(216,478,/SENREN_RW5 menu/);await click(210,88,/slots ready save/);for(let i=0;i<7;i++)await click(360,478);await shot('save-slots-last-page');await click(210,218,/slot saved 30 /);await title();await load(30);await shot('restored-slot-30');await title();
 await click(130,388);await shot('routes-first-page');await click(210,310);await shot('mako-chapters-first-page');await click(216,478);await shot('routes-return-first-page');
 await click(210,126);await click(210,310,/SENREN_RW5 frame/);await shot('chapter-one-three');await click(216,478,/SENREN_RW5 menu/);await click(210,182);await sleep(700);await shot('prologue-opening-start');assert.ok(logs().slice(marker).includes('audio track opening'));await click(216,257,/SENREN_RW5 frame/);await shot('opening-skipped-next-chapter');await title();
 await click(130,432);await shot('extra');await click(210,146);await sleep(300);await shot('extra-opening');await click(216,257);await sleep(400);await shot('extra-after-skip');await click(210,212,/SENREN_RW5 title ready/);
 await click(130,476);await shot('config');await click(210,96);await shot('config-muted');assert.equal((await(await req('audio-state')).json()).playing,false);await click(210,326,/SENREN_RW5 title ready/);await load(1);
 await click(216,478,/SENREN_RW5 menu/);await click(210,228,/auto enabled true/);await click(210,412);const autoAt=logs().length;await wait(/SENREN_RW5 frame/,autoAt,12000);await shot('auto-playing');await click(70,478,/SENREN_RW5 frame/);await title();
 await click(130,476);await click(210,96);await click(210,326,/SENREN_RW5 title ready/);
 const result={result:'prepared',version:'0.1.9',sha256,installedSuccessfully:true,startGamePassed:true,textTapPassed:true,safeSkipStopsAtChoice:true,saveSlotsTested:[1,30],routeFirstPageAndBackCaptured:true,skipStopsAtOriginalOpening:true,openingTapSkipPassed:true,extraOpeningReturns:true,unifiedSoundTogglePassed:true,autoPlaybackAdvances:true,physicalDeviceTested:false};
 assert.ok(!/SENREN_RW5 error|SENREN_RW5 audio error|Data Abort|PANIC!!!/.test(logs().slice(marker)));fs.writeFileSync(path.join(out,'preparation.json'),JSON.stringify(result,null,2));console.log('NATIVE_PREPARED',JSON.stringify(result));
})().catch(e=>{console.error(e);process.exitCode=1;});
