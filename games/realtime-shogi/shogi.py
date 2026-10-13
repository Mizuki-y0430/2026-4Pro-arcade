"""Turn-free shogi rules and a small local AI. No external dependencies."""
from dataclasses import dataclass
import random

HAND_KINDS = "RBGSNLP"
PROMOTABLE = "RBSNLP"
VALUES = {"K": 10000, "R": 1000, "B": 850, "G": 600, "S": 500,
          "N": 350, "L": 300, "P": 100, "+R": 1300, "+B": 1150,
          "+S": 600, "+N": 600, "+L": 600, "+P": 600}


def opponent(color):
    return "b" if color == "w" else "w"


@dataclass(frozen=True)
class Move:
    er: int
    ec: int
    sr: int | None = None
    sc: int | None = None
    drop: str | None = None
    promote: bool = False


class ShogiGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[None] * 9 for _ in range(9)]
        for c, kind in enumerate("LNSGKGSNL"):
            self.board[0][c], self.board[8][c] = "b" + kind, "w" + kind
        self.board[1][1], self.board[1][7] = "bR", "bB"
        self.board[7][1], self.board[7][7] = "wB", "wR"
        self.board[2], self.board[6] = ["bP"] * 9, ["wP"] * 9
        self.hands = {color: {kind: 0 for kind in HAND_KINDS} for color in ("w", "b")}
        self.history = []
        self.move_count = 0
        self.game_over, self.winner, self.reason = False, None, ""
        self.positions = {}
        self.check_log = []

    @staticmethod
    def inside(r, c):
        return 0 <= r < 9 and 0 <= c < 9

    @staticmethod
    def zone(color, r):
        return r <= 2 if color == "w" else r >= 6

    @staticmethod
    def forced(color, kind, r):
        distance = r if color == "w" else 8 - r
        return (kind in "PL" and distance == 0) or (kind == "N" and distance <= 1)

    def destinations(self, r, c):
        """Movement geometry, including occupied enemy squares, for attack tests."""
        piece = self.board[r][c]
        if not piece:
            return
        color, kind = piece[0], piece[1:]
        f = -1 if color == "w" else 1
        gold = [(f, -1), (f, 0), (f, 1), (0, -1), (0, 1), (-f, 0)]
        orthogonal = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        diagonal = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        steps, rays = [], []
        if kind == "K": steps = orthogonal + diagonal
        elif kind in ("G", "+P", "+L", "+N", "+S"): steps = gold
        elif kind == "S": steps = [(f, -1), (f, 0), (f, 1), (-f, -1), (-f, 1)]
        elif kind == "N": steps = [(2 * f, -1), (2 * f, 1)]
        elif kind == "P": steps = [(f, 0)]
        elif kind == "L": rays = [(f, 0)]
        elif kind in ("R", "+R"):
            rays = orthogonal
            if kind == "+R": steps = diagonal
        elif kind in ("B", "+B"):
            rays = diagonal
            if kind == "+B": steps = orthogonal
        for dr, dc in steps:
            er, ec = r + dr, c + dc
            if self.inside(er, ec):
                yield er, ec
        for dr, dc in rays:
            er, ec = r + dr, c + dc
            while self.inside(er, ec):
                yield er, ec
                if self.board[er][ec]:
                    break
                er, ec = er + dr, ec + dc

    def king(self, color):
        return next(((r, c) for r in range(9) for c in range(9)
                     if self.board[r][c] == color + "K"), None)

    def attacked(self, r, c, by):
        return any((r, c) in self.destinations(sr, sc)
                   for sr in range(9) for sc in range(9)
                   if self.board[sr][sc] and self.board[sr][sc][0] == by)

    def in_check(self, color):
        king = self.king(color)
        return king is None or self.attacked(*king, opponent(color))

    def push(self, color, move):
        """Apply a candidate without recording it; return enough data to undo it."""
        captured = self.board[move.er][move.ec]
        piece = color + move.drop if move.drop else self.board[move.sr][move.sc]
        if move.drop:
            self.hands[color][move.drop] -= 1
        else:
            self.board[move.sr][move.sc] = None
        if captured:
            self.hands[color][captured[1:].lstrip("+")] += 1
        self.board[move.er][move.ec] = color + "+" + piece[1:] if move.promote else piece
        return piece, captured

    def pop(self, color, move, backup):
        piece, captured = backup
        self.board[move.er][move.ec] = captured
        if move.drop:
            self.hands[color][move.drop] += 1
        else:
            self.board[move.sr][move.sc] = piece
        if captured:
            self.hands[color][captured[1:].lstrip("+")] -= 1

    def legal(self, color, move, pawn_mate=True):
        backup = self.push(color, move)
        try:
            if self.in_check(color):
                return False
            # Only the dropped pawn's direct check can constitute uchi-fuzume.
            enemy = opponent(color)
            f = -1 if color == "w" else 1
            if pawn_mate and move.drop == "P" and self.king(enemy) == (move.er + f, move.ec):
                # An adjacent pawn check cannot be blocked by a drop. Avoid recursion.
                if not next(self.moves(enemy, include_drops=False), None):
                    return False
            return True
        finally:
            self.pop(color, move, backup)

    def moves(self, color, include_drops=True):
        for r in range(9):
            for c in range(9):
                piece = self.board[r][c]
                if not piece or piece[0] != color:
                    continue
                kind = piece[1:]
                for er, ec in self.destinations(r, c):
                    target = self.board[er][ec]
                    if target and (target[0] == color or target[1:] == "K"):
                        continue
                    options = [False]
                    if kind in PROMOTABLE and (self.zone(color, r) or self.zone(color, er)):
                        options = [True] if self.forced(color, kind, er) else [False, True]
                    for promote in options:
                        move = Move(er, ec, r, c, promote=promote)
                        if self.legal(color, move):
                            yield move
        if not include_drops:
            return
        for kind, count in self.hands[color].items():
            if not count:
                continue
            pawn_files = {c for r in range(9) for c in range(9) if self.board[r][c] == color + "P"}
            for r in range(9):
                if self.forced(color, kind, r):
                    continue
                for c in range(9):
                    if self.board[r][c] or (kind == "P" and c in pawn_files):
                        continue
                    move = Move(r, c, drop=kind)
                    if self.legal(color, move):
                        yield move

    def play(self, color, move):
        if self.game_over or move not in self.moves(color):
            return False
        piece, captured = self.push(color, move)
        self.move_count += 1
        self.history.append({"from": [move.sr, move.sc] if not move.drop else None,
                             "to": [move.er, move.ec], "piece": piece,
                             "captured": captured, "promote": move.promote, "drop": bool(move.drop)})
        enemy = opponent(color)
        self.check_log.append((color, self.in_check(enemy)))
        # Check both kings after every move: there is no alternating turn.
        for side in (enemy, color):
            if not next(self.moves(side), None):
                self.game_over, self.winner, self.reason = True, opponent(side), "詰み" if self.in_check(side) else "合法手なし"
                return True
        key = (tuple(tuple(row) for row in self.board),
               tuple(self.hands[s][k] for s in ("w", "b") for k in HAND_KINDS), color)
        occurrences = self.positions.setdefault(key, [])
        occurrences.append(len(self.check_log))
        if len(occurrences) >= 4:
            cycle = self.check_log[occurrences[-4]:]
            checker = next((s for s in ("w", "b") if any(c == s for c, _ in cycle)
                            and all(check for c, check in cycle if c == s)), None)
            self.game_over = True
            self.winner = opponent(checker) if checker else "draw"
            self.reason = "連続王手の千日手" if checker else "千日手（同じ局面が4回）"
        return True

    def choose_ai(self, color, level="normal", exclude=()):
        moves = [m for m in self.moves(color) if m.drop or (m.sr, m.sc) not in exclude]
        if not moves:
            return None
        if level == "weak":
            return random.choice(moves)
        enemy = opponent(color)

        def score(move):
            target = self.board[move.er][move.ec]
            value = 2 * VALUES[target[1:]] if target else 0
            backup = self.push(color, move)
            try:
                kind = self.board[move.er][move.ec][1:]
                if move.promote:
                    value += VALUES[kind] - VALUES[backup[0][1:]]
                if self.attacked(move.er, move.ec, enemy):
                    value -= VALUES[kind] * 1.3
                if self.in_check(enemy):
                    value += 90
                    if not next(self.moves(enemy), None):
                        value += 100000
                value += (8 - move.er if color == "w" else move.er) * 4
                value += (4 - abs(4 - move.ec)) * 2 + random.random() * 15
                if move.drop:
                    value -= 20
                return value
            finally:
                self.pop(color, move, backup)

        ranked = sorted(((score(m), m) for m in moves), key=lambda item: item[0], reverse=True)
        if level == "strong":
            best = []
            for value, move in ranked[:8]:
                backup = self.push(color, move)
                try:
                    replies = list(self.moves(enemy))
                    if not replies:
                        value += 100000
                    else:
                        # One reply: estimate the opponent's strongest legal capture/promotion.
                        threat = max((2 * VALUES[self.board[m.er][m.ec][1:]] if self.board[m.er][m.ec] else 0)
                                     + (250 if m.promote else 0) for m in replies)
                        value -= threat * .7
                    best.append((value, move))
                finally:
                    self.pop(color, move, backup)
            ranked = sorted(best, key=lambda item: item[0], reverse=True)
        return ranked[0][1]
