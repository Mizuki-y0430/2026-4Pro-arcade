import importlib.util
import json
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener


spec = importlib.util.spec_from_file_location(
    "reaction_web", Path(__file__).resolve().parents[1] / "games/samples/reaction-lab/web.py"
)
sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sample)


class ReactionWebRulesTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.game = sample.ReactionRound(clock=lambda: self.now, delay=lambda: 1500)

    def test_early_input_does_not_record_score(self):
        round_data = self.game.start()
        result = self.game.finish({"round_id": round_data["round_id"], "elapsed_ms": 0})
        self.assertEqual(result["result"], "early")
        self.assertIsNone(result["best_ms"])
        self.assertEqual(result["attempts"], 0)

    def test_browser_early_flag_handles_delayed_rendering(self):
        round_data = self.game.start()
        self.now += 2
        result = self.game.finish({"round_id": round_data["round_id"], "early": True})
        self.assertEqual(result["result"], "early")

    def test_success_best_score_and_round_cannot_be_reused(self):
        for elapsed in [300.4, 180.2, 250.1]:
            round_data = self.game.start()
            self.now += 2
            data = {"round_id": round_data["round_id"], "elapsed_ms": elapsed}
            result = self.game.finish(data)
            self.assertEqual(result["result"], "success")
            with self.assertRaises(ValueError):
                self.game.finish(data)
        self.assertEqual(result["best_ms"], 180)
        self.assertEqual(result["attempts"], 3)

    def test_invalid_scores_rejected(self):
        round_data = self.game.start()
        self.now += 2
        for elapsed in [None, True, -1, 60001, float("nan"), float("inf"), "100"]:
            with self.subTest(elapsed=elapsed), self.assertRaises(ValueError):
                self.game.finish({"round_id": round_data["round_id"], "elapsed_ms": elapsed})

    def test_restarting_invalidates_previous_round(self):
        first = self.game.start()
        second = self.game.start()
        self.assertNotEqual(first["round_id"], second["round_id"])
        self.now += 2
        with self.assertRaises(ValueError):
            self.game.finish({"round_id": first["round_id"], "elapsed_ms": 123})


class ReactionWebHTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = sample.make_server()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.opener = build_opener(ProxyHandler({}))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)

    def request(self, path, method="GET", data=None, headers=None):
        request = Request(self.base + path, method=method, data=json.dumps(data).encode() if data is not None else None, headers=headers or {})
        with self.opener.open(request, timeout=3) as response:
            return response.read()

    def test_web_assets_and_session_api(self):
        self.assertIn(b"REACTION LAB", self.request("/"))
        self.assertIn(b"/api/start", self.request("/game.js"))
        token = json.loads(self.request("/api/session"))["token"]
        headers = {"Origin": self.base, "X-Reaction-Token": token}
        round_data = json.loads(self.request("/api/start", "POST", {}, headers))
        result = json.loads(self.request("/api/finish", "POST", {"round_id": round_data["round_id"], "early": True}, headers))
        self.assertEqual(result["result"], "early")

    def test_cross_origin_mutation_and_source_access_rejected(self):
        token = json.loads(self.request("/api/session"))["token"]
        with self.assertRaises(HTTPError) as error:
            self.request("/api/start", "POST", {}, {"Origin": "http://other.invalid", "X-Reaction-Token": token})
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            self.request("/../web.py")
        self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
