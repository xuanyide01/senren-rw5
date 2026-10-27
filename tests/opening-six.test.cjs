const test=require('node:test'),assert=require('assert/strict'),fs=require('fs'),path=require('path'),vm=require('vm');
test('six fps clock uses independent fixed-position frames, one timer, pause/resume and full original duration',()=>{
 let now=0,id=0,done=0;const timers=new Map(),draws=[];
 const context={};vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../src/common/opening.js'),'utf8').replace(/export /g,'')+'\nglobalThis.make=makeOpeningClock',context);
 const clock=context.make((fn,ms)=>{const n=++id;timers.set(n,{fn,at:now+ms});return n;},n=>timers.delete(n),()=>now,(src,x,y)=>draws.push({src,x,y}),()=>done++);
 function tick(ms){const end=now+ms;for(let guard=0;guard<3000;guard++){const next=[...timers].filter(x=>x[1].at<=end).sort((a,b)=>a[1].at-b[1].at)[0];if(!next){now=end;return;}timers.delete(next[0]);now=next[1].at;next[1].fn();assert.ok(timers.size<=1);}throw Error('Unbounded frame loop');}
 clock.reset();clock.resume();tick(1000);assert.ok(draws[0].x===0);assert.ok(draws.length>=6&&draws.length<=7);assert.ok(draws.every(d=>d.y===0&&d.x===0));
 clock.pause();const n=draws.length;tick(1000);assert.equal(draws.length,n);clock.resume();tick(107001);assert.equal(done,1);assert.equal(timers.size,0);assert.equal(draws.at(-1).src,'/common/opening/frames/0647.jpg');assert.equal(draws.at(-1).x,0);assert.equal(draws.length,648);
});
