"use strict";
const $ = id => document.getElementById(id);
const el = (tag, text, className) => { const node = document.createElement(tag); if (text != null) node.textContent = text; if (className) node.className = className; return node; };
const parts = location.pathname.split("/");
const gid = parts[2], slideMode = parts[3] === "slides";
let game, profile, page = 0;

function list(items, ordered = false) {
  const node = el(ordered ? "ol" : "ul");
  for (const text of items || []) node.append(el("li", text));
  return node;
}
function link(text, href, className = "text-link") { const node = el("a", text, className); node.href = href; return node; }
function section(title) { const node = el("section", null, "detail-section"); node.append(el("h2", title)); return node; }
function stateText() {
  return profile.status === "sample" ? "教材用サンプル。学生の制作・学習実績ではありません。" : profile.status === "draft" ? "提出・確認前の下書き。本人の記録を入れてから発表資料を完成させます。" : "本人と担当者が確認した紹介・学習成果";
}

function detail() {
  const root = $("game-detail"); root.hidden = false;
  const hero = el("section", null, "detail-hero");
  hero.append(el("p", game.author || "作者の公開名は未登録", "eyebrow"), el("h1", game.title), el("p", profile.summary, "detail-summary"));
  const actions = el("div", null, "detail-actions");
  if (!["unregistered", "missing"].includes(game.status)) actions.append(link("このゲームをプレイ ↗", `/?play=${encodeURIComponent(gid)}`, "small-primary"));
  actions.append(link("発表3ページを見る ↗", `/games/${gid}/slides`), link("学習コースとプロンプト ↗", "/learn"));
  hero.append(actions); root.append(hero);
  if (profile.screenshot) {
    const image = el("img", null, "game-screenshot");
    image.src = profile.screenshot; image.alt = `${game.title}の実際のプレイ画面`;
    root.append(image);
  }
  const play = section("遊び方");
  play.append(profile.how_to_play.length ? list(profile.how_to_play, true) : el("p", "操作・ルール・終了条件は、作者の提出後に掲載します。", "muted"));
  root.append(play);
  const tech = section("使った技術と役割");
  if (profile.technologies.length) {
    const table = el("table", null, "technology-table");
    const head = el("tr"); head.append(el("th", "技術"), el("th", "このゲームでの役割")); table.append(head);
    for (const item of profile.technologies) { const row = el("tr"); row.append(el("td", item.name), el("td", item.role)); table.append(row); }
    tech.append(table);
  } else tech.append(el("p", "現行コードを確認してから登録します。", "muted"));
  root.append(tech);
  const flow = section("操作から結果まで"); flow.append(list(profile.flow, true)); root.append(flow);
  const code = section("実際のコードを読む");
  code.append(el("p", "引用は登録された実ファイルから読み込みます。説明とコードを対応させてみましょう。", "muted"));
  for (const ref of profile.code_refs || []) {
    const block = el("article", null, "code-example");
    block.append(el("h3", ref.label), el("p", ref.explanation), el("p", `${ref.file} : ${ref.start_line}–${ref.end_line}行`, "code-source"));
    const pre = el("pre"); pre.append(el("code", ref.code)); block.append(pre); code.append(block);
  }
  if (!profile.code_refs.length) code.append(el("p", "コード引用はまだ登録されていません。", "muted"));
  root.append(code);
  const learn = section("このゲームで学ぶこと");
  learn.append(el("p", profile.audience, "muted"), list(profile.learning_goals));
  for (const item of profile.questions || []) {
    const question = el("div", null, "question"); question.append(el("h3", item.question));
    const hint = el("details"); hint.append(el("summary", "ヒントを見る"), el("p", item.hint));
    const answer = el("details"); answer.append(el("summary", "自分で答えた後に、答えを確認"), el("p", item.answer));
    question.append(hint, answer); learn.append(question);
  }
  root.append(learn);
  const creation = section("AIとの制作・本人の学習記録");
  const dl = el("dl", null, "creation-facts");
  for (const [key, label] of [["goal", "制作のねらい"], ["ai_role", "AIに頼んだこと"], ["human_role", "本人が担当したこと"], ["evidence", "確認できる記録"]]) {
    dl.append(el("dt", label), el("dd", profile.creation?.[key] || "未提出"));
  }
  creation.append(dl); root.append(creation);
  if (profile.limitations.length) { const limits = section("対応範囲と未確認のこと"); limits.append(list(profile.limitations)); root.append(limits); }
  if (profile.sources?.length) {
    const sources = section("参考資料");
    for (const source of profile.sources) { const a = link(source.label + " ↗", source.url); a.target = "_blank"; a.rel = "noopener noreferrer"; sources.append(a); }
    root.append(sources);
  }
}

function renderPage() {
  document.querySelectorAll(".slide").forEach((slide, index) => slide.hidden = index !== page);
  $("page-count").textContent = `${page + 1} / 3`;
  $("previous").disabled = page === 0; $("next").disabled = page === 2;
  $("notes-text").textContent = profile.slides[page].notes || "発表メモはまだありません。";
}

function presentation() {
  $("presentation").hidden = false;
  $("detail-link").href = `/games/${gid}`;
  profile.slides.forEach((data, index) => {
    const slide = el("article", null, "slide");
    const top = el("div", null, "slide-top"); top.append(el("span", game.title), el("span", profile.status === "sample" ? "教材用サンプル" : profile.status === "draft" ? "下書き" : "学習成果"));
    slide.append(top, el("h2", data.title));
    const content = el("div", null, "slide-content");
    const words = el("div", null, "slide-words"); words.append(el("p", data.message, "slide-message"), list(data.points));
    content.append(words);
    if (index === 0 && profile.screenshot) {
      const image = el("img", null, "slide-screenshot");
      image.src = profile.screenshot; image.alt = `${game.title}の実際のプレイ画面`;
      content.append(image);
    }
    if (index === 1 && profile.code_refs?.length) {
      const ref = profile.code_refs[data.code_ref ?? 0];
      const code = el("div", null, "slide-code"); code.append(el("p", ref.label), el("pre", ref.code), el("small", `${ref.file} : ${ref.start_line}–${ref.end_line}行`)); content.append(code);
    }
    slide.append(content, el("p", `${index + 1} / 3　${profile.status === "sample" ? "学生の学習成果は未提出" : profile.status === "draft" ? "内容確認前" : "4Pro Arcade"}`, "slide-foot"));
    $("slides").append(slide);
  });
  $("previous").addEventListener("click", () => { page = Math.max(0, page - 1); renderPage(); });
  $("next").addEventListener("click", () => { page = Math.min(2, page + 1); renderPage(); });
  $("notes-toggle").addEventListener("click", () => { $("speaker-notes").hidden = !$("speaker-notes").hidden; $("notes-toggle").setAttribute("aria-expanded", String(!$("speaker-notes").hidden)); });
  $("print").addEventListener("click", () => window.print());
  $("slide-fullscreen").addEventListener("click", async () => { try { await $("slide-stage").requestFullscreen(); } catch { $("page-error").hidden = false; $("page-error").textContent = "全画面表示を利用できません。"; } });
  window.addEventListener("keydown", event => {
    if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) return;
    if (!["ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    page = event.key === "Home" ? 0 : event.key === "End" ? 2 : Math.max(0, Math.min(2, page + (event.key === "ArrowRight" ? 1 : -1)));
    renderPage();
  });
  renderPage();
}

(async () => {
  try {
    const response = await fetch(`/api/games/${encodeURIComponent(gid)}/profile`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "資料を読み込めません。");
    game = data.game; profile = data.profile;
    document.title = `${game.title} — ${slideMode ? "発表3ページ" : "紹介・技術"}`;
    $("game-link").href = `/games/${gid}`; $("game-link").textContent = game.title;
    $("slide-crumb").hidden = !slideMode;
    $("publication-status").textContent = stateText();
    if (slideMode) { document.body.classList.add("presentation-mode"); presentation(); }
    else detail();
  } catch (error) { $("page-error").hidden = false; $("page-error").textContent = error.message; }
})();
