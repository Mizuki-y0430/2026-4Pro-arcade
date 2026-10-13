#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""対局ロジックモジュール: ルール判定・合法手生成・行移動・勝敗判定。"""

from .ai import ChessAI


class ChessGame(ChessAI):
    """盤面ロジック。ターン管理なし(どちらの色もいつでも動かせる)。"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        back = ["R", "N", "B", "Q", "K", "B", "N", "R"]
        for c, p in enumerate(back):
            self.board[0][c] = "b" + p
            self.board[1][c] = "bP"
            self.board[6][c] = "wP"
            self.board[7][c] = "w" + p
        self.castling = {"wK": True, "wQ": True, "bK": True, "bQ": True}
        self.en_passant = None  # (r, c) 取られる対象ではなく、通過マス
        self.move_count = 0
        self.history = []
        self.game_over = False
        self.winner = None

    def in_board(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def find_king(self, board, color):
        for r in range(8):
            for c in range(8):
                if board[r][c] == color + "K":
                    return (r, c)
        return None

    def is_attacked(self, board, r, c, by_color):
        """(r,c) が by_color から攻撃されているか"""
        opp = by_color
        # ポーンの攻撃
        direction = -1 if opp == "w" else 1
        for dc in (-1, 1):
            pr, pc = r - direction, c - dc
            if self.in_board(pr, pc) and board[pr][pc] == opp + "P":
                return True
        # ナイト
        for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)]:
            nr, nc = r + dr, c + dc
            if self.in_board(nr, nc) and board[nr][nc] == opp + "N":
                return True
        # キング
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if self.in_board(nr, nc) and board[nr][nc] == opp + "K":
                    return True
        # スライディング
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            while self.in_board(nr, nc):
                p = board[nr][nc]
                if p is not None:
                    if p[0] == opp and p[1] in ("R", "Q"):
                        return True
                    break
                nr += dr
                nc += dc
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            while self.in_board(nr, nc):
                p = board[nr][nc]
                if p is not None:
                    if p[0] == opp and p[1] in ("B", "Q"):
                        return True
                    break
                nr += dr
                nc += dc
        return False

    def is_in_check(self, color, board=None):
        if board is None:
            board = self.board
        kpos = self.find_king(board, color)
        if kpos is None:
            return False
        opp = "b" if color == "w" else "w"
        return self.is_attacked(board, kpos[0], kpos[1], opp)

    def get_pseudo_moves(self, r, c):
        """チェックを無視した擬似合法手。[(er,ec), ...]"""
        piece = self.board[r][c]
        if piece is None:
            return []
        color, kind = piece[0], piece[1]
        moves = []

        def add_slide(dirs):
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                while self.in_board(nr, nc):
                    t = self.board[nr][nc]
                    if t is None:
                        moves.append((nr, nc))
                    else:
                        if t[0] != color and t[1] != "K":
                            moves.append((nr, nc))
                        break
                    nr += dr
                    nc += dc

        if kind == "P":
            direction = -1 if color == "w" else 1
            start_row = 6 if color == "w" else 1
            if self.in_board(r + direction, c) and self.board[r + direction][c] is None:
                moves.append((r + direction, c))
                if r == start_row and self.board[r + 2 * direction][c] is None:
                    moves.append((r + 2 * direction, c))
            for dc in (-1, 1):
                nr, nc = r + direction, c + dc
                if self.in_board(nr, nc):
                    t = self.board[nr][nc]
                    if t is not None and t[0] != color and t[1] != "K":
                        moves.append((nr, nc))
                    if self.en_passant == (nr, nc):
                        moves.append((nr, nc))
        elif kind == "N":
            for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                           (1, -2), (1, 2), (2, -1), (2, 1)]:
                nr, nc = r + dr, c + dc
                if self.in_board(nr, nc):
                    t = self.board[nr][nc]
                    if t is None or (t[0] != color and t[1] != "K"):
                        moves.append((nr, nc))
        elif kind == "B":
            add_slide([(-1, -1), (-1, 1), (1, -1), (1, 1)])
        elif kind == "R":
            add_slide([(-1, 0), (1, 0), (0, -1), (0, 1)])
        elif kind == "Q":
            add_slide([(-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (-1, 1), (1, -1), (1, 1)])
        elif kind == "K":
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if self.in_board(nr, nc):
                        t = self.board[nr][nc]
                        if t is None or (t[0] != color and t[1] != "K"):
                            moves.append((nr, nc))
            opp = "b" if color == "w" else "w"
            home = 7 if color == "w" else 0
            if r == home and c == 4:
                if not self.is_in_check(color):
                    key = color + "K"
                    if self.castling.get(key):
                        if (self.board[home][5] is None and self.board[home][6] is None):
                            rook = self.board[home][7]
                            if rook == color + "R":
                                if (not self.is_attacked(self.board, home, 5, opp) and
                                        not self.is_attacked(self.board, home, 6, opp)):
                                    moves.append((home, 6))
                    key = color + "Q"
                    if self.castling.get(key):
                        if (self.board[home][1] is None and self.board[home][2] is None and
                                self.board[home][3] is None):
                            rook = self.board[home][0]
                            if rook == color + "R":
                                if (not self.is_attacked(self.board, home, 3, opp) and
                                        not self.is_attacked(self.board, home, 2, opp)):
                                    moves.append((home, 2))
        return moves

    def get_legal_moves(self, r, c):
        """自玉を危険に晒さない合法手のみ返す"""
        piece = self.board[r][c]
        if piece is None:
            return []
        color = piece[0]
        legal = []
        for er, ec in self.get_pseudo_moves(r, c):
            backup_src = self.board[r][c]
            backup_dst = self.board[er][ec]
            ep_captured = None
            is_ep = (backup_src[1] == "P" and (er, ec) == self.en_passant and
                     backup_dst is None)
            if is_ep:
                cap_r = er + (1 if color == "w" else -1)
                ep_captured = self.board[cap_r][ec]
                self.board[cap_r][ec] = None
            self.board[er][ec] = backup_src
            self.board[r][c] = None
            in_check = self.is_in_check(color, self.board)
            self.board[r][c] = backup_src
            self.board[er][ec] = backup_dst
            if is_ep:
                cap_r = er + (1 if color == "w" else -1)
                self.board[cap_r][ec] = ep_captured
            if not in_check:
                legal.append((er, ec))
        return legal

    def has_any_legal_move(self, color):
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p is not None and p[0] == color:
                    if self.get_legal_moves(r, c):
                        return True
        return False

    def get_all_moves(self, color):
        all_moves = []
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p is not None and p[0] == color:
                    for er, ec in self.get_legal_moves(r, c):
                        all_moves.append((r, c, er, ec))
        return all_moves

    def move(self, sr, sc, er, ec, promotion="Q"):
        """1手動かす。成功時 True。ターン制なしなので色チェックはしない。"""
        if self.game_over:
            return False
        if not (self.in_board(sr, sc) and self.in_board(er, ec)):
            return False
        piece = self.board[sr][sc]
        if piece is None:
            return False
        color, kind = piece[0], piece[1]
        legal = self.get_legal_moves(sr, sc)
        if (er, ec) not in legal:
            return False
        captured = self.board[er][ec]
        if kind == "P" and (er, ec) == self.en_passant and captured is None:
            cap_r = er + (1 if color == "w" else -1)
            captured = self.board[cap_r][ec]
            self.board[cap_r][ec] = None
        self.board[er][ec] = piece
        self.board[sr][sc] = None
        if kind == "K" and abs(ec - sc) == 2:
            home = sr
            if ec == 6:
                self.board[home][5] = self.board[home][7]
                self.board[home][7] = None
            elif ec == 2:
                self.board[home][3] = self.board[home][0]
                self.board[home][0] = None
        if kind == "P" and (er == 0 or er == 7):
            if promotion not in ("Q", "R", "B", "N"):
                promotion = "Q"
            self.board[er][ec] = color + promotion
        if kind == "K":
            self.castling[color + "K"] = False
            self.castling[color + "Q"] = False
        if kind == "R":
            if color == "w" and sr == 7 and sc == 0:
                self.castling["wQ"] = False
            if color == "w" and sr == 7 and sc == 7:
                self.castling["wK"] = False
            if color == "b" and sr == 0 and sc == 0:
                self.castling["bQ"] = False
            if color == "b" and sr == 0 and sc == 7:
                self.castling["bK"] = False
        if captured is not None and captured[1] == "R":
            if er == 7 and ec == 0:
                self.castling["wQ"] = False
            if er == 7 and ec == 7:
                self.castling["wK"] = False
            if er == 0 and ec == 0:
                self.castling["bQ"] = False
            if er == 0 and ec == 7:
                self.castling["bK"] = False
        if kind == "P" and abs(er - sr) == 2:
            self.en_passant = ((sr + er) // 2, sc)
        else:
            self.en_passant = None
        self.move_count += 1
        self.history.append(((sr, sc), (er, ec), piece, captured))
        self.update_game_status()
        return True

    def update_game_status(self):
        for color in ("w", "b"):
            if not self.has_any_legal_move(color):
                if self.is_in_check(color):
                    self.game_over = True
                    self.winner = "b" if color == "w" else "w"
                    return
                else:
                    self.game_over = True
                    self.winner = "draw"
                    return
