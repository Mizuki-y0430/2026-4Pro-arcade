# 6作品の操作とルールの説明画像

チャットで生成・確認した最終版の画像を、加工せずにコピーしています。生成には組み込みの画像生成ツールを使用しました。これまでの `*-guide.png` は上書きしていません。

| ゲームID | 採用画像 | 生成元のファイル名 |
| --- | --- | --- |
| kosen-survivor | kosen-survivor-rules-poster.png | exec-3502f504-ac34-4f43-9fb8-d236711a1401.png |
| balloon-hunter | balloon-hunter-rules-poster.png | exec-bcf00890-6db8-4f79-8ec2-f68f2874e732.png |
| yuugure-fishing | yuugure-fishing-rules-poster.png | exec-1e35c454-bd1f-43d0-b8f1-1700213e118b.png |
| brain-mole | brain-mole-rules-poster.png | exec-e1faefbe-afeb-4e07-bc8c-d49ba8dc1755.png |
| realtime-chess | realtime-chess-rules-poster.png | exec-4276dca9-2f45-4aa4-9c8a-f21dfe286e08.png |
| realtime-shogi | realtime-shogi-rules-poster.png | exec-0f817065-0235-46f5-8105-75b3c7c18e74.png |

## 共通の生成指示

横長16:9の1枚で、赤いタイトル帯・白い背景・大きな黒文字・01〜03の番号付きの区分を使用。ゲームの実装を確認し、実際に使える入力、標準の時間や得点、勝敗条件を日本語と模式図で説明。駒やモグラなどはゲーム内の色を維持し、画面全体をスクロールせずに読める構成としています。

モグラはライフ3から2への減少と50点刻みのスコア例、チェスはポーンを前へ1マス進める図を修正した最終版を採用しています。チェスのAI間隔は難易度で3・2・1秒、将棋のAI間隔は全難易度で約1秒です。

表示・更新方法は [ルールページの共通フォーマット](../../launcher/RULES_FORMAT.md) を参照してください。画像の表示先は `/games/ゲームID/rules` です。
