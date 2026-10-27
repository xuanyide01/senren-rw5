const test=require('node:test'),assert=require('assert/strict'),http=require('http'),fs=require('fs'),path=require('path');
const R=path.resolve(__dirname,'..');
test('preview stops on native page destruction even when the audio stop callback is detached',()=>{
 const m=require('../tools/emulator-audio.cjs').makeAudioMonitor();
 m.feed('SENREN_RW5 audio playing {"source":"/common/title-original.opus","role":"yoshino"}\n');
 assert.equal(m.get().playing,true);m.feed('SENREN_RW5 destroyed\n');assert.equal(m.get().playing,false);
});
