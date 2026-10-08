"""Local PC launcher. Python 3.11+, standard library only."""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import ProxyHandler, build_opener
import webbrowser

ROOT = Path(__file__).resolve().parent
KINDS = {"static", "python", "service"}


def inside(root: Path, value: str) -> Path:
    """Resolve paths, including symlinks, and disallow escaping the given root."""
    result = (root / value).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f"フォルダ外のパスは指定できません: {value}")
    return result


def load_games(root: Path, config: Path) -> list[dict]:
    data = json.loads(config.read_text(encoding="utf-8-sig"))
    games = data.get("games") if isinstance(data, dict) else None
    if not isinstance(games, list) or not 1 <= len(games) <= 8:
        raise ValueError("gamesには1〜8個のゲームを設定してください。")
    seen = set()
    for game in games:
        if not isinstance(game, dict):
            raise ValueError("ゲーム設定はオブジェクトにしてください。")
        gid = game.get("id", "")
        if not isinstance(gid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", gid) or gid in seen:
            raise ValueError("idは重複しない半角英数字とハイフンにしてください。")
        seen.add(gid)
        if not isinstance(game.get("title"), str) or not game["title"].strip():
            raise ValueError(f"{gid}: titleが必要です。")
        if not isinstance(game.get("enabled", True), bool):
            raise ValueError(f"{gid}: enabledはtrueかfalseにしてください。")
        if not game.get("enabled", True):
            continue
        kind = game.get("kind")
        if kind not in KINDS:
            raise ValueError(f"{gid}: kindはstatic / python / serviceから選択してください。")
        path = game.get("path")
        if not isinstance(path, str) or not path:
            raise ValueError(f"{gid}: pathが必要です。")
        folder = inside(root, path)
        if kind in {"static", "python"}:
            entry = game.get("entry", "index.html" if kind == "static" else "main.py")
            if not isinstance(entry, str) or not entry:
                raise ValueError(f"{gid}: entryを文字列で指定してください。")
            inside(folder, entry)
        if kind == "python" and (not isinstance(game.get("args", []), list) or
                                 not all(isinstance(arg, str) for arg in game.get("args", []))):
            raise ValueError(f"{gid}: argsは文字列の配列にしてください。")
        if kind == "service":
            command = game.get("command")
            if not isinstance(command, list) or not command or not all(isinstance(arg, str) for arg in command):
                raise ValueError(f"{gid}: commandは空でない文字列の配列にしてください。")
            web_path = game.get("url_path", "/")
            if not isinstance(web_path, str) or not web_path.startswith("/") or web_path.startswith("//"):
                raise ValueError(f"{gid}: url_pathは/から始まるパスにしてください。")
            port = game.get("port", 0)
            if type(port) is not int or not 0 <= port <= 65535:
                raise ValueError(f"{gid}: portは0〜65535の整数にしてください。")
            timeout = game.get("startup_timeout", 30)
            if not isinstance(timeout, (int, float)) or not 1 <= timeout <= 300:
                raise ValueError(f"{gid}: startup_timeoutは1〜300秒にしてください。")
        if "python" in game:
            if not isinstance(game["python"], str):
                raise ValueError(f"{gid}: pythonは実行ファイルへの相対パスにしてください。")
            inside(root, game["python"])
    return games


class StaticHandler(BaseHTTPRequestHandler):
    """Serve only files inside this game's public folder, without directory listings."""
    def do_GET(self):
        path = unquote(urlsplit(self.path).path).lstrip("/")
        if not path:
            path = self.server.entry
        try:
            if any(part.startswith(".") for part in Path(path).parts):
                raise ValueError("private path")
            file = inside(self.server.root, path)
            if not file.is_file():
                self.send_error(404)
                return
            content = file.read_bytes()
        except (ValueError, OSError):
            self.send_error(404)
            return
        mime = mimetypes.guess_type(str(file))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *_args):
        pass


class GameManager:
    def __init__(self, root: Path, games: list[dict]):
        self.root = root
        self.games = {game["id"]: game for game in games}
        self.runtime: dict[str, dict] = {}
        self.lock = threading.RLock()
        self.closed = False

    def availability(self, game):
        if not game.get("enabled", True):
            return "unregistered", "ゲームを登録すると遊べます"
        folder = inside(self.root, game["path"])
        if not folder.is_dir():
            return "missing", f"ゲームフォルダが見つかりません: {game['path']}"
        if game["kind"] in {"static", "python"}:
            entry = game.get("entry", "index.html" if game["kind"] == "static" else "main.py")
            if not inside(folder, entry).is_file():
                return "missing", f"起動ファイルが見つかりません: {entry}"
        if game["kind"] != "static" and not self.interpreter(game).is_file():
            return "missing", "Python実行ファイルが見つかりません"
        return "ready", "プレイできます"

    def interpreter(self, game):
        return inside(self.root, game["python"]) if game.get("python") else Path(sys.executable)

    def _refresh(self, runtime):
        process = runtime.get("process")
        if process is not None and process.poll() is not None and runtime["status"] in {"starting", "running"}:
            code = process.returncode
            runtime["status"] = "ready" if code == 0 else "error"
            runtime["message"] = "ゲームが終了しました" if code == 0 else f"起動・実行に失敗しました（終了コード {code}）。ログを確認してください。"
            runtime.pop("url", None)
            runtime["log_handle"].close()

    def snapshot(self, gid):
        game = self.games[gid]
        status, message = self.availability(game)
        runtime = self.runtime.get(gid)
        if runtime:
            self._refresh(runtime)
            status, message = runtime["status"], runtime["message"]
        result = {key: game.get(key, "") for key in ("id", "title", "description", "author", "kind", "controls", "color")}
        result.update(status=status, message=message)
        if runtime:
            result.update({key: runtime[key] for key in ("url", "log") if key in runtime})
        return result

    def list_games(self):
        with self.lock:
            return [self.snapshot(gid) for gid in self.games]

    def start(self, gid):
        with self.lock:
            if self.closed:
                raise ValueError("ランチャーは終了しています。")
            game = self.games[gid]
            current = self.snapshot(gid)
            if current["status"] in {"running", "starting"}:
                return current
            state, reason = self.availability(game)
            if state != "ready":
                raise ValueError(reason)
            if gid in self.runtime:
                self.stop(gid)
            folder = inside(self.root, game["path"])
            if game["kind"] == "static":
                server = ThreadingHTTPServer(("127.0.0.1", 0), StaticHandler)
                server.daemon_threads = True
                server.root = folder
                server.entry = game.get("entry", "index.html")
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                self.runtime[gid] = {"server": server, "thread": thread, "status": "running", "message": "プレイ中", "url": f"http://127.0.0.1:{server.server_port}/"}
            else:
                log_dir = self.root / ".logs"
                log_dir.mkdir(exist_ok=True)
                log_path = log_dir / f"{gid}.log"
                log_handle = log_path.open("w", encoding="utf-8")
                env = os.environ.copy()
                env.update(PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
                port = 0
                if game["kind"] == "python":
                    command = [str(self.interpreter(game)), str(inside(folder, game.get("entry", "main.py"))), *game.get("args", [])]
                else:
                    port = game.get("port", 0)
                    with socket.socket() as sock:
                        sock.bind(("127.0.0.1", port))
                        port = sock.getsockname()[1]
                    values = {"python": str(self.interpreter(game)), "port": str(port), "root": str(folder)}
                    command = [self._expand(arg, values) for arg in game["command"]]
                    env["PORT"] = str(port)
                options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
                try:
                    process = subprocess.Popen(command, cwd=folder, env=env, stdin=subprocess.DEVNULL, stdout=log_handle, stderr=subprocess.STDOUT, shell=False, **options)
                except (OSError, ValueError):
                    log_handle.close()
                    raise ValueError("起動コマンドを実行できません。実行ファイルと依存パッケージを確認してください。") from None
                runtime = {"process": process, "log_handle": log_handle, "log": log_path.relative_to(self.root).as_posix(), "status": "running", "message": "別ウィンドウで起動中"}
                self.runtime[gid] = runtime
                if game["kind"] == "service":
                    runtime.update(status="starting", message="ゲームサーバーを起動しています")
                    url = f"http://127.0.0.1:{port}{game.get('url_path', '/')}"
                    threading.Thread(target=self._wait_service, args=(gid, runtime, url, game.get("startup_timeout", 30)), daemon=True).start()
            return self.snapshot(gid)

    @staticmethod
    def _expand(arg, values):
        for key, value in values.items():
            arg = arg.replace("{" + key + "}", value)
        return arg

    def _wait_service(self, gid, runtime, url, timeout):
        opener = build_opener(ProxyHandler({}))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self.lock:
                if self.runtime.get(gid) is not runtime or runtime["status"] != "starting":
                    return
                self._refresh(runtime)
                if runtime["status"] != "starting":
                    return
            try:
                with opener.open(url, timeout=0.5) as response:
                    ready = response.status < 400
                if ready:
                    with self.lock:
                        if self.runtime.get(gid) is runtime and runtime["status"] == "starting":
                            runtime.update(status="running", message="プレイ中", url=url)
                    return
            except (HTTPError, URLError, OSError, TimeoutError):
                pass
            time.sleep(0.2)
        with self.lock:
            if self.runtime.get(gid) is runtime and runtime["status"] == "starting":
                self.stop(gid)
                self.runtime[gid] = {"status": "error", "message": "起動がタイムアウトしました。ポート・起動コマンド・ログを確認してください。", "log": runtime["log"]}

    def stop(self, gid):
        with self.lock:
            runtime = self.runtime.pop(gid, None)
            if runtime:
                if server := runtime.get("server"):
                    server.shutdown()
                    server.server_close()
                    runtime["thread"].join(timeout=2)
                if process := runtime.get("process"):
                    if process.poll() is None:
                        if os.name == "nt":
                            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
                        else:
                            import signal
                            os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)
                    runtime["log_handle"].close()
            return self.snapshot(gid)

    def close(self):
        with self.lock:
            self.closed = True
            for gid in list(self.runtime):
                self.stop(gid)


class LauncherHandler(BaseHTTPRequestHandler):
    def valid_host(self):
        return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

    def json_response(self, data, status=200):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if not self.valid_host():
            self.send_error(403)
            return
        path = urlsplit(self.path).path
        if path == "/api/games":
            self.json_response({"games": self.server.manager.list_games(), "token": self.server.token})
            return
        allowed = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}
        if path not in allowed:
            self.send_error(404)
            return
        file = self.server.root / "launcher" / allowed[path]
        content = file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", (mimetypes.guess_type(file.name)[0] or "text/plain") + "; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        origin = f"http://127.0.0.1:{self.server.server_port}"
        token = self.headers.get("X-Arcade-Token", "")
        if not self.valid_host() or self.headers.get("Origin") != origin or not secrets.compare_digest(token, self.server.token):
            self.json_response({"error": "ランチャー画面から操作してください。"}, 403)
            return
        path = urlsplit(self.path).path
        if path == "/api/shutdown":
            self.json_response({"ok": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        match = re.fullmatch(r"/api/games/([a-z0-9-]+)/(start|stop)", path)
        if not match or match[1] not in self.server.manager.games:
            self.json_response({"error": "ゲームが見つかりません。"}, 404)
            return
        try:
            action = self.server.manager.start if match[2] == "start" else self.server.manager.stop
            self.json_response(action(match[1]))
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            self.json_response({"error": str(exc)}, 400)

    def log_message(self, *_args):
        pass


def make_server(root: Path, games: list[dict], port=0):
    server = ThreadingHTTPServer(("127.0.0.1", port), LauncherHandler)
    server.daemon_threads = True
    server.root = root
    server.manager = GameManager(root, games)
    server.token = secrets.token_hex(32)
    return server


def main():
    # Windows terminals may otherwise use cp932, which cannot print all UI text.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="4Pro Arcade — PC用ミニゲームランチャー")
    parser.add_argument("--config", type=Path, default=ROOT / "games.json")
    parser.add_argument("--port", type=int, default=0, help="0なら空きポートを自動選択")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--check", action="store_true", help="設定とファイルを確認して終了")
    args = parser.parse_args()
    try:
        games = load_games(ROOT, args.config)
        if args.check:
            manager = GameManager(ROOT, games)
            items = manager.list_games()
            for item in items:
                print(f"{item['id']}: {item['status']} — {item['title']} / {item['message']}")
            return int(any(item["status"] == "missing" for item in items))
        server = make_server(ROOT, games, args.port)
    except (OSError, ValueError) as exc:
        print(f"起動できません: {exc}", file=sys.stderr)
        return 1
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"4Pro Arcade: {url}\n終了: メニューの「終了」、または Ctrl+C", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.manager.close()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
