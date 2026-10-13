"""Fetch the five member games and prepare all six games on a new PC."""
from __future__ import annotations

import argparse
import importlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from arcade import GameManager, inside, load_games

ROOT = Path(__file__).resolve().parent


def load_sources(root: Path):
    games = load_games(root, root / "games.json")
    registered = {game["id"]: game for game in games if game.get("enabled", True)}
    data = json.loads((root / "game-sources.json").read_text(encoding="utf-8-sig"))
    sources = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(sources, list):
        raise ValueError("game-sources.json の sources は配列にしてください。")
    seen = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("ゲーム取得先の形式が不正です。")
        gid = source.get("game_id")
        if not isinstance(gid, str) or gid not in registered or gid in seen:
            raise ValueError("ゲーム取得先のIDが未登録または重複しています。")
        seen.add(gid)
        repository, branch, revision = (source.get(key) for key in ("repository", "branch", "revision"))
        if not isinstance(repository, str) or not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git", repository):
            raise ValueError(f"{gid}: 取得先にはGitHubのHTTPS URLを指定してください。")
        if not isinstance(branch, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", branch):
            raise ValueError(f"{gid}: ブランチ名が不正です。")
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError(f"{gid}: 確認済みのコミットSHAを指定してください。")
        folder = inside(root, registered[gid]["path"])
        local = (root / "games/local").resolve()
        if folder == local or not folder.is_relative_to(local):
            raise ValueError(f"{gid}: 自動取得先は games/local/ 内にしてください。")
        required = source.get("required_files")
        if not isinstance(required, list) or not required or not all(isinstance(name, str) and name for name in required):
            raise ValueError(f"{gid}: 必須ファイルの一覧が必要です。")
        for name in required:
            inside(folder, name)
    expected = {gid for gid, game in registered.items()
                if inside(root, game["path"]).is_relative_to((root / "games/local").resolve())}
    if seen != expected:
        raise ValueError("games/local/ の登録ゲームすべてに取得先を設定してください。")
    return registered, sources


def missing_files(folder: Path, source: dict):
    return [name for name in source["required_files"] if not inside(folder, name).is_file()]


def run(command, root):
    # Authentication must be prepared by the player; do not hang on a hidden prompt.
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
    subprocess.run(command, cwd=root, env=env, check=True, timeout=300)


def prepare_game(root: Path, game: dict, source: dict, check=False):
    folder = inside(root, game["path"])
    if folder.exists():
        missing = missing_files(folder, source)
        if missing:
            raise ValueError(f"{game['title']}: 既存フォルダに {', '.join(missing)} がありません。"
                             f"既存の内容は変更しません。READMEのWeb版取得手順を確認してください。\n  {folder}")
        print(f"[OK] {game['title']}: 取得済み（既存の変更・記録を保持）", flush=True)
        return
    if check:
        raise ValueError(f"{game['title']}: 未取得です。setup.bat を実行してください。")
    git = shutil.which("git")
    if not git:
        raise ValueError("Gitが見つかりません。Git for Windowsをインストールし、setup.batを再実行してください。")
    folder.parent.mkdir(parents=True, exist_ok=True)
    print(f"[GET] {game['title']}: {source['branch']}", flush=True)
    # Clone in a temporary sibling first. A failed download never leaves a half-ready game.
    with tempfile.TemporaryDirectory(prefix=".arcade-download-", dir=folder.parent) as temporary:
        checkout = Path(temporary) / "game"
        try:
            run([git, "clone", "--single-branch", "--branch", source["branch"],
                 "--no-checkout", "--", source["repository"], str(checkout)], root)
            run([git, "-C", str(checkout), "checkout", "--detach", source["revision"]], root)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ValueError(f"{game['title']}を取得できませんでした。ネット接続・GitHubへのログイン・"
                             f"このリポジトリの閲覧権限を確認してください。\n  {source['repository']}\n"
                             "再度setup.batを実行すると、取得済みの作品を残して再試行できます。") from exc
        missing = missing_files(checkout, source)
        if missing:
            raise ValueError(f"{game['title']}: 取得したWeb版に必要なファイルがありません: {', '.join(missing)}")
        if folder.exists():
            raise ValueError(f"取得中に {folder} が作られました。既存フォルダを保持して停止します。")
        checkout.rename(folder)
    print(f"[OK] {game['title']}: 取得完了", flush=True)


def ensure_dependencies(root: Path, check=False):
    try:
        installed = version("openpyxl") == "3.1.5"
        if installed:
            importlib.import_module("openpyxl")
    except (PackageNotFoundError, ImportError):
        installed = False
    if installed:
        print("[OK] Excel問題の読込パッケージ: 準備済み", flush=True)
        return
    if check:
        raise ValueError("Excel問題の読込パッケージが未準備です。setup.bat を実行してください。")
    print("[INSTALL] Excel問題の読込パッケージ", flush=True)
    try:
        run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
             "-r", str(root / "requirements/arcade-web.txt")], root)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError("パッケージをインストールできませんでした。ネット接続を確認してsetup.batを再実行してください。") from exc


def prepare(root: Path, check=False):
    registered, sources = load_sources(root)
    for source in sources:
        prepare_game(root, registered[source["game_id"]], source, check=check)
    ensure_dependencies(root, check=check)
    manager = GameManager(root, list(registered.values()))
    try:
        items = manager.list_games()
        errors = [f"{item['title']}: {item['message']}" for item in items if item["status"] != "ready"]
        if errors:
            raise ValueError("\n".join(errors))
    finally:
        manager.close()
    print(f"\n準備完了: {len(items)} / {len(items)} ゲーム。start.batをダブルクリックして遊べます。", flush=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="4Pro Arcadeの全ゲームを自動取得・セットアップ")
    parser.add_argument("--check", action="store_true", help="ネット取得やインストールをせず準備状況を確認")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        print("Python 3.11以上をインストールしてください。", file=sys.stderr)
        return 1
    try:
        prepare(ROOT, check=args.check)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"\nセットアップ未完了: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
