"use strict";
const canvas = document.getElementById("canvas"), ctx = canvas.getContext("2d");
const overlay = document.getElementById("overlay"), timeLabel = document.getElementById("time");
let playing = false, elapsed = 0, lastTime = 0, spawn = 0, blocks = [], playerX = 342;
const keys = new Set();
function begin() {
  elapsed = 0; spawn = 0; blocks = []; playerX = 342; keys.clear();
  playing = true; overlay.hidden = true; timeLabel.textContent = "0.0"; lastTime = performance.now();
}
function finish(won) {
  playing = false; keys.clear(); overlay.hidden = false;
  document.getElementById("label").textContent = won ? "MISSION COMPLETE" : "TRY AGAIN";
  document.getElementById("title").textContent = won ? "30秒、生き残った！" : `${elapsed.toFixed(1)}秒。もう一度挑戦しよう。`;
  document.getElementById("hint").textContent = won ? "見事なフットワーク。次は別のゲームにも挑戦！" : "ブロックの間を見つけて、少しずつ移動してみよう。";
  document.getElementById("start").firstChild.textContent = "もう一度 ";
}
function frame(now) {
  const dt = Math.min((now - lastTime) / 1000, .05); lastTime = now;
  if (playing) {
    elapsed = Math.min(elapsed + dt, 30); spawn += dt;
    if (keys.has("ArrowLeft") || keys.has("a")) playerX -= 365 * dt;
    if (keys.has("ArrowRight") || keys.has("d")) playerX += 365 * dt;
    playerX = Math.max(6, Math.min(678, playerX));
    if (spawn > .48 - elapsed * .007) { spawn = 0; const size = 18 + Math.random() * 25; blocks.push({x: Math.random() * (720 - size), y: -size, size, speed: 95 + elapsed * 4 + Math.random() * 55}); }
    for (const block of blocks) {
      block.y += block.speed * dt;
      if (block.x < playerX + 32 && block.x + block.size > playerX + 4 && block.y < 369 && block.y + block.size > 348) finish(false);
    }
    blocks = blocks.filter(block => block.y < 420);
    timeLabel.textContent = elapsed.toFixed(1);
    if (playing && elapsed >= 30) finish(true);
  }
  ctx.fillStyle = "#e5f6ff"; ctx.fillRect(0, 0, 720, 400);
  ctx.strokeStyle = "#c4e7fa"; ctx.lineWidth = 1;
  for (let x = 0; x < 720; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 400); ctx.stroke(); }
  for (let y = 0; y < 400; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(720, y); ctx.stroke(); }
  ctx.fillStyle = "#a671e1"; ctx.shadowColor = "#a671e1"; ctx.shadowBlur = 12;
  for (const block of blocks) ctx.fillRect(block.x, block.y, block.size, block.size);
  ctx.fillStyle = "#07867c"; ctx.shadowColor = "#07867c";
  ctx.beginPath(); ctx.moveTo(playerX + 18, 340); ctx.lineTo(playerX + 36, 372); ctx.lineTo(playerX, 372); ctx.closePath(); ctx.fill();
  ctx.shadowBlur = 0; ctx.fillStyle = "#07867c"; ctx.fillRect(0, 396, 720 * elapsed / 30, 4);
  requestAnimationFrame(frame);
}
document.getElementById("start").addEventListener("click", begin);
window.addEventListener("keydown", event => {
  const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
  if (["ArrowLeft", "ArrowRight", "a", "d", " "].includes(key)) event.preventDefault();
  keys.add(key); if (key === " " && !playing && !event.repeat) begin();
});
window.addEventListener("keyup", event => keys.delete(event.key.length === 1 ? event.key.toLowerCase() : event.key));
window.addEventListener("blur", () => keys.clear());
for (const [id, key] of [["left", "ArrowLeft"], ["right", "ArrowRight"]]) {
  const button = document.getElementById(id);
  button.addEventListener("pointerdown", event => { button.setPointerCapture(event.pointerId); keys.add(key); });
  for (const event of ["pointerup", "pointercancel", "lostpointercapture"]) button.addEventListener(event, () => keys.delete(key));
}
requestAnimationFrame(frame);
