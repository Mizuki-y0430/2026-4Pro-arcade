import copy
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

from arcade import make_server
from learning_content import learning_file, load_profile, validate_profile

ROOT = Path(__file__).resolve().parents[1]


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "game").mkdir()
        (self.root / "game/game.js").write_text("const speed = 10;\nmove(speed);\n", encoding="utf-8")
        (self.root / "showcase").mkdir()
        self.profile = json.loads((ROOT / "showcase/template.json").read_text(encoding="utf-8"))
        self.profile["code_refs"] = [{"file": "game.js", "start_line": 1, "end_line": 2, "label": "移動", "explanation": "速度を渡す"}]
        self.game = {"id": "test", "title": "Test", "kind": "static", "path": "game", "entry": "game.js", "profile": "showcase/test.json"}
        self.save()
        self.server = None

    def save(self):
        (self.root / "showcase/test.json").write_text(json.dumps(self.profile), encoding="utf-8")

    def tearDown(self):
        if self.server:
            self.server.shutdown()
            self.server.manager.close()
            self.server.server_close()
            self.thread.join(2)
        self.temp.cleanup()

    def http(self):
        shutil.copytree(ROOT / "learning", self.root / "learning")
        shutil.copy(ROOT / "showcase/template.json", self.root / "showcase/template.json")
        shutil.copytree(ROOT / "launcher", self.root / "launcher")
        self.server = make_server(self.root, [self.game])
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.opener = build_opener(ProxyHandler({}))

    def read(self, path):
        with self.opener.open(Request(self.base + path), timeout=3) as response:
            return response.read(), dict(response.headers)

    def test_template_and_samples_validate_with_real_code(self):
        validate_profile(json.loads((ROOT / "showcase/template.json").read_text(encoding="utf-8")))
        # メニューの先頭はメンバー作品。実装例は登録順から独立して検証する。
        for name in ("neon-dodge", "reaction-lab"):
            game = {"id": name, "title": name, "path": f"games/samples/{name}",
                    "profile": f"showcase/{name}.json"}
            result = load_profile(ROOT, game)
            self.assertEqual(len(result["slides"]), 3)
            self.assertEqual(result["status"], "sample")
            self.assertTrue(all(ref["code"] for ref in result["code_refs"]))

    def test_code_excerpts_are_read_from_current_source(self):
        self.assertIn("speed = 10", load_profile(self.root, self.game)["code_refs"][0]["code"])
        (self.root / "game/game.js").write_text("const speed = 20;\nmove(speed);\n", encoding="utf-8")
        self.assertIn("speed = 20", load_profile(self.root, self.game)["code_refs"][0]["code"])

    def test_source_paths_cannot_escape_or_quote_private_files(self):
        for filename in ["../arcade.js", ".env.py"]:
            with self.subTest(filename=filename):
                self.profile["code_refs"][0]["file"] = filename
                self.save()
                with self.assertRaises(ValueError):
                    load_profile(self.root, self.game)
        self.profile["code_refs"] = []
        self.profile["source_root"] = "../outside"
        self.save()
        with self.assertRaises(ValueError):
            load_profile(self.root, self.game)

    def test_code_line_ranges_are_bounded_and_exist(self):
        for end in [0, 31, 3]:
            with self.subTest(end=end):
                self.profile["code_refs"][0]["end_line"] = end
                self.save()
                with self.assertRaises(ValueError):
                    load_profile(self.root, self.game)

    def test_slide_count_and_public_content_types_validated(self):
        invalid_slides = copy.deepcopy(self.profile["slides"])
        invalid_slides[1]["code_ref"] = 99
        changes = [
            {"slides": []}, {"status": "done"}, {"schema_version": True},
            {"slides": invalid_slides},
            {"questions": None}, {"sources": [{"label": "bad", "url": "javascript:alert(1)"}]},
            {"screenshot": "/.git/config"}
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_profile({**copy.deepcopy(self.profile), **change})

    def test_unregistered_slot_shows_draft_without_invented_evidence(self):
        result = load_profile(self.root, {"id": "empty", "title": "Empty", "enabled": False})
        self.assertEqual(result["status"], "draft")
        self.assertEqual(len(result["slides"]), 3)
        self.assertEqual(result["code_refs"], [])
        self.assertIn("記入", result["slides"][0]["message"])

    def test_learning_api_and_document_download(self):
        self.http()
        data = json.loads(self.read("/api/learning")[0])
        self.assertEqual(len(data["steps"]), 4)
        self.assertIn("コメントアウト", data["steps"][0]["prompt_text"])
        body, headers = self.read("/learning/files/workbook.md?download")
        self.assertIn("本人", body.decode())
        self.assertIn("attachment", headers["Content-Disposition"])

    def test_profile_api_returns_selected_code_only(self):
        self.http()
        data = json.loads(self.read("/api/games/test/profile")[0])
        self.assertEqual(data["profile"]["code_refs"][0]["code"], "const speed = 10;\nmove(speed);")
        for route in ["/api/games/unknown/profile", "/learning/files/../../arcade.py", "/showcase/test.json"]:
            with self.subTest(route=route), self.assertRaises(HTTPError) as error:
                self.read(route)
            self.assertEqual(error.exception.code, 404)

    def test_learning_file_whitelist(self):
        with self.assertRaises(ValueError):
            learning_file(ROOT, "../arcade.py")

    def test_web_pages_and_three_page_template_are_served(self):
        self.http()
        for route in ["/learn", "/games/test", "/games/test/slides"]:
            self.assertIn(b"<!doctype html>", self.read(route)[0])
        self.assertEqual(len(json.loads(self.read("/showcase/template.json")[0])["slides"]), 3)


if __name__ == "__main__":
    unittest.main()
