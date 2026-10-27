// Single original title stream. No role calls, cache creation or system-volume writes.
export const TITLE_CONTENT_MS=234000;
export const TITLE_RESTART_GAP_MS=1200;
export function makeTitleMusic(audio,changed){
 let owned=false,failed=false,track='title',source='',duration=0,seek=0,wanted=false,timer=null,destroyed=false,generation=0,busy=false,announced=false;
 function cancel(){if(timer!==null)clearTimeout(timer);timer=null;}
 function notify(value){if(busy===value)return;busy=value;if(changed)changed(!failed,busy);}
 function state(event){console.log('SENREN_RW5 audio '+event,JSON.stringify({track,source,role:'',loop:false,currentTime:seek,duration,gain:1,positionIsEventEstimate:true}));}
 function close(){if(!owned)return;owned=false;try{audio.stop();}catch(e){}}
 function stop(){wanted=false;generation++;cancel();close();notify(false);}
 function fail(data,code){failed=true;console.error('SENREN_RW5 audio error',JSON.stringify(data),code);stop();if(changed)changed(false,false);}
 function later(fn,ms,token){cancel();timer=setTimeout(()=>{timer=null;if(token!==generation||destroyed)return;fn();},ms);}
 function arm(token){if(!wanted||!owned||failed||track!=='title')return;
  later(()=>{notify(true);later(()=>{close();console.log('SENREN_RW5 title guarded stop');later(()=>{if(wanted&&!failed)title();},TITLE_RESTART_GAP_MS,token);},500,token);},TITLE_CONTENT_MS-500,token);
 }
 function play(src,nextTrack,seconds,offset=0){if(destroyed||failed||!audio)return;const token=++generation;announced=false;source=src;track=nextTrack;duration=seconds;seek=offset;
  try{audio.autoplay=false;audio.loop=false;console.log('SENREN_RW5 audio track '+track,JSON.stringify({source,role:''}));audio.src=source;owned=true;audio.play();if(seek>0)audio.currentTime=seek;if(!announced)arm(token);}catch(e){fail(String(e));}
 }
 function title(){if(wanted&&!failed)play('/common/title-original.opus','title',235.033333);}
 if(audio){audio.onerror=fail;audio.onstop=()=>{if(!owned)state('stopped');};
  audio.onplay=()=>{if(!owned)return;state('playing');if(wanted&&!announced){announced=true;notify(false);arm(generation);}};
  audio.onloadeddata=()=>{if(!owned)return;if(seek>0){try{audio.currentTime=seek;}catch(e){}}state('loaded');};
  audio.onended=()=>{if(!owned)return;state('ended');if(wanted)fail('Unexpected title EOF; automatic replay disabled');};
 }
 return {update(value){if(!value){stop();return;}wanted=true;if(owned||busy||timer!==null||failed||!audio||destroyed)return;title();},
  playOpening(offset){stop();if(failed||!audio||destroyed)return;play('/common/opening/op.mp3','opening',108,Math.max(0,offset||0)/1000);},
  stop,retry(){failed=false;},destroy(){stop();destroyed=true;if(audio){audio.onerror=null;audio.onstop=null;audio.onplay=null;audio.onloadeddata=null;audio.onended=null;}}
 };
}
