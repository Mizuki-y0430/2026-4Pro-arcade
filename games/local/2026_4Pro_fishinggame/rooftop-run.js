// canvas はゲームを描く領域、ctx は2D描画用の道具です。
// W / H はキャンバスの大きさ、ground は地面の高さです。
const canvas=document.querySelector('#game'),ctx=canvas.getContext('2d'),$=id=>document.getElementById(id),W=960,H=500,ground=375;
let mode='ready',last=0,world=0,distance=0,speed=300,playerY=0,vy=0,sliding=0,runT=0,roofs=[],obstacles=[],nextRoof=0,nextObs=0,buildings=[],best=Number(localStorage.getItem('rooftop-best')||0),gapWarn=0;
// localStorageからベスト記録を読み込み、画面に表示します。
$('best').textContent=best;
// プレイヤーや障害物を初期化して、ゲームループを開始します。
function reset() {
  world=0;
  distance=0;
  speed=300;
  playerY=0;
  vy=0;
  sliding=0;
  runT=0;
  roofs=[ {
    x:-100,w:1000,gap:false
  }];
  obstacles=[];
  nextRoof=900;
  nextObs=1500;
  mode='play';
  last=performance.now();
  $('overlay').classList.add('hidden');
  $('message').textContent='いい走り！屋上の先をよく見て。';
  requestAnimationFrame(loop)
}
// 地上にいるときだけジャンプできます。vy は上向きの初速です。
function jump() {
  if(mode==='ready'||mode==='over') {
    reset();
    return
  }
  if(mode==='play'&&playerY===0) {
    vy=-700;
    sliding=0
  }

}
// 先の地形を追加します。ランダムに屋上のすき間を作ります。
function addRoof() {
  let gap= Math.random()<.29,w=gap?150+Math.random()*75:700+Math.random()*420;
  roofs.push( {
    x:nextRoof,w,gap
  });
  nextRoof+=w+(gap?0:0)
}
// 換気扇・看板・ドローンからランダムに障害物を追加します。
function addObstacle() {
  const r=Math.random();
  let type=r<.38?'fan':r<.69?'sign':'drone';
  obstacles.push( {
    x:nextObs,type,phase:Math.random()*6,y:0,passed:false
  });
  nextObs+=620+Math.random()*340
}
function roundRect(x,y,w,h,r,fill) {
  ctx.fillStyle=fill;
  ctx.beginPath();
  ctx.roundRect(x,y,w,h,r);
  ctx.fill()
}
// 空、太陽、雲、遠景のビルを描きます。worldに応じて横に流します。
function drawSky() {
  let g=ctx.createLinearGradient(0,0,0,H);
  g.addColorStop(0,'#f7a17b');
  g.addColorStop(.57,'#ffd18b');
  g.addColorStop(1,'#f7d8a5');
  ctx.fillStyle=g;
  ctx.fillRect(0,0,W,H);
  ctx.fillStyle='#ffe99b';
  ctx.beginPath();
  ctx.arc(760,115,50,0,Math.PI*2);
  ctx.fill();
  for(let i=0;i<9;i++) {
    let x=((i*173-world*.11)%1200+1200)%1200-100,y=98+(i%3)*36;
    roundRect(x,y,95,18,12,'#fff0d4aa');
    roundRect(x+18,y-10,35,24,12,'#fff0d4aa')
  }
  // distant skyline
   for(let i=0;i<20;i++) {
    let x=((i*75-world*.22)%1600+1600)%1600-200,h=95+(i*47%145);
    ctx.fillStyle=i%2?'#897b91':'#7a7890';
    ctx.fillRect(x,ground-h-15,58,h+15);
    ctx.fillStyle='#ffd58a88';
    for(let yy=ground-h+9;yy<ground-22;yy+=21)for(let xx=x+9;xx<x+53;xx+=17)ctx.fillRect(xx,yy,7,9)
  }

}
// 現在画面に見える屋上だけを描画します。
function drawRoof() {
  for(const r of roofs) {
    let x=r.x-world;
    if(x>W||x+r.w<0)continue;
    if(r.gap) {
      continue
    }
    ctx.fillStyle='#40475e';
    ctx.fillRect(x,ground,r.w,H-ground);
    ctx.fillStyle='#687087';
    ctx.fillRect(x,ground,r.w,15);
    ctx.fillStyle='#9ba1ae';
    ctx.fillRect(x,ground+15,r.w,5);
    for(let i=0;i<r.w;i+=80) {
      ctx.fillStyle='#ffffff10';
      ctx.fillRect(x+i,ground+26,35,2)
    }
    ctx.fillStyle='#d4a36f';
    ctx.fillRect(x+30,ground+28,30,8);
    ctx.fillRect(x+r.w-80,ground+26,45,11)
  }

}
// 障害物の種類ごとにcanvasの図形を描き分けます。
function drawObstacle(o) {
  let x=o.x-world, bob=Math.sin(runT*3+o.phase)*10,y=ground-20+ bob;
  if(x<-80||x>W+80)return;
  ctx.save();
  if(o.type==='fan') {
    roundRect(x-30,ground-42,60,40,8,'#8c9ba6');
    ctx.fillStyle='#f5bd51';
    ctx.beginPath();
    ctx.arc(x,ground-45,21,0,Math.PI*2);
    ctx.fill();
    ctx.strokeStyle='#73523a';
    ctx.lineWidth=4;
    ctx.beginPath();
    ctx.moveTo(x-12,ground-55);
    ctx.lineTo(x+12,ground-35);
    ctx.moveTo(x+12,ground-55);
    ctx.lineTo(x-12,ground-35);
    ctx.stroke();
    ctx.fillStyle='#fff3ca';
    ctx.font='bold 13px system-ui';
    ctx.fillText('跳ぶ',x-16,ground-78)
  }
  else if(o.type==='sign') {
    ctx.fillStyle='#5b637b';
    ctx.fillRect(x-5,ground-82,10,82);
    roundRect(x-39,ground-113,78,40,8,'#75d9dc');
    ctx.fillStyle='#205566';
    ctx.font='bold 13px system-ui';
    ctx.fillText('CAFE',x-18,ground-88);
    ctx.fillStyle='#fff';
    ctx.beginPath();
    ctx.moveTo(x-10,ground-93);
    ctx.lineTo(x+8,ground-93);
    ctx.lineTo(x+2,ground-99);
    ctx.fill()
  }
  else {
    ctx.fillStyle='#393f53';
    ctx.beginPath();
    ctx.ellipse(x,y-64,31,9,0,0,Math.PI*2);
    ctx.fill();
    ctx.fillStyle='#f4797c';
    ctx.beginPath();
    ctx.arc(x,y-66,11,0,Math.PI*2);
    ctx.fill();
    ctx.strokeStyle='#393f53';
    ctx.lineWidth=3;
    ctx.beginPath();
    ctx.moveTo(x-19,y-65);
    ctx.lineTo(x-33,y-78+Math.sin(runT*8)*5);
    ctx.moveTo(x+19,y-65);
    ctx.lineTo(x+33,y-78-Math.sin(runT*8)*5);
    ctx.stroke();
    ctx.fillStyle='#fff';
    ctx.beginPath();
    ctx.arc(x,y-82,3,0,Math.PI*2);
    ctx.fill();

  }
  ctx.restore()
}
function line(x1,y1,x2,y2,color,width) {
  ctx.strokeStyle=color;
  ctx.lineWidth=width;
  ctx.lineCap='round';
  ctx.beginPath();
  ctx.moveTo(x1,y1);
  ctx.lineTo(x2,y2);
  ctx.stroke()
}
// プレイヤーを手足の線や図形で描き、走る／滑る姿を表現します。
function drawRunner() {
  let x=220,feet=ground-5-playerY,slide=sliding>0, stride=Math.sin(runT*13), swing= stride*19, torsoY=slide?feet-39:feet-70;
  ctx.save();
  ctx.translate(x,0);
  ctx.fillStyle='#27334d33';
  ctx.beginPath();
  ctx.ellipse(0,ground+1,31,6,0,0,Math.PI*2);
  ctx.fill();
  if(slide) {
    ctx.rotate(-.08);
    roundRect(-24,feet-43,55,27,12,'#f05d67');
    line(19,feet-25,43,feet-9,'#f4c5a1',7);
    line(-5,feet-18,-30,feet-8,'#30334b',8);
    line(40,feet-8,54,feet-8,'#f5dcb9',7)
  }
  else {
    // articulated runner
     line(-5,feet-30,-15+swing*.7,feet-3,'#27334d',10);
    line(-15+swing*.7,feet-3,-28+swing,feet-2,'#f3d9b8',8);
    line(5,feet-30,15-swing*.7,feet-3,'#27334d',10);
    line(15-swing*.7,feet-3,29-swing,feet-2,'#f3d9b8',8);
    roundRect(-14,torsoY,30,39,10,'#ed5d67');
    ctx.fillStyle='#ffca63';
    ctx.fillRect(-14,torsoY+25,30,6);
    line(-9,torsoY+11,-24-swing*.45,torsoY+27,'#f3d9b8',8);
    line(10,torsoY+11,23+swing*.45,torsoY+26,'#f3d9b8',8);
    ctx.fillStyle='#f2c7a0';
    ctx.beginPath();
    ctx.arc(1,torsoY-14,15,0,Math.PI*2);
    ctx.fill();
    ctx.fillStyle='#3f3445';
    ctx.beginPath();
    ctx.arc(-1,torsoY-18,15,Math.PI,Math.PI*2);
    ctx.fill();
    ctx.fillRect(8,torsoY-18,8,8);
    ctx.fillStyle='#29314a';
    ctx.beginPath();
    ctx.arc(7,torsoY-14,1.8,0,7);
    ctx.fill();
    ctx.fillStyle='#f8bb51';
    ctx.beginPath();
    ctx.moveTo(-13,torsoY-21);
    ctx.lineTo(-2,torsoY-39);
    ctx.lineTo(13,torsoY-21);
    ctx.closePath();
    ctx.fill();
    ctx.fillRect(-14,torsoY-23,29,5);

  }
  ctx.restore()
}
// 1フレーム分の背景、地形、障害物、プレイヤーを順番に描きます。
function draw() {
  drawSky();
  drawRoof();
  // rooftop air conditioning / parapets
   for(let x=(((-world*.55)%230)+230)%230-230;x<W;x+=230) {
    ctx.fillStyle='#646d82';
    ctx.fillRect(x,ground-28,56,28);
    ctx.fillStyle='#99a4ad';
    ctx.fillRect(x-4,ground-34,64,8);
    ctx.fillStyle='#d2d5d1';
    for(let a=0;a<4;a++)ctx.fillRect(x+7+a*11,ground-21,4,11)
  }
  for(const o of obstacles)drawObstacle(o);
  drawRunner();
  if(gapWarn>0) {
    ctx.fillStyle='#fff8de';
    ctx.font='900 19px system-ui';
    ctx.fillText('GAP!',270,ground-102)
  }

}
// dt は前フレームからの秒数です。速度や時間に応じて世界を進めます。
// この中で落下や障害物との接触も判定します。
function update(dt) {
  if(mode!=='play')return;
  runT+=dt;
  speed=Math.min(555,300+distance*.72);
  world+=speed*dt;
  distance+=speed*dt/10;
  $('distance').textContent=Math.floor(distance);
  $('speed').textContent=(speed/300).toFixed(1)+'x';
  vy+=1800*dt;
  playerY-=vy*dt;
  if(playerY<0) {
    playerY=0;
    vy=0
  }
  sliding=Math.max(0,sliding-dt);
  while(world>nextRoof-800)addRoof();
  while(world>nextObs-700)addObstacle();
  roofs=roofs.filter(r=>r.x+r.w>world-100);
  obstacles=obstacles.filter(o=>o.x>world-100);
  for(const r of roofs) {
    if(!r.gap)continue;
    let sx=r.x-world;
    if(sx<255&&sx+r.w>198) {
      gapWarn=.1;
      if(playerY<8) {
        endGame('ビルのすき間に落ちてしまった…');
        return
      }

    }

  }
  gapWarn=Math.max(0,gapWarn-dt);
  for(const o of obstacles) {
    let x=o.x-world;
    if(Math.abs(x-220)<35&&!o.passed) {
      let safe=o.type==='fan'?playerY>45:o.type==='sign'?sliding>0.2:playerY>45||sliding>0.2;
      if(!safe) {
        endGame(o.type==='fan'?'換気扇にぶつかった！':o.type==='sign'?'看板にぶつかった！':'ドローンにぶつかった！');
        return
      }
      o.passed=true
    }

  }

}
// ゲームを止め、今回の距離とベスト記録を画面に反映します。
function endGame(why) {
  mode='over';
  best=Math.max(best,Math.floor(distance));
  localStorage.setItem('rooftop-best',best);
  $('best').textContent=best;
  $('title').textContent='ラン終了！';
  $('intro').innerHTML=`${why}<br><strong>${Math.floor(distance)} m</strong> 走ったよ。ベスト記録：${best} m`;
  document.querySelector('#start').textContent='もう一度走る';
  $('overlay').classList.remove('hidden');
  $('message').textContent='ナイスラン！次はもっと遠くまで。'
}
// requestAnimationFrameから繰り返し呼ばれるメインループです。
function loop(now) {
  if(mode!=='play')return;
  let dt=Math.min((now-last)/1000,.04);
  last=now;
  update(dt);
  draw();
  if(mode==='play')requestAnimationFrame(loop)
}
// 地上にいる間だけ短時間しゃがみ、低い障害物をくぐります。
function slide() {
  if(mode==='play'&&playerY===0)sliding=.7
}
// 待機中も背景を描き続け、開始画面のゲーム画面を保ちます。
function frame() {
  draw();
  requestAnimationFrame(frame)
}
// ボタン、画面タップ、キーボードをゲーム操作に接続します。
frame();
$('start').addEventListener('click',reset);
$('jump').addEventListener('click',jump);
$('slide').addEventListener('pointerdown',slide);
canvas.addEventListener('pointerdown',jump);
document.addEventListener('keydown',e=> {
  if(['Space','ArrowUp','ArrowDown'].includes(e.code))e.preventDefault();if(e.code==='Space'||e.code==='ArrowUp')jump();if(e.code==='ArrowDown')slide()
});
