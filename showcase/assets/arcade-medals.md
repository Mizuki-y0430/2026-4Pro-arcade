# 6作品のメダルアイコン

`arcade-medals-red-white.png` は内蔵画像生成ツールで作成し、ユーザーが採用した6作品のアイコンシートです。1536×1024ピクセル。2026年10月30日。

元の生成画像：`exec-3e179715-b3db-49dd-9696-47d7c2b53e9f.png`。元画像を変更せず、プロジェクトにコピーしています。

## デザイン

- 同じ太さの黒い外周と金の細い縁取り。
- 幅広いリングは各メダルの上半分が赤、下半分が白。
- 上段はスネークと単位カード、風船とカーソル、夕日と魚。
- 下段は茶色のモグラ、赤いナイトと白いポーン、王の将棋駒と時計。

## 最終の色変更プロンプト

内蔵ツールの参照画像には、銀色リングの前段階のシートを指定しました。

> Precise color edit of the supplied six-medal arcade icon sheet. Change ONLY the broad silver / pale blue metallic annular rim on EACH of the six circular medals. On every individual medal, recolor the UPPER SEMICIRCLE of that annular rim to bright arcade RED (#f3273c), and recolor the LOWER SEMICIRCLE of that annular rim to clean WHITE. Divide the ring at that medal's own horizontal centerline, so the upper arc from 9 o'clock through 12 o'clock to 3 o'clock is red, and the lower arc from 3 o'clock through 6 o'clock to 9 o'clock is white. BOTH the top-row medals AND the bottom-row medals must EACH have their OWN upper half red and lower half white. This is NOT a division between the top row and bottom row of the whole sheet. Remove the pale-blue/silver hue from those broad annular rings. Preserve their same width, circular shape, subtle bevel, lighting and dimensional highlights, with shaded red on top and shaded white below. Keep all thin GOLD trim lines and black outer edges unchanged. Keep all interior illustrations, inner cream backgrounds, game characters, props, words, Japanese caption typography, layout, sizes, spacing, white sheet background and drop shadows exactly as in the original. Do not recolor any other blue, red or white objects, especially do not recolor the blue fish. No other design changes, no added symbols, no cropping. Output the full same 3-column by 2-row concept sheet with all six names and all six badges visible.

## 表示範囲

`launcher/app.js` の `medalCrops` がSVGのviewBoxで各メダルだけを表示します。画像に描かれたキャプションは表示範囲に含めず、ゲーム名・ルール・技術説明ボタンはHTMLで表示します。画像の再生成や加工は不要です。

| ゲームID | x | y | 幅 | 高さ |
| --- | ---: | ---: | ---: | ---: |
| kosen-survivor | 64 | 10 | 422 | 407 |
| balloon-hunter | 552 | 10 | 426 | 407 |
| yuugure-fishing | 1043 | 10 | 424 | 407 |
| brain-mole | 61 | 494 | 426 | 412 |
| realtime-chess | 551 | 494 | 427 | 412 |
| realtime-shogi | 1041 | 494 | 425 | 412 |

`games.json` の明示的な `cover` は優先されます。未登録・未準備のゲームは従来のロック表示を使用し、メダル画像の読込失敗時は共通のゲームイラストを表示します。
