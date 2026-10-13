# 4Pro Arcadeを別のPCで遊ぶ

全6ゲーム、メニュー、ルール、技術説明をこのリポジトリに同梱しています。GitHubへのログインや、各メンバーの元リポジトリへの招待は不要です。プレイはWindowsのPCでPythonを動かして行います。

## 初回だけ行うこと

1. **Python 3.11以上**をインストールします。「Add python.exe to PATH」を有効にしてください。
2. [4Pro Arcade](https://github.com/Mizuki-y0430/2026-4Pro-arcade) の「Code → Download ZIP」で取得し、ZIPを展開します。
3. 展開したフォルダの `setup.bat` をダブルクリックします。Pythonの仮想環境と、モグラたたきのExcel読込パッケージを準備します。初回のパッケージ取得にはネット接続が必要です。
4. `start.bat` をダブルクリックするとブラウザーにメニューが開きます。

Gitを使える人は、PowerShellで次を実行しても取得できます。

```powershell
git clone https://github.com/Mizuki-y0430/2026-4Pro-arcade.git
cd 2026-4Pro-arcade
.\setup.bat
.\start.bat
```

ゲーム本体はすべて含まれています。元の非公開リポジトリをクローンする必要はありません。ZIPで取得した場合はGit自体も不要です。

## 2回目から

`start.bat` をダブルクリックするだけです。「6 / 6 あそべる」と表示され、ゲーム、ルール、「？」からの技術説明を使えます。準備済みならネット接続は不要です。

終了はメニューの「終了」を押します。ブラウザーのタブを閉じるだけではPythonサーバーが残ります。

## うまくいかないとき

- **Pythonが見つかりません**：Python 3.11以上をPATH付きでインストールしてください。古いPythonで作った `.venv` がある場合は、ゲームを終了して `.venv` を別の名前へ変更し、`setup.bat` を再実行してください。
- **同梱ファイルがありません／web.pyなどがありません**：本体を最新のZIPで再取得し、完全に展開してください。Gitを使う場合は `git pull --ff-only` で更新します。
- **パッケージ導入に失敗**：ネット接続を戻して `setup.bat` を再実行してください。

準備状況だけを確認するには、PowerShellで次を実行します。

```powershell
.\.venv\Scripts\python.exe setup_arcade.py --check
```

## 開発者向け

ゲーム1〜5のソースは `games/local/`、将棋は `games/realtime-shogi/` に含まれます。元の作者・リポジトリ・ブランチ・コミットは `games/local/README.md` と `game-sources.json` に記録しています。元のリポジトリの公開設定はそれぞれの所有者が管理します。

各ゲームは本体リポジトリでまとめて管理します。別リポジトリの `.git`、仮想環境、キャッシュ、プレイ記録、環境変数ファイルは配布対象外です。モグラたたきの新しいプレイヤーは空のランキングから始まります。

本体の更新はゲームを終了してから `git pull --ff-only` → `setup.bat` → `start.bat` の順で行います。ZIPで取得した場合は、新しいZIPを別フォルダに展開してください。
