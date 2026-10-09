# 現在の背景

背景: `launcher/assets/red-white-matte-honeycomb.png`。組み込み画像生成ツールで元画像を参照して新規生成。黒い帯と六角形のサイズを維持し、輪郭を薄く、光沢と陰影を弱くしました。上半分は赤、下半分は白基調です。配信URLは `/assets/red-champagne-honeycomb-background.png`。元の画像も保存しています。

# 赤と白のハニカム背景とPOPテーマ

## 以前の赤と白の生成背景

背景ファイル: `launcher/assets/red-white-honeycomb-background.png`
生成方法: Codexの組み込み画像生成ツール（image_gen）。
生成日: 2026-10-09。

上半分は赤系、下半分は白の六角形のハニカム模様です。新規生成した画像をホームと共通ページの背景として使用します。背景の色をそのまま見せるため、ホームの青い重ね色とメニューを囲む白い縁・半透明パネルを外しました。メニューの余白を減らし、ゲームタイルやロゴ・ボタンを大きく表示します。高さが低いPC画面では収まるサイズに調整します。

### 使用したプロンプト

```text
Use case: stylized-concept
Asset type: original raster background for a colorful family-friendly PC web arcade, wide landscape 16:9.
Primary request: an edge-to-edge geometric honeycomb pattern of regular tessellated hexagons. The TOP HALF is red, the BOTTOM HALF is white. Make the upper half clearly warm scarlet and coral red, and the lower half bright white with very pale cool-gray hexagon outlines. The red transitions gently into white around the horizontal midpoint, without a hard stripe. Keep regular hexagon cells consistent in size across the whole image; subtle alternating tone-on-tone fills and delicate inset highlights give a polished playful game-menu feel.
Composition: flat front-facing pattern, fills the entire canvas; medium-sized hexagons, about 20 columns across a wide canvas. Calm low-contrast pattern suitable behind actual HTML buttons and readable text. Keep red strongly red at the top and white clean at the bottom. No perspective, no objects, no characters, no interface, no lettering, no logos, no watermark, no existing franchise motifs. Render a crisp, cheerful, clean high-resolution background only.
```

## 以前の青い背景

背景ファイル: `launcher/assets/pop-blue-background.png`
生成方法: Codexの組み込み画像生成ツール（image_gen）。
生成日: 2026-10-08。

参考: ユーザー提供の `yokai-punipuni_bg_3.jpg` と [ゲームUIの参考記事](https://gameui.matme.info/blog/archives/8870)。
参考画像は色合いと楽しさの確認に使いました。配信する背景は新しく生成した画像です。
キャラクター、ロゴ、固有のモチーフや元画像の配置を再現せず、泡・星・抽象的な丸い図形で構成しています。
元の参考画像はWeb配信・コミットの対象にしていません。

### 使用したプロンプト

```text
Use case: stylized-concept
Asset type: original background illustration for a family-friendly PC web arcade, landscape 16:9.
Primary request: create a brand new cheerful blue POP background. Input image is ONLY a reference for a cyan-to-blue palette and subtle playful pattern, not an edit target. Do not reproduce its shapes or layout.
Scene/backdrop: a luminous sky-blue to azure gradient with softly floating translucent bubbles, rounded stars, abstract rounded puzzle tiles and tiny confetti. Low contrast playful tone-on-tone pattern, with a few pale yellow, peach and lavender accents near the outer edges. Gentle highlights, crisp polished playful illustration, no dark areas.
Composition: wide full-bleed texture with lots of calm blue space throughout the middle for actual HTML interface cards. Background art only, no UI, no text, no lettering, no watermark, no characters, no ghosts, no logos. Original geometric motifs, no franchise-specific imagery. Fun and welcoming to children and adults. Keep the decoration restrained enough for readable foreground content.
```

## タイトルロゴと表示サイズ

タイトルはユーザー提供の `launcher/assets/4PROARCADE_logo.png`（2172×724、透過PNG）を使用します。元画像は変更せず、表示枠で透明な上下余白を調整します。

PCでは画面の幅と高さから共通のサイズ単位を計算し、ロゴ・タイル・文字・ボタン・余白を連動して拡大・縮小します。1360×900を目安に、4Kでは約2.4倍のサイズになります。高さが低いPC画面では一覧を少し縮め、タブレットは3列、スマートフォンは2列で縦にスクロールできます。補助ボタンは44px以上を確保します。

## UI方針

- ゲームアイコンは真っ黒の太枠と細い白い内縁、短い黒い影で統一。ゲーム名は黄色い文字と黒い縁取りにする。
- 「ルール」「？」は黒枠・白から淡い赤のグラデーション・赤い文字・白いツヤを合わせる。下部の「まなぶ」「ゲームを追加」も同じ配色にし、「終了」は赤い面と白い文字を使う。ルールページにも同じ配色を使う。

- 赤と白の背景、白い読み取りパネル、ゲームごとのアクセント色。
- 主操作は高さ48px以上、補助操作も44px以上を基本にする。
- 押すと沈むボタン、選択状態が明確なフィルター、浮かぶコントローラー。
- 「準備中」「プレイする」「ゲーム一覧」など、短い日本語を使う。
- キーボードのフォーカスを表示し、OSで動きを減らす設定がある場合は装飾アニメーションを止める。
- 紹介・学習・Webスライド・サンプルゲームも明るいテーマにそろえる。
- WebスライドのPDF保存では背景を印刷する設定を推奨。

## 背景位置とルール画面

背景は共通CSSの固定レイヤーで表示し、ページの高さにかかわらず同じ画面位置・拡大率を維持します。スクロールバーの領域も常に確保し、遷移時の横ずれを防ぎます。ルール画面はホームと同じ画面の幅・高さから求めたサイズ単位で、説明欄・見出し・本文・ボタン・余白を拡大縮小します。小さい画面では文字の読みやすさを確保し、縦スクロールで読めます。
