# ゲームメニューのイラスト

生成方法: Codexの組み込み画像生成ツール（image_gen）。
生成日: 2026-10-08。

保存先:
- `showcase/assets/neon-dodge-cover.png`: ブロックよけの表紙
- `showcase/assets/reaction-lab-cover.png`: 反応チャレンジの表紙

ユーザー提供のUIスクリーンショットは、丸い枠・大きな絵・太い縁取り文字という画面構成の参考にしました。
元のキャラクター・道具・ロゴは使用していません。
表紙は新しく生成したゲーム内容のイラストで、画面内の日本語はHTMLのテキストです。
学習メニュー等の既存のベクター表現はSVGで描画しています。

## ブロックよけ

```text
Use case: stylized-concept. Asset type: square illustrated game menu cover, full bleed, no typography. Create original colorful hand-drawn arcade key art: a small turquoise triangular player ship nimbly dodging three falling rounded purple blocks, with curved speed trails showing sideways movement. This accurately represents a simple avoid-the-blocks game, not a space shooter. Big expressive toy-like objects, thick dark navy ink outlines, cheerful chunky proportions, glossy painted highlights, bright mint and pale lemon background with a few starbursts. Strong playful Japanese family game menu energy, clean appealing illustration. The player ship should be the dominant object in the lower middle, blocks above. All objects fit comfortably within the central 80 percent. Square framing, no border, no card frame, no lettering, no numbers, no logos, no mascot or franchise characters. This is original game artwork to sit underneath a real HTML title.
```

## 反応チャレンジ

```text
Use case: stylized-concept. Asset type: square illustrated game menu cover, full bleed, no typography. Create original colorful hand-drawn arcade key art for a reaction-speed clicking game: a big cheerful rounded purple stopwatch behind an oversized green glowing push button, with a simple white lightning symbol on the button and a small cartoon glove pointing at its edge. Thick dark navy ink outlines, chunky toy-like proportions, glossy painted highlights, energetic yellow spark accents. Pale lavender and peach backdrop, strong playful family game menu energy, clean appealing illustration. Stopwatch and green button fill the central 80 percent. Square framing, no border, no card frame, no lettering, no digits, no logos, no mascot or franchise characters. This is original game artwork to sit underneath a real HTML title.
```

## トップ画面の構成

- 大きいタイル全体を押してゲームを起動。
- 「？」は独立したボタンで、遊び方・作者・技術紹介・3ページの発表を表示。
- 未登録枠は半透明の鍵付きタイルで示し、起動ボタンを無効化。
- 長い説明文は遊び方ダイアログと詳細ページに置く。
- 下のメニューから学習コース・ゲーム追加方法・終了を選ぶ。
- タイルのイラストは設定の `cover` で差し替える。画像が読めない場合は共通のSVGを表示。
