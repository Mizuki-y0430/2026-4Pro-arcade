"""Web画面用の進行管理。作者のChessGame / ChessAIを共通で使用する。"""
import math
import random
import time

from .constants import AI_PIECE_CD_MS, AUTO_NEXT_MS
from .game import ChessGame


class WebGame:
    """画面から独立した対局状態。サーバーがロックを持って操作する。"""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.game = ChessGame()
        self.mode = "ai"
        self.level = "normal"
        self.cooldown_ms = 500
        self.animation = True
        self.revision = 0
        self.reset()

    def reset(self):
        self.game.reset()
        self.phase = "ready"
        self.active = False
        self.countdown_until = 0
        self.next_ai = 0
        self.rematch_at = 0
        self.cd_until = {"w": 0, "b": 0}
        self.piece_cd = {}
        self.match_no = 0
        self.match_score = {"w": 0, "b": 0, "draw": 0}
        self.next_color = "w"
        self.revision += 1

    def configure(self, data):
        # 値はすべて検証してから反映する。途中まで設定が変わるのを防ぐ。
        mode = data.get("mode", self.mode)
        level = data.get("level", self.level)
        cooldown = data.get("cooldown_ms", self.cooldown_ms)
        animation = data.get("animation", self.animation)
        if mode not in ("ai", "aivsai") or level not in ("weak", "normal", "strong"):
            raise ValueError("対戦モードまたはAIの強さが不正です。")
        if type(cooldown) is not int or not 0 <= cooldown <= 1500:
            raise ValueError("クールタイムは0〜1500msにしてください。")
        if type(animation) is not bool:
            raise ValueError("アニメーション設定が不正です。")
        changed_mode = mode != self.mode
        self.mode, self.level = mode, level
        self.cooldown_ms, self.animation = cooldown, animation
        if changed_mode:
            self.reset()
        self.revision += 1

    def _new_match(self):
        self.game.reset()
        self.cd_until = {"w": 0, "b": 0}
        self.piece_cd = {}
        self.match_no += 1
        self.next_color = "w" if self.match_no % 2 else "b"
        self.revision += 1

    def start(self):
        if self.active:
            return
        if self.mode == "aivsai":
            self._new_match()
        elif self.game.game_over:
            self.game.reset()
            self.cd_until = {"w": 0, "b": 0}
        self.active = True
        self.phase = "countdown"
        self.countdown_until = self.clock() + 3
        self.rematch_at = 0
        self.revision += 1

    def stop(self):
        self.active = False
        self.countdown_until = self.rematch_at = 0
        self.phase = "finished" if self.game.game_over else "paused"
        self.revision += 1

    def _begin_play(self, now):
        self.phase = "playing"
        self.countdown_until = 0
        self.next_ai = now + 1
        if self.mode == "aivsai":
            # 元のGUI同様、AI同士では各駒にランダムな初期クールタイム。
            self.piece_cd = {
                (r, c): now + random.uniform(0, AI_PIECE_CD_MS / 1000)
                for r in range(8) for c in range(8) if self.game.board[r][c]
            }
        self.revision += 1

    def tick(self):
        """ブラウザーの更新頻度に依存せず、Python側でAIと時間を進める。"""
        now = self.clock()
        if not self.active:
            return
        if self.phase == "finished":
            if self.rematch_at and now >= self.rematch_at:
                self._new_match()
                self.rematch_at = 0
                self._begin_play(now)
            return
        if self.phase == "countdown":
            if now >= self.countdown_until:
                self._begin_play(now)
            return
        if self.phase != "playing" or now < self.next_ai:
            return
        color = self.next_color if self.mode == "aivsai" else "b"
        if self.mode == "aivsai":
            self.next_color = "b" if color == "w" else "w"
            self.piece_cd = {sq: deadline for sq, deadline in self.piece_cd.items() if deadline > now}
            exclude = self.piece_cd
        else:
            exclude = ()
        move = self.game.choose_ai_move(color, level=self.level, exclude=exclude)
        if move:
            self._apply(*move[:4], promotion=move[4])
        # 固まった後に何手も一気に進めない。次の手は計算終了後の1秒先。
        self.next_ai = self.clock() + 1

    def move(self, data):
        if self.mode != "ai" or self.phase != "playing":
            raise ValueError("スタートしてから白の駒を動かしてください。")
        coordinates = [data.get(key) for key in ("sr", "sc", "er", "ec")]
        if any(type(value) is not int or not 0 <= value < 8 for value in coordinates):
            raise ValueError("移動するマスが不正です。")
        sr, sc, er, ec = coordinates
        promotion = data.get("promotion", "Q")
        if promotion not in ("Q", "R", "B", "N"):
            raise ValueError("昇格先を選んでください。")
        if self.game.board[sr][sc] is None or self.game.board[sr][sc][0] != "w":
            raise ValueError("白の駒を選んでください。")
        if self.clock() < self.cd_until["w"]:
            raise ValueError("クールタイム中です。少し待ってから動かしてください。")
        if not self._apply(sr, sc, er, ec, promotion):
            raise ValueError("そのマスには移動できません。駒を選び直してください。")

    def _apply(self, sr, sc, er, ec, promotion="Q"):
        piece = self.game.board[sr][sc]
        if not self.game.move(sr, sc, er, ec, promotion=promotion):
            return False
        now = self.clock()
        if self.mode == "aivsai":
            self.piece_cd.pop((sr, sc), None)
            self.piece_cd.pop((er + (1 if piece[0] == "w" else -1), ec), None)
            self.piece_cd[(er, ec)] = now + AI_PIECE_CD_MS / 1000
            if piece[1] == "K" and abs(ec - sc) == 2:
                rook_from, rook_to = (sr, 7 if ec == 6 else 0), (sr, 5 if ec == 6 else 3)
                self.piece_cd.pop(rook_from, None)
                self.piece_cd[rook_to] = now + AI_PIECE_CD_MS / 1000
        else:
            self.cd_until[piece[0]] = now + (self.cooldown_ms / 1000 if piece[0] == "w" else 1)
        self.revision += 1
        if self.game.game_over:
            self.phase = "finished"
            if self.mode == "aivsai" and self.active:
                self.match_score[self.game.winner] += 1
                self.rematch_at = now + AUTO_NEXT_MS / 1000
            else:
                self.active = False
        return True

    def snapshot(self):
        now = self.clock()
        legal = {}
        if self.phase == "playing" and self.mode == "ai":
            for sr, sc, er, ec in self.game.get_all_moves("w"):
                legal.setdefault(f"{sr},{sc}", []).append([er, ec])
        history = [
            {"from": list(source), "to": list(target), "piece": piece, "captured": captured}
            for source, target, piece, captured in self.game.history[-120:]
        ]
        return {
            "stamp": now, "revision": self.revision,
            "board": [row[:] for row in self.game.board],
            "phase": self.phase, "active": self.active,
            "mode": self.mode, "level": self.level,
            "cooldown_ms": self.cooldown_ms, "animation": self.animation,
            "countdown": max(0, math.ceil(self.countdown_until - now)),
            "cooldowns": {color: max(0, round((deadline - now) * 1000)) for color, deadline in self.cd_until.items()},
            "piece_cooldowns": {f"{r},{c}": max(0, round((deadline-now)*1000)) for (r,c), deadline in self.piece_cd.items() if deadline > now},
            "legal_moves": legal, "history": history,
            "move_count": self.game.move_count, "winner": self.game.winner, "game_over": self.game.game_over,
            "captures": {color: [captured for _, _, piece, captured in self.game.history if piece[0] == color and captured] for color in ("w", "b")},
            "checks": {color: self.game.find_king(self.game.board, color) if self.game.is_in_check(color) else None for color in ("w", "b")},
            "match_no": self.match_no, "match_score": self.match_score.copy(),
            "rematch_in": max(0, math.ceil(self.rematch_at - now)),
        }
