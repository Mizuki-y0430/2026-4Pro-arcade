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

## 最初に入っているサンプル

- **NEON DODGE**: Webゲーム。← → / A Dで光のブロックをよけて30秒生き残る。
- **REACTION LAB**: Python + Webゲーム。緑になったらクリック / スペースで反応速度を測る。Pythonが待ち時間・フライング判定・ベスト記録を管理し、ブラウザーが描画と入力を担当します。反応時間は通信の待ち時間が混ざらないようにブラウザーで測定します。
- 残り6枠は未登録です。2つのサンプルも差し替えて、メンバーのゲーム8個にできます。

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

REACTION LABは追加パッケージなしで起動します。現在の `games.json` では `web.py` を起動し、メニュー内でプレイします。
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

開発ブランチ: `codex/arcade-launcher`。初期状態のGitHubリポジトリは空でした。
このブランチにランチャー本体、サンプル、設定、テストをコミットします。
`.venv`、`.logs`、メンバーのクローンはGit管理対象外です。GitHubへのpushは別途行ってください。

```powershell
git status
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git push -u origin codex/arcade-launcher
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
