# 技術スライド用画像

- `kosen-survivor-ready.png`：このPCの `games/local/2026-4Pro-ishida/` を起動して撮影した開始画面。
- `kosen-survivor-play.png`：同じゲームで下へ移動した直後のプレイ画面。盤面内に点滅する留年の出現予告と、大きくした単位の札を表示しています。
- 撮影日：2026年10月25日。どちらも1196×585ピクセル。生成画像ではありません。

ゲーム画面を更新したら、同じ範囲（得点欄と盤面）を撮り直して差し替えます。3ページ目のキャラクターと単位は、プレイ画面の一部をCSSの背景位置で表示しています。画像の寸法や構図を変えたら、`launcher/technology.css` の `.snake-piece` と `.credit-piece` の位置も確認してください。650px以下の画面用設定もあります。

2ページ目のマス目と3ページ目の衝突図は、HTMLとCSSで作った説明用の模式図です。実際の盤面は32列×20行です。難易度の数値は現行 `game.js` の `difficultySettings` にある開始時の移動間隔（180 / 160 / 138ミリ秒）に対応します。ゲーム側の設定を変更したら、スライドの表示と代替テキストも更新してください。

## 追加4作品

以下も2026年10月13日に、このPCで実際のゲームを起動して撮影しています。生成画像ではありません。

- `balloon-hunter-play.png`：`games/local/3hu/` のプレイ画面。
- `yuugure-fishing-play.png`：`games/local/2026_4Pro_fishinggame/` の釣り画面。
- `realtime-chess-ready.png`：`games/local/chess/` の開始前の盤面と設定。
- `brain-mole-play.png`：`games/local/tesuto/` の基礎数学のプレイ画面。

図はHTMLとCSSによる説明用の模式図です。魚の割合・反応時間は `fishing.js` の魚データ、チェスの待ち時間・AIは `web_game.py` と `chess/ai.py`、クイズの得点・時間は `tesuto/web_game.py` に対応します。ゲーム側の設定を変えたときは本文と図、画像の代替テキストも合わせて更新してください。
