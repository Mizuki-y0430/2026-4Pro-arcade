"use strict";
const $=id=>document.getElementById(id);
const glyphs={wK:"♔",wQ:"♕",wR:"♖",wB:"♗",wN:"♘",wP:"♙",bK:"♚",bQ:"♛",bR:"♜",bB:"♝",bN:"♞",bP:"♟"};
const names={K:"キング",Q:"クイーン",R:"ルーク",B:"ビショップ",N:"ナイト",P:"ポーン"};
const colorName=color=>color==="w"?"白":"赤";
const squareName=(r,c)=>`${String.fromCharCode(97+c)}${8-r}`;
let token="",state=null,selected=null,busy=false,polling=false,timer=null,promotionResolve=null,noticeTimer,adjustingCooldown=false;
const cells=[];
for(let r=0;r<8;r++)for(let c=0;c<8;c++){
  const button=document.createElement("button");button.type="button";button.className="square";button.dataset.square=`${r},${c}`;button.tabIndex=r===6&&c===4?0:-1;
  const coordinate=document.createElement("span");coordinate.className="coordinate";coordinate.textContent=c===0?String(8-r):r===7?String.fromCharCode(97+c):"";
  const piece=document.createElement("span");piece.className="piece";
  const cd=document.createElement("span");cd.className="piece-cd";cd.hidden=true;
  button.append(coordinate,piece,cd);button.addEventListener("click",()=>choose(r,c));
  button.addEventListener("keydown",event=>{
    const delta={ArrowUp:[-1,0],ArrowDown:[1,0],ArrowLeft:[0,-1],ArrowRight:[0,1]}[event.key];
    if(!delta)return;event.preventDefault();const nr=Math.max(0,Math.min(7,r+delta[0])),nc=Math.max(0,Math.min(7,c+delta[1]));
    cells.forEach(cell=>cell.button.tabIndex=-1);cells[nr*8+nc].button.tabIndex=0;cells[nr*8+nc].button.focus();
  });
  cells.push({button,piece,cd});$("board").append(button);
}

function notice(message){clearTimeout(noticeTimer);$("notice").textContent=message;$("notice").hidden=false;noticeTimer=setTimeout(()=>$("notice").hidden=true,6000);}
async function request(path,data){
  const options={headers:{"X-Chess-Token":token},cache:"no-store"};
  if(data!==undefined){options.method="POST";options.headers["Content-Type"]="application/json";options.body=JSON.stringify(data);}
  const response=await fetch(path,options);const value=await response.json();
  if(!response.ok)throw new Error(value.error||"操作できませんでした。");return value;
}
function draw(next){
  if(state&&(next.revision<state.revision||next.stamp<state.stamp))return;
  const previous=state;state=next;
  if(selected&&(!state.board[selected[0]][selected[1]]||state.board[selected[0]][selected[1]][0]!=="w"))selected=null;
  if(state.mode!=="ai"||state.phase!=="playing")selected=null;
  const targets=selected?(state.legal_moves[selected.join(",")]||[]):[];
  const last=state.history.at(-1);
  for(let r=0;r<8;r++)for(let c=0;c<8;c++){
    const {button,piece,cd}=cells[r*8+c],code=state.board[r][c];
    const isAt=position=>position&&position[0]===r&&position[1]===c;
    button.className=`square ${(r+c)%2?"dark":""} ${code?"occupied":""} ${isAt(selected)?"selected":""} ${targets.some(isAt)?"legal":""} ${last&&(isAt(last.from)||isAt(last.to))?"last":""} ${Object.values(state.checks).some(isAt)?"check":""}`;
    button.setAttribute("aria-label",`${squareName(r,c)} ${code?colorName(code[0])+"の"+names[code[1]]:"空きマス"}`);
    button.setAttribute("aria-pressed",String(Boolean(isAt(selected))));
    button.disabled=busy||state.mode!=="ai"||state.phase!=="playing";
    piece.textContent=glyphs[code]||"";piece.className=`piece ${code?.[0]==="w"?"white":"black"}`;
    const remain=state.piece_cooldowns[`${r},${c}`]||0;cd.hidden=!remain;cd.textContent=(remain/1000).toFixed(1);
  }
  // 盤面はPythonの結果を表示する。アニメーションだけをブラウザーが担当。
  if(previous&&state.move_count===previous.move_count+1&&last&&state.animation&&!matchMedia("(prefers-reduced-motion: reduce)").matches){
    const [r,c]=last.to,[sr,sc]=last.from;const piece=cells[r*8+c].piece,rect=cells[r*8+c].button.getBoundingClientRect();
    piece.animate([{transform:`translate(${(sc-c)*rect.width}px,${(sr-r)*rect.height}px)`},{transform:"translate(0,0)"}],{duration:220,easing:"ease-out"});
  }
  // 設定を送信している間は、ユーザーが今選んだ値を元の値に戻さない。
  if(!busy){
    $("mode").value=state.mode;$("level").value=state.level;$("animation").checked=state.animation;
    if(!adjustingCooldown){$("cooldown").value=state.cooldown_ms;$("cooldown-value").textContent=`${(state.cooldown_ms/1000).toFixed(1)}秒`;}
  }
  for(const id of ["mode","level","cooldown","animation","start","reset"])$(id).disabled=busy;
  $("cooldown").disabled=busy||state.mode==="aivsai";
  $("start").textContent=state.active?"停止":state.game_over||state.phase==="finished"?"もう一局":state.phase==="paused"?(state.mode==="aivsai"?"新しい対局 ▶":"再開"):"スタート";
  $("start").classList.toggle("running",state.active);
  const status={ready:"白の駒で挑戦！",countdown:`開始まで ${state.countdown}…`,playing:state.mode==="ai"?"あなたは白！":"AI同士の対局中",paused:"停止中",finished:state.winner==="draw"?"引き分け！":`${colorName(state.winner)}の勝ち！`};
  $("status").textContent=status[state.phase];
  $("status-detail").textContent=state.rematch_in?`${state.rematch_in}秒後に次の対局へ。Q・Escで停止できます。`:state.phase==="finished"?"対局終了。もう一局に挑戦しよう！":state.mode==="aivsai"?"駒ごとに2秒のクールタイム。白と赤が交互に動きます。":"スタートして駒と移動先を選ぼう。AIは1秒ごとに動きます。";
  $("countdown").hidden=state.phase!=="countdown";$("countdown").textContent=state.countdown;
  $("play-hint").textContent=state.mode==="aivsai"?"AIの対局を観戦。停止ボタン・Q・Escで停止できます。":"白の駒 → 移動先をクリック。ターン待ちはありません。";
  $("key-hint").textContent=state.mode==="aivsai"?"終局後3秒で次局へ。停止後は「新しい対局」で最初から。":"矢印キーでマス移動・Enterで選択 / Q・Escで停止";
  $("matches").textContent=`白 ${state.match_score.w}勝 / 赤 ${state.match_score.b}勝 / 引分 ${state.match_score.draw}${state.match_no?` · 第${state.match_no}局`:""}`;
  for(const [color,label]of[["w","white"],["b","black"]]){
    let remain=state.cooldowns[color];
    if(state.mode==="aivsai"){
      const count=Object.keys(state.piece_cooldowns).filter(key=>{const[r,c]=key.split(",").map(Number);return state.board[r][c]?.[0]===color;}).length;
      $(label+"-cd").textContent=`${colorName(color)}：${count?`${count}駒が待機中`:"動かせる"}`;$(label+"-bar").value=count/16*100;
    }else{
      $(label+"-cd").textContent=`${colorName(color)}：${remain?`あと${(remain/1000).toFixed(1)}秒`:"動かせる"}`;
      $(label+"-bar").value=remain/Math.max(1,color==="w"?state.cooldown_ms:1000)*100;
    }
  }
  if(!previous||previous.revision!==state.revision){
    $("history").replaceChildren(...state.history.map(move=>{const li=document.createElement("li");li.textContent=`${colorName(move.piece[0])} ${names[move.piece[1]]} ${squareName(...move.from)} → ${squareName(...move.to)}${move.captured?" × "+names[move.captured[1]]:""}`;return li;}));
    $("history").scrollTop=$("history").scrollHeight;
    for(const[color,label]of[["w","white"],["b","black"]]){
      const captured=state.captures[color].map(code=>{
        const piece=document.createElement("span");piece.className=`captured-piece ${code[0]==="w"?"white":"black"}`;
        piece.textContent=glyphs[code];piece.setAttribute("aria-label",`${colorName(code[0])}の${names[code[1]]}`);return piece;
      });
      $(label+"-captures").replaceChildren(...(captured.length?captured:[document.createTextNode("—")]));
    }
  }
  $("move-count").textContent=`${state.move_count}手`;
}
async function action(operation,data={}){
  if(busy||!token)return;busy=true;draw(state);
  try{draw(await request(`/api/${operation}`,data));}
  catch(error){notice(error.message);try{draw(await request("/api/state"));}catch{}}
  finally{busy=false;if(state)draw(state);}
}
async function choose(r,c){
  if(busy||!state||state.phase!=="playing"||state.mode!=="ai")return;
  const targets=selected?(state.legal_moves[selected.join(",")]||[]):[];
  if(selected&&targets.some(([er,ec])=>er===r&&ec===c)){
    const [sr,sc]=selected;let promotion="Q";
    if(state.board[sr][sc]==="wP"&&r===0){promotion=await askPromotion();if(!promotion)return;}
    selected=null;await action("move",{sr,sc,er:r,ec:c,promotion});return;
  }
  selected=state.board[r][c]?.[0]==="w"?[r,c]:null;draw(state);
}
function askPromotion(){return new Promise(resolve=>{promotionResolve=resolve;$("promotion").showModal();});}
function closePromotion(value){$("promotion").close();const resolve=promotionResolve;promotionResolve=null;resolve?.(value);}
document.querySelectorAll("[data-promotion]").forEach(button=>button.addEventListener("click",()=>closePromotion(button.dataset.promotion)));
$("promotion-cancel").addEventListener("click",()=>closePromotion(null));
$("promotion").addEventListener("cancel",event=>{event.preventDefault();closePromotion(null);});
$("start").addEventListener("click",()=>action(state.active?"stop":"start"));
$("reset").addEventListener("click",()=>{selected=null;action("reset");});
for(const id of ["mode","level","animation"])$(id).addEventListener("change",()=>action("settings",{mode:$("mode").value,level:$("level").value,animation:$("animation").checked}));
$("cooldown").addEventListener("input",()=>{adjustingCooldown=true;$("cooldown-value").textContent=`${(Number($("cooldown").value)/1000).toFixed(1)}秒`;});
$("cooldown").addEventListener("change",()=>{adjustingCooldown=false;action("settings",{cooldown_ms:Number($("cooldown").value)});});
for(const name of ["settings","help"]){$(name+"-open").addEventListener("click",()=>$(name+"-dialog").showModal());$(name+"-close").addEventListener("click",()=>$(name+"-dialog").close());}

document.addEventListener("keydown",event=>{if(!$("settings-dialog").open&&!$("help-dialog").open&&!$("promotion").open&&["q","Q","Escape"].includes(event.key)&&state?.active){event.preventDefault();action("stop");}});
async function refresh(){if(polling||busy)return;polling=true;try{draw(await request("/api/state"));}catch(error){notice(error.message);}finally{polling=false;}}
async function boot(){
  try{const session=await request("/api/session");token=session.token;draw(session.state);timer=setInterval(refresh,200);}
  catch(error){$("status").textContent="接続できませんでした";notice(error.message);}
}
window.addEventListener("pagehide",()=>clearInterval(timer));boot();
