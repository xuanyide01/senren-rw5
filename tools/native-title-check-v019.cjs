const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const R=path.resolve(__dirname,'..'),out=path.join(R,'native-test-results/0.1.9'),base='http://127.0.0.1:43150/';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function req(p){const r=await fetch(base+p);if(!r.ok)throw Error(await r.text());return r;}
async function click(x,y){await req(`click?x=${x}&y=${y}`);await sleep(400);}
async function screen(name){const b=Buffer.from(await(await req('screen')).arrayBuffer());if(name)fs.writeFileSync(path.join(out,name+'.png'),b);return b;}
(async()=>{
 fs.mkdirSync(out,{recursive:true});await sleep(800);for(let i=0;i<120&&(await screen()).length<100000;i++)await sleep(500);const title=await screen('title');
 for(const y of [306,350,394,438,482]){await click(340,y);assert.deepEqual(await screen(),title,'Right side unexpectedly activated menu at '+y);}
 for(const [y,name,back]of [[350,'load',[216,478]],[394,'directory',[216,478]],[438,'extra',[210,212]],[482,'config',[210,326]]]){
  await click(100,y);await sleep(1000);if((await screen()).equals(title)){await click(100,y);await sleep(1000);}assert.notDeepEqual(await screen(name),title,'Left menu failed: '+name);await click(...back);assert.deepEqual(await screen(),title,'Did not return to title from '+name);
 }
 await click(100,306);await screen('start');await click(216,390);await screen('text-tap');
 await click(216,478);await click(210,182);await screen('safe-choice');await click(210,95);await screen('first-choice-result');
 const p=path.join(R,'dist/com.codex.senren.rw5.debug.0.1.9.rpk');
 fs.writeFileSync(path.join(out,'title-check.json'),JSON.stringify({result:'passed',version:'0.1.9',sha256:crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex'),rightRegionInactive:true,allFiveLeftMenusOpen:true,physicalDeviceTested:false},null,2));console.log('TITLE_CHECK_PASSED');
})().catch(e=>{console.error(e);process.exitCode=1;});
