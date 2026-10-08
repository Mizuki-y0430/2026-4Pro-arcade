# POPな青い背景とテーマ

背景ファイル: `launcher/assets/pop-blue-background.png`
生成方法: Codexの組み込み画像生成ツール（image_gen）。
生成日: 2026-10-08。

参考: ユーザー提供の `yokai-punipuni_bg_3.jpg` と [ゲームUIの参考記事](https://gameui.matme.info/blog/archives/8870)。
参考画像は色合いと楽しさの確認に使いました。配信する背景は新しく生成した画像です。
キャラクター、ロゴ、固有のモチーフや元画像の配置を再現せず、泡・星・抽象的な丸い図形で構成しています。
元の参考画像はWeb配信・コミットの対象にしていません。

## 使用したプロンプト

```text
Use case: stylized-concept
Asset type: original background illustration for a family-friendly PC web arcade, landscape 16:9.
Primary request: create a brand new cheerful blue POP background. Input image is ONLY a reference for a cyan-to-blue palette and subtle playful pattern, not an edit target. Do not reproduce its shapes or layout.
Scene/backdrop: a luminous sky-blue to azure gradient with softly floating translucent bubbles, rounded stars, abstract rounded puzzle tiles and tiny confetti. Low contrast playful tone-on-tone pattern, with a few pale yellow, peach and lavender accents near the outer edges. Gentle highlights, crisp polished playful illustration, no dark areas.
Composition: wide full-bleed texture with lots of calm blue space throughout the middle for actual HTML interface cards. Background art only, no UI, no text, no lettering, no watermark, no characters, no ghosts, no logos. Original geometric motifs, no franchise-specific imagery. Fun and welcoming to children and adults. Keep the decoration restrained enough for readable foreground content.
```

## UI方針

- 青い背景、白い読み取りパネル、ゲームごとのアクセント色。
- 主操作は高さ48px以上、補助操作も44px以上を基本にする。
- 押すと沈むボタン、選択状態が明確なフィルター、浮かぶコントローラー。
- 「準備中」「プレイする」「ゲーム一覧」など、短い日本語を使う。
- キーボードのフォーカスを表示し、OSで動きを減らす設定がある場合は装飾アニメーションを止める。
- 紹介・学習・Webスライド・サンプルゲームも明るいテーマにそろえる。
- WebスライドのPDF保存では背景を印刷する設定を推奨。
