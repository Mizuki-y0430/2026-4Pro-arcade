"use strict";

// 単独で開いた説明ページでは、通常のリンクとして動きます。
// タイトル画面内で開いた場合だけ、親画面へ「戻る・遊ぶ」を伝えます。
if (window.parent !== window) {
  document.addEventListener("click", event => {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest("a[href]");
    if (!link) return;
    const url = new URL(link.href);
    if (url.origin !== location.origin || url.pathname !== "/") return;
    const gameId = url.searchParams.get("play");
    event.preventDefault();
    window.parent.postMessage({
      type: "arcade-guide",
      action: gameId ? "play" : "close",
      gameId
    }, location.origin);
  });
}
