# 4Pro Arcade

8個のミニゲームを、1つのPC用メニューから選んで遊ぶランチャーです。
Windows + Python 3.11以上 + 現行のEdge / Chromeを想定しています。
ランチャー本体はPython標準ライブラリだけで動きます。インターネット接続はプレイに不要です（各ゲームが外部サービスを使う場合は別途必要です）。

## 起動

1. 初回は `setup.bat` をダブルクリックします。フォルダ内に `.venv` を作ります。
2. `start.bat` をダブルクリックします。ブラウザーに8枠のメニューが開きます。
3. ゲームを選択します。Webゲームはメニュー内、Pythonのデスクトップゲームは別ウィンドウで動きます。
4. Webゲームの「← ゲーム一覧」でゲームを停止して戻ります。Pythonゲームはゲームのウィンドウを閉じるか、カードの「停止する」で終了します。
5. 終了はメニュー右上の「終了」を押します。起動したサーバーとゲームのプロセスも停止します。

**ブラウザーのタブを閉じるだけではランチャーは終了しません。** メニューの「終了」、または起動したターミナルで `Ctrl+C` を使ってください。

このフォルダには `.venv` を作成済みです。他のPCにクローンした際には `setup.bat` で作り直してください。
Pythonサンプルはブラウザー内で動きます。元のTkinter版も `games/samples/reaction-lab/main.py` に残しています。元の版を使う場合とテストには Tcl/Tk が必要です。

## 現在のゲーム一覧

- **ゲーム1：こうせんサバイバー**: メンバーのWebゲーム。単位を集めながら留年・壁・自分の体をよけます。矢印キー / WASDで移動、スペース / Enterで開始します。
- **ゲーム2：ふうせんハンター**: メンバーのWebゲーム（3hu）。30秒間で風船をクリック / タップして得点を集めます。小さい風船は3点、中くらいは2点、大きい風船は1点。スタートボタン / Enterで開始します。
- **ゲーム3：保留**: 釣りゲームの本体を作者に確認中です。
- **ゲーム4：リアルタイムチェス**: Python + Webのゲーム（chess）。メニュー内で遊べます。スタート後、白の駒と移動先をクリックしてAIと対戦します。ターン制ではなくクールタイムがあります。AI同士の観戦、AIの強さ変更、Q / Escで対局停止、リセットにも対応します。原作：k4m4b0k02009、Web対応：yamamoto。
- **ゲーム5〜8**: 未登録です。メンバーのゲームを順に追加できます。

NEON DODGEとREACTION LABはゲーム一覧から外しています。実装例のコードは `games/samples/` にあります。

## コード理解から発表までの学習コース

メニューの「学習コース」から、50分×4回を目安に学習できます。
高専1・2年生の初学者を基本に、Pythonを使う3年生向けの補足もあります。

1. AIへプロンプトを渡し、動作を保ってコードの整理と説明コメントを追加。
2. 自分のゲームのコードに対応した学習資料を作り、重要な処理を読む。
3. 本人が理解確認に答え、1項目の変更を予測・実行・比較。
4. 本人の記録から、ゲーム説明と3ページの発表資料を作る。

各ゲームのカードから「紹介・技術」「発表3ページ」を開けます。
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

### 1. GitHubからクローン

PowerShellでこのフォルダに移動し、各メンバーのURLに置き換えて実行します。

```powershell
git clone https://github.com/MEMBER/GAME-REPO.git games/local/member-game
```

`games/local/` 内のクローンは、このリポジトリのGit管理から除外しています。
各ゲームは独立したリポジトリとして、必要に応じて `git -C games/local/member-game pull` で更新できます。
各ゲームの依存パッケージ、アセット、起動方法はそのゲームのREADMEに従って準備してください。
このランチャーのリポジトリをクローンしただけでは、メンバーのゲームは付属しません。

GitHub Actionsではユニットテスト、`games.json` の形式・パス・資料の検証、同梱サンプルの起動設定確認を行います。別管理のメンバー作品の動作確認は、各リポジトリをクローンしたPCで行います。CI用のサンプル登録は `.github/sample-games.json` に分け、通常のゲーム一覧には表示しません。

現在登録済みの「こうせんサバイバー」は、別のPCでは次のコマンドで用意します（このランチャーのフォルダ内で実行）。すでにクローン済みなら再実行は不要です。

```powershell
git clone https://github.com/gkykw5cyzc-alt/2026-4Pro-ishida.git games/local/2026-4Pro-ishida
```

このゲームはHTML / CSS / JavaScriptで動き、追加パッケージやビルドは不要です。

ゲーム2の「ふうせんハンター」も、別のPCでは次のコマンドで用意します。クローン済みなら再実行は不要です。追加パッケージやビルドは不要で、`index.html` だけで動きます。

```powershell
git clone https://github.com/hi-1505/3hu.git games/local/3hu
```

ゲーム3の「ゆうぐれ釣り日和」は、別のPCでは次のコマンドで用意します。クローン済みなら `git -C games/local/2026_4Pro_fishinggame pull --ff-only` で更新してください。

```powershell
git clone https://github.com/yuu-rgb000/2026_4Pro_fishinggame.git games/local/2026_4Pro_fishinggame
```

HTML / CSS / JavaScriptで動くため、追加パッケージやビルドは不要です。`index.html` が釣りゲームの起動ファイルです。同じリポジトリの `rooftop-run.html` は別のゲームで、今回のゲーム3には登録していません。

60秒以内に魚を釣り、匹数と得点を伸ばします。Spaceまたは「投げる」で仕掛けを投げ、HITが表示されたらEnterまたは「合わせる」を押します。魚ごとに得点と合わせる猶予が異なります。終了後は「もう一度遊ぶ」で再挑戦できます。ゲーム一覧から起動すると、ブラウザー内のゲーム画面で遊べます。

ゲーム4の「リアルタイムチェス」は次のコマンドで用意します。クローン済みなら再実行は不要です。

```powershell
git clone --branch yamamoto/web-chess https://github.com/k4m4b0k02009/chess.git games/local/chess
```

Web対応はGitHubの `yamamoto/web-chess` ブランチで共有しています。別のPCでは上のコマンドでWeb版を取得できます。元のPython版は `main` に残しています。変更内容は[チェスのWeb対応Pull Request](https://github.com/k4m4b0k02009/chess/pull/1)で確認できます。

ランチャーの `.venv` のPythonで `web.py` を起動し、ブラウザー内に表示します。追加パッケージ・ビルド・TkinterはWeb版には不要です。元のPython / Tkinter版は残してあり、`chess.py` または `python -m chess` で起動できます。両方の版で作者のルール・AIを共通利用します。詳細は `games/local/chess/README.md` を参照してください。

ゲーム5の「デス・モグラたたき」（`tesuto`）は、Python + Web版で画面内に表示します。問題・得点・時間はPythonで管理し、回答や設定の画面はHTML / CSS / JavaScriptで表示します。ランチャーの `.venv` を使います。問題をExcelから読み込むため `openpyxl` が必要です。PygameはWeb版には不要です。tesutoのクローン後に `setup.bat` を実行するとExcel読込用パッケージをインストールします。

Web版のファイルは `tesuto` リポジトリの `yamamoto/web-mole` ブランチにあります。GitHubで共有しています。別のPCでは次のコマンドで取得できます。

```powershell
git clone --branch yamamoto/web-mole https://github.com/painaplle/tesuto.git games/local/tesuto
```

クローン済みの場合は、そのリポジトリで `git fetch origin` と `git switch --track origin/yamamoto/web-mole` を実行します（ローカルに同名ブランチがある場合は `git switch yamamoto/web-mole`）。

正解のモグラをクリック・タップして回答します。1〜9 / 0で分野を選択、Spaceで開始、Sで設定、Rでランキング、Escでメニューに戻ります。設定画面のEscは保存して戻ります。時間・ライフ・色・文字スタイルを変更でき、分野別のランキングも表示できます。

Web版は初回に元の設定・記録を読み、`games/local/tesuto/.web-data/` にWeb専用のコピーを保存します。以後の更新・記録消去は元の `mole_settings.json` / `mole_rankings.json` に影響しません。Pygame版も起動でき、このブランチではWeb版と同じExcelから出題します。元の作品はtesutoの `main` ブランチに残っています。元の版に必要なPython 3.12用の仮想環境 `.game-venvs/tesuto/` と `requirements/tesuto.txt` も残しています。Web版の構成と起動方法は `games/local/tesuto/README.md` を参照してください。

モグラたたきの問題は `games/local/tesuto/data/questions.xlsx` で管理します。「問題一覧」に問題文・正解・不正解・有効／無効を入力し、「分野設定」で分野名やLv.1の自動計算の範囲を変更できます。保存後、次のゲーム開始時に読み直します。編集手順はtesutoのREADMEに記載しています。ゲームはExcelを読み取るだけで、設定・ランキングはJSONへ保存します。

### 2. `games.json` の枠を書き換える

`games` 配列は1〜8枠。`id` は重複しない半角英数字とハイフン、`path` はランチャーのフォルダからの相対パスです。
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
`.venv`、`.logs`、メンバーのクローンはGit管理対象外です。GitHubへのpushは別途行ってください。

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
├── games.json                # 最大8枠の設定
├── launcher/                 # 共通メニューのHTML / CSS / JS
├── games/
│   ├── samples/              # Web / Pythonサンプル
│   └── local/                # メンバーのゲームをクローン（Git対象外）
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
