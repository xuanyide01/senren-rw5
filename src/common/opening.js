// The original MAIN00 movie 32 belongs between prologue and chapter 1.
export const OPENING_DURATION=108000;
export const OPENING_FRAMES=648;
export const OPENING_FPS=6;
export const OPENING_INTERVAL=1000/OPENING_FPS;
export function wantsOpening(s){return s.chapter==='n0'&&s.cursor===557&&s.openingDone!==true;}
// Elapsed-time clock prevents slow image loads from extending the movie/audio.
// One clipped image and at most one timeout; no desktop VM on the watch.
export function makeOpeningClock(schedule,cancel,now,draw,done){
 let timer=null,elapsed=0,started=0,running=false,index=-1,generation=0;
 function path(strip){return '/common/opening/frames/'+('000'+strip).slice(-4)+'.jpg';}
 function show(){const frame=Math.min(OPENING_FRAMES-1,Math.floor(elapsed*OPENING_FPS/1000));if(frame===index)return;index=frame;const tile=frame%4;draw(path(frame),0,0,frame);}
 function position(){return Math.min(OPENING_DURATION,elapsed+(running?Math.max(0,now()-started):0));}
 function pause(){elapsed=position();running=false;generation++;if(timer!==null)cancel(timer);timer=null;}
 function tick(){if(!running)return;timer=null;elapsed=position();started=now();if(elapsed>=OPENING_DURATION){running=false;generation++;done();return;}show();const due=Math.min(OPENING_DURATION,Math.ceil((index+1)*1000/OPENING_FPS)),token=generation;timer=schedule(()=>{if(token===generation&&running)tick();},Math.max(16,Math.ceil(due-elapsed)));}
 return {reset(){pause();elapsed=0;index=-1;show();},resume(){if(running)return;running=true;started=now();tick();},pause,position,stop(){pause();elapsed=0;index=-1;}};
}
