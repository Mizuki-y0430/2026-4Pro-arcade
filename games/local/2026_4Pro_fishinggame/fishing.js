// 魚ごとの得点、出現率、待ち時間、バーの成功エリア幅を定義します。
// weight が大きい魚ほど抽選で選ばれやすくなります。
const fish=[
  {
  name:'アジ',emoji:'🐟',points:10,weight:30,wait:[1300,2600],zone:26,level:'かんたん'
},
  {
  name:'サバ',emoji:'🐟',points:15,weight:28,wait:[1500,2900],zone:20,level:'ふつう'
},
  {
  name:'タイ',emoji:'🐠',points:25,weight:26,wait:[1800,3500],zone:14,level:'むずかしい'
},
  {
  name:'カレイ',emoji:'🐡',points:40,weight:15,wait:[2000,3800],zone:9,level:'むずかしい'
},
  {
  name:'キンメダイ',emoji:'🐠',points:100,weight:1,wait:[2400,4400],zone:5,level:'激むず'
}];
// ゲームの状態と、画面に表示するスコア・タイマーを管理します。
// state は ready / waiting / bite / recovering / ended の順に変化します。
const AIM_DURATION=5000, NEEDLE_TRAVEL=1000, AUTO_CAST_DELAY=1400;
let aimStarted=0, targetStart=0, aimFrame=null, recastTimer=null;
let state='ready',seconds=60,caught=0,points=0,gameTimer=null,eventTimer=null,artTimer=null,currentFish=null;
const $=id=>document.getElementById(id),cast=$('cast'),hook=$('hook'),msg=$('message'),hint=$('hint'),bobber=$('bobber'),bite=$('bite'),catchArt=$('catchArt'),overlay=$('overlay'),timerDisplay=$('timer');
const timingMeter=$('timingMeter'),targetZone=$('targetZone'),needle=$('needle'),timingName=$('timingName'),timingTime=$('timingTime'),recastProgress=$('recastProgress'),castLabel=$('castLabel'),timingCaption=$('timingCaption');
function setMessage(a,b) {
  msg.textContent=a;
  hint.innerHTML=b
}
// 魚の weight を確率として使う「重み付き抽選」です。
// 全重みの中から乱数の位置を引き、該当する魚を返します。
function weightedFish() {
  let total=fish.reduce((s,f)=>s+f.weight,0),n=Math.random()*total;
  for(const f of fish) {
    n-=f.weight;
    if(n<0)return f
  }
  return fish[0]
}
// 魚の種類に応じた色や形を選び、表示用SVGを組み立てます。
function fishDrawing(f) {
  const art= {
    アジ:['#a9c6c8','#628b99','M24 48 Q50 22 82 43 Q88 49 82 56 Q51 76 24 53 Z','<path d="M49 37 Q56 48 49 61" fill="none" stroke="#f5e4c4" stroke-width="3"/>'],サバ:['#6899a7','#315b70','M24 48 Q50 22 82 43 Q88 49 82 56 Q51 76 24 53 Z','<path d="M42 34l7 9m2-12 7 10m1-8 7 9" stroke="#e7eee0" stroke-width="3"/>'],タイ:['#f08a78','#b74f50','M24 48 Q50 22 82 43 Q88 49 82 56 Q51 76 24 53 Z','<path d="M44 38l6 21m7-22 5 20m6-18 4 14" stroke="#ffd2a2" stroke-width="2.5"/>'],カレイ:['#c99d62','#8d6744','M24 49 Q51 30 83 43 Q91 49 83 57 Q51 69 24 53 Z','<circle cx="67" cy="45" r="2" fill="#6b4937"/><circle cx="73" cy="50" r="2" fill="#6b4937"/>'],キンメダイ:['#f28543','#c84c32','M24 48 Q50 22 82 43 Q88 49 82 56 Q51 76 24 53 Z','<path d="M49 37 Q56 48 49 61m8-21q7 11 0 20" fill="none" stroke="#ffd07b" stroke-width="3"/>']
  }
  [f.name];
  const [body,fin,shape,detail]=art;
  return `<svg viewBox="0 0 112 88" role="img" aria-label="${f.name}のイラスト"><path d="M25 48 7 32 9 65 26 54Z" fill="${fin}" stroke="#15334a" stroke-width="2.5" stroke-linejoin="round"/><path d="${shape}" fill="${body}" stroke="#15334a" stroke-width="2.5"/><path d="M48 35 59 23 69 38M48 61 59 72 69 59" fill="${fin}" stroke="#15334a" stroke-width="2" stroke-linejoin="round"/>${detail}<circle cx="76" cy="46" r="3" fill="#15334a"/><circle cx="77" cy="45" r="1" fill="white"/><path d="M85 52q4 2 7-1" fill="none" stroke="#15334a" stroke-width="1.5" stroke-linecap="round"/></svg>`
}
// タイマーや前回の演出をリセットし、新しい60秒を開始します。
function startGame() {
  clearInterval(gameTimer);
  clearTimeout(eventTimer);
  clearTimeout(recastTimer);
  recastTimer=null;
  recastProgress.hidden=true;
  stopNeedle();
  timingMeter.hidden=true;
  clearTimeout(artTimer);
  catchArt.classList.remove('show');
  seconds=60;
  caught=0;
  points=0;
  state='idle';
  currentFish=null;
  hook.classList.remove('pulse');
  $('score').textContent='0';
  $('points').textContent='0';
  timerDisplay.querySelector('span').textContent=seconds;
  timerDisplay.classList.remove('low');
  document.querySelectorAll('.fish-chip').forEach(c=> {
    c.classList.remove('got');c.textContent='？ '+c.dataset.fish
  });
  overlay.classList.add('hidden');
  cast.disabled=false;
  hook.disabled=true;
  bite.classList.remove('show');
  bobber.classList.remove('show','hit');
  gameTimer=setInterval(()=> {
    seconds--;timerDisplay.querySelector('span').textContent=seconds;if(seconds<=10)timerDisplay.classList.add('low');if(seconds<=0)endGame()
  },1000);
  castLine();
}
// 仕掛けを投げ、魚がかかるまでの待ち時間を設定します。
function castLine() {
  if((state!=='idle'&&state!=='recovering')||seconds<=0)return;
  clearTimeout(recastTimer);
  recastTimer=null;
  recastProgress.hidden=true;
  clearTimeout(artTimer);
  const angler=document.querySelector('.angler');
  angler.classList.remove('casting');
  void angler.offsetWidth;
  angler.classList.add('casting');
  angler.addEventListener('animationend',()=>angler.classList.remove('casting'), {
    once:true
  });
  timingMeter.hidden=true;
  catchArt.classList.remove('show');
  state='waiting';
  castLabel.textContent='魚を待っています';
  cast.disabled=true;
  hook.disabled=true;
  bobber.classList.add('show');
  setMessage('仕掛けを投げた！魚を待とう…','投げる操作は自動。魚がかかったら、黄色のエリアでEnter！');
  currentFish=weightedFish();
  const delay=currentFish.wait[0]+Math.random()*(currentFish.wait[1]-currentFish.wait[0]);
  eventTimer=setTimeout(()=> {
    if(seconds<=0||state!=='waiting')return;
    beginBite();
  },delay)
}
// 針は一定速度で往復。魚ごとの幅だけを変え、見た目と判定で同じ時計を使います。
function needlePosition(now){
  const phase=Math.max(0,now-aimStarted)/NEEDLE_TRAVEL%2;
  return (phase<=1?phase:2-phase)*100;
}
function stopNeedle(){cancelAnimationFrame(aimFrame);aimFrame=null;}
function updateNeedle(now){
  if(state!=='bite')return;
  needle.style.left=`${needlePosition(now)}%`;
  timingTime.textContent=`残り${Math.max(0,Math.ceil((AIM_DURATION-(now-aimStarted))/1000))}秒`;
  if(now-aimStarted>=AIM_DURATION){missFish('timeout');return;}
  aimFrame=requestAnimationFrame(updateNeedle);
}
function beginBite(){
  if(state!=='waiting'||seconds<=0)return;
  clearTimeout(eventTimer);
  state='bite';
  castLabel.textContent='投げ直しは自動';
  aimStarted=performance.now();
  targetStart=8+Math.random()*(84-currentFish.zone);
  targetZone.style.left=`${targetStart}%`;
  targetZone.style.width=`${currentFish.zone}%`;
  needle.style.left='0%';
  timingMeter.hidden=false;
  timingMeter.dataset.result='aiming';
  timingName.textContent=`${currentFish.name} · ${currentFish.level}`;
  timingTime.textContent=`残り${AIM_DURATION/1000}秒`;
  timingCaption.innerHTML='黄色のエリアで <kbd>Enter</kbd> ／ 合わせる';
  hook.disabled=false;
  hook.classList.add('pulse');bobber.classList.add('hit');bite.classList.add('show');
  setMessage('黄色のエリアで止めよう！',`<span class="key">Enter</span> または「合わせる」／チャンスは1回`);
  aimFrame=requestAnimationFrame(updateNeedle);
  eventTimer=setTimeout(()=>missFish('timeout'),AIM_DURATION);
}
// エリア外で押すと失敗。長押しや連打でも1匹分の判定は1回だけです。
function hookFish() {
  if(state!=='bite')return;
  const now=performance.now();
  if(seconds<=0){endGame();return;}
  if(now-aimStarted>=AIM_DURATION){missFish('timeout');return;}
  const position=needlePosition(now);
  needle.style.left=`${position}%`;
  if(position<targetStart||position>targetStart+currentFish.zone){missFish('outside');return;}
  stopNeedle();
  timingMeter.dataset.result='success';
  timingName.textContent='釣り上げ成功！';
  timingTime.textContent=`+${currentFish.points} pt`;
  clearTimeout(eventTimer);
  clearTimeout(artTimer);
  const f=currentFish;
  state='idle';
  caught++;
  points+=f.points;
  $('score').textContent=caught;
  $('points').textContent=points;
  bite.classList.remove('show');
  bobber.classList.remove('show','hit');
  hook.classList.remove('pulse');
  hook.disabled=true;
  cast.disabled=false;
  const chip=document.querySelector(`[data-fish="${f.name}"]`);
  chip.classList.add('got');
  chip.textContent=`${f.emoji} ${f.name}`;
  catchArt.innerHTML=fishDrawing(f)+`<strong>${f.name}　+${f.points} pt</strong>`;
  catchArt.classList.remove('show');
  void catchArt.offsetWidth;
  catchArt.classList.add('show');
  artTimer=setTimeout(()=>catchArt.classList.remove('show'),1450);
  setMessage(`${f.emoji} ${f.name}を釣った！ +${f.points} pt`,'次の仕掛けは自動で投げます。<span class="key">Space</span> ですぐ次へ');
  scheduleNextCast();
}
// 合わせる時間を過ぎたときの後片付けをします。
function missFish(reason='timeout') {
  if(state!=='bite')return;
  clearTimeout(eventTimer);
  stopNeedle();
  needle.style.left=`${needlePosition(performance.now())}%`;
  timingMeter.dataset.result='miss';
  timingName.textContent=reason==='timeout'?'時間切れ！':'エリアから外れた！';
  timingTime.textContent='もう一度挑戦';
  state='idle';
  bite.classList.remove('show');
  bobber.classList.remove('show','hit');
  hook.classList.remove('pulse');
  hook.disabled=true;
  cast.disabled=false;
  setMessage('あっ、逃げられた！次の魚をねらおう。','次の仕掛けは自動で投げます。<span class="key">Space</span> ですぐ次へ');
  scheduleNextCast();
}
// 結果を読む時間を挟んで自動で投げ直す。Space／ボタンなら待たずに次へ進めます。
function scheduleNextCast(){
  clearTimeout(recastTimer);
  state='recovering';
  castLabel.textContent='次を投げる';
  cast.disabled=false;
  timingTime.textContent='次は自動で投げる';
  timingCaption.innerHTML='<kbd>Space</kbd> ですぐ次へ ／ 待っても自動';
  recastProgress.style.setProperty('--recast-duration',`${AUTO_CAST_DELAY}ms`);
  recastProgress.hidden=false;
  recastTimer=setTimeout(()=>{
    recastTimer=null;
    if(state==='recovering'&&seconds>0)castLine();
  },AUTO_CAST_DELAY);
}
// 制限時間が終わったらタイマーを止め、最終結果を表示します。
function endGame() {
  clearInterval(gameTimer);
  clearTimeout(eventTimer);
  clearTimeout(recastTimer);
  recastTimer=null;
  recastProgress.hidden=true;
  clearTimeout(artTimer);
  catchArt.classList.remove('show');
  stopNeedle();
  timingMeter.hidden=true;
  state='ended';
  cast.disabled=true;
  hook.disabled=true;
  bite.classList.remove('show');
  bobber.classList.remove('show','hit');
  hook.classList.remove('pulse');
  timerDisplay.querySelector('span').textContent='0';
  overlay.classList.remove('hidden');
  $('overlayTitle').textContent='チャレンジ終了！';
  $('overlayText').innerHTML=`<strong>${caught}匹</strong>釣って、<strong>${points} pt</strong>獲得！<br>もう一度挑戦して記録を更新しよう。`;
  $('start').textContent='もう一度遊ぶ';
  setMessage('おつかれさま！','「もう一度遊ぶ」で再挑戦');

}
// ボタン操作とキーボード操作を同じゲーム処理につなぎます。
cast.addEventListener('click',castLine);
hook.addEventListener('click',hookFish);
$('start').addEventListener('click',startGame);
document.addEventListener('keydown',e=> {
  if(e.repeat){if(e.code==='Space'||e.code==='Enter')e.preventDefault();return;}
  if(e.code==='Space') {
    e.preventDefault();if(state==='ready'||state==='ended')startGame();else castLine()
  }
  else if(e.code==='Enter') {
    e.preventDefault();if(state==='ready'||state==='ended')startGame();else if(state==='bite')hookFish()
  }

});

// The line follows the resized illustration; game timing and hit detection use the original logic.
const fishingScene=document.querySelector('.scene'), fishingRod=document.querySelector('.angler');
function alignFishingLine(){
  const area=fishingScene.getBoundingClientRect(),rod=fishingRod.getBoundingClientRect();
  const line=document.querySelector('.fishing-line line');
  const width=fishingScene.clientWidth,height=fishingScene.clientHeight;
  line.setAttribute('x1',rod.left-area.left-fishingScene.clientLeft+rod.width*131/180);
  line.setAttribute('y1',rod.top-area.top-fishingScene.clientTop+rod.height*10/180);
  line.setAttribute('x2',width*.61+47);
  line.setAttribute('y2',height*.44);
}
new ResizeObserver(alignFishingLine).observe(fishingScene);
