import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

from arcade import GameManager, inside, load_games, make_server


class ArcadeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / "game"
        self.folder.mkdir()
        (self.folder / "index.html").write_text("<h1>TEST GAME</h1>", encoding="utf-8")
        (self.folder / ".env").write_text("SECRET", encoding="utf-8")
        (self.root / "private.txt").write_text("PRIVATE", encoding="utf-8")
        self.game = {"id": "test", "title": "テスト", "kind": "static", "path": "game"}
        self.manager = GameManager(self.root, [self.game])
        self.opener = build_opener(ProxyHandler({}))
        self.server = None

    def tearDown(self):
        self.manager.close()
        if self.server:
            self.server.shutdown()
            self.server.manager.close()
            self.server.server_close()
            self.server_thread.join(2)
        self.temp.cleanup()

    def configure(self, games):
        config = self.root / "games.json"
        config.write_text(json.dumps({"games": games}), encoding="utf-8")
        return load_games(self.root, config)

    def read(self, url, **kwargs):
        with self.opener.open(Request(url, **kwargs), timeout=3) as response:
            return response.read()

    def assert_http(self, status, url, **kwargs):
        with self.assertRaises(HTTPError) as error:
            self.read(url, **kwargs)
        self.assertEqual(error.exception.code, status)

    def api_server(self):
        self.server = make_server(self.root, [self.game])
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        return f"http://127.0.0.1:{self.server.server_port}"

    def python_manager(self, source, kind="python", **extra):
        (self.folder / "main.py").write_text(source, encoding="utf-8")
        self.manager.close()
        self.game.update(kind=kind, **extra)
        self.manager = GameManager(self.root, [self.game])

    def wait_for(self, status, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            item = self.manager.list_games()[0]
            if item["status"] == status:
                return item
            time.sleep(.05)
        self.fail(f"Expected {status}, got {item}")

    def test_eight_slots_and_disabled_placeholder(self):
        self.assertEqual(len(self.configure([self.game, *[{"id": f"slot-{i}", "title": "Empty", "enabled": False} for i in range(7)]])), 8)
        with self.assertRaises(ValueError):
            self.configure([{"id": f"slot-{i}", "title": "Empty", "enabled": False} for i in range(9)])

    def test_duplicates_and_unknown_kind_are_rejected(self):
        with self.assertRaises(ValueError):
            self.configure([self.game, self.game])
        with self.assertRaises(ValueError):
            self.configure([{**self.game, "kind": "shell"}])

    def test_escape_paths_are_rejected(self):
        for change in [{"path": "../other"}, {"entry": "../private.txt"}, {"python": "../python.exe"}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.configure([{**self.game, **change}])

    def test_missing_game_reported_without_starting(self):
        (self.folder / "index.html").unlink()
        self.assertEqual(self.manager.list_games()[0]["status"], "missing")
        with self.assertRaises(ValueError):
            self.manager.start("test")

    def test_static_start_is_idempotent_and_stop_releases_port(self):
        item = self.manager.start("test")
        self.assertEqual(self.read(item["url"]), b"<h1>TEST GAME</h1>")
        self.assertEqual(self.manager.start("test")["url"], item["url"])
        self.assertEqual(self.manager.stop("test")["status"], "ready")
        with self.assertRaises(OSError):
            self.read(item["url"])

    def test_static_private_files_traversal_and_directory_listing_blocked(self):
        url = self.manager.start("test")["url"]
        (self.folder / "nested").mkdir()
        for path in [".env", "../private.txt", "%2e%2e/private.txt", "nested/", ".git/config"]:
            with self.subTest(path=path):
                self.assert_http(404, url + path)

    def test_python_uses_game_cwd_and_captures_exit(self):
        self.python_manager("from pathlib import Path\nprint(Path.cwd().name, flush=True)\n")
        self.manager.start("test")
        self.wait_for("ready")
        self.assertEqual((self.root / ".logs/test.log").read_text().strip(), "game")

    def test_python_errors_are_reported_with_log_and_retry(self):
        self.python_manager("raise RuntimeError('game failed')\n")
        self.manager.start("test")
        item = self.wait_for("error")
        self.assertEqual(item["log"], ".logs/test.log")
        self.assertIn("game failed", (self.root / item["log"]).read_text())
        (self.folder / "main.py").write_text("print('retry successful')\n", encoding="utf-8")
        self.manager.start("test")
        self.wait_for("ready")

    def test_python_stop_terminates_process(self):
        self.python_manager("import time\ntime.sleep(60)\n")
        self.manager.start("test")
        process = self.manager.runtime["test"]["process"]
        self.manager.stop("test")
        self.assertIsNotNone(process.poll())

    @unittest.skipUnless(sys.platform == "win32", "Windows process-tree check")
    def test_windows_stop_also_terminates_child(self):
        self.python_manager("import subprocess, sys, time\nfrom pathlib import Path\np = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\nPath('child.pid').write_text(str(p.pid))\ntime.sleep(60)\n")
        self.manager.start("test")
        deadline = time.monotonic() + 5
        while not (self.folder / "child.pid").exists():
            self.assertLess(time.monotonic(), deadline)
            time.sleep(.05)
        pid = (self.folder / "child.pid").read_text()
        self.manager.stop("test")
        result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True)
        self.assertNotIn(f'"{pid}"', result.stdout)

    def test_service_waits_until_http_ready_and_stops(self):
        self.python_manager("", kind="service", command=["{python}", "-m", "http.server", "{port}", "--bind", "127.0.0.1"])
        self.assertEqual(self.manager.start("test")["status"], "starting")
        item = self.wait_for("running")
        self.assertIn(b"TEST GAME", self.read(item["url"]))
        process = self.manager.runtime["test"]["process"]
        self.manager.close()
        self.assertIsNotNone(process.poll())

    def test_service_timeout_kills_process_and_reports_error(self):
        self.python_manager("import time\ntime.sleep(60)\n", kind="service", command=["{python}", "main.py"], startup_timeout=1)
        self.manager.start("test")
        process = self.manager.runtime["test"]["process"]
        self.assertIn("タイムアウト", self.wait_for("error")["message"])
        self.assertIsNotNone(process.poll())

    def test_api_requires_origin_and_token_for_launch(self):
        base = self.api_server()
        data = json.loads(self.read(base + "/api/games"))
        self.assert_http(403, base + "/api/games/test/start", method="POST")
        self.assert_http(403, base + "/api/games/test/start", method="POST", headers={"Origin": "http://evil.invalid", "X-Arcade-Token": data["token"]})
        result = json.loads(self.read(base + "/api/games/test/start", method="POST", headers={"Origin": base, "X-Arcade-Token": data["token"]}))
        self.assertEqual(result["status"], "running")

    def test_api_rejects_wrong_host_and_unlisted_files(self):
        base = self.api_server()
        self.assert_http(403, base + "/api/games", headers={"Host": "evil.invalid"})
        self.assert_http(404, base + "/games.json")
        self.assert_http(404, base + "/.git/config")

    def test_config_rejects_invalid_command_and_remote_url(self):
        for changes in [{"command": "python main.py"}, {"command": [sys.executable], "url_path": "//evil.invalid"}, {"command": [sys.executable], "port": -1}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.configure([{**self.game, "kind": "service", **changes}])

    def test_closed_manager_cannot_launch(self):
        self.manager.close()
        with self.assertRaises(ValueError):
            self.manager.start("test")


if __name__ == "__main__":
    unittest.main()
