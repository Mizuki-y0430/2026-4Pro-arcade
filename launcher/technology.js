"use strict";

// 全ゲーム共通。本文と図は各HTMLにあり、このファイルはページ送りを担当します。
const slides = [...document.querySelectorAll(".slide")];
const dots = [...document.querySelectorAll("[data-page]")];
const previous = document.getElementById("previous");
const next = document.getElementById("next");
let page = 0;

function showPage(number, moveFocus = false) {
  page = Math.max(0, Math.min(slides.length - 1, number));
  slides.forEach((slide, index) => {
    slide.hidden = index !== page;
    // サイズ確保のため重ねた非表示ページには、フォーカスを移せなくします。
    slide.inert = index !== page;
    slide.setAttribute("aria-hidden", String(index !== page));
  });
  dots.forEach((dot, index) => {
    if (index === page) dot.setAttribute("aria-current", "page");
    else dot.removeAttribute("aria-current");
  });
  previous.disabled = page === 0;
  next.disabled = page === slides.length - 1;
  document.getElementById("page-count").textContent = `${page + 1} / ${slides.length}`;
  if (moveFocus) {
    slides[page].querySelector("h1").focus({ preventScroll: true });
    // 縦に長くなるスマートフォンでも、次のページの見出しから読めます。
    window.scrollTo({ top: 0, behavior: "instant" });
  }
}

previous.addEventListener("click", () => showPage(page - 1, true));
next.addEventListener("click", () => showPage(page + 1, true));
dots.forEach(dot => dot.addEventListener("click", () => showPage(Number(dot.dataset.page), true)));
document.addEventListener("keydown", event => {
  if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  showPage(event.key === "Home" ? 0 : event.key === "End" ? slides.length - 1 : page + (event.key === "ArrowRight" ? 1 : -1), true);
});

document.querySelector(".deck-controls").hidden = false;
document.querySelector(".key-hint").hidden = false;
document.getElementById("slides").classList.add("is-paged");
showPage(0);
