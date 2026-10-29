# 4Pro Arcade

最大6個のミニゲームを、上3個・下3個のPC用メニューから選んで遊ぶランチャーです。
Windows + Python 3.11以上 + 現行のEdge / Chromeを想定しています。
ランチャー本体はPython標準ライブラリだけで動きます。インターネット接続はプレイに不要です（各ゲームが外部サービスを使う場合は別途必要です）。

## 起動

別の人・別のPCで全体を使う場合の手順は **[4Pro Arcadeを別のPCで遊ぶ](PLAYING.md)** にまとめています。本体を1回クローンし、`setup.bat` → `start.bat` の順で実行すれば全6ゲームを準備できます。全作品を同梱しているため、各メンバーの非公開リポジトリへの権限は不要です。

1. 初回は `setup.bat` をダブルクリックします。`.venv` を作り、同梱の全6作品を確認して必要なパッケージを準備します。Python 3.11以上と、初回のパッケージ取得用のネット接続が必要です。
2. `start.bat` をダブルクリックします。ブラウザーに6枠のメニューが開きます。
3. ゲームを選択します。Webゲームはメニュー内、Pythonのデスクトップゲームは別ウィンドウで動きます。
4. Webゲームの「← ゲーム一覧」でゲームを停止して戻ります。Pythonゲームはゲームのウィンドウを閉じるか、カードの「停止する」で終了します。
5. 終了はメニュー右上の「終了」を押します。起動したサーバーとゲームのプロセスも停止します。

**ブラウザーのタブを閉じるだけではランチャーは終了しません。** メニューの「終了」、または起動したターミナルで `Ctrl+C` を使ってください。

ゲーム本体はすべてGit管理対象です。`.venv` とプレイ記録は管理対象外で、他のPCでは `setup.bat` が実行環境を準備します。`start.bat` から始めても、不足があると自動でセットアップします。準備済みのゲーム・記録・制作途中の編集は上書きしません。
Pythonサンプルはブラウザー内で動きます。元のTkinter版も `games/samples/reaction-lab/main.py` に残しています。元の版を使う場合とテストには Tcl/Tk が必要です。

## 現在のゲーム一覧

- **ゲーム1：こうせんサバイバー**: 単位を集めるスネークゲーム。大きなカードから3年生・4年生・5年生を選び、電気情報工学科の進級・卒業累計85／125／167単位をめざします。目標以上でクリア。落単は6単位まで続行、7単位目・壁・自分の体で終了します。[単位数の根拠](games/local/2026-4Pro-ishida/CREDIT_TARGETS.md)。
- **ゲーム2：ふうせんハンター**: メンバーのWebゲーム（3hu）。30秒間で風船をクリック / タップして得点を集めます。小さい風船は3点、中くらいは2点、大きい風船は1点。スタートボタン / Enterで開始します。
- **ゲーム3：ゆうぐれ釣り日和**: 60秒間で魚を釣るWebゲーム。開始すると自動で投げ、HIT後に動く針を黄色のエリア内でEnterで止めて釣り上げます。難しい魚ほど成功エリアが狭く、1回の挑戦は5秒以内です。結果の約1.4秒後に自動で投げ直します。Spaceで待たずに次へ進めます。
- **ゲーム4：デス・モグラたたき**: Python + Webのクイズゲーム。正解のモグラを選び、得点を集めます。
- **ゲーム5：リアルタイムチェス**: Python + Webのゲーム（chess）。メニュー内で遊べます。スタート後、白の駒と移動先をクリックしてAIと対戦します。ターン制ではなくクールタイムがあります。AI同士の観戦、AIの強さ変更、Q / Escで対局停止、リセットにも対応します。原作：k4m4b0k02009、Web対応：yamamoto。
- **ゲーム6：リアルタイム将棋**: チェスと同じPython + Web方式のゲーム。先手の駒でAIとリアルタイム対戦できます。9×9の盤、持ち駒、成り、AIの強さ3段階、AI同士の観戦に対応します。コードは `games/realtime-shogi/` に同梱しているため、追加のクローンやパッケージは不要です。

NEON DODGEとREACTION LABはゲーム一覧から外しています。実装例のコードは `games/samples/` にあります。

## コード理解から発表までの学習コース

メニューの「学習コース」から、50分×4回を目安に学習できます。
高専1・2年生の初学者を基本に、Pythonを使う3年生向けの補足もあります。

1. AIへプロンプトを渡し、動作を保ってコードの整理と説明コメントを追加。
2. 自分のゲームのコードに対応した学習資料を作り、重要な処理を読む。
3. 本人が理解確認に答え、1項目の変更を予測・実行・比較。
4. 本人の記録から、ゲーム説明と3ページの発表資料を作る。

本人の学習記録から作る「紹介・技術」「発表3ページ」は、`/games/ゲームID` と `/games/ゲームID/slides` で開けます。ホームの「？」は、下記の図解付き技術スライドを開きます。
Webスライドは左右キーで移動でき、発表メモ、全画面、全3ページの印刷 / PDF保存に対応します。
サンプル資料は見本です。学生の制作履歴や学習成果はまだ提出されていません。
未登録枠には、本人が記入する紹介・発表のひな形を表示します。

- [学生向けガイド](learning/student-guide.md)
- [記録ワークシート](learning/workbook.md)
- [担当者向けガイド](learning/teacher-guide.md)
- [提出と掲載の手順](learning/submission-guide.md)
- [発表用JSONひな形](showcase/template.json)

作者の資料を `showcase/ゲーム名.json` に保存し、games.jsonに `"profile": "showcase/ゲーム名.json"` を追加します。
形式とコード引用の行番号は `arcade.py --check` で確認できます。コードは登録された実ファイルから引用します。
内容確認前は `status: "draft"`、本人と担当者が確認後は `"published"` にします。詳細は提出手順をご覧ください。
この仕組みはローカルPC用です。外部へ資料を公開する場合は、別途Webサイトの公開構成が必要です。

## メンバーのゲームを追加する

### PythonのゲームもWeb画面で遊べる？

できます。ゲームの作り方によって組み込み方が変わります。

| Pythonゲームの種類 | メニュー内で遊ぶ方法 |
| --- | --- |
| Flask / FastAPIなど、すでにWeb画面がある | `service` で登録。Pythonサーバーを起動し、その画面をメニュー内に表示 |
| Pythonでルールや計算、Tkinter等で画面を作っている | Pythonの処理をAPIにし、画面・入力をHTML / JavaScriptに変更。REACTION LABがこの例 |
| pygameを使っている | [pygbag](https://pygame-web.github.io/wiki/pygbag/)等でWeb向けに移植・ビルドし、ビルド後の公開フォルダを `static` で登録。非同期のゲームループ、使うライブラリ、アセット等に調整が必要 |

Pythonのデスクトップ用GUIを、設定変更だけで自動的にWeb画面へ変換する機能はありません。
どの方式で移植できるかは、メンバーのゲームのコードと依存ライブラリを確認して判断します。
Web画面のあるゲームを `service` に登録する場合、`"language": "python"` を付けるとPythonフィルターにも表示できます。

実装例のREACTION LABは追加パッケージなしで起動します。登録する場合は、`service` の `command` で `web.py` を起動するとメニュー内でプレイできます。
Tkinter版を試す場合は、その枠を `"kind": "python"`, `"entry": "main.py"` に変更できます。
ベスト記録はゲーム画面を閉じるまで保持します。正式なスコアランキング用の不正対策は実装していません。

ランチャーを終了してから登録してください。変更は次の起動時に読み込まれます。

### 1. ゲーム本体と出典

現在の6作品は本体にすべて同梱しています。ゲーム1〜5は `games/local/`、将棋は `games/realtime-shogi/` にあります。クローンまたはZIP取得で全体が揃い、元の非公開リポジトリへのアクセスは不要です。

出典と取り込み元のコミットは [同梱ゲームの出典](games/local/README.md) と `game-sources.json` に記録しています。現在のゲームソースはこの本体リポジトリで管理します。更新は本体の `git pull --ff-only` で取得してください。

新しい作品を取り込む際も、ソース・画像・必要なデータを本体に含めます。別リポジトリの `.git`、仮想環境、キャッシュ、個人のプレイ記録、環境変数ファイルは含めません。

モグラたたきの問題は `games/local/tesuto/data/questions.xlsx` で管理します。Web版は `openpyxl` を使い、Pygameは不要です。設定とランキングは `.web-data/` に保存され、Git管理対象から除外しています。将棋・チェスはPython標準ライブラリだけで動きます。

GitHub Actionsでランチャー・セットアップ・将棋のテストと、同梱ゲームの設定・ファイルの確認を行います。

### 2. `games.json` の枠を書き換える

`games` 配列は1〜6枠。`id` は重複しない半角英数字とハイフン、`path` はランチャーのフォルダからの相対パスです。
空き枠の `enabled: false` を **削除するか `true` に変更** します。
`color` は `mint` / `violet` / `amber` / `pink` / `blue` を使えます。
以下は設定例です。JSONにコメントは書けません。

#### HTML / CSS / JavaScriptのみのWebゲーム

```json
{
  "id": "member-web",
  "title": "メンバーのWebゲーム",
  "description": "ゲームの紹介文",
  "author": "メンバー名",
  "kind": "static",
  "path": "games/local/member-game",
  "entry": "index.html",
  "controls": "矢印キーで移動 / スペースで決定",
  "color": "mint"
}
```

各ゲーム専用のローカルHTTPサーバーで配信します。`file://` ではありません。
Vite等でビルドしたゲームは、ゲームのREADMEに従って先にビルドし、`path` を `games/local/member-game/dist` にしてください。
`entry` はその公開フォルダ内のファイルを指定します。通常は公開フォルダ直下の `index.html` です。
SPAのURL書き換え、PHP、データベース、バックエンドAPIは `static` では動きません。必要なら次の `service` を使用します。

#### pygame / TkinterなどのPythonデスクトップゲーム

```json
{
  "id": "member-python",
  "title": "メンバーのPythonゲーム",
  "description": "別ウィンドウでプレイするゲーム",
  "author": "メンバー名",
  "kind": "python",
  "path": "games/local/member-python",
  "entry": "main.py",
  "args": [],
  "controls": "クリックでプレイ",
  "color": "violet"
}
```

デフォルトではランチャーの `.venv` のPythonを使います。例:

```powershell
.\.venv\Scripts\python.exe -m pip install -r games/local/member-python/requirements.txt
```

ゲームを起動するときの作業フォルダは `path` です。相対パスの画像・音声をそのまま読み込めます。
`args` には起動時の追加引数を文字列の配列で指定できます。
PythonゲームのウィンドウをWeb画面に埋め込む機能はありません。
ターミナルへの対話入力が必要なゲームは、GUIへの変更などが必要です。

**ゲーム間で依存パッケージのバージョンが競合する場合** は、ゲーム専用の仮想環境を作ります。

```powershell
python -m venv games/local/member-python/.venv
.\games\local\member-python\.venv\Scripts\python.exe -m pip install -r games/local/member-python/requirements.txt
```

その枠に次の設定を追加します（ランチャーのフォルダからの相対パス）:

```json
"python": "games/local/member-python/.venv/Scripts/python.exe"
```

#### Pythonバックエンド付きWebゲーム

Flaskの例です。ゲームの依存パッケージはあらかじめインストールしてください。

```json
{
  "id": "member-service",
  "title": "サーバー付きゲーム",
  "description": "PythonのバックエンドとWeb画面を使うゲーム",
  "author": "メンバー名",
  "kind": "service",
  "language": "python",
  "path": "games/local/member-service",
  "command": ["{python}", "-m", "flask", "--app", "app", "run", "--host", "127.0.0.1", "--port", "{port}"],
  "url_path": "/",
  "startup_timeout": 30,
  "color": "blue"
}
```

- `command` は実行ファイルと引数の配列です。シェルのコマンド文字列や `&&` は使いません。
- `{python}` は選択されたPython実行ファイル、`{port}` は空きポート、`{root}` はゲームのフォルダに置き換わります。
- 環境変数 `PORT` にも同じポート番号を渡します。ゲームがそのポートを使うように起動コマンドを設定してください。
- 固定ポートが必要なら `"port": 5000` のように追加します。使用中のポートはエラーにします。
- HTTP応答を待ってからWeb画面を開きます。初期値30秒、`startup_timeout` で最大300秒まで設定できます。
- `url_path` はゲーム画面へのパス。デフォルトは `/` です。
- `python` を指定してゲーム専用の仮想環境を使用することもできます。
- WindowsではNode / Viteも、例えば `"command": ["node", "node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--port", "{port}", "--strictPort"]` で起動できます。先にゲーム側で `npm install` してください。`npm.cmd` 等のシェルスクリプト経由より、サーバーの実行ファイルを直接指定する方式を推奨します。
- ゲーム側がiframe表示を禁止している場合は、その設定の変更が必要です。

### 3. 設定を確認して再起動

```powershell
.\.venv\Scripts\python.exe arcade.py --check
```

`ready` は起動準備済み、`unregistered` は未登録、`missing` はゲームフォルダ等が見つからない状態です。
依存パッケージまで確認するには実際にゲームを起動してください。
起動時の出力・エラーは `.logs/ゲームID.log` に保存します（再起動時に上書き）。

## Gitと開発

開発ブランチ: `codex/pop-blue-arcade`（`codex/arcade-launcher`から分岐）。初期状態のGitHubリポジトリは空でした。
このブランチにランチャー本体、サンプル、設定、テストをコミットします。
`.venv`、`.logs`、別リポジトリのGit内部情報、個人のプレイ記録はGit管理対象外です。GitHubへのpushは別途行ってください。

```powershell
git status
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git push -u origin codex/pop-blue-arcade
```

GitHub ActionsでもWindows + Python 3.11でバックエンドのテストを実行する設定を入れています。

## 構成

```text
2026-4Pro-arcade/
├── .venv/                    # このPCのPython仮想環境（Git対象外）
├── arcade.py                 # ローカルHTTPとゲーム起動・停止の管理
├── games.json                # 最大6枠の設定
├── game-sources.json         # 同梱5作品の出典・取り込み元コミット
├── setup_arcade.py           # 同梱作品の確認・パッケージ導入
├── PLAYING.md                # 別の人・別PCで遊ぶ手順
├── launcher/                 # 共通メニューのHTML / CSS / JS
├── games/
│   ├── samples/              # Web / Pythonサンプル
│   ├── realtime-shogi/       # 同梱のリアルタイム将棋
│   └── local/                # 同梱するメンバーのゲーム（Git管理対象）
├── tests/                    # 設定・HTTP・プロセス管理のテスト
├── .logs/                    # ゲームの実行ログ（Git対象外）
├── setup.bat
└── start.bat
```

ランチャーは `127.0.0.1` のみに公開し、LANやインターネットへは公開しません。
ゲームごとに別のポートを使います。空きポートは自動選択されます。
メニュー内の画面で全画面表示を選べます。`Esc` で全画面解除、一覧へは上部の戻るボタンを使います。
信頼できるメンバーのゲームを登録してください。Pythonやサーバー型のゲームは、このPCの通常のプログラムとして実行されます。

開発時にブラウザーを自動起動したくない場合:

```powershell
.\.venv\Scripts\python.exe arcade.py --no-browser --port 8765
```

表示された `http://127.0.0.1:8765/` を開いてください。

## 画面デザイン

6作品のプレイ画面は、鮮やかな赤の看板・白い表示板と押しボタン・黄色のマークを共通に使います。タイトルには作品ごとの星・太陽・王冠・将棋駒のマークと斜めラインを添えています。画面の高さに合わせてゲーム領域を広げ、プレイ中はページ全体をスクロールせずに操作できます。将棋とチェスはPCで対局情報を右側に配置し、設定・操作説明は上部ボタンから開きます。小さい画面では情報を下に回し、分野選択・棋譜・詳しい説明などは各欄の中でスクロールします。風船とモグラにはSVGの空・草原・柵、釣りにはSVGの夕景・釣り竿と釣果の棚を使います。背景は画面の大きさに合わせて描画し、将棋の木の盤面・茶色のモグラ・チェスの赤対白は維持しています。正解や得点は黄色で強調し、動きを減らす設定にも対応します。

青いPOPな背景は組み込み画像生成ツールで新しく生成しました。
元の参考画像は配信していません。生成プロンプトとUI方針は [背景の記録](launcher/assets/README.md) に保存しています。
主なボタンは大きくし、押下時の反応・キーボードのフォーカス・動きを減らす設定に対応しています。

## ゲームタイルの表紙と名前

トップ画面はタイル全体を押すとプレイできます。「？」から遊び方・紹介・発表を開けます。
メニューに表示する短い名前は `menu_title`、表紙画像は `cover` で指定します（どちらも任意）。

```json
"menu_title": "ゲームの短い名前",
"cover": "/showcase/assets/member-game-cover.png"
```

画像を `showcase/assets/` に保存します。ファイル名は半角小文字・数字・ハイフン、形式はPNG / JPG / WebP、5MB以下です。
`menu_title` は1〜24文字で、未設定なら `title` を表示します。表紙は正方形を推奨します。
`cover` が未設定、または表示時に画像が読めない場合は、共通のゲームイラストを使います。
サンプルの表紙は新しく生成したものです。[生成プロンプト](showcase/assets/menu-artwork.md) を記録しています。

## ゲームのルールページ

各ゲームの左上にある丸い「ルール」ボタンから、ルールと操作方法を確認できます。ページ内の「このゲームであそぶ」でゲームを開始します。ゲームアイコン本体は直接プレイ、右上の「？」は下記の技術スライドへ直接移動します。

説明は `games.json` の各ゲームにある `rules`（ルール）と `operations`（操作方法）を編集します。どちらも日本語の説明を並べた配列で、最大10項目・各300文字までです。`operations` が未登録の場合は既存の `controls` を表示します。変更後はランチャーを再起動してください。

ルールページのURLは `/games/ゲームID/rules` です。説明を開くだけではゲームは起動しません。

タイトル画面の「？」と「ルール」は、同じ画面内のフレームで説明を表示します。タイトルで全画面表示にしておけば、説明を開く・ゲーム一覧に戻る・ルールから遊ぶ操作でも継続します。ブラウザーの戻る・進むにも対応します。本文は従来のHTMLを使い、リンクの連携だけを `launcher/guide-navigation.js` が担当します。URLを直接開く場合は、通常の説明ページとして表示されます。

## 各ゲームの技術スライド

登録済み作品の「？」から、図を使った各3ページの説明を開けます。背景はルールページと同じ画像です。
URLは `/games/ゲームID/technology` です。前へ・次へ、ページの丸いボタン、左右キーで切り替えます。全画面ボタンはタイトル画面にあります。説明を開くだけではゲームは起動しません。

| ゲーム | 本文・図のファイル（launcher内） | 主な説明 |
| --- | --- | --- |
| こうせんサバイバー | `kosen-technology.html` | HTML/CSS/JS、Canvas、移動と衝突 |
| ふうせんハンター | `balloon-technology.html` | 位置と時間、タップ、ブラウザー内の保存 |
| ゆうぐれ釣り日和 | `fishing-technology.html` | CSS/SVG、状態、魚の抽選と制限時間 |
| リアルタイムチェス | `chess-technology.html` | WebとPythonの通信、盤面、ルールとAI |
| リアルタイム将棋 | `shogi-technology.html` | 9×9の盤面、持ち駒・成り、リアルタイム対局とAI |
| デス・モグラたたき | `mole-technology.html` | PythonとExcel、出題、正誤判定とJSON保存 |

1・2年生が編集しやすいよう、追加ライブラリやビルドを使わず、各ページをコメント付きの `<section>` にしています。色・配置・文字サイズは共通の `launcher/technology.css`、ページ送りは `launcher/technology.js` を編集します。HTML・CSS・JSの修正はページの再読み込みで反映されます。

新しいゲームの説明は既存のHTMLをコピーして3ページを編集し、`arcade.py` の `TECHNOLOGY_PAGES` にゲームIDとファイル名を登録します。登録後はランチャーを再起動してください。一覧にないゲームの「？」は `launcher/technology-pending.html` を開きます。

画像の出典と差し替え時の注意は [技術スライドの画像](showcase/assets/technology.md) を参照してください。
