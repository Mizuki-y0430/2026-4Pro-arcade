"""ローカルPC用のPython + Web版。実行: python web.py --port 8766"""
import argparse
import json
import mimetypes
from pathlib import Path
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from web_game import Store, WebGame

WEB = Path(__file__).resolve().parent / "web"


class Handler(BaseHTTPRequestHandler):
    def json_response(self, data, status=200):
        self.respond(json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def respond(self, content, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # 一覧へ戻ったときに閉じた画面への送信は不要。

    def valid_host(self):
        return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

    def session(self):
        token = self.headers.get("X-Mole-Token", "")
        session = self.server.sessions.get(token)
        if session:
            session["seen"] = time.monotonic()
        return session

    def do_GET(self):
        if not self.valid_host():
            self.send_error(403)
            return
        path = urlsplit(self.path).path
        if path == "/api/session":
            with self.server.lock:
                now = time.monotonic()
                self.server.sessions = {token: session for token, session in self.server.sessions.items() if now-session["seen"] < 3600}
                if len(self.server.sessions) >= 32:
                    self.json_response({"error": "画面を開きすぎています。ゲームを起動し直してください。"}, 429)
                    return
                token = secrets.token_hex(32)
                try:
                    game = WebGame(self.server.store)
                except ValueError as exc:
                    self.json_response({"error": str(exc)}, 400)
                    return
                self.server.sessions[token] = {"game": game, "seen": now}
                self.json_response({"token": token, "state": game.snapshot()})
            return
        if path == "/api/state":
            with self.server.lock:
                session = self.session()
                if not session:
                    self.json_response({"error": "ゲーム画面を開き直してください。"}, 403)
                else:
                    self.json_response(session["game"].snapshot())
            return
        if path == "/api/rankings":
            with self.server.lock:
                if not self.session():
                    self.json_response({"error": "ゲーム画面を開き直してください。"}, 403)
                    return
                try:
                    query = parse_qs(urlsplit(self.path).query)
                    level = int(query.get("level", ["1"])[0])
                    category = query.get("sort", ["score"])[0]
                    self.json_response({"entries": self.server.store.ranking(level, category)})
                except ValueError as exc:
                    self.json_response({"error": str(exc)}, 400)
            return
        assets = {"/": "index.html", "/style.css": "style.css", "/game.js": "game.js"}
        if path not in assets:
            self.send_error(404)
            return
        file = WEB / assets[path]
        self.respond(file.read_bytes(), (mimetypes.guess_type(file.name)[0] or "text/plain") + "; charset=utf-8")

    def do_POST(self):
        origin = f"http://127.0.0.1:{self.server.server_port}"
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= 4096:
                raise ValueError("操作データが大きすぎます。")
            self.connection.settimeout(3)
            raw = self.rfile.read(length)
            # 小さなリクエスト本文を読み終えてから拒否する。Windowsで
            # 未読の本文を残して接続を閉じると、403の応答が届かない場合がある。
            if not self.valid_host() or self.headers.get("Origin") != origin:
                self.json_response({"error": "ゲーム画面から操作してください。"}, 403)
                return
            data = json.loads(raw) if length else {}
            if not isinstance(data, dict):
                raise ValueError("操作データが不正です。")
            path = urlsplit(self.path).path
            with self.server.lock:
                session = self.session()
                if not session:
                    self.json_response({"error": "ゲーム画面を開き直してください。"}, 403)
                    return
                game = session["game"]
                operations = {"/api/start": lambda: game.start(data), "/api/stop": game.stop,
                              "/api/settings": lambda: game.configure(data), "/api/hit": lambda: game.hit(data),
                              "/api/submit": lambda: game.submit(data), "/api/clear": self.server.store.clear}
                if path not in operations:
                    self.json_response({"error": "操作が見つかりません。"}, 404)
                    return
                operations[path]()
                self.json_response(game.snapshot())
        except (ValueError, UnicodeDecodeError, TimeoutError) as exc:
            self.json_response({"error": str(exc)}, 400)
        except OSError:
            self.json_response({"error": "記録を保存できませんでした。保存フォルダを確認して再度操作してください。"}, 500)

    def log_message(self, *_args):
        pass


def make_server(port=0, data_dir=None):
    store = Store(data_dir or WEB.parent/".web-data", WEB.parent)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.store = store
    server.sessions = {}
    server.lock = threading.RLock()
    return server


def main():
    parser = argparse.ArgumentParser(description="Death Mole — Python + Web")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--data-dir", type=Path, help="Web版の保存先（省略時は .web-data）")
    args = parser.parse_args()
    server = make_server(args.port, args.data_dir)
    print(f"Death Mole: http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
