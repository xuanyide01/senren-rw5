const test=require('node:test'),assert=require('assert/strict'),fs=require('fs'),path=require('path');
test('game sound paths never assign shared system volume or mute',()=>{
 const R=path.resolve(__dirname,'../src');
 const walk=p=>fs.readdirSync(p,{withFileTypes:true}).flatMap(d=>d.isDirectory()?walk(path.join(p,d.name)):[path.join(p,d.name)]);
 for(const p of walk(R).filter(p=>/\.(js|ux)$/.test(p)))assert.doesNotMatch(fs.readFileSync(p,'utf8'),/\baudio\.(?:volume|muted)\s*=/,p);
});
