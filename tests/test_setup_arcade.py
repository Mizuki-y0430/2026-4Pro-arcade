import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from setup_arcade import load_sources, prepare_game, ensure_dependencies


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.game = {"id": "member", "title": "Member", "kind": "static", "path": "games/local/member"}
        self.source = {"game_id": "member", "repository": "https://github.com/example/member.git",
                       "branch": "main", "revision": "a" * 40, "required_files": ["index.html"]}
        self.folder = self.root / self.game["path"]

    def tearDown(self):
        self.temp.cleanup()

    def save(self, games=None, sources=None):
        (self.root / "games.json").write_text(json.dumps({"games": games or [self.game]}), encoding="utf-8")
        (self.root / "game-sources.json").write_text(json.dumps({"sources": sources if sources is not None else [self.source]}), encoding="utf-8")

    def test_manifest_covers_every_external_game(self):
        self.save()
        games, sources = load_sources(self.root)
        self.assertEqual(sources, [self.source])
        self.assertEqual(games["member"], self.game)
        self.save(sources=[])
        with self.assertRaisesRegex(ValueError, "すべて"):
            load_sources(self.root)

    def test_real_manifest_covers_five_sources_and_six_games(self):
        games, sources = load_sources(Path(__file__).resolve().parents[1])
        self.assertEqual(len(games), 6)
        self.assertEqual(len(sources), 5)
        self.assertNotIn("realtime-shogi", {s["game_id"] for s in sources})

    def test_manifest_rejects_bad_repository_revision_duplicates_and_paths(self):
        for change in [{"repository": "file:///private"}, {"revision": "main"},
                       {"branch": "--bad"}, {"required_files": ["../private"]},
                       {"game_id": "unknown"}, {"required_files": []}]:
            with self.subTest(change=change):
                self.save(sources=[{**self.source, **change}])
                with self.assertRaises(ValueError): load_sources(self.root)
        self.save(sources=[self.source, self.source])
        with self.assertRaises(ValueError): load_sources(self.root)
        self.save(games=[{**self.game, "path": "games/samples/existing"}])
        with self.assertRaises(ValueError): load_sources(self.root)

    def test_existing_game_and_records_are_kept_without_git_or_network(self):
        self.folder.mkdir(parents=True)
        (self.folder / "index.html").write_text("my edited game", encoding="utf-8")
        (self.folder / "score.json").write_text("player record", encoding="utf-8")
        with patch("setup_arcade.run") as run, patch("setup_arcade.shutil.which", return_value=None):
            prepare_game(self.root, self.game, self.source)
            prepare_game(self.root, self.game, self.source, check=True)
        run.assert_not_called()
        self.assertEqual((self.folder / "index.html").read_text(), "my edited game")
        self.assertEqual((self.folder / "score.json").read_text(), "player record")

    def test_wrong_existing_branch_is_reported_without_overwrite(self):
        self.folder.mkdir(parents=True)
        (self.folder / "main.py").write_text("desktop game", encoding="utf-8")
        with patch("setup_arcade.run") as run, self.assertRaisesRegex(ValueError, "既存フォルダ"):
            prepare_game(self.root, self.game, self.source)
        run.assert_not_called()
        self.assertEqual((self.folder / "main.py").read_text(), "desktop game")

    def test_check_mode_does_not_fetch_missing_games(self):
        with patch("setup_arcade.run") as run, self.assertRaisesRegex(ValueError, "未取得"):
            prepare_game(self.root, self.game, self.source, check=True)
        run.assert_not_called()
        self.assertFalse(self.folder.exists())

    def test_failed_clone_reports_access_and_can_be_retried(self):
        with patch("setup_arcade.shutil.which", return_value="git"), patch("setup_arcade.run", side_effect=subprocess.CalledProcessError(128, "git")):
            with self.assertRaisesRegex(ValueError, "閲覧権限"):
                prepare_game(self.root, self.game, self.source)
        self.assertFalse(self.folder.exists())
        self.assertEqual(list(self.folder.parent.iterdir()), [])

    def test_download_missing_required_files_does_not_publish_half_game(self):
        def fake_run(command, root):
            if "clone" in command:
                Path(command[-1]).mkdir()
        with patch("setup_arcade.shutil.which", return_value="git"), patch("setup_arcade.run", side_effect=fake_run):
            with self.assertRaisesRegex(ValueError, "必要なファイル"):
                prepare_game(self.root, self.game, self.source)
        self.assertFalse(self.folder.exists())

    def test_prepared_dependencies_need_no_network(self):
        with patch("setup_arcade.run") as run, patch("setup_arcade.version", return_value="3.1.5"), patch("setup_arcade.importlib.import_module"):
            ensure_dependencies(self.root)
        run.assert_not_called()

    def test_missing_dependency_check_fails_without_installing(self):
        with patch("setup_arcade.version", return_value="3.0.0"), patch("setup_arcade.run") as run:
            with self.assertRaisesRegex(ValueError, "未準備"):
                ensure_dependencies(self.root, check=True)
        run.assert_not_called()

    @unittest.skipUnless(shutil.which("git"), "Git clone integration")
    def test_fresh_clone_uses_confirmed_revision_and_can_run_again(self):
        repository = self.root / "source"
        repository.mkdir()

        def git(*args):
            return subprocess.check_output(["git", "-C", str(repository), *args], text=True).strip()

        git("init", "--initial-branch=main")
        git("config", "user.name", "Setup Test")
        git("config", "user.email", "setup-test@example.invalid")
        (repository / "index.html").write_text("tested version", encoding="utf-8")
        git("add", "index.html")
        git("commit", "-m", "tested version")
        revision = git("rev-parse", "HEAD")
        (repository / "index.html").write_text("new upstream version", encoding="utf-8")
        git("commit", "-am", "new upstream version")
        source = {**self.source, "repository": str(repository), "revision": revision}
        prepare_game(self.root, self.game, source)
        self.assertEqual((self.folder / "index.html").read_text(), "tested version")
        (self.folder / "score.json").write_text("saved", encoding="utf-8")
        prepare_game(self.root, self.game, source)
        self.assertEqual((self.folder / "score.json").read_text(), "saved")


if __name__ == "__main__":
    unittest.main()
