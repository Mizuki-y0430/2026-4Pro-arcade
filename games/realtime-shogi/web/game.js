"use strict";
const $=id=>document.getElementById(id);
const names={K:"玉将",R:"飛車",B:"角行",G:"金将",S:"銀将",N:"桂馬",L:"香車",P:"歩兵","+R":"龍王","+B":"龍馬","+S":"成銀","+N":"成桂","+L":"成香","+P":"と金"};
const glyphs={K:"玉",R:"飛",B:"角",G:"金",S:"銀",N:"桂",L:"香",P:"歩","+R":"龍","+B":"馬","+S":"全","+N":"圭","+L":"杏","+P":"と"};
const help={K:"周りの8方向に1マス。相手の駒が利く場所には進めません。",R:"縦・横に何マスでも。駒を飛び越せません。",B:"斜めに何マスでも。駒を飛び越せません。",G:"前の3方向・左右・真後ろに1マス。斜め後ろには進めません。",S:"前の3方向と斜め後ろに1マス。",N:"前に2マス、左右に1マス。途中の駒を飛び越せます。",L:"前に何マスでも。駒を飛び越せません。",P:"前に1マス。取るときも同じ方向です。","+R":"飛車の動きに加え、斜めにも1マス。","+B":"角の動きに加え、縦・横にも1マス。"};
const side=color=>color==="w"?"先手":"後手";
const squareName=(r,c)=>`${9-c}${"一二三四五六七八九"[r]}`;
let token="",state=null,selected=null,busy=false,polling=false,timer,promotionResolve=null,noticeTimer,adjustingCooldown=false;
const cells=[],handButtons={w:{},b:{}};
for(let r=0;r<9;r++)for(let c=0;c<9;c++){
  const button=document.createElement("button");button.type="button";button.className="square";button.dataset.square=`${r},${c}`;button.tabIndex=r===6&&c===4?0:-1;
  const coordinate=document.createElement("span");coordinate.className="coordinate";coordinate.textContent=r===0?String(9-c):c===8?"一二三四五六七八九"[r]:"";
  const piece=document.createElement("span");piece.className="piece";
  const cd=document.createElement("span");cd.className="piece-cd";cd.hidden=true;
  button.append(coordinate,piece,cd);button.addEventListener("click",()=>choose(r,c));
  button.addEventListener("keydown",event=>{
    const delta={ArrowUp:[-1,0],ArrowDown:[1,0],ArrowLeft:[0,-1],ArrowRight:[0,1]}[event.key];
    if(!delta)return;event.preventDefault();const nr=Math.max(0,Math.min(8,r+delta[0])),nc=Math.max(0,Math.min(8,c+delta[1]));
    cells.forEach(cell=>cell.button.tabIndex=-1);cells[nr*9+nc].button.tabIndex=0;cells[nr*9+nc].button.focus();
  });
  cells.push({button,piece,cd});$("board").append(button);
}
for(const [color,label] of [["w","white"],["b","black"]])for(const kind of "RBGSNLP"){
  const button=document.createElement("button");button.type="button";button.disabled=true;button.dataset.drop=kind;
  button.addEventListener("click",()=>{selected=selected===`drop:${kind}`?null:`drop:${kind}`;draw(state);});
  handButtons[color][kind]=button;$(label+"-hand").append(button);
}
function notice(message){clearTimeout(noticeTimer);$("notice").textContent=message;$("notice").hidden=false;noticeTimer=setTimeout(()=>$("notice").hidden=true,6000);}
async function request(path,data){
  const options={headers:{"X-Shogi-Token":token},cache:"no-store"};
  if(data!==undefined){options.method="POST";options.headers["Content-Type"]="application/json";options.body=JSON.stringify(data);}
  const response=await fetch(path,options),value=await response.json();
  if(!response.ok)throw new Error(value.error||"操作できませんでした。");return value;
}
function draw(next){
  if(!next||state&&(next.revision<state.revision||next.stamp<state.stamp))return;
  const previous=state;state=next;
  if(selected?.startsWith("drop:")){if(!state.hands.w[selected.slice(5)])selected=null;}
  else if(selected){const[r,c]=selected.split(",").map(Number);if(state.board[r][c]?.[0]!=="w")selected=null;}
  if(state.mode!=="ai"||state.phase!=="playing")selected=null;
  if($("promotion").open&&(state.mode!=="ai"||state.phase!=="playing"))closePromotion(null);
  const targets=state.legal_moves[selected]||[],last=state.history.at(-1);
  for(let r=0;r<9;r++)for(let c=0;c<9;c++){
    const {button,piece,cd}=cells[r*9+c],code=state.board[r][c],isAt=p=>p&&p[0]===r&&p[1]===c;
    button.className=`square ${code?"occupied":""} ${selected===`${r},${c}`?"selected":""} ${targets.some(isAt)?"legal":""} ${last&&(isAt(last.from)||isAt(last.to))?"last":""} ${Object.values(state.checks).some(isAt)?"check":""}`;
    button.setAttribute("aria-label",`${squareName(r,c)} ${code?side(code[0])+"の"+names[code.slice(1)]:"空きマス"}`);
    button.setAttribute("aria-pressed",String(selected===`${r},${c}`));
    button.disabled=busy||state.mode!=="ai"||state.phase!=="playing";
    piece.textContent=code?glyphs[code.slice(1)]:"";piece.className=`piece ${code?.[0]==="b"?"enemy":""} ${code?.includes("+")?"promoted":""}`;
    const remain=state.piece_cooldowns[`${r},${c}`]||0;cd.hidden=!remain;cd.textContent=(remain/1000).toFixed(1);
  }
  for(const color of ["w","b"])for(const kind of "RBGSNLP"){
    const button=handButtons[color][kind],count=state.hands[color][kind];
    button.textContent=`${glyphs[kind]} ${count}`;button.setAttribute("aria-label",`${side(color)}の持ち駒 ${names[kind]} ${count}枚`);
    button.disabled=color!=="w"||!count||busy||state.mode!=="ai"||state.phase!=="playing";
    button.classList.toggle("selected",color==="w"&&selected===`drop:${kind}`);
    button.setAttribute("aria-pressed",String(color==="w"&&selected===`drop:${kind}`));
  }
  let kind=selected?.startsWith("drop:")?selected.slice(5):null;
  if(selected&&!kind){const[r,c]=selected.split(",").map(Number);kind=state.board[r][c]?.slice(1);}
  $("piece-name").textContent=kind?names[kind]:"駒を選んでみよう";
  $("piece-help").textContent=kind?(selected.startsWith("drop:")?"持ち駒は空きマスへ打てます。緑の印から選んでください。":help[kind]||help.G):"緑の印が、いま指せる場所です。王手を放置する手は指せません。";
  if(previous&&state.move_count===previous.move_count+1&&last?.from&&state.animation&&!matchMedia("(prefers-reduced-motion: reduce)").matches){
    const[r,c]=last.to,[sr,sc]=last.from,cell=cells[r*9+c],rect=cell.button.getBoundingClientRect();
    const rotate=state.board[r][c]?.[0]==="b"?" rotate(180deg)":"";
    cell.piece.animate([{transform:`translate(${(sc-c)*rect.width}px,${(sr-r)*rect.height}px)${rotate}`},{transform:`translate(0,0)${rotate}`}],{duration:220,easing:"ease-out"});
  }
  if(!busy){
    $("mode").value=state.mode;$("level").value=state.level;$("animation").checked=state.animation;
    if(!adjustingCooldown){$("cooldown").value=state.cooldown_ms;$("cooldown-value").textContent=`${(state.cooldown_ms/1000).toFixed(1)}秒`;}
  }
  for(const id of ["mode","level","cooldown","animation","start","reset"])$(id).disabled=busy;
  $("cooldown").disabled=busy||state.mode==="aivsai";
  $("start").textContent=state.active?"停止 ■":state.game_over?"もう一局 ▶":state.phase==="paused"?(state.mode==="aivsai"?"新しい対局 ▶":"再開 ▶"):"スタート ▶";
  $("start").classList.toggle("running",state.active);
  const checked=Object.entries(state.checks).filter(([,p])=>p).map(([c])=>side(c));
  const status={ready:"先手の駒で挑戦！",countdown:`開始まで ${state.countdown}…`,playing:checked.length?`${checked.join("・")}に王手！`:state.mode==="ai"?"あなたは先手！":"AI同士の対局中",paused:"停止中",finished:state.winner==="draw"?"引き分け！":`${side(state.winner)}の勝ち！`};
  $("status").textContent=status[state.phase];
  $("status-detail").textContent=state.rematch_in?`${state.reason}。${state.rematch_in}秒後に次の対局へ。`:state.phase==="finished"?`${state.reason}。もう一局に挑戦しよう！`:state.mode==="aivsai"?"各駒に2秒のクールタイム。AIは交互に1秒間隔で指します。":"相手を待たずに指せます。AIは1秒ごとに動きます。";
  $("countdown").hidden=state.phase!=="countdown";$("countdown").textContent=state.countdown;
  $("play-hint").textContent=state.mode==="aivsai"?"AIの対局を観戦。終局3秒後に次局へ。":"自分の駒、または持ち駒 → 緑の移動先。ターン待ちはありません。";
  $("matches").textContent=`先手 ${state.match_score.w}勝 / 後手 ${state.match_score.b}勝 / 引分 ${state.match_score.draw}${state.match_no?` · 第${state.match_no}局`:""}`;
  for(const[color,label]of[["w","white"],["b","black"]]){
    const remain=state.cooldowns[color];
    if(state.mode==="aivsai"){
      const count=Object.keys(state.piece_cooldowns).filter(key=>{const[r,c]=key.split(",").map(Number);return state.board[r][c]?.[0]===color;}).length;
      $(label+"-cd").textContent=`${side(color)}：${count?`${count}駒が待機中`:"動かせる"}`;$(label+"-bar").value=count/20*100;
    }else{
      $(label+"-cd").textContent=`${side(color)}：${remain?`あと${(remain/1000).toFixed(1)}秒`:"動かせる"}`;
      $(label+"-bar").value=Math.min(100,remain/Math.max(1,color==="w"?state.cooldown_ms:1000)*100);
    }
  }
  if(!previous||previous.revision!==state.revision){
    $("history").replaceChildren(...state.history.map(move=>{const li=document.createElement("li");li.textContent=`${side(move.piece[0])} ${squareName(...move.to)} ${names[move.piece.slice(1)]}${move.drop?"打":move.promote?"成":""}${move.captured?"（"+names[move.captured.slice(1)]+"を取る）":""}`;return li;}));
    $("history").scrollTop=$("history").scrollHeight;
  }
  $("move-count").textContent=`${state.move_count}手`;
}
async function action(operation,data={}){
  if(busy||!token)return;busy=true;draw(state);
  try{draw(await request(`/api/${operation}`,data));}
  catch(error){notice(error.message);try{draw(await request("/api/state"));}catch{}}
  finally{busy=false;draw(state);}
}
async function choose(r,c){
  if(busy||promotionResolve||!state||state.phase!=="playing"||state.mode!=="ai")return;
  const options=(state.legal_moves[selected]||[]).filter(([er,ec])=>er===r&&ec===c);
  if(selected&&options.length){
    const source=selected;let promote=options[0][2];
    if(options.some(m=>m[2])&&options.some(m=>!m[2])){promote=await askPromotion();if(promote===null)return;}
    const data=source.startsWith("drop:")?{drop:source.slice(5),er:r,ec:c}:{sr:Number(source.split(",")[0]),sc:Number(source.split(",")[1]),er:r,ec:c,promote};
    selected=null;await action("move",data);return;
  }
  selected=state.board[r][c]?.[0]==="w"?`${r},${c}`:null;draw(state);
}
function askPromotion(){return new Promise(resolve=>{promotionResolve=resolve;$("promotion").showModal();});}
function closePromotion(value){$("promotion").close();const resolve=promotionResolve;promotionResolve=null;resolve?.(value);}
document.querySelectorAll("[data-promotion]").forEach(button=>button.addEventListener("click",()=>closePromotion(button.dataset.promotion==="yes")));
$("promotion-cancel").addEventListener("click",()=>closePromotion(null));
$("promotion").addEventListener("cancel",event=>{event.preventDefault();closePromotion(null);});
$("start").addEventListener("click",()=>action(state.active?"stop":"start"));
$("reset").addEventListener("click",()=>{selected=null;action("reset");});
for(const id of ["mode","level","animation"])$(id).addEventListener("change",()=>action("settings",{mode:$("mode").value,level:$("level").value,animation:$("animation").checked}));
$("cooldown").addEventListener("input",()=>{adjustingCooldown=true;$("cooldown-value").textContent=`${(Number($("cooldown").value)/1000).toFixed(1)}秒`;});
$("cooldown").addEventListener("change",()=>{adjustingCooldown=false;action("settings",{cooldown_ms:Number($("cooldown").value)});});
for(const name of ["settings","help"]){
  $(name+"-open").addEventListener("click",()=>$(name+"-dialog").showModal());
  $(name+"-close").addEventListener("click",()=>$(name+"-dialog").close());
}
document.addEventListener("keydown",event=>{if(!$("settings-dialog").open&&!$("help-dialog").open&&!$("promotion").open&&["q","Q","Escape"].includes(event.key)&&state?.active){event.preventDefault();action("stop");}});
async function refresh(){if(polling||busy)return;polling=true;try{draw(await request("/api/state"));}catch(error){notice(error.message);}finally{polling=false;}}
async function boot(){try{const session=await request("/api/session");token=session.token;draw(session.state);timer=setInterval(refresh,200);}catch(error){$("status").textContent="接続できませんでした";notice(error.message);}}
window.addEventListener("pagehide",()=>clearInterval(timer));boot();
