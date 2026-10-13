"""Server-owned real-time match lifecycle, matching the chess game's timing."""
import math
import random
import time
from shogi import ShogiGame, Move, HAND_KINDS


class WebGame:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.mode, self.level, self.cooldown_ms, self.animation = "ai", "normal", 500, True
        self.revision = 0
        self.reset()

    def reset(self):
        self.game = ShogiGame()
        self.phase, self.active = "ready", False
        self.countdown_until = self.next_ai = self.rematch_at = 0
        self.cd_until = {"w": 0, "b": 0}
        self.piece_cd = {}
        self.match_no = 0
        self.match_score = {"w": 0, "b": 0, "draw": 0}
        self.next_color = "w"
        self.revision += 1
        self.legal_revision = -1

    def configure(self, data):
        mode, level = data.get("mode", self.mode), data.get("level", self.level)
        cooldown, animation = data.get("cooldown_ms", self.cooldown_ms), data.get("animation", self.animation)
        if mode not in ("ai", "aivsai") or level not in ("weak", "normal", "strong"):
            raise ValueError("対戦モードまたはAIの強さが不正です。")
        if type(cooldown) is not int or not 0 <= cooldown <= 1500:
            raise ValueError("クールタイムは0〜1500msにしてください。")
        if type(animation) is not bool:
            raise ValueError("アニメーション設定が不正です。")
        changed = self.mode != mode
        self.mode, self.level, self.cooldown_ms, self.animation = mode, level, cooldown, animation
        if changed:
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
        if self.mode == "aivsai" or self.game.game_over:
            self._new_match()
        self.active, self.phase = True, "countdown"
        self.countdown_until, self.rematch_at = self.clock() + 3, 0
        self.revision += 1

    def stop(self):
        self.active = False
        self.countdown_until = self.rematch_at = 0
        self.phase = "finished" if self.game.game_over else "paused"
        self.revision += 1

    def _begin_play(self, now):
        self.phase, self.countdown_until, self.next_ai = "playing", 0, now + 1
        self.cd_until["b"] = now + 1
        if self.mode == "aivsai":
            self.piece_cd = {(r, c): now + random.uniform(0, 2)
                             for r in range(9) for c in range(9) if self.game.board[r][c]}
        self.revision += 1

    def tick(self):
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
        self.piece_cd = {sq: deadline for sq, deadline in self.piece_cd.items() if deadline > now}
        if self.mode == "aivsai":
            self.next_color = "b" if color == "w" else "w"
        move = self.game.choose_ai(color, self.level, self.piece_cd if self.mode == "aivsai" else ())
        if move:
            self._apply(color, move)
        self.next_ai = self.clock() + 1
        self.cd_until[color] = self.next_ai

    def move(self, data):
        if self.mode != "ai" or self.phase != "playing":
            raise ValueError("スタートしてから先手の駒を動かしてください。")
        if self.clock() < self.cd_until["w"]:
            raise ValueError("クールタイム中です。少し待ってください。")
        coords = [data.get(k) for k in ("er", "ec")]
        drop = data.get("drop")
        if drop is not None:
            if not isinstance(drop, str) or drop not in HAND_KINDS or len(drop) != 1:
                raise ValueError("持ち駒を選び直してください。")
        else:
            coords += [data.get(k) for k in ("sr", "sc")]
        if any(type(v) is not int or not 0 <= v < 9 for v in coords):
            raise ValueError("移動するマスが不正です。")
        promote = data.get("promote", False)
        if type(promote) is not bool or (drop and promote):
            raise ValueError("成りの指定が不正です。")
        move = Move(coords[0], coords[1], drop=drop, promote=promote) if drop else Move(coords[0], coords[1], coords[2], coords[3], promote=promote)
        if not self._apply("w", move):
            raise ValueError("そこには指せません。駒と移動先を選び直してください。")

    def _apply(self, color, move):
        if not self.game.play(color, move):
            return False
        now = self.clock()
        self.piece_cd.pop((move.sr, move.sc), None)
        self.piece_cd.pop((move.er, move.ec), None)
        if self.mode == "aivsai":
            self.piece_cd[(move.er, move.ec)] = now + 2
        self.cd_until[color] = now + (self.cooldown_ms / 1000 if color == "w" else 1)
        self.revision += 1
        if self.game.game_over:
            self.phase = "finished"
            if self.mode == "aivsai" and self.active:
                self.match_score[self.game.winner] += 1
                self.rematch_at = now + 3
            else:
                self.active = False
        return True

    def snapshot(self):
        now = self.clock()
        if self.legal_revision != self.revision:
            self.legal_moves = {}
            if self.phase == "playing" and self.mode == "ai":
                for m in self.game.moves("w"):
                    key = "drop:" + m.drop if m.drop else f"{m.sr},{m.sc}"
                    self.legal_moves.setdefault(key, []).append([m.er, m.ec, m.promote])
            self.legal_revision = self.revision
        return {
            "stamp": now, "revision": self.revision, "board": [row[:] for row in self.game.board],
            "hands": {c: hand.copy() for c, hand in self.game.hands.items()},
            "phase": self.phase, "active": self.active, "mode": self.mode, "level": self.level,
            "cooldown_ms": self.cooldown_ms, "animation": self.animation,
            "countdown": max(0, math.ceil(self.countdown_until - now)),
            "cooldowns": {c: max(0, round((d - now) * 1000)) for c, d in self.cd_until.items()},
            "piece_cooldowns": {f"{r},{c}": max(0, round((d - now) * 1000)) for (r, c), d in self.piece_cd.items() if d > now},
            "legal_moves": self.legal_moves, "history": self.game.history[-120:],
            "move_count": self.game.move_count, "winner": self.game.winner,
            "game_over": self.game.game_over, "reason": self.game.reason,
            "checks": {c: self.game.king(c) if self.game.in_check(c) else None for c in ("w", "b")},
            "match_no": self.match_no, "match_score": self.match_score.copy(),
            "rematch_in": max(0, math.ceil(self.rematch_at - now)),
        }
