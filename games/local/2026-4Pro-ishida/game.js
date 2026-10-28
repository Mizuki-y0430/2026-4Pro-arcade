(() => {
  const canvas = document.querySelector('#game');
  const ctx = canvas.getContext('2d');
  const COLS = 32, ROWS = 20, CELL = 24;
  const MAX_DROPPED = 6;
  const palette = {red:'#b71929',white:'#ffffff',ink:'#181818',grid:'#333333'};
  const scoreEl = document.querySelector('#score');
  const lengthEl = document.querySelector('#length');
  const bestEl = document.querySelector('#best');
  const droppedEl = document.querySelector('#dropped');
  const effectStatusEl = document.querySelector('#effect-status');
  const overlay = document.querySelector('#overlay');
  const startBtn = document.querySelector('#start');
  const titleEl = document.querySelector('#overlay-title');
  const copyEl = document.querySelector('#overlay-copy');
  const eyebrowEl = document.querySelector('#overlay-eyebrow');
  const directions = {up:{x:0,y:-1},down:{x:0,y:1},left:{x:-1,y:0},right:{x:1,y:0}};
  const difficultySettings = {
    easy: {speed:180,minSpeed:145,hazardSpeed:420,minHazardSpeed:350,warning:1100,interval:2000,intervalDrop:3,minInterval:1100,startHazards:1,capStart:2,capEvery:24,waveEvery:70,maxWave:1},
    normal: {speed:160,minSpeed:125,hazardSpeed:340,minHazardSpeed:270,warning:1000,interval:1600,intervalDrop:4,minInterval:850,startHazards:1,capStart:3,capEvery:20,waveEvery:55,maxWave:2},
    hard: {speed:138,minSpeed:105,hazardSpeed:270,minHazardSpeed:210,warning:900,interval:1250,intervalDrop:6,minInterval:600,startHazards:2,capStart:4,capEvery:16,waveEvery:40,maxWave:2}
  };
  let difficulty='normal', collectedOrbs=0, droppedCredits=0;
  let snake, previousSnake, dir, directionQueue, food, hazards, powerup, score, stepMs, lastStep, lastSpawn, lastPowerSpawn, startedAt, running, gameOver, shieldCharges=0, slowUntil=0, magnetUntil=0, growthPending=0, frame=0, lastStatsUpdate=0;
  const leaderboardKey='neon-serpent-leaderboard-v1';
  function loadLeaderboard(){
    const saved=localStorage.getItem(leaderboardKey);
    if(saved){try{const parsed=JSON.parse(saved);return Object.fromEntries(['easy','normal','hard'].map(level=>[level,Array.isArray(parsed[level])?parsed[level].filter(Number.isFinite).sort((a,b)=>b-a).slice(0,3):[]]));}catch{}}
    return {easy:[],normal:[],hard:[]};
  }
  let leaderboard=loadLeaderboard();
  let best=Math.max(Number(localStorage.getItem('neon-serpent-best-units')||0),...Object.values(leaderboard).flat());
  function renderLeaderboard(){for(const level of ['easy','normal','hard'])for(let rank=0;rank<3;rank++){const cell=document.querySelector(`#hs-${level}-${rank}`);cell.textContent=leaderboard[level][rank]===undefined?'---':String(leaderboard[level][rank]).padStart(2,'0');}}
  function recordScore(){if(score>0){leaderboard[difficulty]=[...new Set([score,...leaderboard[difficulty]])].sort((a,b)=>b-a).slice(0,3);localStorage.setItem(leaderboardKey,JSON.stringify(leaderboard));renderLeaderboard();}if(score>best){best=score;localStorage.setItem('neon-serpent-best-units',best);bestEl.textContent=String(best).padStart(3,'0');}}
  bestEl.textContent = String(best).padStart(3,'0');
  renderLeaderboard();
  const randCell = () => ({x:Math.floor(Math.random()*COLS),y:Math.floor(Math.random()*ROWS)});
  const same = (a,b) => a.x===b.x && a.y===b.y;
  function placeFood(){
    const ranges={easy:{x:8,y:5},normal:{x:12,y:7},hard:{x:15,y:9}};
    const range=ranges[difficulty];
    const centerX=Math.floor(COLS/2),centerY=Math.floor(ROWS/2);
    let choices=[];
    for(let y=Math.max(0,centerY-range.y);y<=Math.min(ROWS-1,centerY+range.y);y++){
      for(let x=Math.max(0,centerX-range.x);x<=Math.min(COLS-1,centerX+range.x);x++){
        const cell={x,y};
        if(!snake.some(s=>same(s,cell))&&!hazards.some(h=>same(h,cell))&&!(powerup&&same(powerup,cell)))choices.push(cell);
      }
    }
    if(!choices.length){for(let y=0;y<ROWS;y++)for(let x=0;x<COLS;x++){const cell={x,y};if(!snake.some(s=>same(s,cell))&&!hazards.some(h=>same(h,cell))&&!(powerup&&same(powerup,cell)))choices.push(cell);}}
    food=choices[Math.floor(Math.random()*choices.length)]||randCell();
  }
  function reset(){
    copyEl.className='';
    snake=[{x:15,y:10},{x:14,y:10},{x:13,y:10}];previousSnake=snake.map(s=>({...s}));dir={x:1,y:0};directionQueue=[];hazards=[];powerup=null;shieldCharges=0;slowUntil=0;magnetUntil=0;growthPending=0;score=0;collectedOrbs=0;droppedCredits=0;stepMs=difficultySettings[difficulty].speed;lastStep=performance.now();lastSpawn=0;lastPowerSpawn=lastStep;startedAt=performance.now();running=true;gameOver=false;placeFood();updateStats();updatePowerStatus();overlay.classList.add('hidden');
  }
  function showReady(){reset();running=false;titleEl.textContent='こうせんサバイバー';copyEl.textContent='単位を集めよう！落単は6単位までOK、7単位で終了。';eyebrowEl.textContent='あそびかた';startBtn.innerHTML='スタート <span>→</span>';overlay.classList.remove('hidden');}
  function updateStats(){
    scoreEl.textContent=String(score).padStart(3,'0');
    lengthEl.textContent=String(snake?.length||3).padStart(2,'0');
    const droppedLabel=`${droppedCredits} / ${MAX_DROPPED}`;
    if(droppedEl.textContent!==droppedLabel)droppedEl.textContent=droppedLabel;
    droppedEl.style.color=droppedCredits>=MAX_DROPPED?palette.red:palette.ink;
  }
  function updatePowerStatus(){const now=performance.now();const active=[];if(shieldCharges)active.push('まもり ×'+shieldCharges);if(slowUntil>now)active.push('ゆっくり '+Math.ceil((slowUntil-now)/1000)+'秒');if(magnetUntil>now)active.push('ひきよせ '+Math.ceil((magnetUntil-now)/1000)+'秒');effectStatusEl.textContent=active.join(' · ')||'なし';}
  function spawnPowerup(ts){const types=['shield','slow','magnet','clear','bonus'];let position;do{position={x:Math.floor(Math.random()*COLS),y:Math.floor(Math.random()*ROWS)}}while(snake.some(s=>same(s,position))||hazards.some(h=>same(h,position))||same(food,position));powerup={...position,type:types[Math.floor(Math.random()*types.length)],expiresAt:ts+10000};lastPowerSpawn=ts;}
  function collectPowerup(){const now=performance.now();if(powerup.type==='shield')shieldCharges=1;else if(powerup.type==='slow')slowUntil=Math.max(now,slowUntil)+7000;else if(powerup.type==='magnet')magnetUntil=Math.max(now,magnetUntil)+8000;else if(powerup.type==='clear')hazards=[];else if(powerup.type==='bonus'){score+=2;collectedOrbs+=2;growthPending++;updateStats();}powerup=null;lastPowerSpawn=now;updatePowerStatus();}
  function resolveHazardCollisions(){
    // 落単に当たるのは頭だけ。札1枚で1単位、6単位までは続行できる。
    for(let i=hazards.length-1;i>=0;i--){
      if(hazards[i].active&&same(snake[0],hazards[i])){
        // 接触済みの札を消して、次のフレームで重複カウントしない。
        hazards.splice(i,1);
        if(shieldCharges>0)shieldCharges--;
        else droppedCredits++;
        updateStats();
        updatePowerStatus();
        if(droppedCredits>MAX_DROPPED)return true;
      }
    }
    updatePowerStatus();
    return false;
  }
  function endGame(){
    running=false;gameOver=true;
    recordScore();
    let result, resultClass;
    if(droppedCredits>MAX_DROPPED){result='落単が7単位に！<br>次の挑戦で取り返そう！';resultClass='result-fail';}
    else if(score<=3){result='まだまだこれから！<br>単位を集めていこう！';resultClass='result-mid';}
    else if(score<=5){result='いい調子！<br>次はもっと単位を集めよう！';resultClass='result-mid';}
    else if(score<10){result='単位をしっかり確保！<br>この調子で挑戦しよう！';resultClass='result-close';}
    else{result='キミはエリート<ruby>高専生<rt>こうせんせい</rt></ruby>だ！';resultClass='result-elite';}
    titleEl.textContent='おつかれさま！';
    copyEl.className=`result-message ${resultClass}`;
    copyEl.innerHTML=`<span class="result-phrase">${result}</span><span class="result-score"><ruby>取得単位<rt>しゅとくたんい</rt></ruby> <b>${String(score).padStart(3,'0')}</b> ・ <ruby>落単<rt>らくたん</rt></ruby> ${droppedCredits}単位 ・ <ruby>長<rt>なが</rt></ruby>さ ${snake.length}</span>`;
    eyebrowEl.textContent='けっか';startBtn.innerHTML='もう一度あそぶ <span>→</span>';overlay.classList.remove('hidden');
  }
  function setDirection(d){
    if(!running)return;
    const n=directions[d];
    const heading=directionQueue.length?directionQueue[directionQueue.length-1]:dir;
    if(n.x===-heading.x&&n.y===-heading.y)return;
    if(directionQueue.length>=2)return;
    directionQueue.push(n);
    const now=performance.now();
    if(now-lastStep>=stepMs*.7){tick(now);lastStep=now;}
  }
  function spawnHazard(ts){
    const choices=[];
    // 頭の近く・単位・アイテム・他の落単を避け、盤面全体から選ぶ。
    for(let y=0;y<ROWS;y++)for(let x=0;x<COLS;x++){
      const cell={x,y};
      if(Math.abs(x-snake[0].x)+Math.abs(y-snake[0].y)<6)continue;
      if(snake.some(s=>same(s,cell))||same(food,cell)||(powerup&&same(powerup,cell)))continue;
      if(hazards.some(h=>Math.abs(h.x-x)+Math.abs(h.y-y)<3))continue;
      choices.push(cell);
    }
    if(!choices.length)return;
    const position=choices[Math.floor(Math.random()*choices.length)];
    // 出てすぐ画面外に消えないよう、4マス以上進める向きを選ぶ。
    const headings=Object.values(directions).filter(v=>position.x+v.x*4>=0&&position.x+v.x*4<COLS&&position.y+v.y*4>=0&&position.y+v.y*4<ROWS);
    const settings=difficultySettings[difficulty];
    const elapsed=Math.max(0,(ts-startedAt)/1000);
    const speed=Math.max(settings.minHazardSpeed,settings.hazardSpeed-elapsed*.5);
    hazards.push({...position,prevX:position.x,prevY:position.y,
      v:headings[Math.floor(Math.random()*headings.length)],
      stepMs:speed*(.95+Math.random()*.2),
      spawnedAt:ts,readyAt:ts+settings.warning,lastMove:ts+settings.warning,active:false});
  }
  function spawnWave(ts){const elapsed=(ts-startedAt)/1000;const settings=difficultySettings[difficulty];const maxHazards=Math.min(12,settings.capStart+Math.floor(elapsed/settings.capEvery));const waveSize=Math.min(settings.maxWave,1+Math.floor(elapsed/settings.waveEvery));for(let i=0;i<waveSize&&hazards.length<maxHazards;i++)spawnHazard(ts);lastSpawn=ts;}
  function spawnInterval(ts){const elapsed=(ts-startedAt)/1000;const settings=difficultySettings[difficulty];return Math.max(settings.minInterval,settings.interval-elapsed*settings.intervalDrop);}
  function tick(ts){
    if(directionQueue.length)dir=directionQueue.shift();
    const head={x:snake[0].x+dir.x,y:snake[0].y+dir.y};
    const magnetReach=ts<magnetUntil&&Math.abs(head.x-food.x)+Math.abs(head.y-food.y)<=4;
    const eatsFood=same(head,food)||magnetReach;
    const grows=growthPending>0||(eatsFood&&(collectedOrbs+1)%2===0);
    // しっぽが移動する手では、直後に空く最後のマスへ進める。
    const body=grows?snake:snake.slice(0,-1);
    if(head.x<0||head.x>=COLS||head.y<0||head.y>=ROWS||body.some(s=>same(s,head))){endGame();return;}
    previousSnake=snake.map(s=>({...s}));snake.unshift(head);
    let grow=growthPending>0;if(grow)growthPending--;
    if(eatsFood){score++;collectedOrbs++;if(collectedOrbs%2===0)grow=true;const settings=difficultySettings[difficulty];stepMs=Math.max(settings.minSpeed,stepMs-.8);placeFood();}
    if(powerup&&same(head,powerup))collectPowerup();
    if(!grow)snake.pop();
    if(resolveHazardCollisions()){endGame();return;}
    updateStats();
    updatePowerStatus();
  }
  function hazardInterval(h,ts){return h.stepMs*(ts<slowUntil?2:1);}
  function updateHazards(ts){
    for(const h of hazards){
      if(!h.active){
        if(ts<h.readyAt)continue;
        // 予告中に頭が重なっていたら、その場で実体化させない。
        if(same(snake[0],h)){h.readyAt=ts+400;continue;}
        h.active=true;h.lastMove=ts;
      }
      if(ts-h.lastMove<hazardInterval(h,ts))continue;
      h.prevX=h.x;h.prevY=h.y;
      h.x+=h.v.x;h.y+=h.v.y;h.lastMove=ts;
    }
    hazards=hazards.filter(h=>h.x>=0&&h.x<COLS&&h.y>=0&&h.y<ROWS);
    if(resolveHazardCollisions())endGame();
  }
  function draw(ts){frame++;ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle=palette.ink;ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.strokeStyle=palette.grid;ctx.lineWidth=1;for(let x=0;x<=COLS;x++){ctx.beginPath();ctx.moveTo(x*CELL+.5,0);ctx.lineTo(x*CELL+.5,canvas.height);ctx.stroke()}for(let y=0;y<=ROWS;y++){ctx.beginPath();ctx.moveTo(0,y*CELL+.5);ctx.lineTo(canvas.width,y*CELL+.5);ctx.stroke()}
    // 黒い盤面の四隅を赤で縁取り、筐体のフレームと色をそろえる。
    ctx.save();ctx.strokeStyle=palette.red;ctx.lineWidth=3;
    for(const [x,y,sx,sy] of [[2,2,1,1],[canvas.width-2,2,-1,1],[2,canvas.height-2,1,-1],[canvas.width-2,canvas.height-2,-1,-1]]){
      ctx.beginPath();ctx.moveTo(x+sx*18,y);ctx.lineTo(x,y);ctx.lineTo(x,y+sy*18);ctx.stroke();
    }
    ctx.restore();
    // 単位は認定カード、落単は警告札で見分ける。
    const progress=running?Math.max(0,Math.min(1,(ts-lastStep)/stepMs)):1;
    const lerp=(a,b)=>a+(b-a)*progress;
    if(food)drawCredit(food.x*CELL+12,food.y*CELL+12,ts);
    if(powerup){
      const p=1+Math.sin(frame*.12)*.08;const x=powerup.x*CELL+12,y=powerup.y*CELL+12;
      const glyphs={shield:'盾',slow:'時',magnet:'引',clear:'消',bonus:'+2'};
      ctx.fillStyle=palette.ink;ctx.strokeStyle=palette.white;ctx.lineWidth=2;
      ctx.beginPath();ctx.roundRect(x-10*p,y-10*p,20*p,20*p,5);ctx.fill();ctx.stroke();
      ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle=palette.white;
      ctx.font='bold 12px sans-serif';ctx.fillText(glyphs[powerup.type],x,y+1);
    }
    const points=snake?.map((s,i)=>{const from=previousSnake?.[i]||s;return{x:lerp(from.x,s.x),y:lerp(from.y,s.y)}})||[];
    if(points.length>1){ctx.beginPath();ctx.moveTo(points[points.length-1].x*CELL+12,points[points.length-1].y*CELL+12);for(let i=points.length-2;i>=0;i--)ctx.lineTo(points[i].x*CELL+12,points[i].y*CELL+12);ctx.strokeStyle='#dedede';ctx.lineWidth=15;ctx.lineCap='round';ctx.lineJoin='round';ctx.stroke()}
    points.forEach((s,i)=>{const x=s.x*CELL,y=s.y*CELL;if(i>0){ctx.fillStyle='#888888';ctx.beginPath();ctx.arc(x+12,y+12,4,0,Math.PI*2);ctx.fill();return;}ctx.fillStyle=palette.white;ctx.beginPath();ctx.roundRect(x+2,y+2,CELL-4,CELL-4,5);ctx.fill();const eyeX=dir.x===1?x+17:dir.x===-1?x+7:x+8;const eyeY=dir.y===1?y+17:dir.y===-1?y+7:y+8;ctx.fillStyle=palette.ink;ctx.beginPath();ctx.arc(eyeX,eyeY,2,0,Math.PI*2);ctx.fill();const ex=dir.x===1?eyeX:dir.x===-1?eyeX:eyeX+8,ey=dir.y===1?eyeY:dir.y===-1?eyeY:eyeY+8;ctx.beginPath();ctx.arc(ex,ey,2,0,Math.PI*2);ctx.fill()});
    drawHazards(ts);
  }
  function drawCredit(x,y,ts){
    ctx.save();ctx.translate(x,y+Math.sin(ts/300));
    // 折り返した紙、赤い帯、合格のチェック印。
    ctx.fillStyle='#000';ctx.globalAlpha=.45;
    ctx.beginPath();ctx.roundRect(-15,-12,33,30,3);ctx.fill();ctx.globalAlpha=1;
    ctx.fillStyle=palette.white;ctx.strokeStyle=palette.ink;ctx.lineWidth=1.5;
    ctx.beginPath();ctx.moveTo(-16,-15);ctx.lineTo(9,-15);ctx.lineTo(16,-8);
    ctx.lineTo(16,15);ctx.lineTo(-16,15);ctx.closePath();ctx.fill();ctx.stroke();
    ctx.fillStyle='#dedede';ctx.beginPath();ctx.moveTo(9,-15);ctx.lineTo(9,-8);ctx.lineTo(16,-8);ctx.closePath();ctx.fill();ctx.stroke();
    ctx.fillStyle=palette.red;ctx.fillRect(-14,9,28,4);
    ctx.fillStyle=palette.ink;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.font='900 13px sans-serif';ctx.fillText('単位',0,0);
    ctx.fillStyle=palette.red;ctx.strokeStyle=palette.white;ctx.lineWidth=1.2;
    ctx.beginPath();ctx.arc(-12,-13,6.5,0,Math.PI*2);ctx.fill();ctx.stroke();
    ctx.strokeStyle=palette.white;ctx.lineWidth=2;ctx.lineCap='round';ctx.lineJoin='round';
    ctx.beginPath();ctx.moveTo(-15,-13);ctx.lineTo(-13,-11);ctx.lineTo(-9,-15);ctx.stroke();
    // 取れるアイテムの目印になる、小さなきらめき。
    ctx.globalAlpha=.45+.35*Math.sin(ts/240);ctx.strokeStyle=palette.white;ctx.lineWidth=1.5;
    ctx.beginPath();ctx.moveTo(21,-19);ctx.lineTo(21,-13);ctx.moveTo(18,-16);ctx.lineTo(24,-16);ctx.stroke();
    ctx.restore();
  }
  function drawHazardBadge(x,y,warning,ts){
    ctx.save();ctx.translate(x,y);
    if(warning)ctx.rotate(Math.sin(ts/75)*.055);
    // 角を落とした停止標識。赤い面と白い縁で危険を伝える。
    ctx.fillStyle=palette.red;ctx.strokeStyle=palette.white;ctx.lineWidth=1.8;
    ctx.beginPath();ctx.moveTo(-10,-15);ctx.lineTo(10,-15);ctx.lineTo(17,-8);
    ctx.lineTo(17,8);ctx.lineTo(10,15);ctx.lineTo(-10,15);ctx.lineTo(-17,8);ctx.lineTo(-17,-8);ctx.closePath();ctx.fill();ctx.stroke();
    // つり上がった眉と警告テープで、単位のカードと形も区別する。
    ctx.strokeStyle=palette.white;ctx.lineWidth=2;ctx.lineCap='round';
    ctx.beginPath();ctx.moveTo(-9,-9);ctx.lineTo(-4,-7);ctx.moveTo(9,-9);ctx.lineTo(4,-7);ctx.stroke();
    ctx.fillStyle=palette.white;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.font='900 13px sans-serif';ctx.fillText('落単',0,2);
    ctx.strokeStyle=palette.ink;ctx.lineWidth=2;
    for(let i=-8;i<=8;i+=4){ctx.beginPath();ctx.moveTo(i,11);ctx.lineTo(i+2,13);ctx.stroke();}
    ctx.fillStyle=palette.white;ctx.strokeStyle=palette.ink;ctx.lineWidth=1;
    ctx.beginPath();ctx.arc(14,-14,6,0,Math.PI*2);ctx.fill();ctx.stroke();
    ctx.fillStyle=palette.red;ctx.font='900 10px sans-serif';ctx.fillText('!',14,-13);
    ctx.restore();
  }
  function drawHazards(ts){
    for(const h of hazards){
      const progress=h.active?Math.min(1,Math.max(0,(ts-h.lastMove)/hazardInterval(h,ts))):1;
      const x=(h.prevX+(h.x-h.prevX)*progress)*CELL+12;
      const y=(h.prevY+(h.y-h.prevY)*progress)*CELL+12;
      ctx.save();
      if(!h.active){
        ctx.globalAlpha=.65+.2*Math.sin(ts/90);
        ctx.strokeStyle=palette.red;ctx.lineWidth=2;ctx.setLineDash([3,3]);
        ctx.beginPath();ctx.arc(x,y,23,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
      }
      drawHazardBadge(x,y,!h.active,ts);
      // 矢印で次に進む向きを示す。
      const tipX=x+h.v.x*23,tipY=y+h.v.y*22;
      const baseX=x+h.v.x*18,baseY=y+h.v.y*17;
      ctx.fillStyle=palette.white;ctx.beginPath();ctx.moveTo(tipX,tipY);
      ctx.lineTo(baseX-h.v.y*3,baseY+h.v.x*3);
      ctx.lineTo(baseX+h.v.y*3,baseY-h.v.x*3);ctx.closePath();ctx.fill();
      ctx.restore();
    }
  }
  function loop(ts){
    if(running){
      if(!lastSpawn){for(let i=0;i<difficultySettings[difficulty].startHazards;i++)spawnHazard(ts);lastSpawn=ts;}
      if(powerup&&ts>powerup.expiresAt)powerup=null;
      if(!powerup&&ts-lastPowerSpawn>12000)spawnPowerup(ts);
      if(ts-lastStatsUpdate>500){updateStats();updatePowerStatus();lastStatsUpdate=ts;}
      if(ts-lastSpawn>spawnInterval(ts))spawnWave(ts);
      if(ts-lastStep>stepMs){tick(ts);lastStep=ts;}
      if(running)updateHazards(ts);
    }
    draw(ts);requestAnimationFrame(loop);
  }
  document.addEventListener('keydown',e=>{if(e.code==='Space'||e.key===' '){e.preventDefault();if(!running)reset();return;}const map={ArrowUp:'up',w:'up',W:'up',ArrowDown:'down',s:'down',S:'down',ArrowLeft:'left',a:'left',A:'left',ArrowRight:'right',d:'right',D:'right'};if(map[e.key]){e.preventDefault();setDirection(map[e.key]);}if(e.key==='Enter'&&!running){e.preventDefault();reset();}});
  document.querySelectorAll('[data-dir]').forEach(b=>{b.addEventListener('pointerdown',e=>{e.preventDefault();setDirection(b.dataset.dir);});});
  document.querySelectorAll('[data-difficulty]').forEach(button=>button.addEventListener('click',()=>{
    const nextDifficulty=button.dataset.difficulty;
    if(nextDifficulty===difficulty)return;
    difficulty=nextDifficulty;
    document.querySelectorAll('[data-difficulty]').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));
    showReady();
  }));
  startBtn.addEventListener('click',reset);
  // Show a compact start prompt over the arena; Space or the button starts play.
  showReady();
  requestAnimationFrame(loop);
})();
