"use strict";
const $ = (id) => document.getElementById(id);
let token = "", games = [], filter = "all", selectedGame = null, pendingGame = null;
let signature = "", ended = false, busy = false, toastTimer;
let requestedGame = new URLSearchParams(location.search).get("play");
const dodgeIcon = '<svg class="game-icon" viewBox="0 0 72 72" aria-hidden="true"><path d="M9 14h10v10H9zM49 5h14v14H49zM32 28h10v10H32z" fill="currentColor" opacity=".35"/><path d="m36 45 16 17H20Z" fill="currentColor"/><path d="M7 65h58" stroke="currentColor" opacity=".3"/></svg>';
const reactionIcon = '<svg class="game-icon" viewBox="0 0 72 72" aria-hidden="true"><circle cx="36" cy="36" r="27" fill="none" stroke="currentColor" opacity=".25"/><path d="m40 9-21 31h16l-3 24 22-33H38Z" fill="currentColor"/></svg>';
const webIcon = '<svg class="game-icon" viewBox="0 0 72 72" aria-hidden="true"><rect x="8" y="13" width="56" height="44" rx="5" fill="none" stroke="currentColor" stroke-width="3"/><path d="M9 24h54m-38 8-9 8 9 8m22-16 9 8-9 8" fill="none" stroke="currentColor" stroke-width="3"/></svg>';

function toast(message) {
  clearTimeout(toastTimer);
  $("toast").textContent = message;
  $("toast").hidden = false;
  toastTimer = setTimeout(() => { $("toast").hidden = true; }, 6500);
}

async function action(id, operation) {
  const response = await fetch(id ? `/api/games/${encodeURIComponent(id)}/${operation}` : "/api/shutdown", {
    method: "POST", headers: { "X-Arcade-Token": token }
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "操作に失敗しました。");
  return result;
}

function render() {
  const currentSignature = JSON.stringify([games, filter]);
  if (signature === currentSignature) return;
  signature = currentSignature;
  const focus = document.activeElement?.dataset?.game;
  $("count").textContent = `${games.filter(g => !["unregistered", "missing"].includes(g.status)).length} / ${games.length} ゲーム`;
  const fragment = document.createDocumentFragment();
  const visible = games.filter(g => filter === "all" || (filter === "web" ? ["static", "service"].includes(g.kind) : g.kind === "python" || g.language === "python"));
  $("empty-filter").hidden = visible.length > 0;
  for (const game of visible) {
    const available = !["unregistered", "missing"].includes(game.status);
    const card = document.createElement("article");
    card.className = `card ${available ? "available" : "unavailable"}`;
    card.dataset.color = game.color || "mint";
    const art = document.createElement("div");
    art.className = "card-art";
    const number = document.createElement("span");
    number.className = "number";
    number.textContent = String(games.indexOf(game) + 1).padStart(2, "0");
    art.append(number);
    if (game.kind) {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = game.kind === "python" ? "PYTHON ↗" : game.language === "python" ? "PYTHON / WEB" : "WEB";
      art.append(tag);
    }
    const icon = document.createElement("div");
    if (available) icon.innerHTML = game.kind === "python" || game.language === "python" ? reactionIcon : game.id === "neon-dodge" ? dodgeIcon : webIcon;
    else { icon.className = "coming-icon"; icon.textContent = "+"; }
    art.append(icon);
    const body = document.createElement("div");
    body.className = "card-body";
    const title = document.createElement("h3");
    title.textContent = game.title;
    title.title = game.title;
    const description = document.createElement("p");
    description.textContent = game.description;
    const author = document.createElement("span");
    author.className = "author";
    author.textContent = game.status === "error" ? `${game.message} ${game.log || ""}` : game.author || "メンバーのゲームを追加予定";
    author.title = game.status === "error" ? author.textContent : game.message;
    const button = document.createElement("button");
    button.className = "play";
    button.dataset.game = game.id;
    button.disabled = !available;
    button.title = game.message;
    const label = document.createElement("span");
    const stop = game.status === "starting" || (game.kind === "python" && game.status === "running");
    label.textContent = !available ? game.status === "missing" ? "ファイル未検出" : "準備中" : stop ? "停止する" : game.status === "error" ? "もう一度起動" : game.kind === "python" ? "ウィンドウで起動" : "プレイする";
    const arrow = document.createElement("span");
    arrow.textContent = !available ? "—" : stop ? "■" : "▶";
    button.append(label, arrow);
    button.addEventListener("click", () => play(game));
    body.append(title, description, author, button);
    const more = document.createElement("div");
    more.className = "card-more";
    for (const [label, suffix] of [["紹介・技術", ""], ["発表3ページ", "/slides"]]) {
      const link = document.createElement("a");
      link.textContent = label;
      link.href = `/games/${encodeURIComponent(game.id)}${suffix}`;
      more.append(link);
    }
    body.append(more);
    card.append(art, body);
    fragment.append(card);
  }
  $("games").replaceChildren(fragment);
  if (focus) [...document.querySelectorAll("[data-game]")].find(el => el.dataset.game === focus)?.focus();
}

async function refresh() {
  if (ended) return;
  const response = await fetch("/api/games", { cache: "no-store" });
  if (!response.ok) throw new Error("ランチャーに接続できません。");
  const data = await response.json();
  token = data.token;
  games = data.games;
  render();
  if (requestedGame) {
    const id = requestedGame;
    requestedGame = null;
    const game = games.find(g => g.id === id);
    if (game && !["unregistered", "missing"].includes(game.status)) play(game);
    else toast("このゲームはまだ起動できません。");
    history.replaceState(null, "", "/");
  }
  if (pendingGame) {
    const game = games.find(g => g.id === pendingGame);
    if (game?.status === "running" && game.url) { pendingGame = null; openPlayer(game); }
    else if (["error", "ready"].includes(game?.status)) { pendingGame = null; toast(`${game.message} ${game.log || ""}`); }
  }
  if (selectedGame) {
    const game = games.find(g => g.id === selectedGame);
    if (game && game.status !== "running") {
      selectedGame = null;
      $("game-frame").src = "about:blank";
      $("player").close();
      toast(`${game.message} ${game.log || ""}`);
    }
  }
}

function openPlayer(game) {
  selectedGame = game.id;
  $("player-title").textContent = game.title;
  $("player-controls").textContent = game.controls;
  $("game-frame").title = game.title;
  $("game-frame").src = game.url;
  if (!$("player").open) $("player").showModal();
  $("game-frame").addEventListener("load", () => $("game-frame").focus(), { once: true });
}

async function play(game) {
  if (busy || ended) return;
  busy = true;
  try {
    if (game.status === "starting" || (game.kind === "python" && game.status === "running")) {
      if (pendingGame === game.id) pendingGame = null;
      await action(game.id, "stop");
      toast("ゲームを停止しました。");
    } else {
      const result = await action(game.id, "start");
      if (result.url) openPlayer(result);
      else if (result.status === "starting") { pendingGame = game.id; toast("ゲームサーバーを起動しています…"); }
      else toast("Pythonゲームを別ウィンドウで起動しました。");
    }
    await refresh();
  } catch (error) { toast(error.message); }
  finally { busy = false; }
}

async function back() {
  const gid = selectedGame;
  selectedGame = null;
  if (document.fullscreenElement) await document.exitFullscreen();
  $("game-frame").src = "about:blank";
  $("player").close();
  if (gid) {
    try { await action(gid, "stop"); await refresh(); }
    catch (error) { toast(error.message); }
  }
}
$("back").addEventListener("click", back);
$("player").addEventListener("cancel", event => { event.preventDefault(); back(); });
$("fullscreen").addEventListener("click", async () => {
  try { await $("play-area").requestFullscreen(); }
  catch { toast("このブラウザーでは全画面表示を利用できません。"); }
});
document.querySelectorAll("[data-filter]").forEach(button => button.addEventListener("click", () => {
  filter = button.dataset.filter;
  document.querySelectorAll("[data-filter]").forEach(el => {
    const selected = el === button;
    el.classList.toggle("selected", selected);
    el.setAttribute("aria-pressed", String(selected));
  });
  render();
}));
$("help").addEventListener("click", () => $("help-dialog").showModal());
$("help-close").addEventListener("click", () => $("help-dialog").close());
$("exit").addEventListener("click", () => $("exit-dialog").showModal());
$("exit-cancel").addEventListener("click", () => $("exit-dialog").close());
$("exit-confirm").addEventListener("click", async () => {
  try {
    await action(null, "shutdown");
    ended = true;
    clearInterval(poll);
    $("game-frame").src = "about:blank";
    $("player").close();
    $("exit-dialog").close();
    document.body.classList.add("ended");
    $("exit").disabled = true;
    toast("終了しました。このタブを閉じてください。");
  } catch (error) { toast(error.message); }
});
refresh().catch(error => toast(error.message));
const poll = setInterval(() => refresh().catch(() => {}), 1200);
