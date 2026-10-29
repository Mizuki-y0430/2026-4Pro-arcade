const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');
const source = readFileSync(join(__dirname, '../games/local/2026_4Pro_fishinggame/fishing.js'), 'utf8');

// Run the real game with a controlled clock, animation frames and DOM events.
function game() {
  const elements = new Map(), keys = {}, timeouts = new Map(), frames = new Map();
  let now = 1000, nextId = 1;
  function element(key) {
    if (!elements.has(key)) {
      const classes = new Set();
      elements.set(key, {
        textContent: '', innerHTML: '', style: { setProperty(key, value) { this[key] = value; } }, dataset: {}, hidden: false, disabled: true,
        classList: { add: (...v) => v.forEach(x => classes.add(x)), remove: (...v) => v.forEach(x => classes.delete(x)) },
        events: {}, addEventListener(type, fn) { this.events[type] = fn; },
        querySelector: s => element(key + s),
      });
    }
    return elements.get(key);
  }
  const document = {
    getElementById: element, querySelector: element, querySelectorAll: () => [],
    addEventListener: (type, fn) => { keys[type] = fn; },
  };
  const math = Object.create(Math); math.random = () => 0.5;
  const context = vm.createContext({
    document, Math: math, performance: { now: () => now },
    setTimeout(fn) { const id = nextId++; timeouts.set(id, fn); return id; },
    clearTimeout: id => timeouts.delete(id), setInterval: () => nextId++, clearInterval() {},
    requestAnimationFrame(fn) { const id = nextId++; frames.set(id, fn); return id; },
    cancelAnimationFrame: id => frames.delete(id), ResizeObserver: class { observe() {} },
  });
  vm.runInContext(source, context);
  return {
    run: code => vm.runInContext(code, context),
    time: value => { now = value; },
    element, frames, timeouts,
    key(code, repeat = false) { keys.keydown({ code, repeat, preventDefault() {} }); },
  };
}

test('開始・魚待ちの間は合わせても得点にならず、HITからバーが動く', () => {
  const g = game();
  g.run('hookFish(); startGame(); castLine(); hookFish();');
  assert.equal(g.run('state'), 'waiting');
  assert.equal(g.run('caught'), 0);
  assert.equal(g.element('timingMeter').hidden, true);
  g.timeouts.get(g.run('eventTimer'))();
  assert.equal(g.run('state'), 'bite');
  assert.equal(g.element('timingMeter').hidden, false);
  assert.equal(g.element('hook').disabled, false);
  assert.equal(g.frames.size, 1);
});

test('難しい魚ほど成功エリアが狭く、エリアはバーの中に収まる', () => {
  const g = game();
  assert.equal(g.run('fish.every((f,i)=>i===0||f.zone<fish[i-1].zone)'), true);
  for (let i = 0; i < 5; i++) {
    g.run(`startGame(); currentFish=fish[${i}]; beginBite();`);
    assert.equal(g.run('targetStart>=0 && targetStart+currentFish.zone<=100'), true);
    assert.equal(g.element('targetZone').style.width, g.run('currentFish.zone') + '%');
  }
});

test('全魚種でエリア内のEnterは成功し、得点・図鑑を1回だけ更新する', () => {
  for (let i = 0; i < 5; i++) {
    const g = game();
    g.run(`startGame(); currentFish=fish[${i}]; beginBite();`);
    g.time(g.run('aimStarted+(targetStart+currentFish.zone/2)/100*NEEDLE_TRAVEL'));
    g.key('Enter'); g.key('Enter');
    assert.equal(g.run('caught'), 1);
    assert.equal(g.run('points'), g.run('currentFish.points'));
    assert.equal(g.element('timingMeter').dataset.result, 'success');
    assert.equal(g.element('hook').disabled, true);
    assert.equal(g.frames.size, 0);
    assert.equal(g.element(g.run('`[data-fish="${currentFish.name}"]`')).textContent, g.run('`${currentFish.emoji} ${currentFish.name}`'));
  }
});

test('エリア外で合わせると失敗し、再び投げるまで連打しても釣れない', () => {
  const g = game();
  g.run('startGame(); currentFish=fish[0]; beginBite(); hookFish();');
  assert.equal(g.run('state'), 'recovering');
  assert.equal(g.run('points'), 0);
  assert.equal(g.element('timingMeter').dataset.result, 'miss');
  assert.equal(g.frames.size, 0);
  g.time(1600); g.element('hook').events.click();
  assert.equal(g.run('caught'), 0);
  g.run('castLine();');
  assert.equal(g.run('state'), 'waiting');
  assert.equal(g.element('timingMeter').hidden, true);
});

test('針は折り返し、戻りのエリア内でも成功する', () => {
  const g = game();
  g.run('startGame(); currentFish=fish[0]; beginBite();');
  assert.equal(g.run('needlePosition(aimStarted)'), 0);
  assert.equal(g.run('needlePosition(aimStarted+NEEDLE_TRAVEL)'), 100);
  assert.equal(g.run('needlePosition(aimStarted+NEEDLE_TRAVEL*2)'), 0);
  g.time(g.run('aimStarted+(2-(targetStart+currentFish.zone/2)/100)*NEEDLE_TRAVEL'));
  g.element('hook').events.click();
  assert.equal(g.run('caught'), 1);
});

test('5秒で失敗し、タイマー通知が遅れても期限後の操作では釣れない', () => {
  for (const action of ['hookFish()', 'updateNeedle(performance.now())', "missFish('timeout')"]) {
    const g = game();
    g.run('startGame(); currentFish=fish[0]; beginBite();');
    g.time(6000); g.run(action);
    assert.equal(g.run('state'), 'recovering');
    assert.equal(g.run('points'), 0);
    assert.equal(g.element('timingName').textContent, '時間切れ！');
    assert.equal(g.frames.size, 0);
  }
});

test('長押しで自動判定せず、終了・再挑戦時に古い針とタイマーを止める', () => {
  const g = game();
  g.run('startGame(); currentFish=fish[0]; beginBite();');
  g.time(1600); g.key('Enter', true);
  assert.equal(g.run('state'), 'bite');
  g.run('seconds=0; hookFish();');
  assert.equal(g.run('state'), 'ended');
  assert.equal(g.run('caught'), 0);
  assert.equal(g.frames.size, 0);
  assert.equal(g.timeouts.size, 0);
  assert.equal(g.element('timingMeter').hidden, true);
  g.key('Space');
  assert.equal(g.run('state'), 'waiting');
  assert.equal(g.run('seconds'), 60);
  g.key('Space', true);
  assert.equal(g.run('state'), 'waiting');
});


test('開始時と成功・失敗後は、操作しなくても自動で投げる', () => {
  for (const success of [true, false]) {
    const g = game();
    g.run('startGame();');
    assert.equal(g.run('state'), 'waiting');
    g.run('currentFish=fish[0]; beginBite();');
    if (success) g.time(g.run('aimStarted+(targetStart+currentFish.zone/2)/100*NEEDLE_TRAVEL'));
    g.run('hookFish();');
    assert.equal(g.run('state'), 'recovering');
    assert.equal(g.element('recastProgress').hidden, false);
    assert.equal(g.element('castLabel').textContent, '次を投げる');
    const id = g.run('recastTimer'), callback = g.timeouts.get(id);
    g.timeouts.delete(id); callback();
    assert.equal(g.run('state'), 'waiting');
    assert.equal(g.element('recastProgress').hidden, true);
    assert.equal(g.element('timingMeter').hidden, true);
    assert.equal(g.element('cast').disabled, true);
  }
});

test('Spaceで結果の待ち時間を省いても自動投下が重複しない', () => {
  const g = game();
  g.run('startGame(); currentFish=fish[0]; beginBite(); hookFish();');
  const id = g.run('recastTimer');
  g.key('Space');
  assert.equal(g.run('state'), 'waiting');
  assert.equal(g.timeouts.has(id), false);
  assert.equal(g.run('recastTimer'), null);
  const next = g.run('eventTimer');
  g.key('Space');
  assert.equal(g.run('eventTimer'), next);
});

test('結果表示中の終了・再挑戦で、前回の自動投下を解除する', () => {
  const g = game();
  g.run('startGame(); currentFish=fish[0]; beginBite(); hookFish();');
  const id = g.run('recastTimer');
  g.run('endGame();');
  assert.equal(g.timeouts.has(id), false);
  assert.equal(g.run('recastTimer'), null);
  assert.equal(g.element('recastProgress').hidden, true);
  g.run('startGame();');
  assert.equal(g.run('state'), 'waiting');
  assert.equal(g.run('points'), 0);
});


test('Enterだけで開始・合わせる・終了後の再挑戦まで操作できる', () => {
  const g = game();
  g.key('Enter');
  assert.equal(g.run('state'), 'waiting');
  g.run('currentFish=fish[0]; beginBite();');
  g.time(g.run('aimStarted+(targetStart+currentFish.zone/2)/100*NEEDLE_TRAVEL'));
  g.key('Enter');
  assert.equal(g.run('caught'), 1);
  g.run('endGame();');
  g.key('Enter');
  assert.equal(g.run('state'), 'waiting');
  assert.equal(g.run('caught'), 0);
});
