#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AIモジュール: 敵陣(黒)の思考ロジック。

`ChessAI` は `ChessGame` に継承される Mixin。
盤面操作は `self.board` / `self.get_all_moves` 等を介して行う。
"""

import random


class ChessAI:
    """AI思考 Mixin。単体では使わず ChessGame と組み合わせる。"""

    AI_VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}

    def evaluate_board(self, color):
        """駒価値+中央配置の簡易評価 (color視点のスコア)"""
        opp = "w" if color == "b" else "b"
        score = 0
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p is None:
                    continue
                v = self.AI_VALUES.get(p[1], 0)
                # 中央ボーナス
                pos = (3 - abs(3.5 - r) - abs(3.5 - c)) * 5
                if p[1] == "P":
                    pos += ((6 - r) if p[0] == "w" else (r - 1)) * 8
                if p[0] == color:
                    score += v + pos
                else:
                    score -= v + pos
        if self.is_in_check(opp):
            score += 120
        if self.is_in_check(color):
            score -= 120
        return score

    def _sim_move(self, sr, sc, er, ec):
        """盤面を一時的に動かす。戻り値はず restoration 用のundo関数"""
        piece = self.board[sr][sc]
        dst = self.board[er][ec]
        is_ep = (piece[1] == "P" and (er, ec) == self.en_passant and dst is None)
        cap_r, ep_cap = None, None
        if is_ep:
            cap_r = er + (1 if piece[0] == "w" else -1)
            ep_cap = self.board[cap_r][ec]
            self.board[cap_r][ec] = None
        self.board[er][ec] = piece
        self.board[sr][sc] = None

        def undo():
            self.board[sr][sc] = piece
            self.board[er][ec] = dst
            if is_ep:
                self.board[cap_r][ec] = ep_cap
        return undo, is_ep

    def _static_score(self, color, opp, sr, sc, er, ec, noise=30):
        """1手読みの静的スコア (choose_ai_move 内部用)"""
        values = self.AI_VALUES
        piece = self.board[sr][sc]
        captured = self.board[er][ec]
        score = 0
        if captured is not None and captured[0] == opp:
            score += 10 * values.get(captured[1], 0) - values.get(piece[1], 0) // 10
        if piece[1] == "P" and (er, ec) == self.en_passant and captured is None:
            score += 10 * values["P"]
        if piece[1] == "P" and (er == 0 or er == 7):
            score += 900
        score += (3 - abs(3.5 - er) - abs(3.5 - ec)) * 5
        if piece[1] == "P":
            adv = (sr - er) if color == "w" else (er - sr)
            score += adv * 8
        undo, _ = self._sim_move(sr, sc, er, ec)
        gives_check = self.is_in_check(opp, self.board)
        attacked = self.is_attacked(self.board, er, ec, opp)
        undo()
        if gives_check:
            score += 120
        if attacked:
            score -= values.get(piece[1], 0) // 4
        if noise:
            score += random.randint(-noise, noise)
        return score

    def choose_ai_move(self, color="b", level="normal", exclude=()):
        """AIの手選択。level: 'weak'(弱い) / 'normal'(ふつう) / 'strong'(強い)。
        exclude: クールタイム中等で動かせない移動元 {(sr,sc)}。該当手は候補から外す。"""
        ex = set(exclude)
        moves = [m for m in self.get_all_moves(color) if (m[0], m[1]) not in ex]
        if not moves:
            return None
        opp = "w" if color == "b" else "b"
        if level == "weak":
            # 弱い: ほぼランダム。駒取りだけ少し考慮
            scored = []
            for sr, sc, er, ec in moves:
                captured = self.board[er][ec]
                s = random.randint(-100, 100)
                if captured is not None and captured[0] == opp:
                    s += self.AI_VALUES.get(captured[1], 0) // 10
                scored.append((s, (sr, sc, er, ec)))
            scored.sort(key=lambda x: x[0], reverse=True)
            top = [m for s, m in scored if s >= scored[0][0] - 80]
            sr, sc, er, ec = random.choice(top)
            return (sr, sc, er, ec, "Q")
        if level == "strong":
            # 強い: 1手読み上位8手について相手の最善応手を読み切り(2手読み相当)
            scored = [(self._static_score(color, opp, sr, sc, er, ec, noise=0), (sr, sc, er, ec))
                      for sr, sc, er, ec in moves]
            scored.sort(key=lambda x: x[0], reverse=True)
            cands = [m for _, m in scored[:8]]
            best, best_ms = None, None
            for sr, sc, er, ec in cands:
                undo, _ = self._sim_move(sr, sc, er, ec)
                # 相手の最善応手(静的スコア最大)を求める
                reply_best = 0
                for rs, cs, re, ce in self.get_all_moves(opp):
                    rs_score = self._static_score(opp, color, rs, cs, re, ce, noise=0)
                    if rs_score > reply_best:
                        reply_best = rs_score
                val = self.evaluate_board(color) - int(reply_best * 0.9)
                undo()
                val += random.randint(-12, 12)
                if best is None or val > best:
                    best, best_ms = val, (sr, sc, er, ec)
            sr, sc, er, ec = best_ms
            return (sr, sc, er, ec, "Q")
        # ふつう: 1手評価+ランダム性
        scored = [(self._static_score(color, opp, sr, sc, er, ec, noise=30), (sr, sc, er, ec))
                  for sr, sc, er, ec in moves]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_score = scored[0][0]
        candidates = [m for s, m in scored if s >= best_score - 20]
        sr, sc, er, ec = random.choice(candidates)
        return (sr, sc, er, ec, "Q")
