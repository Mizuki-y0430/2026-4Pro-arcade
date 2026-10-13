#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UIモジュール: Canvas盤面・アニメーション・クールタイム・AI対局進行。"""

import random
import time
import tkinter as tk
from tkinter import messagebox, ttk

from .constants import (
    PIECE_UNICODE,
    LIGHT_COLOR,
    DARK_COLOR,
    SELECT_COLOR,
    MOVE_COLOR,
    CHECK_COLOR,
    LASTMOVE_COLOR,
    BG_COLOR,
    PANEL_COLOR,
    ACCENT_COLOR,
    SQUARE,
    BOARD_PX,
    AI_PIECE_CD_MS,
    AUTO_NEXT_MS,
)
from .game import ChessGame


def sq_name(r, c):
    return "%s%d" % (chr(ord("a") + c), 8 - r)


class ChessGUI:
    """Canvas盤面 + アニメーション + クールタイム + サイドパネルUI"""

    def __init__(self, root):
        self.game = ChessGame()
        self.root = root
        self.root.title("リアルタイムチェス (AI対戦 / AI同士)")
        self.root.configure(bg=BG_COLOR)
        self.selected = None
        self.legal_cache = []
        self._destroyed = False

        # AI設定
        self.ai_color = "b"
        self.ai_interval = 1000  # ms (1秒に1手)
        self.mode_var = tk.StringVar(value="ai")
        self.ai_running = False
        self.ai_job = None
        self.AI_LEVELS = {"よわい": "weak", "ふつう": "normal", "つよい": "strong"}
        self.ai_level_var = tk.StringVar(value="ふつう")
        self._ai_thinking = False
        self._hover = None
        # スタート後の3カウント
        self._countdown_n = 0
        self._countdown_job = None
        # AI同士の自動対局
        self._aivsai_next = "w"
        self._auto_job = None
        self._match_no = 0
        self.match_score = {"w": 0, "b": 0, "draw": 0}
        # 駒ごとのクールタイム (AI同士用): {(r,c): 解除時刻}
        self.piece_cd = {}

        # アニメーション設定
        self.anim_var = tk.BooleanVar(value=True)
        self.anim_ms = 220
        self._anim = None
        self._anim_job = None
        self.animating = False
        self._anim_hidden = set()

        # クールタイム設定 (ms)
        self.player_cd_var = tk.IntVar(value=500)
        self.cd_until = {"w": 0.0, "b": 0.0}
        self._cd_job = None

        self._build_ui()
        self.draw_board()
        self.refresh_side()
        self._cd_tick()

    # ---------------- UI構築 ----------------
    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG_COLOR)
        header.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(header, text="♞ リアルタイムチェス",
                 font=("", 16, "bold"), bg=BG_COLOR, fg="white").pack(side=tk.LEFT)
        tk.Label(header, text="ターンなし・好きなタイミングで操作",
                 font=("", 10), bg=BG_COLOR, fg="#B0BEC5").pack(side=tk.LEFT, padx=10)

        ctrl = tk.Frame(self.root, bg=BG_COLOR)
        ctrl.pack(fill=tk.X, padx=10, pady=4)
        tk.Radiobutton(ctrl, text="🤖 AI対戦(あなた:白 / 敵陣黒=AI)",
                       variable=self.mode_var, value="ai", font=("", 10),
                       bg=BG_COLOR, fg="white", selectcolor=PANEL_COLOR,
                       activebackground=BG_COLOR, activeforeground="white",
                       command=self.on_mode_change).pack(side=tk.LEFT, padx=4)
        tk.Radiobutton(ctrl, text="⚔️ AI同士(自動対局・Qキーで停止)",
                       variable=self.mode_var, value="aivsai",
                       font=("", 10), bg=BG_COLOR, fg="white",
                       selectcolor=PANEL_COLOR,
                       activebackground=BG_COLOR, activeforeground="white",
                       command=self.on_mode_change).pack(side=tk.LEFT, padx=4)
        self.start_btn = tk.Button(ctrl, text="▶ スタート", font=("", 11, "bold"),
                                   bg=ACCENT_COLOR, fg="white", relief=tk.FLAT,
                                   padx=12, pady=4, command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=8)
        tk.Button(ctrl, text="↺ リセット", font=("", 11), bg="#607D8B", fg="white",
                  relief=tk.FLAT, padx=12, pady=4,
                  command=self.reset).pack(side=tk.LEFT, padx=4)

        opt = tk.Frame(self.root, bg=BG_COLOR)
        opt.pack(fill=tk.X, padx=10, pady=2)
        tk.Checkbutton(opt, text="🎞 駒アニメーション", variable=self.anim_var,
                       font=("", 9), bg=BG_COLOR, fg="white",
                       selectcolor=PANEL_COLOR,
                       activebackground=BG_COLOR,
                       activeforeground="white").pack(side=tk.LEFT, padx=4)
        tk.Label(opt, text="あなたのクールタイム(ms):", font=("", 9),
                 bg=BG_COLOR, fg="white").pack(side=tk.LEFT, padx=(12, 2))
        tk.Scale(opt, from_=0, to=1500, resolution=100, orient=tk.HORIZONTAL,
                 variable=self.player_cd_var, length=140, font=("", 8),
                 bg=BG_COLOR, fg="white", highlightthickness=0).pack(side=tk.LEFT)
        tk.Label(opt, text="AI: 1秒/1手", font=("", 9),
                 bg=BG_COLOR, fg="#B0BEC5").pack(side=tk.LEFT, padx=8)
        tk.Label(opt, text="AIの強さ:", font=("", 9),
                 bg=BG_COLOR, fg="white").pack(side=tk.LEFT, padx=(12, 2))
        tk.OptionMenu(opt, self.ai_level_var,
                      "よわい", "ふつう", "つよい").pack(side=tk.LEFT)
        tk.Label(opt, text="⌨ Qキーで自動対局を停止", font=("", 9),
                 bg=BG_COLOR, fg="#FFCC80").pack(side=tk.LEFT, padx=8)

        main = tk.Frame(self.root, bg=BG_COLOR)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.canvas = tk.Canvas(main, width=BOARD_PX, height=BOARD_PX,
                                highlightthickness=0, bg=LIGHT_COLOR,
                                cursor="hand2")
        self.canvas.pack(side=tk.LEFT)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_hover)
        self.canvas.bind("<Leave>", lambda e: self._set_hover(None))

        side = tk.Frame(main, bg=PANEL_COLOR, width=260)
        side.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))
        side.pack_propagate(False)

        self.status_var = tk.StringVar(value="...")
        tk.Label(side, textvariable=self.status_var, font=("", 11, "bold"),
                 bg=PANEL_COLOR, fg="white", wraplength=240,
                 justify=tk.LEFT).pack(fill=tk.X, padx=8, pady=(8, 2))
        self.match_var = tk.StringVar(value="通算: 白0勝 黒0勝 分け0")
        tk.Label(side, textvariable=self.match_var, font=("", 10, "bold"),
                 bg=PANEL_COLOR, fg="#FFCC80", wraplength=240,
                 justify=tk.LEFT).pack(fill=tk.X, padx=8, pady=(0, 6))

        # クールタイム表示
        cd_frame = tk.Frame(side, bg=PANEL_COLOR)
        cd_frame.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(cd_frame, text="クールタイム", font=("", 10, "bold"),
                 bg=PANEL_COLOR, fg="white").pack(anchor=tk.W)
        self.cd_w_var = tk.StringVar(value="白: OK")
        self.cd_b_var = tk.StringVar(value="黒: OK")
        tk.Label(cd_frame, textvariable=self.cd_w_var, font=("", 9),
                 bg=PANEL_COLOR, fg="#E1F5FE").pack(anchor=tk.W)
        self.cd_w_bar = ttk.Progressbar(cd_frame, length=220, mode="determinate",
                                        maximum=100)
        self.cd_w_bar.pack(fill=tk.X, pady=1)
        tk.Label(cd_frame, textvariable=self.cd_b_var, font=("", 9),
                 bg=PANEL_COLOR, fg="#E1F5FE").pack(anchor=tk.W)
        self.cd_b_bar = ttk.Progressbar(cd_frame, length=220, mode="determinate",
                                        maximum=100)
        self.cd_b_bar.pack(fill=tk.X, pady=1)

        tk.Label(side, text="取った駒", font=("", 10, "bold"),
                 bg=PANEL_COLOR, fg="white").pack(anchor=tk.W, padx=8)
        self.info_var = tk.StringVar(value="")
        tk.Label(side, textvariable=self.info_var, font=("", 12),
                 bg=PANEL_COLOR, fg="#FFECB3", wraplength=240,
                 justify=tk.LEFT).pack(fill=tk.X, padx=8, pady=2)
        self.score_var = tk.StringVar(value="")
        tk.Label(side, textvariable=self.score_var, font=("", 9),
                 bg=PANEL_COLOR, fg="#B0BEC5").pack(anchor=tk.W, padx=8)

        tk.Label(side, text="棋譜", font=("", 10, "bold"),
                 bg=PANEL_COLOR, fg="white").pack(anchor=tk.W, padx=8, pady=(6, 0))
        log_frame = tk.Frame(side, bg=PANEL_COLOR)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.log_list = tk.Listbox(log_frame, font=("", 9), height=14,
                                   bg="#262B33", fg="#ECEFF1",
                                   selectbackground=ACCENT_COLOR)
        sb = tk.Scrollbar(log_frame, command=self.log_list.yview)
        self.log_list.config(yscrollcommand=sb.set)
        self.log_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # 自動対局の停止キー (Q / Esc)
        self.root.bind("<KeyPress>", self._on_key)

    def _on_key(self, event):
        """特定キー(Q/Esc)で自動対局を停止する。"""
        if event.keysym in ("q", "Q", "Escape"):
            if self.ai_running or self._countdown_n > 0:
                self._cancel_countdown()
                self._cancel_auto()
                self.stop_ai()
                try:
                    self.start_btn.config(text="▶ スタート")
                except tk.TclError:
                    pass
                self.refresh_side()

    # ---------------- 座標変換 ----------------
    def _rc_to_xy(self, r, c):
        return (c * SQUARE + SQUARE / 2, r * SQUARE + SQUARE / 2)

    # ---------------- 描画 ----------------
    def draw_board(self, hidden=None, anim_items=None):
        if self._destroyed:
            return
        try:
            cv = self.canvas
            cv.delete("all")
            hidden = hidden or set()
            last = None
            if self.game.history:
                (sr, sc), (er, ec), _, _ = self.game.history[-1]
                last = {(sr, sc), (er, ec)}
            wk = self.game.find_king(self.game.board, "w")
            bk = self.game.find_king(self.game.board, "b")
            w_check = self.game.is_in_check("w")
            b_check = self.game.is_in_check("b")
            for r in range(8):
                for c in range(8):
                    x0, y0 = c * SQUARE, r * SQUARE
                    base = LIGHT_COLOR if (r + c) % 2 == 0 else DARK_COLOR
                    if last and (r, c) in last:
                        fill = LASTMOVE_COLOR
                    else:
                        fill = base
                    if self.selected == (r, c):
                        fill = SELECT_COLOR
                    elif self.selected is not None and (r, c) in self.legal_cache:
                        fill = MOVE_COLOR
                    if w_check and wk == (r, c):
                        fill = CHECK_COLOR
                    if b_check and bk == (r, c):
                        fill = CHECK_COLOR
                    cv.create_rectangle(x0, y0, x0 + SQUARE, y0 + SQUARE,
                                        fill=fill, outline="")
                    # 座標
                    if c == 0:
                        cv.create_text(x0 + 8, y0 + 10, text=str(8 - r),
                                       font=("", 9), fill="#555555")
                    if r == 7:
                        cv.create_text(x0 + SQUARE - 10, y0 + SQUARE - 12,
                                       text=chr(ord("a") + c),
                                       font=("", 9), fill="#555555")
                    # 合法手ドット
                    if (self.selected is not None and (r, c) in self.legal_cache
                            and (r, c) not in hidden):
                        t = self.game.board[r][c]
                        if t is None:
                            cv.create_oval(x0 + SQUARE / 2 - 9, y0 + SQUARE / 2 - 9,
                                           x0 + SQUARE / 2 + 9, y0 + SQUARE / 2 + 9,
                                           fill="#4CAF50", outline="")
                        else:
                            cv.create_rectangle(x0 + 3, y0 + 3,
                                                x0 + SQUARE - 3, y0 + SQUARE - 3,
                                                outline="#4CAF50", width=4)
                    # ホバー枠
                    if (self._hover == (r, c) and self.selected != (r, c)
                            and not self.animating):
                        cv.create_rectangle(x0 + 2, y0 + 2,
                                            x0 + SQUARE - 2, y0 + SQUARE - 2,
                                            outline="#2196F3", width=3)
                    # 駒
                    if (r, c) not in hidden:
                        p = self.game.board[r][c]
                        if p is not None:
                            glyph = PIECE_UNICODE.get(p, "")
                            fg = "#FAFAFA" if p[0] == "w" else "#212121"
                            # 白駒に影を付けて視認性UP
                            cv.create_text(x0 + SQUARE / 2 + 1, y0 + SQUARE / 2 + 2,
                                           text=glyph, font=("Segoe UI Symbol", 44),
                                           fill="black" if p[0] == "w" else "white")
                            cv.create_text(x0 + SQUARE / 2, y0 + SQUARE / 2,
                                           text=glyph, font=("Segoe UI Symbol", 44),
                                           fill=fg)
            # アニメーション中の駒を上書き描画
            if anim_items:
                for glyph, x, y, is_white in anim_items:
                    fg = "#FAFAFA" if is_white else "#212121"
                    cv.create_text(x + 1, y + 2, text=glyph,
                                   font=("Segoe UI Symbol", 44),
                                   fill="black" if is_white else "white")
                    cv.create_text(x, y, text=glyph,
                                   font=("Segoe UI Symbol", 44), fill=fg)
            # 3カウントの数字オーバーレイ
            if self._countdown_n > 0:
                cx, cy = BOARD_PX / 2, BOARD_PX / 2
                cv.create_text(cx + 4, cy + 4, text=str(self._countdown_n),
                               font=("", 120, "bold"), fill="black")
                cv.create_text(cx, cy, text=str(self._countdown_n),
                               font=("", 120, "bold"), fill="#FFEB3B")
                cv.create_text(cx + 2, cy + 92, text="開始まで…",
                               font=("", 24, "bold"), fill="black")
                cv.create_text(cx, cy + 90, text="開始まで…",
                               font=("", 24, "bold"), fill="white")
        except tk.TclError:
            pass

    # ---------------- アニメーション ----------------
    def _cancel_animation(self):
        if self._anim_job is not None:
            try:
                self.root.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None
        self._anim = None
        self.animating = False
        self._anim_hidden = set()

    def _start_animation(self, items, hidden, on_done=None):
        """items: [(glyph, x0,y0,x1,y1, is_white)]"""
        self._cancel_animation()
        if not items:
            if on_done:
                on_done()
            return
        steps = max(6, int(self.anim_ms / 16))
        self._anim = {"items": items, "step": 0, "steps": steps,
                      "on_done": on_done}
        self._anim_hidden = set(hidden)
        self.animating = True
        self._anim_step()

    def _anim_step(self):
        if self._destroyed or self._anim is None:
            return
        try:
            a = self._anim
            a["step"] += 1
            t = min(1.0, a["step"] / a["steps"])
            e = 1 - (1 - t) ** 2  # ease-out
            cur = []
            for glyph, x0, y0, x1, y1, is_white in a["items"]:
                x = x0 + (x1 - x0) * e
                y = y0 + (y1 - y0) * e
                cur.append((glyph, x, y, is_white))
            self.draw_board(hidden=self._anim_hidden, anim_items=cur)
            if a["step"] >= a["steps"]:
                cb = a["on_done"]
                self._anim = None
                self.animating = False
                self._anim_hidden = set()
                self.draw_board()
                self.refresh_side()
                if cb:
                    cb()
            else:
                self._anim_job = self.root.after(16, self._anim_step)
        except tk.TclError:
            pass

    # ---------------- クールタイム ----------------
    def _now(self):
        return time.monotonic()

    def _cd_remain(self, color):
        return max(0.0, self.cd_until.get(color, 0.0) - self._now())

    def _cd_max(self, color):
        if self.is_ai_mode() and color == self.ai_color:
            return self.ai_interval / 1000.0
        return max(0, self.player_cd_var.get()) / 1000.0

    def _set_cd(self, color):
        ms = self.ai_interval if (self.is_ai_mode() and color == self.ai_color) \
            else max(0, self.player_cd_var.get())
        if ms > 0:
            self.cd_until[color] = self._now() + ms / 1000.0

    def _cd_tick(self):
        if self._destroyed:
            return
        try:
            if self.is_aivsai_mode():
                # AI同士用: 駒ごとのCD状況 (冷却中の駒数)
                for color, var, bar in (("w", self.cd_w_var, self.cd_w_bar),
                                        ("b", self.cd_b_var, self.cd_b_bar)):
                    now = self._now()
                    n = sum(1 for r in range(8) for c in range(8)
                            if self.game.board[r][c] is not None
                            and self.game.board[r][c][0] == color
                            and self.piece_cd.get((r, c), 0.0) > now)
                    name = "白" if color == "w" else "黒"
                    if n > 0:
                        var.set("%s冷却中: %d駒" % (name, n))
                        bar["value"] = min(100, n / 16 * 100)
                    else:
                        var.set("%s: OK" % name)
                        bar["value"] = 0
            else:
                for color, var, bar in (("w", self.cd_w_var, self.cd_w_bar),
                                        ("b", self.cd_b_var, self.cd_b_bar)):
                    rem = self._cd_remain(color)
                    mx = self._cd_max(color)
                    name = "白" if color == "w" else "黒"
                    if rem > 0:
                        var.set("%s: ⏳%.1fs" % (name, rem))
                        pct = 0 if mx <= 0 else rem / mx * 100
                        bar["value"] = pct
                    else:
                        var.set("%s: OK" % name)
                        bar["value"] = 0
        except tk.TclError:
            return
        self._cd_job = self.root.after(100, self._cd_tick)

    # ---------------- モード/開始/終了 ----------------
    def is_ai_mode(self):
        return self.mode_var.get() == "ai"

    def is_aivsai_mode(self):
        return self.mode_var.get() == "aivsai"

    def on_mode_change(self):
        self.selected = None
        self.legal_cache = []
        self._cancel_countdown()
        if not self.is_ai_mode():
            self.stop_ai(silent=True)
            self.start_btn.config(text="▶ スタート")
        self.draw_board()
        self.refresh_side()

    def start(self, immediate=False):
        """スタートボタン: 3カウント後に開始。
        - AI対戦: AIループ開始 / AI同士: 自動対局ループ開始(Qキーで停止まで反復)。
        immediate=True でカウントを省略(テスト用)。"""
        if self.is_aivsai_mode():
            if self.ai_running or self._countdown_n > 0:
                # 動作中/カウントダウン中の2度押しで中止
                self._cancel_countdown()
                self._cancel_auto()
                self.stop_ai()
                self.start_btn.config(text="▶ スタート")
                self.refresh_side()
                return
            self._new_match_board()
            if immediate:
                self._start_auto_loop()
            else:
                self._begin_countdown()
                return
        elif self.is_ai_mode():
            if self.game.game_over:
                self.game.reset()
                self.selected = None
                self.legal_cache = []
            if self.ai_running or self._countdown_n > 0:
                # 動作中/カウントダウン中の2度押しで中止
                self._cancel_countdown()
                self.stop_ai()
                self.start_btn.config(text="▶ スタート")
            elif immediate:
                self.ai_running = True
                self.start_btn.config(text="⏸ ストップ")
                self.schedule_ai()
            else:
                self._begin_countdown()
                return
        else:
            return
        self.draw_board()
        self.refresh_side()

    # ---------- AI同士の自動対局 ----------
    def _new_match_board(self):
        """次局の盤面を用意する(手番色を交互に入れ替え)。"""
        self._cancel_auto()
        self.game.reset()
        self.selected = None
        self.legal_cache = []
        self.cd_until = {"w": 0.0, "b": 0.0}
        self.piece_cd = {}
        self._match_no += 1
        self._aivsai_next = "w" if self._match_no % 2 == 1 else "b"
        self._refresh_match()
        self.draw_board()
        self.refresh_side()

    def _start_auto_loop(self):
        """自動対局ループを開始する(初手の駒CDは0〜100%ランダム)。"""
        if self.is_aivsai_mode():
            self._randomize_piece_cd()
        self.ai_running = True
        try:
            self.start_btn.config(text="⏸ ストップ")
        except tk.TclError:
            pass
        self.refresh_side()
        self.schedule_ai()

    def _auto_rematch(self):
        """終局後の自動再戦(Qキー押下まで繰り返す)。"""
        self._auto_job = None
        if self._destroyed or not self.ai_running or not self.is_aivsai_mode():
            return
        self._new_match_board()
        self._start_auto_loop()

    def _cancel_auto(self):
        if self._auto_job is not None:
            try:
                self.root.after_cancel(self._auto_job)
            except Exception:
                pass
            self._auto_job = None

    def _refresh_match(self):
        try:
            self.match_var.set("通算: 白%d勝 黒%d勝 分け%d (第%d局)" % (
                self.match_score["w"], self.match_score["b"],
                self.match_score["draw"], max(1, self._match_no)))
        except tk.TclError:
            pass

    # ---------- 3カウント ----------
    def is_countdown(self):
        return self._countdown_n > 0

    def _begin_countdown(self):
        self._cancel_countdown()
        self.selected = None
        self.legal_cache = []
        self._countdown_n = 3
        try:
            self.start_btn.config(text="⏸ 中止")
        except tk.TclError:
            pass
        self._show_countdown()
        self._countdown_job = self.root.after(1000, self._countdown_tick)

    def _show_countdown(self):
        self.draw_board()
        try:
            self.status_var.set("⏳ 開始まで %d…" % self._countdown_n)
        except tk.TclError:
            pass

    def _countdown_tick(self):
        self._countdown_job = None
        if self._destroyed or self._countdown_n <= 0:
            return
        self._countdown_n -= 1
        if self._countdown_n <= 0:
            self._countdown_n = 0
            self.draw_board()
            if self.is_ai_mode() or self.is_aivsai_mode():
                self._start_auto_loop()
            else:
                self.refresh_side()
        else:
            self._show_countdown()
            self._countdown_job = self.root.after(1000, self._countdown_tick)

    def _cancel_countdown(self):
        if self._countdown_job is not None:
            try:
                self.root.after_cancel(self._countdown_job)
            except Exception:
                pass
            self._countdown_job = None
        self._countdown_n = 0

    def reset(self):
        self.stop_ai(silent=True)
        self._cancel_countdown()
        self._cancel_auto()
        self._cancel_animation()
        self.game.reset()
        self.selected = None
        self.legal_cache = []
        self.cd_until = {"w": 0.0, "b": 0.0}
        self.piece_cd = {}
        self._match_no = 0
        self.match_score = {"w": 0, "b": 0, "draw": 0}
        self._refresh_match()
        if self.is_ai_mode() and self.ai_running:
            self.schedule_ai()
        else:
            self.ai_running = False
            try:
                self.start_btn.config(text="▶ スタート")
            except tk.TclError:
                pass
        self.draw_board()
        self.refresh_side()

    def schedule_ai(self):
        self.cancel_ai_job()
        if self.ai_running and (self.is_ai_mode() or self.is_aivsai_mode()) \
                and not self.game.game_over:
            self.ai_job = self.root.after(self.ai_interval, self.ai_tick)

    def cancel_ai_job(self):
        if self.ai_job is not None:
            try:
                self.root.after_cancel(self.ai_job)
            except Exception:
                pass
            self.ai_job = None

    def stop_ai(self, silent=False):
        self.ai_running = False
        self.cancel_ai_job()
        self._cancel_auto()
        if not silent:
            try:
                self.start_btn.config(text="▶ スタート")
            except tk.TclError:
                pass
            self.refresh_side()

    def ai_tick(self):
        self.ai_job = None
        if not self.ai_running:
            return
        if not (self.is_ai_mode() or self.is_aivsai_mode()):
            return
        if self.game.game_over:
            if self.is_aivsai_mode():
                return  # 自動再戦待ち (_after_move_common が予約済み)
            self.stop_ai()
            return
        if self.animating:
            self.schedule_ai()
            return
        try:
            level = self.AI_LEVELS.get(self.ai_level_var.get(), "normal")
            self._ai_thinking = True
            self.refresh_side()
            try:
                self.root.update_idletasks()
            except tk.TclError:
                pass
            try:
                if self.is_aivsai_mode():
                    # 白黒交互に1手ずつ。駒ごとのCDで動けない駒は候補外。
                    color = self._aivsai_next
                    self._aivsai_next = "b" if color == "w" else "w"
                    mv = self.game.choose_ai_move(
                        color, level=level,
                        exclude=self._cooling_squares())
                    use_piece_cd = True
                else:
                    if self._cd_remain(self.ai_color) > 0:
                        return  # finally側で再スケジュール
                    mv = self.game.choose_ai_move(self.ai_color, level=level)
                    use_piece_cd = False
            finally:
                self._ai_thinking = False
            if mv is not None:
                sr, sc, er, ec, promo = mv
                self._apply_move_with_anim(sr, sc, er, ec, promo,
                                           ai_move=True,
                                           use_piece_cd=use_piece_cd)
                return  # 再スケジュールはアニメ完了コールバック側で行う
        finally:
            if self.ai_running and not self.game.game_over and not self.animating:
                self.schedule_ai()

    # ---------- 駒ごとのクールタイム (AI同士用) ----------
    def _piece_cd_ms(self):
        return max(0, AI_PIECE_CD_MS)

    def _piece_remain(self, r, c):
        until = self.piece_cd.get((r, c), 0.0)
        rem = until - self._now()
        if rem <= 0:
            self.piece_cd.pop((r, c), None)
            return 0.0
        return rem

    def _cooling_squares(self):
        """CD中のマス集合 (期限切れは掃除)。"""
        now = self._now()
        expired = [sq for sq, t in self.piece_cd.items() if t <= now]
        for sq in expired:
            del self.piece_cd[sq]
        return set(self.piece_cd)

    def _set_piece_cd(self, r, c):
        ms = self._piece_cd_ms()
        if ms > 0:
            self.piece_cd[(r, c)] = self._now() + ms / 1000.0

    def _randomize_piece_cd(self):
        """初手の駒CDを0〜100%のランダム残量で開始する。"""
        ms = self._piece_cd_ms()
        now = self._now()
        self.piece_cd = {}
        if ms <= 0:
            return
        for r in range(8):
            for c in range(8):
                if self.game.board[r][c] is not None:
                    self.piece_cd[(r, c)] = now + random.uniform(0, ms) / 1000.0

    def _refresh_selection_after_move(self):
        """指し手後に自分の選択を維持する。

        AI(敵陣)の手で自分の選択駒が取られていなければ選択を解除せず、
        合法手だけ再計算する(ピン等で変化するため)。選択駒自体が
        盤上から消えた(取られた/自分が動かした)場合のみ解除する。
        """
        if self.selected is None:
            self.legal_cache = []
            return
        r0, c0 = self.selected
        if not self.game.in_board(r0, c0) or self.game.board[r0][c0] is None:
            self.selected = None
            self.legal_cache = []
        else:
            self.legal_cache = self.game.get_legal_moves(r0, c0)

    def _after_move_common(self, ai_move=False):
        self._refresh_selection_after_move()
        self.draw_board()
        self.refresh_side()
        if self.game.game_over:
            if self.is_aivsai_mode() and self.ai_running:
                # 通算を記録し、Qキー押下まで自動で次局へ
                w = self.game.winner
                self.match_score[w] = self.match_score.get(w, 0) + 1
                self._refresh_match()
                self.refresh_side()
                self._auto_job = self.root.after(AUTO_NEXT_MS, self._auto_rematch)
                return
            self.stop_ai(silent=True)
            try:
                self.start_btn.config(text="▶ スタート")
            except tk.TclError:
                pass
            # アニメ直後のダイアログが埋もれないよう少し遅延
            try:
                self.root.after(350, self.show_result)
            except tk.TclError:
                pass
        elif ai_move and self.ai_running:
            self.schedule_ai()

    def _apply_move_with_anim(self, sr, sc, er, ec, promo, ai_move=False,
                                use_piece_cd=False):
        moving = self.game.board[sr][sc]
        if moving is None:
            return False
        color = moving[0]
        # キャスリング検出(事前)
        is_castle = (moving[1] == "K" and abs(ec - sc) == 2)
        rook_from = rook_to = None
        if is_castle:
            if ec == 6:
                rook_from, rook_to = (sr, 7), (sr, 5)
            else:
                rook_from, rook_to = (sr, 0), (sr, 3)
        ok = self.game.move(sr, sc, er, ec, promotion=promo)
        if not ok:
            return False
        if use_piece_cd:
            # AI同士用: 駒ごとのCD (移動元は解除・移動先に設定)
            self.piece_cd.pop((sr, sc), None)
            # アンパッサンで取られたポーンの entry も掃除
            self.piece_cd.pop((er + (1 if color == "w" else -1), ec), None)
            self._set_piece_cd(er, ec)
            if is_castle and rook_to is not None:
                self.piece_cd.pop(rook_from, None)
                self._set_piece_cd(*rook_to)
        else:
            self._set_cd(color)
        # 選択の維持/解除は _after_move_common 内の
        # _refresh_selection_after_move が行う(AIの手で自分の選択は消さない)
        if self.anim_var.get():
            x0, y0 = self._rc_to_xy(sr, sc)
            x1, y1 = self._rc_to_xy(er, ec)
            final_piece = self.game.board[er][ec]
            glyph = PIECE_UNICODE.get(final_piece, "")
            items = [(glyph, x0, y0, x1, y1, color == "w")]
            hidden = {(er, ec)}
            if is_castle and rook_from is not None:
                rp = self.game.board[rook_to[0]][rook_to[1]]
                rg = PIECE_UNICODE.get(rp, "")
                rx0, ry0 = self._rc_to_xy(*rook_from)
                rx1, ry1 = self._rc_to_xy(*rook_to)
                items.append((rg, rx0, ry0, rx1, ry1, color == "w"))
                hidden.add(rook_to)
            self.draw_board()
            self.refresh_side()
            self._start_animation(items, hidden,
                                  on_done=lambda: self._after_move_common(ai_move))
        else:
            self._after_move_common(ai_move)
        return True

    def on_closing(self):
        self._destroyed = True
        self.stop_ai(silent=True)
        self._cancel_countdown()
        self._cancel_animation()
        if self._cd_job is not None:
            try:
                self.root.after_cancel(self._cd_job)
            except Exception:
                pass
            self._cd_job = None
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    # ---------------- 入力 ----------------
    def _on_canvas_click(self, event):
        c = int(event.x // SQUARE)
        r = int(event.y // SQUARE)
        if 0 <= r < 8 and 0 <= c < 8:
            self.on_click_square(r, c)

    def _on_hover(self, event):
        c = int(event.x // SQUARE)
        r = int(event.y // SQUARE)
        if 0 <= r < 8 and 0 <= c < 8:
            self._set_hover((r, c))
        else:
            self._set_hover(None)

    def _set_hover(self, pos):
        if self.animating or self._destroyed:
            self._hover = None
            return
        if self._hover == pos:
            return
        self._hover = pos
        self.draw_board()

    def on_click(self, r, c):
        """後方互換: テスト用エイリアス"""
        return self.on_click_square(r, c)

    def on_click_square(self, r, c):
        if self._destroyed or self.game.game_over:
            return
        if self._countdown_n > 0:
            return  # 開始カウント中は操作不可
        if self.is_aivsai_mode():
            return  # AI同士の対局中は人間は操作不可
        if self.animating:
            return
        piece = self.game.board[r][c]
        if self.is_ai_mode():
            if self.selected is None:
                if piece is None or piece[0] != "w":
                    return
            else:
                sr, sc = self.selected
                moving = self.game.board[sr][sc]
                if moving is None or moving[0] != "w":
                    self.selected = None
                    self.legal_cache = []
                    self.draw_board()
                    self.refresh_side()
                    return
                if (r, c) not in self.legal_cache:
                    if piece is not None and piece[0] == "w":
                        self.selected = (r, c)
                        self.legal_cache = self.game.get_legal_moves(r, c)
                        self.draw_board()
                        self.refresh_side()
                        return
                    self.selected = None
                    self.legal_cache = []
                    self.draw_board()
                    self.refresh_side()
                    return
        if self.selected is not None:
            sr, sc = self.selected
            if (r, c) in self.legal_cache:
                moving = self.game.board[sr][sc]
                if moving is None:
                    self.selected = None
                    self.legal_cache = []
                    self.draw_board()
                    self.refresh_side()
                    return
                mover_color = moving[0]
                # クールタイム判定
                rem = self._cd_remain(mover_color)
                if rem > 0:
                    self.status_var.set("⏳ クールタイム中 (%.1fs)" % rem)
                    return
                promo = "Q"
                if moving[1] == "P" and (r == 0 or r == 7):
                    promo = self.ask_promotion(moving[0])
                    if promo is None:
                        return
                ok = self._apply_move_with_anim(sr, sc, r, c, promo)
                if not ok:
                    self.status_var.set("その手は指せません")
                return
            if piece is not None:
                if self.is_ai_mode() and piece[0] != "w":
                    return
                self.selected = (r, c)
                self.legal_cache = self.game.get_legal_moves(r, c)
                self.draw_board()
                self.refresh_side()
                return
            self.selected = None
            self.legal_cache = []
            self.draw_board()
            self.refresh_side()
            return
        else:
            if piece is not None:
                if self.is_ai_mode() and piece[0] != "w":
                    return
                self.selected = (r, c)
                self.legal_cache = self.game.get_legal_moves(r, c)
                self.draw_board()
                self.refresh_side()

    def ask_promotion(self, color):
        result = {"choice": "Q"}
        dlg = tk.Toplevel(self.root)
        dlg.title("プロモーション")
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Label(dlg, text="成る駒を選んでください", font=("", 11)).pack(padx=12, pady=8)
        frm = tk.Frame(dlg)
        frm.pack(padx=12, pady=8)
        choices = [("Q", PIECE_UNICODE[color + "Q"]),
                   ("R", PIECE_UNICODE[color + "R"]),
                   ("B", PIECE_UNICODE[color + "B"]),
                   ("N", PIECE_UNICODE[color + "N"])]
        for kind, glyph in choices:
            b = tk.Button(frm, text=glyph, font=("Segoe UI Symbol", 24), width=3,
                          command=lambda k=kind: (result.__setitem__("choice", k),
                                                  dlg.destroy()))
            b.pack(side=tk.LEFT, padx=4)
        self.root.wait_window(dlg)
        return result["choice"]

    def show_result(self):
        if self._destroyed or not self.game.game_over:
            return
        w = self.game.winner
        try:
            if w == "draw":
                messagebox.showinfo("対局終了", "ステイルメイトで引き分けです")
            elif w == "w":
                messagebox.showinfo("対局終了", "♔ 白の勝ち (チェックメイト)！")
            elif w == "b":
                messagebox.showinfo("対局終了", "♚ 黒の勝ち (チェックメイト)！")
        except tk.TclError:
            pass
        self.refresh_side()

    # ---------------- 状態表示 ----------------
    def refresh(self):
        """後方互換"""
        self.draw_board()
        self.refresh_side()

    def refresh_side(self):
        if self._destroyed:
            return
        try:
            if self.game.game_over:
                if self.game.winner == "draw":
                    end = "引き分け"
                else:
                    if self.is_aivsai_mode() or not self.is_ai_mode():
                        wn = "白" if self.game.winner == "w" else "黒"
                    else:
                        wn = "白(あなた)" if self.game.winner == "w" else "黒(AI)"
                    end = "★ %sの勝ち" % wn
                msg = "%s (手数:%d)" % (end, self.game.move_count)
                if self.is_aivsai_mode() and self.ai_running:
                    msg += " / %d秒後に次局(Qで停止)" % (AUTO_NEXT_MS // 1000)
                self.status_var.set(msg)
            else:
                if self.is_ai_mode():
                    mode_txt = "AI対戦中" if self.ai_running else "AI停止中"
                elif self.is_aivsai_mode():
                    mode_txt = ("AI同士自動対局中(第%d局)" % max(1, self._match_no)
                                if self.ai_running else "AI同士停止中")
                else:
                    mode_txt = "停止中"
                msg = "[%s] 手数:%d" % (mode_txt, self.game.move_count)
                if self._ai_thinking:
                    msg += " / 🤖AI思考中…"
                if self.game.is_in_check("w"):
                    msg += " / ♔白チェック!"
                if self.game.is_in_check("b"):
                    msg += " / ♚黒チェック!"
                if self.selected is not None:
                    p = self.game.board[self.selected[0]][self.selected[1]]
                    if p:
                        msg += " / 選択:%s(維持中)" % PIECE_UNICODE.get(p, p)
                self.status_var.set(msg)
            caps_w, caps_b = [], []
            for _, _, _, cap in self.game.history:
                if cap:
                    glyph = PIECE_UNICODE.get(cap, cap)
                    if cap[0] == "b":
                        caps_w.append(glyph)
                    else:
                        caps_b.append(glyph)
            self.info_var.set("白戦果:%s | 黒戦果:%s" %
                              (" ".join(caps_w) or "-", " ".join(caps_b) or "-"))
            values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}
            sw = sum(values.get(cap[1], 0) for _, _, _, cap in self.game.history
                     if cap and cap[0] == "b")
            sb = sum(values.get(cap[1], 0) for _, _, _, cap in self.game.history
                     if cap and cap[0] == "w")
            self.score_var.set("評価: 白+%d / 黒+%d" % (sw, sb))
            # 棋譜再構築
            self.log_list.delete(0, tk.END)
            for i, ((sr, sc), (er, ec), pc, cap) in enumerate(self.game.history):
                mark = "x" if cap else "-"
                chk = ""
                glyph = PIECE_UNICODE.get(pc, pc)
                self.log_list.insert(tk.END, "%d.%s%s%s%s%s" %
                                     (i + 1, glyph, sq_name(sr, sc), mark,
                                      sq_name(er, ec), chk))
            if self.game.history:
                self.log_list.see(tk.END)
        except tk.TclError:
            pass


def main():
    root = tk.Tk()
    gui = ChessGUI(root)
    root.protocol("WM_DELETE_WINDOW", gui.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
