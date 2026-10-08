"use strict";
const $ = id => document.getElementById(id);
const el = (tag, text, className) => { const node = document.createElement(tag); if (text != null) node.textContent = text; if (className) node.className = className; return node; };
let curriculum, currentStep = 0, track = "basic", noticeTimer;
function notice(text) { $("notice").textContent = text; $("notice").hidden = false; clearTimeout(noticeTimer); noticeTimer = setTimeout(() => $("notice").hidden = true, 5000); }
function fileUrl(file, download = false) { return `/learning/files/${file.split("/").map(encodeURIComponent).join("/")}${download ? "?download" : ""}`; }

function renderStep() {
  $("step-nav").replaceChildren();
  curriculum.steps.forEach((step, index) => {
    const button = el("button", null, index === currentStep ? "step-nav selected" : "step-nav");
    button.setAttribute("aria-current", index === currentStep ? "step" : "false");
    button.append(el("span", `0${step.number}`, "step-number"), el("span", step.title));
    button.addEventListener("click", () => { currentStep = index; renderStep(); });
    $("step-nav").append(button);
  });
  const step = curriculum.steps[currentStep], body = $("step-content");
  body.replaceChildren(el("p", `STEP 0${step.number} / ${step.time}`, "eyebrow"), el("h3", step.title), el("p", step.outcome, "step-outcome"));
  const list = el("dl", null, "step-facts");
  for (const [label, value] of [["本人がすること", step.student_task], [track === "basic" ? "1・2年生の基本" : "Python・3年生の追加", step[track]], ["次へ進む前の確認", step.check]]) {
    list.append(el("dt", label), el("dd", value));
  }
  body.append(list);
  const details = el("details", null, "prompt-box");
  details.open = true;
  details.append(el("summary", "AIに渡すプロンプト"));
  const tools = el("div", null, "prompt-tools");
  const copy = el("button", "プロンプトをコピー", "small-primary");
  copy.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(step.prompt_text); notice("コピーしました。学年・経験・ゲーム名を記入してAIへ渡してください。"); }
    catch { textarea.focus(); textarea.select(); notice("文章を選択しました。Ctrl+Cでコピーしてください。"); }
  });
  const download = el("a", "保存 ↓", "text-link");
  download.href = fileUrl(step.prompt_file, true);
  tools.append(copy, download);
  const textarea = el("textarea", null, "prompt-text");
  textarea.value = step.prompt_text;
  textarea.readOnly = true;
  textarea.setAttribute("aria-label", `${step.title}のプロンプト`);
  details.append(tools, textarea, el("p", "学年・経験・ゲーム名を書いて使います。本人の回答や制作履歴は、実際の記録を渡してください。", "muted"));
  body.append(details);
}

function inline(node, text) {
  for (const part of text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g)) {
    if (part.startsWith("`")) node.append(el("code", part.slice(1, -1)));
    else if (part.startsWith("**")) node.append(el("strong", part.slice(2, -2)));
    else node.append(document.createTextNode(part));
  }
}

// Render the subset of Markdown used by our guides with text nodes, never raw HTML.
function markdown(text) {
  const fragment = document.createDocumentFragment(), lines = text.replace(/\r/g, "").split("\n");
  let code = null, list = null, table = null;
  for (const line of lines) {
    if (line.startsWith("```")) {
      if (code) code = null;
      else { const pre = el("pre"); code = el("code"); pre.append(code); fragment.append(pre); }
      list = null; table = null; continue;
    }
    if (code) { code.textContent += line + "\n"; continue; }
    if (!line.trim()) { list = null; table = null; continue; }
    if (line.startsWith("|")) {
      if (/^\|[\s:|\-]+\|$/.test(line)) continue;
      if (!table) { table = el("table"); const wrap = el("div", null, "table-scroll"); wrap.append(table); fragment.append(wrap); }
      const row = el("tr");
      for (const value of line.split("|").slice(1, -1)) { const cell = el(table.rows.length ? "td" : "th"); inline(cell, value.trim()); row.append(cell); }
      table.append(row); continue;
    }
    table = null;
    const heading = line.match(/^(#{1,3})\s+(.+)/);
    if (heading) { const h = el(`h${heading[1].length}`); inline(h, heading[2]); fragment.append(h); list = null; continue; }
    const item = line.match(/^(- |\d+\. )(.+)/);
    if (item) {
      const type = item[1] === "- " ? "ul" : "ol";
      if (!list || list.tagName.toLowerCase() !== type) { list = el(type); fragment.append(list); }
      const li = el("li"); inline(li, item[2]); list.append(li); continue;
    }
    list = null;
    const p = el("p"); inline(p, line); fragment.append(p);
  }
  return fragment;
}

async function openDocument(doc) {
  try {
    const response = await fetch(fileUrl(doc.file));
    if (!response.ok) throw new Error("資料を読み込めません。");
    $("document-body").replaceChildren(markdown(await response.text()));
    $("document-download").href = fileUrl(doc.file, true);
    $("document-dialog").showModal();
    $("document-dialog").scrollTop = 0;
  } catch (error) { notice(error.message); }
}

document.querySelectorAll("[data-track]").forEach(button => button.addEventListener("click", () => {
  if (!curriculum) return;
  track = button.dataset.track;
  document.querySelectorAll("[data-track]").forEach(node => { node.classList.toggle("selected", node === button); node.setAttribute("aria-pressed", String(node === button)); });
  renderStep();
}));
$("document-close").addEventListener("click", () => $("document-dialog").close());
(async () => {
  try {
    const response = await fetch("/api/learning");
    if (!response.ok) throw new Error("学習資料を読み込めません。ランチャーを起動してください。");
    curriculum = await response.json();
    $("course-description").textContent = curriculum.description;
    $("project-question").textContent = curriculum.question;
    $("time-plan").textContent = curriculum.time_plan;
    renderStep();
    for (const doc of curriculum.documents) {
      const button = el("button", null, "document-card");
      button.append(el("strong", doc.title + " ↗"), el("span", doc.description));
      button.addEventListener("click", () => openDocument(doc));
      $("documents").append(button);
    }
  } catch (error) { notice(error.message); }
})();
