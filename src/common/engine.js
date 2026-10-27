// Bounded reader state: current graph node, one text chunk, original choice flags.
const clone=x=>JSON.parse(JSON.stringify(x));
function create(graph,progress){return {format:1,node:graph.initial,index:0,flag:{},progress:clone(progress||{}),history:[]};}
function checkpoint(state){const {history,...saved}=state;return clone(saved);}
function restore(graph,saved){if(!saved||saved.format!==1||!graph.nodes[saved.node]||!Number.isInteger(saved.index)||saved.index<0||saved.index>graph.nodes[saved.node].count||!saved.flag||typeof saved.flag!=='object')throw Error('存档数据不匹配');return {...clone(saved),progress:clone(saved.progress||{}),history:[]};}
function remember(state){state.history.push(checkpoint(state));if(state.history.length>24)state.history.shift();}
function flags(graph,state){const out=Object.assign({},state.flag);for(const key of Object.keys(graph.flagRules))out[key]=graph.flagRules[key].reduce((v,r)=>v+(state.flag[r[0]]===r[1]?r[2]:0),0);out.checkAnyClear=['yoshino','mako','murasame','lena','koharu','roka'].some(x=>state.progress[x]);return out;}
function matches(test,graph,state){if(!test)return true;const f=flags(graph,state);const result=test[0].split('&&').every(part=>{part=part.trim();if(part==='.checkAnyClear')return f.checkAnyClear;const m=/^(\w+)\s*(==|!=)\s*(\d+)$/.exec(part);if(!m)throw Error('未知分支条件');const equal=(f[m[1]]||0)===+m[3];return m[2]==='=='?equal:!equal;});return test[1]?!result:result;}
function locate(graph,state){for(let steps=0;steps<1000;steps++){
 if(state.node==='@end')return {type:'end'};
 const n=graph.nodes[state.node];if(!n)throw Error('剧情连接缺失');
 if(state.index<n.count){if(n.ops.indexOf(state.index)>=0)return {type:'op'};let offset=state.index;for(const c of n.chunks){if(offset<c.count)return {type:'text',file:c.file,index:offset,title:n.title,chapter:n.chapter};offset-=c.count;}throw Error('剧情块下标错误');}
 if(state.progression!=='chapter')for(const key of n.complete)state.progress[key]=true;
 if(n.choices.length)return {type:'choice',items:n.choices};
 const next=n.next.find(x=>matches(x.when,graph,state));if(!next)throw Error('剧情意外中断');state.node=next.to;state.index=0;
}throw Error('剧情连接超出范围');}
function advance(graph,state){const p=locate(graph,state);if(p.type!=='text'&&p.type!=='op')return p;remember(state);state.index++;return locate(graph,state);}
function choose(graph,state,index){const p=locate(graph,state);if(p.type!=='choice')throw Error('当前位置没有选项');const o=p.items[index];if(!o)throw Error('选项不存在');remember(state);state.flag[o.effect[0]]=o.effect[1];state.node=o.to;state.index=0;return locate(graph,state);}
function skipChapter(graph,state){const initial=locate(graph,state);if(initial.type!=='text')return initial;remember(state);for(let steps=0;steps<1000;steps++){
 const n=graph.nodes[state.node],stop=n.ops.find(x=>x>state.index);state.index=stop===undefined?n.count:stop;
 const p=locate(graph,state);if(p.type!=='text'||p.chapter!==initial.chapter)return p;
}throw Error('章节跳转超出范围');}
function previous(graph,state){if(!state.history.length)return locate(graph,state);const h=state.history,s=h.pop();Object.assign(state,s,{history:h});return locate(graph,state);}
function trueAvailable(){return false;}function startTrue(){return false;}
export {create,checkpoint,restore,locate,advance,choose,skipChapter,previous,flags,matches,trueAvailable,startTrue};
