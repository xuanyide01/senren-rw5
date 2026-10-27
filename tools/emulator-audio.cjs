// Preview only. Extrapolate the last native position between query events.
exports.makeAudioMonitor=function(now=()=>Date.now()){let pending='',state={playing:false,track:'title',loop:true,revision:0,position:0,duration:0,updatedAt:now()};
 return {get(){return {...state};},feed(chunk){pending+=chunk;const lines=pending.split('\n');pending=lines.pop().slice(-12000);for(const line of lines){
  const track=line.match(/SENREN_RW5 audio track (title-call|title|opening)/);if(track){state.track=track[1];state.loop=false;state.position=0;state.duration=0;state.updatedAt=now();}
  if(/(?:SENREN_RW5|STELLA_RW5) app (created|destroyed)|SENREN_RW5 (destroyed|frame|choice|ending|error|chapter card)\b/.test(line))state.playing=false;
  if(/SENREN_RW5 audio stopped|SENREN_RW5 audio ended|SENREN_RW5 audio error/.test(line)){state.playing=false;state.position=0;state.updatedAt=now();}
  if(/SENREN_RW5 audio playing /.test(line)){state.playing=true;state.revision++;state.position=0;state.updatedAt=now();const json=line.match(/audio playing (\{.*\})/);if(json){try{const data=JSON.parse(json[1]);if(data.source)state.source=data.source;if(typeof data.role==='string')state.role=data.role;if(Number.isFinite(data.gain))state.gain=data.gain;if(Number.isFinite(data.duration))state.duration=data.duration;if(Number.isFinite(data.currentTime))state.position=data.currentTime;if(typeof data.loop==='boolean')state.loop=data.loop;}catch(e){}}}
  const m=line.match(/audio_media_player_query_cb\(\),volume:\d+ position:(\d+) duration:(\d+)/);if(m&&state.playing&&(!state.duration||Math.abs(Number(m[2])/1000-state.duration)<0.1)){state.position=Number(m[1])/1000;state.duration=Number(m[2])/1000;state.updatedAt=now();}
 }}};
};
