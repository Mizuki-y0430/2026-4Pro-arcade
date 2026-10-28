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

test('留年は内側にも出現し、頭・単位・アイテム・他の留年を避ける', () => {
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

test('胴体への接触は安全で、頭に留年が当たると衝突する', () => {
  const run = game();
  run('hazards=[{x:14,y:10,active:true}];');
  assert.equal(run('resolveHazardCollisions()'), false);
  run('hazards[0].x=15;');
  assert.equal(run('resolveHazardCollisions()'), true);
  run('shieldCharges=1;');
  assert.equal(run('resolveHazardCollisions()'), false);
  assert.equal(run('shieldCharges'), 0);
  assert.equal(run('hazards.length'), 0);
});

test('出現予告は無害で、頭に重なっている間は実体化を待つ', () => {
  const run = game();
  run('hazards=[{x:15,y:10,prevX:15,prevY:10,v:{x:0,y:1},active:false,readyAt:2000,lastMove:2000,stepMs:340}];');
  assert.equal(run('resolveHazardCollisions()'), false);
  run('updateHazards(2000);');
  assert.equal(run('hazards[0].active'), false);
  assert.equal(run('running'), true);
  run('snake[0]={x:16,y:10}; updateHazards(2400);');
  assert.equal(run('hazards[0].active'), true);
});

test('留年はプレーヤーの移動とは別の時計で動く', () => {
  const run = game();
  run('hazards=[{x:2,y:2,prevX:2,prevY:2,v:{x:1,y:0},active:true,lastMove:1000,stepMs:340}];');
  run('tick(1160); tick(1320); updateHazards(1320);');
  assert.equal(run('snake[0].x'), 17);
  assert.equal(run('hazards[0].x'), 2);
  run('updateHazards(1340);');
  assert.equal(run('hazards[0].x'), 3);
});

test('ゆっくりアイテムは留年を停止させず半分の速さにする', () => {
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

test('2単位ごとに成長し、取得後の長さがすぐ画面に反映される', () => {
  const run = game();
  run('food={x:16,y:10}; tick(1160);');
  assert.equal(run('score'), 1);
  assert.equal(run('snake.length'), 3);
  run('food={x:17,y:10}; tick(1320);');
  assert.equal(run('score'), 2);
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

test('画面端を抜けた留年は消える', () => {
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
