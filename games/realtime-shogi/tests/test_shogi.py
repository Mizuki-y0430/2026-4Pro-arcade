import copy
import json
from pathlib import Path
import sys
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shogi import ShogiGame, Move
from web_game import WebGame
from web import make_server, tick_games


class RulesTests(unittest.TestCase):
    def empty(self):
        game = ShogiGame()
        game.board = [[None] * 9 for _ in range(9)]
        game.board[8][4], game.board[0][4] = "wK", "bK"
        return game

    def test_initial_board_and_both_colors_can_move_without_turn(self):
        g = ShogiGame()
        self.assertEqual(sum(bool(p) for row in g.board for p in row), 40)
        self.assertEqual(len(list(g.moves("w"))), 30)
        self.assertEqual(len(list(g.moves("b"))), 30)
        self.assertTrue(g.play("w", Move(5, 4, 6, 4)))
        self.assertTrue(g.play("w", Move(4, 4, 5, 4)))
        self.assertTrue(g.play("b", Move(3, 4, 2, 4)))

    def test_geometry_forward_direction_and_sliding_blockers(self):
        expected = {"K": 8, "R": 16, "B": 16, "G": 6, "S": 5,
                    "N": 2, "L": 4, "P": 1, "+R": 20, "+B": 20,
                    "+S": 6, "+N": 6, "+L": 6, "+P": 6}
        for color in ("w", "b"):
            for kind, count in expected.items():
                with self.subTest(color=color, kind=kind):
                    g = self.empty()
                    g.board[8][4] = g.board[0][4] = None
                    g.board[4][4] = color + kind
                    self.assertEqual(len(list(g.destinations(4, 4))), count)
        g = self.empty()
        g.board[4][4], g.board[3][4] = "wL", "bP"
        self.assertEqual(list(g.destinations(4, 4)), [(3, 4)])
        g.board[4][4] = "bP"
        self.assertEqual(list(g.destinations(4, 4)), [(5, 4)])

    def test_capture_demotes_and_drop_reuses_piece(self):
        g = self.empty()
        g.board[5][0], g.board[4][0] = "wR", "b+S"
        self.assertTrue(g.play("w", Move(4, 0, 5, 0)))
        self.assertEqual(g.hands["w"]["S"], 1)
        self.assertTrue(g.play("w", Move(5, 5, drop="S")))
        self.assertEqual(g.board[5][5], "wS")
        self.assertEqual(g.hands["w"]["S"], 0)
        self.assertFalse(g.play("w", Move(5, 6, drop="S")))

    def test_optional_and_forced_promotion_both_sides(self):
        for color, sr, er in [("w", 3, 2), ("b", 5, 6)]:
            for promote in (True, False):
                g = self.empty()
                g.board[sr][0] = color + "P"
                self.assertTrue(g.play(color, Move(er, 0, sr, 0, promote=promote)))
                self.assertEqual(g.board[er][0], color + ("+P" if promote else "P"))
        for color, sr, er in [("w", 1, 0), ("b", 7, 8)]:
            for kind in ("P", "L", "N"):
                g = self.empty()
                source = sr if kind != "N" else (2 if color == "w" else 6)
                g.board[source][0] = color + kind
                target_c = 1 if kind == "N" else 0
                self.assertFalse(g.play(color, Move(er, target_c, source, 0)))
                self.assertTrue(g.play(color, Move(er, target_c, source, 0, promote=True)))

    def test_cannot_promote_gold_king_or_already_promoted_piece(self):
        for kind in ("G", "K", "+P"):
            g = self.empty()
            g.board[3][0] = "w" + kind
            self.assertFalse(g.play("w", Move(2, 0, 3, 0, promote=True)))

    def test_nifu_dead_rank_and_promoted_pawn_exception(self):
        for color in ("w", "b"):
            g = self.empty()
            g.hands[color].update(P=1, L=1, N=1)
            g.board[4][0] = color + "P"
            moves = list(g.moves(color))
            self.assertNotIn(Move(5, 0, drop="P"), moves)
            last = 0 if color == "w" else 8
            next_last = 1 if color == "w" else 7
            for kind in "PLN":
                self.assertNotIn(Move(last, 2, drop=kind), moves)
            self.assertNotIn(Move(next_last, 2, drop="N"), moves)
            g.board[4][0] = color + "+P"
            self.assertIn(Move(5, 0, drop="P"), list(g.moves(color)))

    def test_king_safety_pin_and_drop_block(self):
        g = self.empty()
        g.board[4][4], g.board[6][4] = "bR", "wG"
        self.assertFalse(g.play("w", Move(6, 3, 6, 4)))
        g.board[6][4] = None
        g.hands["w"]["G"] = 1
        self.assertTrue(g.in_check("w"))
        self.assertFalse(g.play("w", Move(5, 3, drop="G")))
        self.assertTrue(g.play("w", Move(5, 4, drop="G")))
        self.assertFalse(g.in_check("w"))

    def pawn_mate_position(self):
        g = self.empty()
        g.board[0][4] = None
        g.board[0][0] = "bK"
        g.board[0][1] = "bL"
        g.board[1][1] = "bP"
        g.board[2][0] = "wG"
        g.hands["w"]["P"] = 1
        return g

    def test_pawn_drop_mate_forbidden_but_ordinary_pawn_mate_allowed(self):
        g = self.pawn_mate_position()
        self.assertNotIn(Move(1, 0, drop="P"), list(g.moves("w")))
        self.assertFalse(g.play("w", Move(1, 0, drop="P")))
        g.board[2][0], g.board[2][1] = "wP", "wG"
        self.assertTrue(g.play("w", Move(1, 0, 2, 0)))
        self.assertEqual((g.game_over, g.winner), (True, "w"))
        self.assertEqual(g.reason, "詰み")

    def test_pawn_drop_check_allowed_when_king_can_escape(self):
        g = self.pawn_mate_position()
        g.board[0][1] = None
        self.assertTrue(g.play("w", Move(1, 0, drop="P")))
        self.assertFalse(g.game_over)
        self.assertTrue(g.in_check("b"))

    def test_king_capture_not_a_legal_move(self):
        g = self.empty()
        g.board[1][4] = "wR"
        self.assertFalse(g.play("w", Move(0, 4, 1, 4)))

    def test_generating_moves_and_ai_do_not_mutate_position(self):
        g = self.empty()
        g.board[4][2], g.board[3][2] = "wR", "bS"
        g.hands["w"].update(P=2, B=1)
        before = copy.deepcopy((g.board, g.hands, g.history))
        moves = list(g.moves("w"))
        for level in ("weak", "normal", "strong"):
            self.assertIn(g.choose_ai("w", level), moves)
            self.assertEqual((g.board, g.hands, g.history), before)

    def test_repetition_finishes_game(self):
        g = self.empty()
        for _ in range(4):
            if g.game_over: break
            g.play("w", Move(8, 3, 8, 4))
            g.play("w", Move(8, 4, 8, 3))
        self.assertTrue(g.game_over)
        self.assertEqual(g.winner, "draw")

    def test_continuous_check_repetition_loses_for_checker(self):
        g = self.empty()
        g.board[8][4] = g.board[0][4] = None
        g.board[8][8], g.board[0][0], g.board[1][0] = "wK", "bK", "wR"
        for _ in range(4):
            for color, move in [("b", Move(0, 1, 0, 0)), ("w", Move(1, 1, 1, 0)),
                                ("b", Move(0, 0, 0, 1)), ("w", Move(1, 0, 1, 1))]:
                if g.game_over: break
                self.assertTrue(g.play(color, move))
        self.assertEqual((g.game_over, g.winner, g.reason), (True, "b", "連続王手の千日手"))


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.now = 100
        self.web = WebGame(clock=lambda: self.now)

    def begin(self):
        self.web.start()
        self.assertEqual(self.web.phase, "countdown")
        self.now += 3
        self.web.tick()
        self.assertEqual(self.web.phase, "playing")

    def test_cooldown_allows_consecutive_human_moves(self):
        self.begin()
        self.web.move(dict(sr=6, sc=4, er=5, ec=4))
        with self.assertRaises(ValueError):
            self.web.move(dict(sr=5, sc=4, er=4, ec=4))
        self.now += .5
        self.web.move(dict(sr=5, sc=4, er=4, ec=4))
        self.assertEqual(self.web.game.move_count, 2)
        self.now += .5
        self.web.tick()
        self.assertEqual(self.web.game.move_count, 3)

    def test_pause_resume_reset_and_validation(self):
        with self.assertRaises(ValueError): self.web.move(dict(sr=6, sc=0, er=5, ec=0))
        self.begin()
        for data in [dict(sr=True, sc=0, er=5, ec=0), dict(drop=[], er=5, ec=0),
                     dict(drop="", er=5, ec=0), dict(sr=6, sc=0, er=9, ec=0),
                     dict(sr=6, sc=0, er=5, ec=0, promote="yes")]:
            with self.subTest(data=data), self.assertRaises(ValueError): self.web.move(data)
        self.web.stop()
        self.now += 10
        self.web.tick()
        self.assertEqual(self.web.game.move_count, 0)
        self.begin()
        self.web.move(dict(sr=6, sc=0, er=5, ec=0))
        self.web.reset()
        self.assertEqual((self.web.phase, self.web.game.move_count), ("ready", 0))

    def test_settings_are_atomic_and_mode_change_resets(self):
        with self.assertRaises(ValueError): self.web.configure(dict(mode="aivsai", cooldown_ms=-1))
        self.assertEqual(self.web.mode, "ai")
        self.begin()
        self.web.configure(dict(mode="aivsai"))
        self.assertEqual((self.web.phase, self.web.active), ("ready", False))

    def test_spectator_cooldown_and_auto_rematch(self):
        self.web.configure(dict(mode="aivsai", level="weak"))
        self.begin()
        self.now += 3
        self.web.tick()
        self.assertEqual(self.web.game.move_count, 1)
        self.assertTrue(self.web.piece_cd)
        self.web.game = RulesTests().pawn_mate_position()
        self.web.game.board[2][0], self.web.game.board[2][1] = "wP", "wG"
        self.assertTrue(self.web._apply("w", Move(1, 0, 2, 0)))
        self.assertEqual(self.web.match_score["w"], 1)
        self.now += 3
        self.web.tick()
        self.assertEqual((self.web.phase, self.web.match_no, self.web.game.move_count), ("playing", 2, 0))


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker = threading.Thread(target=tick_games, args=(self.server,), daemon=True)
        self.thread.start()
        self.worker.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.opener = build_opener(ProxyHandler({}))

    def tearDown(self):
        self.server.stop_event.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.worker.join(2)

    def read(self, path, data=None, token=None, origin=True):
        headers = {"X-Shogi-Token": token or ""}
        if origin: headers["Origin"] = self.base
        request = Request(self.base + path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
        with self.opener.open(request, timeout=5) as response:
            return response.read()

    def test_sessions_auth_assets_settings_and_tick(self):
        self.assertIn("リアルタイム将棋", self.read("/").decode())
        for path in ("/style.css", "/game.js"): self.assertTrue(self.read(path))
        first, second = [json.loads(self.read("/api/session")) for _ in range(2)]
        token = first["token"]
        for path, data, supplied_token, origin in [("/api/state", None, None, True),
                ("/api/start", {}, token, False), ("/api/start", {}, None, True)]:
            with self.assertRaises(HTTPError) as error: self.read(path, data, supplied_token, origin)
            self.assertEqual(error.exception.code, 403)
        started = json.loads(self.read("/api/start", {}, token))
        self.assertEqual(started["phase"], "countdown")
        self.assertEqual(json.loads(self.read("/api/state", token=second["token"]))["phase"], "ready")
        # Advance the server-owned deadline to verify ticks work without polling.
        with self.server.lock:
            self.server.sessions[token]["game"].countdown_until = time.monotonic() - 1
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if self.server.sessions[token]["game"].phase == "playing": break
            time.sleep(.02)
        self.assertEqual(json.loads(self.read("/api/state", token=token))["phase"], "playing")
        moved = json.loads(self.read("/api/move", dict(sr=6, sc=0, er=5, ec=0), token))
        self.assertEqual(moved["board"][5][0], "wP")
        with self.assertRaises(HTTPError) as error: self.read("/api/settings", {"level": "invalid"}, token)
        self.assertEqual(error.exception.code, 400)
        with self.assertRaises(HTTPError) as error: self.read("/shogi.py")
        self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
