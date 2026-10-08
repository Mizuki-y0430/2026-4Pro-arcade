"""Python game rules + a browser UI, served locally using the standard library."""
import argparse
import json
import math
import mimetypes
from pathlib import Path
import random
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent / "web"


class ReactionRound:
    def __init__(self, clock=time.monotonic, delay=lambda: random.randint(1500, 4200)):
        self.clock = clock
        self.delay = delay
        self.round_id = None
        self.ready_at = 0
        self.best = None
        self.attempts = 0

    def start(self):
        delay_ms = self.delay()
        self.round_id = secrets.token_hex(16)
        self.ready_at = self.clock() + delay_ms / 1000
        return {"round_id": self.round_id, "delay_ms": delay_ms}

    def finish(self, data):
        if not self.round_id or data.get("round_id") != self.round_id:
            raise ValueError("このラウンドは終了しています。もう一度スタートしてください。")
        early = data.get("early", False)
        if type(early) is not bool:
            raise ValueError("earlyはtrueかfalseにしてください。")
        if early or self.clock() < self.ready_at:
            self.round_id = None
            return {"result": "early", "best_ms": self.best, "attempts": self.attempts}
        elapsed = data.get("elapsed_ms")
        if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or not 0 <= elapsed <= 60000:
            raise ValueError("反応時間が不正です。")
        # Time from the browser's actual green paint to input excludes HTTP latency.
        elapsed = round(elapsed)
        self.best = elapsed if self.best is None else min(self.best, elapsed)
        self.attempts += 1
        self.round_id = None
        return {"result": "success", "elapsed_ms": elapsed, "best_ms": self.best, "attempts": self.attempts}


class ReactionHandler(BaseHTTPRequestHandler):
    def valid_host(self):
        return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

    def json_response(self, data, status=200):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if not self.valid_host():
            self.send_error(403)
            return
        path = urlsplit(self.path).path
        if path == "/api/session":
            with self.server.lock:
                now = time.monotonic()
                self.server.sessions = {token: pair for token, pair in self.server.sessions.items() if now - pair[1] < 3600}
                if len(self.server.sessions) >= 128:
                    self.json_response({"error": "ゲーム画面を開きすぎています。ゲームを再起動してください。"}, 429)
                    return
                token = secrets.token_hex(32)
                self.server.sessions[token] = (ReactionRound(), now)
            self.json_response({"token": token})
            return
        assets = {"/": "index.html", "/style.css": "style.css", "/game.js": "game.js"}
        if path not in assets:
            self.send_error(404)
            return
        file = ROOT / assets[path]
        content = file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", (mimetypes.guess_type(file.name)[0] or "text/plain") + "; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        origin = f"http://127.0.0.1:{self.server.server_port}"
        if not self.valid_host() or self.headers.get("Origin") != origin:
            self.json_response({"error": "ゲーム画面から操作してください。"}, 403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= 4096:
                raise ValueError("リクエストが大きすぎます。")
            data = json.loads(self.rfile.read(length)) if length else {}
            if not isinstance(data, dict):
                raise ValueError("ゲーム操作の形式が不正です。")
            with self.server.lock:
                session = self.server.sessions.get(self.headers.get("X-Reaction-Token", ""))
                if not session:
                    self.json_response({"error": "ゲーム画面を開き直してください。"}, 403)
                    return
                path = urlsplit(self.path).path
                if path == "/api/start":
                    result = session[0].start()
                elif path == "/api/finish":
                    result = session[0].finish(data)
                else:
                    self.json_response({"error": "操作が見つかりません。"}, 404)
                    return
            self.json_response(result)
        except (ValueError, UnicodeDecodeError) as exc:
            self.json_response({"error": str(exc)}, 400)

    def log_message(self, *_args):
        pass


def make_server(port=0):
    server = ThreadingHTTPServer(("127.0.0.1", port), ReactionHandler)
    server.daemon_threads = True
    server.sessions = {}
    server.lock = threading.Lock()
    return server


def main():
    parser = argparse.ArgumentParser(description="REACTION LAB Python + Web sample")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    server = make_server(args.port)
    print(f"REACTION LAB: http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
