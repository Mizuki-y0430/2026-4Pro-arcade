#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定数モジュール: 駒の絵文字・盤面の色・サイズ。"""

PIECE_UNICODE = {
    "wK": "♔", "wQ": "♕", "wR": "♖", "wB": "♗", "wN": "♘", "wP": "♙",
    "bK": "♚", "bQ": "♛", "bR": "♜", "bB": "♝", "bN": "♞", "bP": "♟",
}

LIGHT_COLOR = "#F0D9B5"
DARK_COLOR = "#B58863"
SELECT_COLOR = "#6FBF73"
MOVE_COLOR = "#F7F769"
CHECK_COLOR = "#E85454"
LASTMOVE_COLOR = "#F6F082"
BG_COLOR = "#2B2F36"
PANEL_COLOR = "#3A4048"
ACCENT_COLOR = "#4CAF50"

SQUARE = 80
BOARD_PX = SQUARE * 8

# AI同士の対局における駒ごとのクールタイム (ms)。
# 1手動かした駒はこの時間だけ再移動できない。初手は0〜100%のランダム残量で開始。
AI_PIECE_CD_MS = 2000
# 自動対局の終局〜次局までの待機時間 (ms)
AUTO_NEXT_MS = 3000
