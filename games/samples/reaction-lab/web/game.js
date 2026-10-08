"use strict";
const target = document.getElementById("target");
const message = document.getElementById("message"), hint = document.getElementById("hint");
const cue = document.getElementById("cue"), notice = document.getElementById("notice");
let token = "", state = "idle", roundId = "", timer = null, greenAt = 0;

async function request(path, data = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Reaction-Token": token },
    body: JSON.stringify(data)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "ゲームに接続できません。");
  return result;
}

async function click() {
  if (target.disabled) return;
  const previous = state;
  const elapsed = performance.now() - greenAt;
  clearTimeout(timer);
  state = "pending";
  target.disabled = true;
  notice.textContent = "";
  try {
    if (previous === "idle") {
      const round = await request("/api/start");
      roundId = round.round_id;
      state = "waiting";
      target.dataset.state = "waiting";
      cue.textContent = "···";
      message.textContent = "まだ…待って！";
      hint.textContent = "緑になった瞬間にクリック";
      timer = setTimeout(() => {
        // Begin timing only once the browser is about to paint the green target.
        requestAnimationFrame(() => {
          if (state !== "waiting") return;
          state = "go";
          target.dataset.state = "go";
          cue.textContent = "ϟ";
          message.textContent = "今！";
          hint.textContent = "クリック / スペース";
          greenAt = performance.now();
        });
      }, round.delay_ms);
    } else {
      const result = await request("/api/finish", previous === "waiting" ? { round_id: roundId, early: true } : { round_id: roundId, elapsed_ms: elapsed });
      state = "idle";
      target.dataset.state = "idle";
      document.getElementById("best").textContent = result.best_ms ?? "—";
      document.getElementById("attempts").textContent = result.attempts;
      if (result.result === "early") {
        cue.textContent = "!";
        message.textContent = "フライング！";
        hint.textContent = "クリックしてもう一度";
      } else {
        document.getElementById("last").textContent = result.elapsed_ms;
        cue.textContent = "✓";
        message.textContent = `${result.elapsed_ms} ms`;
        hint.textContent = "クリックしてベストを更新しよう";
      }
    }
  } catch (error) {
    state = "idle";
    target.dataset.state = "idle";
    message.textContent = "もう一度スタート";
    hint.textContent = "クリック / スペース";
    notice.textContent = error.message;
  } finally {
    target.disabled = false;
  }
}

target.addEventListener("click", click);
window.addEventListener("keydown", event => {
  if (event.key === " ") { event.preventDefault(); if (!event.repeat) target.click(); }
});

(async () => {
  try {
    const response = await fetch("/api/session", { cache: "no-store" });
    const session = await response.json();
    if (!response.ok) throw new Error(session.error || "ゲームを準備できません。");
    token = session.token;
    target.disabled = false;
    message.textContent = "クリックしてスタート";
    hint.textContent = "スペースキーでもプレイできます";
    target.focus({ preventScroll: true });
  } catch (error) { notice.textContent = `${error.message} 一覧へ戻って再起動してください。`; }
})();
