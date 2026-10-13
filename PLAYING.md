# 4Pro Arcadeを別のPCで遊ぶ

メニュー、ルール、技術説明と全6ゲームを使えます。WindowsのPCごとに実行する方式です。公開サイトのURLだけで遊ぶ方式ではありません。

## 初回だけ行うこと

1. **Python 3.11以上**と**Git for Windows**をインストールします。Pythonはインストール時に「Add python.exe to PATH」を有効にしてください。
2. 配布者にGitHubアカウント名を伝え、下の6リポジトリの閲覧権限をもらいます。招待メール／GitHubの通知から招待を承認してください。
3. GitHubへのログインを済ませ、PowerShellで本体を取得します。

   ```powershell
   git clone https://github.com/Mizuki-y0430/2026-4Pro-arcade.git
   cd 2026-4Pro-arcade
   .\setup.bat
   .\start.bat
   ```

`setup.bat` と `start.bat` はエクスプローラーからダブルクリックしても実行できます。`setup.bat` はPythonの仮想環境を作り、別管理の5作品を自動クローンし、モグラたたきのExcel読込パッケージを入れます。将棋とサイトのページ・画像は本体に含まれています。各ゲームを手作業でクローンする必要はありません。

**GitHubの「Code → Download ZIP」で本体を取得して展開しても使えます。** ただし、初回のゲーム自動取得にはGit・GitHubへのログイン・各作品の閲覧権限が必要です。

GitHub CLIを使う場合は、初回に `gh auth login`、続けて `gh auth setup-git` でGitから使うアカウントを設定できます。Git Credential ManagerなどでGitの認証設定が済んでいれば、追加のログインは不要です。セットアップは新しいログイン画面を自動操作しません。

## 閲覧権限が必要なリポジトリ

2026年10月13日時点で、以下はすべて非公開です。それぞれの所有者がプレイヤーを共同編集者などとして招待する必要があります。本体の権限だけでは、別管理の作品を自動取得できません。

| 内容 | 所有者／リポジトリ | 自動取得するブランチ |
| --- | --- | --- |
| 本体・将棋・メニュー・説明 | [Mizuki-y0430/2026-4Pro-arcade](https://github.com/Mizuki-y0430/2026-4Pro-arcade) | `main` |
| こうせんサバイバー | [gkykw5cyzc-alt/2026-4Pro-ishida](https://github.com/gkykw5cyzc-alt/2026-4Pro-ishida) | `main` |
| ふうせんハンター | [hi-1505/3hu](https://github.com/hi-1505/3hu) | `main` |
| ゆうぐれ釣り日和 | [yuu-rgb000/2026_4Pro_fishinggame](https://github.com/yuu-rgb000/2026_4Pro_fishinggame) | `main` |
| リアルタイムチェス | [k4m4b0k02009/chess](https://github.com/k4m4b0k02009/chess) | `yamamoto/web-chess` |
| デス・モグラたたき | [painaplle/tesuto](https://github.com/painaplle/tesuto) | `yamamoto/web-mole` |

## 2回目から

`start.bat` をダブルクリックするだけです。ブラウザーに「6 / 6 あそべる」と表示され、ゲーム、ルール、「？」からの技術説明を使えます。ゲームやパッケージが不足しているときは、自動でセットアップをやり直します。準備済みならネット接続は不要です。

終了はメニューの「終了」を押します。ブラウザーのタブを閉じるだけでは、Pythonサーバーが残ります。

## うまくいかないとき

- **Repository not found / Authentication failed / 取得できません**：GitHubアカウントのログインと、上の各リポジトリの招待承認を確認してください。非公開の作品は、存在していても権限がない人には見えません。
- **Gitが見つかりません**：Git for Windowsをインストール後、新しくPowerShellを開くか、セットアップをダブルクリックし直してください。
- **Pythonが見つかりません**：Python 3.11以上をPATH付きでインストールしてください。古いPythonで作った `.venv` がある場合は、ゲームを終了して `.venv` を別の名前へ変更し、`setup.bat` を再実行してください。
- **既存フォルダにweb.pyなどがありません**：以前取得したデスクトップ版の可能性があります。READMEのWeb版ブランチの取得手順に従ってください。自動セットアップは既存のゲームを上書き・削除しません。
- **途中でネットが切れた／パッケージ導入に失敗**：接続を戻して `setup.bat` を再実行します。取得完了した作品とプレイ記録は保持します。

準備状況だけを確認するには、PowerShellで次を実行します。

```powershell
.\.venv\Scripts\python.exe setup_arcade.py --check
```

## 配布者・開発者向け

取得先は `game-sources.json` にまとめています。初回は確認済みのコミットを取得するため、他のPCでも同じWeb版になります。初回取得した作品はそのコミットに固定されたdetached HEADになります。すでにあるゲームは自動更新しません。プレイ記録や制作途中の編集を保持するためです。

作品の配布版を更新するときは、対象ブランチと新しいコミットSHAを確認して `game-sources.json` を更新します。既存のプレイヤーは記録・編集を保存したうえで対象作品を手動更新してください。開発者がブランチに戻す場合は、対象の `games/local/作品名` 内で `git switch ブランチ名`、続けて `git pull --ff-only` を実行できます。

本体の更新はゲームを終了してから `git pull --ff-only` → `setup.bat` → `start.bat` の順で行います。本体からは各作品の既存の編集内容を自動的に巻き戻しません。
