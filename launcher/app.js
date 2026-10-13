"use strict";
const $ = (id) => document.getElementById(id);
let token = "", games = [], filter = "all", selectedGame = null, pendingGame = null;
let signature = "", ended = false, busy = false, toastTimer;
let requestedGame = new URLSearchParams(location.search).get("play");
const genericCover = '<svg class="tile-fallback" viewBox="0 0 120 120" aria-hidden="true"><circle cx="60" cy="60" r="50" fill="#fff2a6" stroke="#000" stroke-width="5"/><path d="M34 37h52c9 0 15 8 18 17l5 26c3 13-8 19-17 10L77 76H43L28 90c-9 9-20 3-17-10l5-26c3-9 9-17 18-17Z" fill="#fff" stroke="#000" stroke-width="5"/><path d="M27 51h10V41h10v10h10v10H47v10H37V61H27Z" fill="#24b8db" stroke="#000" stroke-width="2"/><circle cx="80" cy="51" r="8" fill="#b582ec" stroke="#000" stroke-width="2"/><circle cx="92" cy="65" r="8" fill="#ffbb60" stroke="#000" stroke-width="2"/></svg>';
const lockedCover = '<svg class="locked-mark" viewBox="0 0 100 100" aria-hidden="true"><path d="M32 38V25a18 18 0 0 1 36 0v13" fill="none" stroke="#555" stroke-width="8" stroke-linecap="round"/><rect x="19" y="36" width="62" height="50" rx="15" fill="currentColor" stroke="#555" stroke-width="5"/><circle cx="50" cy="56" r="7" fill="#555"/><path d="M50 60v10" stroke="#555" stroke-width="7" stroke-linecap="round"/></svg>';

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
  const focused = document.activeElement;
  const focusGame = focused?.dataset?.game;
  const focusAction = focused?.dataset?.action;
  const ready = games.filter(g => !["unregistered", "missing"].includes(g.status)).length;
  $("count").textContent = `${ready} / ${games.length} あそべる`;
  const visible = games.filter(g => filter === "all" || (filter === "web" ? ["static", "service"].includes(g.kind) : g.kind === "python" || g.language === "python"));
  $("empty-filter").hidden = visible.length > 0;
  const fragment = document.createDocumentFragment();

  for (const game of visible) {
    const available = !["unregistered", "missing"].includes(game.status);
    const stop = game.status === "starting" || (game.kind === "python" && game.status === "running");
    const card = document.createElement("article");
    card.className = `card ${available ? "available" : "unavailable"}`;
    card.dataset.color = game.color || "mint";

    // Play, rules and information are separate controls, never nested buttons.
    const button = document.createElement("button");
    button.className = "play game-launch";
    button.dataset.game = game.id;
    button.dataset.action = "play";
    button.disabled = !available;
    button.title = game.message;
    button.setAttribute("aria-label", `${game.title}を${!available ? "準備中" : stop ? "停止する" : "プレイする"}`);
    const art = document.createElement("span");
    art.className = "tile-art";
    art.setAttribute("aria-hidden", "true");
    art.innerHTML = available ? genericCover : lockedCover;
    // Only curated, local cover URLs are used. Missing images retain the vector fallback.
    if (available && /^\/showcase\/assets\/[a-z0-9-]+\.(png|jpg|webp)$/.test(game.cover)) {
      const image = document.createElement("img");
      image.className = "tile-illustration";
      image.src = game.cover;
      image.alt = "";
      image.decoding = "async";
      image.addEventListener("error", () => image.remove());
      art.append(image);
    }
    const title = document.createElement("span");
    title.className = "tile-title";
    title.textContent = available ? game.menu_title || game.title : "準備中";
    button.append(art, title);
    if (!available) {
      const number = document.createElement("span");
      number.className = "slot-number";
      number.textContent = String(games.indexOf(game) + 1).padStart(2, "0");
      number.setAttribute("aria-hidden", "true");
      button.append(number);
    }
    button.addEventListener("click", () => play(game));

    const info = document.createElement("button");
    info.className = "tile-info";
    info.dataset.game = game.id;
    info.dataset.action = "info";
    info.textContent = "？";
    info.setAttribute("aria-label", `${game.title}の技術を知る`);
    info.title = game.kind ? "このゲームの技術を知る（3ページ）" : "技術説明は準備中です";
    info.addEventListener("click", () => {
      openGuide(game, "technology");
    });
    card.append(button, info);
    if (game.kind) {
      const rules = document.createElement("a");
      rules.className = "tile-rules";
      rules.href = `/games/${encodeURIComponent(game.id)}/rules`;
      rules.dataset.game = game.id;
      rules.dataset.action = "rules";
      rules.textContent = "ルール";
      rules.setAttribute("aria-label", `${game.title}のルールと操作方法`);
      rules.addEventListener("click", event => {
        if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        openGuide(game, "rules");
      });
      card.append(rules);
    }
    fragment.append(card);
  }
  $("games").replaceChildren(fragment);
  if (focusGame) [...document.querySelectorAll("[data-game]")].find(el => el.dataset.game === focusGame && el.dataset.action === focusAction)?.focus();
}

// ページ自体を移動すると全画面が解除されるので、説明だけをフレームに読み込みます。
function openGuide(game, section, addHistory = true) {
  const title = `${game.title}の${section === "rules" ? "ルール" : "技術説明"}`;
  const url = `/games/${encodeURIComponent(game.id)}/${section}`;
  $("guide").setAttribute("aria-label", title);
  $("guide-frame").title = title;
  // フレーム側の履歴を増やさず、履歴は親画面のpushStateだけで管理します。
  $("guide-frame").contentWindow.location.replace(url);
  if (!$("guide").open) $("guide").showModal();
  document.title = `${title} — 4Pro Arcade`;
  if (addHistory) history.pushState({ arcadeGuide: true }, "", url);
}

function closeGuide() {
  if (history.state?.arcadeGuide) history.back();
  else $("guide").close();
}
$("guide").addEventListener("cancel", event => { event.preventDefault(); closeGuide(); });
$("guide").addEventListener("close", () => {
  $("guide-frame").contentWindow.location.replace("about:blank");
  document.title = "4Pro Arcade";
});
// ブラウザーの「戻る・進む」でも、文書を再読み込みせず説明を切り替えます。
window.addEventListener("popstate", () => {
  const match = location.pathname.match(/^\/games\/([a-z0-9-]+)\/(technology|rules)$/);
  const game = match && games.find(item => item.id === match[1]);
  if (history.state?.arcadeGuide && game) openGuide(game, match[2], false);
  else if ($("guide").open) $("guide").close();
});
// 説明内の戻るリンクと、ルール内の開始リンクから受け取ります。
window.addEventListener("message", event => {
  if (event.origin !== location.origin || event.source !== $("guide-frame").contentWindow ||
      !$("guide").open || event.data?.type !== "arcade-guide") return;
  if (event.data.action === "close") closeGuide();
  if (event.data.action === "play") {
    const game = games.find(item => item.id === event.data.gameId);
    if (game && !["unregistered", "missing"].includes(game.status)) {
      closeGuide();
      play(game);
    }
  }
});

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
  if (document.fullscreenElement && document.fullscreenElement !== document.documentElement) await document.exitFullscreen();
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

// タイトル画面全体を全画面表示にします。Escで解除した場合も表示を更新します。
$("home-fullscreen").addEventListener("click", async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch { toast("このブラウザーでは全画面表示を利用できません。"); }
});
function updateHomeFullscreen() {
  const active = Boolean(document.fullscreenElement);
  $("home-fullscreen").textContent = active ? "⛶ 全画面を終了" : "⛶ 全画面";
  $("home-fullscreen").setAttribute("aria-pressed", String(active));
}
document.addEventListener("fullscreenchange", updateHomeFullscreen);
$("home-fullscreen").hidden = !document.fullscreenEnabled;
updateHomeFullscreen();
document.querySelectorAll("[data-filter]").forEach(button => button.addEventListener("click", () => {
  filter = button.dataset.filter;
  document.querySelectorAll("[data-filter]").forEach(el => {
    const selected = el === button;
    el.classList.toggle("selected", selected);
    el.setAttribute("aria-pressed", String(selected));
  });
  render();
}));
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
