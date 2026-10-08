import importlib.util
from pathlib import Path
import tkinter as tk
import unittest


spec = importlib.util.spec_from_file_location(
    "reaction_game", Path(__file__).resolve().parents[1] / "games/samples/reaction-lab/main.py"
)
sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sample)


class ReactionGameTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.game = sample.ReactionGame(self.root)

    def tearDown(self):
        self.game.close()

    def test_early_click_cancels_timer_and_allows_retry(self):
        self.game.click()
        self.assertEqual(self.game.state, "waiting")
        self.assertIsNotNone(self.game.timer)
        self.game.click()
        self.assertEqual(self.game.state, "idle")
        self.assertIsNone(self.game.timer)
        self.assertIn("フライング", self.game.button.cget("text"))
        self.game.click()
        self.assertEqual(self.game.state, "waiting")

    def test_green_click_records_best_time(self):
        self.game.click()
        self.root.after_cancel(self.game.timer)
        self.game.go()
        self.game.started -= .25
        self.game.click()
        first = self.game.best
        self.assertGreaterEqual(first, 250)
        self.assertEqual(self.game.state, "idle")
        self.game.click()
        self.root.after_cancel(self.game.timer)
        self.game.go()
        self.game.started -= .1
        self.game.click()
        self.assertLess(self.game.best, first)
        self.assertIn("ms", self.game.record.cget("text"))


if __name__ == "__main__":
    unittest.main()
