const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

// 実際のゲームを仮の画面と時計で動かし、再現しづらい衝突も確認する。
const source = readFileSync(join(__dirname, '../games/local/2026-4Pro-ishida/game.js'), 'utf8');
function game() {
  const elements = new Map();
  const drawing = new Proxy({}, { get: (_, name) => name === 'createRadialGradient'
    ? () => ({ addColorStop() {} }) : () => {} });
  const document = {
    querySelector(selector) {
      if (!elements.has(selector)) elements.set(selector, {
        textContent: '', style: {}, classList: { add() {}, remove() {} },
        addEventListener() {}, getContext: () => drawing, width: 768, height: 480,
      });
      return elements.get(selector);
    },
    querySelectorAll: () => [], addEventListener() {},
  };
  let seed = 12345;
  const math = Object.create(Math);
  math.random = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 2 ** 32);
  const context = vm.createContext({
    document, Math: math, performance: { now: () => 1000 }, requestAnimationFrame() {},
    localStorage: { getItem: () => null, setItem() {} },
  });
  // このテスト用VMだけで外側の関数を外す。本番にテストAPIは追加しない。
  vm.runInContext(source.replace(/^\(\(\) => \{/, '').replace(/\}\)\(\);\s*$/, ''), context);
  const run = code => vm.runInContext(code, context);
  run('reset(); food={x:25,y:15};');
  return run;
}

test('落単は内側にも出現し、頭・単位・アイテム・他の落単を避ける', () => {
  for (const level of ['easy', 'normal', 'hard']) {
    const run = game();
    run(`difficulty='${level}'; powerup={x:5,y:5};`);
    let interior = 0;
    const quadrants = new Set();
    const speeds = new Set();
    for (let i = 0; i < 120; i++) {
      run('hazards=[]; spawnHazard(1000); spawnHazard(1000);');
      assert.equal(run(`hazards.every(h =>
        Math.abs(h.x-snake[0].x)+Math.abs(h.y-snake[0].y)>=6 &&
        !snake.some(s=>same(s,h)) && !same(food,h) && !same(powerup,h))`), true);
      assert.equal(run('Math.abs(hazards[0].x-hazards[1].x)+Math.abs(hazards[0].y-hazards[1].y)>=3'), true);
      assert.equal(run('hazards.every(h=>h.stepMs>stepMs && !h.active && h.readyAt>1000)'), true);
      if (run('hazards[0].x>0&&hazards[0].x<31&&hazards[0].y>0&&hazards[0].y<19')) interior++;
      quadrants.add(run('`${hazards[0].x<16}:${hazards[0].y<10}`'));
      speeds.add(run('Math.round(hazards[0].stepMs)'));
    }
    assert.ok(interior > 80);
    assert.equal(quadrants.size, 4);
    assert.ok(speeds.size > 10);
  }
});

test('胴体への接触は安全で、頭に当たった札だけ落単として数える', () => {
  const run = game();
  run('hazards=[{x:14,y:10,active:true}];');
  assert.equal(run('resolveHazardCollisions()'), false);
  assert.equal(run('droppedCredits'), 0);
  run('hazards[0].x=15;');
  assert.equal(run('resolveHazardCollisions()'), false);
  assert.equal(run('droppedCredits'), 1);
  assert.equal(run('hazards.length'), 0);
  // 同じフレームや次のフレームでも二重に数えない。
  run('resolveHazardCollisions(); resolveHazardCollisions();');
  assert.equal(run('droppedCredits'), 1);
  run('shieldCharges=1; hazards=[{x:15,y:10,active:true}];');
  assert.equal(run('resolveHazardCollisions()'), false);
  assert.equal(run('droppedCredits'), 1);
  assert.equal(run('shieldCharges'), 0);
  assert.equal(run('hazards.length'), 0);
});

test('全難易度で落単6単位までは続行し、7単位目で終了する', () => {
  for (const level of ['easy', 'normal', 'hard']) {
    const run = game();
    run(`difficulty='${level}'; reset(); score=12;`);
    for (let count = 1; count <= 7; count++) {
      run('hazards=[{x:15,y:10,prevX:15,prevY:10,v:{x:1,y:0},active:true,lastMove:1000,stepMs:340}]; updateHazards(1000);');
      assert.equal(run('droppedCredits'), count);
      assert.equal(run('running'), count <= 6);
      assert.equal(run('gameOver'), count === 7);
      assert.equal(run('score'), 12);
      assert.equal(run('droppedEl.textContent'), `${count} / 6`);
      assert.equal(run('hazards.length'), 0);
    }
    assert.match(run('copyEl.innerHTML'), /落単が7単位/);
    assert.match(run('copyEl.innerHTML'), /7単位/);
    run('reset();');
    assert.equal(run('droppedCredits'), 0);
    assert.equal(run('droppedEl.textContent'), '0 / 6');
    assert.equal(run('gameOver'), false);
  }
});

test('落単6単位のときも、まもりで防いだ札は落単数に含めない', () => {
  const run = game();
  run('droppedCredits=6; shieldCharges=1; hazards=[{x:15,y:10,prevX:15,prevY:10,v:{x:1,y:0},active:true,lastMove:1000,stepMs:340}]; updateHazards(1000);');
  assert.equal(run('running'), true);
  assert.equal(run('droppedCredits'), 6);
  assert.equal(run('shieldCharges'), 0);
  run('hazards=[{x:15,y:10,prevX:15,prevY:10,v:{x:1,y:0},active:true,lastMove:1000,stepMs:340}]; updateHazards(1000);');
  assert.equal(run('gameOver'), true);
  assert.equal(run('droppedCredits'), 7);
});

test('プレーヤーが札に進んでも落単1単位で続行し、取得単位も記録する', () => {
  const run = game();
  run('food={x:16,y:10}; hazards=[{x:16,y:10,active:true}]; tick(1160);');
  assert.equal(run('running'), true);
  assert.equal(run('droppedCredits'), 1);
  assert.equal(run('score'), 5);
  assert.equal(run('hazards.length'), 0);
  assert.equal(run('droppedEl.textContent'), '1 / 6');
});

test('同じマスに重なった別々の札はそれぞれ1単位だけ数える', () => {
  const run = game();
  run('hazards=Array.from({length:2},()=>({x:15,y:10,prevX:15,prevY:10,v:{x:1,y:0},active:true,lastMove:1000,stepMs:340})); updateHazards(1000); updateHazards(1000);');
  assert.equal(run('running'), true);
  assert.equal(run('droppedCredits'), 2);
  assert.equal(run('hazards.length'), 0);
});

test('出現予告は無害で、頭に重なっている間は実体化を待つ', () => {
  const run = game();
  run('hazards=[{x:15,y:10,prevX:15,prevY:10,v:{x:0,y:1},active:false,readyAt:2000,lastMove:2000,stepMs:340}];');
  assert.equal(run('resolveHazardCollisions()'), false);
  run('updateHazards(2000);');
  assert.equal(run('hazards[0].active'), false);
  assert.equal(run('droppedCredits'), 0);
  assert.equal(run('running'), true);
  run('snake[0]={x:16,y:10}; updateHazards(2400);');
  assert.equal(run('hazards[0].active'), true);
});

test('落単はプレーヤーの移動とは別の時計で動く', () => {
  const run = game();
  run('hazards=[{x:2,y:2,prevX:2,prevY:2,v:{x:1,y:0},active:true,lastMove:1000,stepMs:340}];');
  run('tick(1160); tick(1320); updateHazards(1320);');
  assert.equal(run('snake[0].x'), 17);
  assert.equal(run('hazards[0].x'), 2);
  run('updateHazards(1340);');
  assert.equal(run('hazards[0].x'), 3);
});

test('ゆっくりアイテムは落単を停止させず半分の速さにする', () => {
  const run = game();
  run('hazards=[{x:2,y:2,prevX:2,prevY:2,v:{x:1,y:0},active:true,lastMove:1000,stepMs:340}]; slowUntil=8000;');
  run('updateHazards(1340);');
  assert.equal(run('hazards[0].x'), 2);
  run('updateHazards(1680);');
  assert.equal(run('hazards[0].x'), 3);
  run('updateHazards(8001);');
  assert.equal(run('hazards[0].x'), 4);
});

test('移動して空くしっぽのマスへは曲がれる', () => {
  const run = game();
  run('snake=[{x:5,y:5},{x:5,y:6},{x:4,y:6},{x:4,y:5}]; dir={x:-1,y:0}; tick(1160);');
  assert.equal(run('running'), true);
  assert.equal(run('snake[0].x'), 4);
  assert.equal(run('snake.length'), 4);
});

test('体が伸びる手ではしっぽのマスは空かない', () => {
  const run = game();
  run('snake=[{x:5,y:5},{x:5,y:6},{x:4,y:6},{x:4,y:5}]; dir={x:-1,y:0}; growthPending=1; tick(1160);');
  assert.equal(run('gameOver'), true);
});

test('自分の胴体と壁への衝突は引き続きゲーム終了', () => {
  const run = game();
  run('snake=[{x:5,y:5},{x:5,y:6},{x:4,y:6},{x:4,y:5},{x:3,y:5}]; dir={x:-1,y:0}; tick(1160);');
  assert.equal(run('gameOver'), true);
  run('reset(); snake=[{x:31,y:5},{x:30,y:5},{x:29,y:5}]; tick(1160);');
  assert.equal(run('gameOver'), true);
});

test('通常カードは1枚5単位、2枚で1マス成長し、長さがすぐ画面に反映される', () => {
  const run = game();
  run('food={x:16,y:10}; tick(1160);');
  assert.equal(run('score'), 5);
  assert.equal(run('snake.length'), 3);
  run('food={x:17,y:10}; tick(1320);');
  assert.equal(run('score'), 10);
  assert.equal(run('snake.length'), 4);
  assert.equal(run('lengthEl.textContent'), '04');
});

test('出現上限と空きマスがない場合にも安全に処理できる', () => {
  const run = game();
  run('for(let i=0;i<30;i++)spawnWave(1000000);');
  assert.ok(run('hazards.length') <= 12);
  run('hazards=[]; snake=Array.from({length:640},(_,i)=>({x:i%32,y:Math.floor(i/32)})); spawnHazard(1000);');
  assert.equal(run('hazards.length'), 0);
});

test('画面端を抜けた落単は消える', () => {
  const run = game();
  run('hazards=[{x:31,y:2,prevX:30,prevY:2,v:{x:1,y:0},active:true,lastMove:1000,stepMs:340}]; updateHazards(1340);');
  assert.equal(run('hazards.length'), 0);
});

test('開始・描画・終了・再挑戦を通して動く', () => {
  const run = game();
  run('loop(1161);');
  assert.equal(run('snake[0].x'), 16);
  assert.equal(run('hazards.length'), 1);
  run('for(let ts=1322;ts<5000&&running;ts+=161)loop(ts);');
  assert.equal(run('gameOver'), true);
  run('reset(); loop(1161);');
  assert.equal(run('running'), true);
  assert.equal(run('gameOver'), false);
});

test('最初は説明ポップアップを出さず、学年選択を表示する', () => {
  const run = game();
  run('showReady();');
  assert.equal(run('running'), false);
  assert.equal(run('lobby.hidden'), false);
  assert.equal(run('arena.hidden'), true);
  assert.equal(run('goalEl.textContent'), '85');
  assert.equal(run('startBtn.textContent'), '3年生に挑戦する');
});

test('電気情報工学科の進級・卒業累計を目標にし、動きの設定は全学年で共通', () => {
  const run = game();
  assert.equal(run('difficultySettings.easy.goal'), 85);
  assert.equal(run('difficultySettings.normal.goal'), 125);
  assert.equal(run('difficultySettings.hard.goal'), 167);
  for (const key of ['speed','minSpeed','hazardSpeed','warning','interval','capStart']) {
    assert.equal(run(`difficultySettings.easy.${key}`), run(`difficultySettings.hard.${key}`));
  }
  run("showReady(); selectDifficulty('hard');");
  assert.equal(run('goalEl.textContent'), '167');
  assert.equal(run('goalProgress.max'), 167);
  assert.equal(run('remainingEl.textContent'), 'あと167単位');
  run("selectDifficulty('unknown');");
  assert.equal(run('difficulty'), 'hard');
});

test('すべての学年で目標の1単位前は続行し、通常の＋5単位で目標を超えてクリアする', () => {
  for (const level of ['easy','normal','hard']) {
    const run = game();
    run(`difficulty='${level}'; reset(); score=difficultySettings[difficulty].goal-CREDIT_VALUE-1; food={x:16,y:10}; tick(1160);`);
    assert.equal(run('running'), true);
    assert.equal(run('cleared'), false);
    assert.equal(run('remainingEl.textContent'), 'あと1単位');
    run('food={x:17,y:10}; tick(1320);');
    assert.equal(run('running'), false);
    assert.equal(run('cleared'), true);
    assert.equal(run('gameOver'), true);
    assert.equal(run('remainingEl.textContent'), 'クリア！');
    assert.equal(run('goalProgress.value'), run('difficultySettings[difficulty].goal'));
    assert.match(run('titleEl.textContent'), level === 'hard' ? /卒業おめでとう/ : /年生クリア/);
  }
});

test('単位ボーナスの＋10で目標を超えてもクリアし、進捗は100%で止まる', () => {
  const run = game();
  run("score=84; powerup={x:16,y:10,type:'bonus'}; food={x:25,y:15}; tick(1160);");
  assert.equal(run('score'), 94);
  assert.equal(run('cleared'), true);
  assert.equal(run('goalProgress.value'), 85);
  assert.equal(run('remainingEl.textContent'), 'クリア！');
});

test('目標単位を取得する手でも、同時に7単位の落単になった場合は失敗する', () => {
  const run = game();
  run('score=84; droppedCredits=6; food={x:16,y:10}; hazards=[{x:16,y:10,active:true}]; tick(1160);');
  assert.equal(run('score'), 89);
  assert.equal(run('droppedCredits'), 7);
  assert.equal(run('cleared'), false);
  assert.equal(run('gameOver'), true);
  assert.match(run('copyEl.innerHTML'), /落単が7単位/);
});

test('クリア後は移動と重複記録を止め、再挑戦すると進捗をリセットする', () => {
  const run = game();
  run('score=85; checkClear();');
  const endedSnake = run('JSON.stringify(snake)');
  const records = run('JSON.stringify(leaderboard)');
  run('tick(1320); endGame();');
  assert.equal(run('JSON.stringify(snake)'), endedSnake);
  assert.equal(run('JSON.stringify(leaderboard)'), records);
  run('reset();');
  assert.equal(run('running'), true);
  assert.equal(run('cleared'), false);
  assert.equal(run('score'), 0);
  assert.equal(run('goalProgress.value'), 0);
  assert.equal(run('lobby.hidden'), true);
  assert.equal(run('arena.hidden'), false);
  run("selectDifficulty('hard');");
  assert.equal(run('difficulty'), 'easy');
});


test('ひきよせでも5単位を取り、ボーナス10単位では体が1マスだけ伸びる', () => {
  const run = game();
  run('magnetUntil=9000; food={x:20,y:10}; tick(1160);');
  assert.equal(run('score'), 5);
  assert.equal(run('snake.length'), 3);
  run("magnetUntil=0; food={x:25,y:15}; powerup={x:17,y:10,type:'bonus'}; tick(1320);");
  assert.equal(run('score'), 15);
  assert.equal(run('growthPending'), 1);
  run('tick(1480);');
  assert.equal(run('snake.length'), 4);
  assert.equal(run('growthPending'), 0);
  run('food={x:19,y:10}; tick(1640);');
  assert.equal(run('score'), 20);
  assert.equal(run('snake.length'), 5);
});
