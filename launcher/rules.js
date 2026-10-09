"use strict";
const $ = id => document.getElementById(id);
function showItems(id, items) {
  const nodes = items.map(text => {
    const item = document.createElement("li");
    item.textContent = text;
    return item;
  });
  $(id).replaceChildren(...nodes);
}
async function loadRules() {
  try {
    const response = await fetch("/api/games", {cache: "no-store"});
    if (!response.ok) throw new Error("ルールを読み込めませんでした。ページを再読み込みしてください。");
    const {games} = await response.json();
    const game = games.find(item => item.id === location.pathname.split("/")[2]);
    if (!game) throw new Error("ゲームが見つかりません。ゲーム一覧から選び直してください。");
    $("rules-title").textContent = game.menu_title || game.title;
    document.title = `${game.title}のルール — 4Pro Arcade`;
    $("rules-summary").textContent = game.description || "";
    showItems("rules-list", game.rules?.length ? game.rules : ["詳しいルールは準備中です。"]);
    showItems("operations-list", game.operations?.length ? game.operations : [game.controls || "操作方法は準備中です。"]);
    $("rules-sections").hidden = false;
    const available = !["unregistered", "missing"].includes(game.status);
    $("rules-play").hidden = !available;
    $("rules-play").href = `/?play=${encodeURIComponent(game.id)}`;
    $("rules-status").textContent = available ? "準備ができたら、下のボタンでスタート！" : game.message;
  } catch (error) {
    $("rules-title").textContent = "ルールと操作方法";
    $("rules-error").textContent = error.message;
    $("rules-error").hidden = false;
  } finally {
    $("rules-main").setAttribute("aria-busy", "false");
  }
}
loadRules();
