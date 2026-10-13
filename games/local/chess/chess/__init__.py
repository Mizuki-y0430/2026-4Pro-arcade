#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""リアルタイムチェス パッケージ。

- constants: 駒絵文字・色・サイズ
- game: 対局ロジック (ChessGame)
- ai: AI思考 (ChessAI)
- gui: UI (ChessGUI) + 起動 main()
"""

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
from .ai import ChessAI
from .game import ChessGame

def __getattr__(name):
    """Web版ではTkinterを読み込まず、Python版の画面は必要時に読み込む。"""
    if name in {"ChessGUI", "sq_name", "main"}:
        from . import gui
        value = getattr(gui, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "PIECE_UNICODE",
    "LIGHT_COLOR",
    "DARK_COLOR",
    "SELECT_COLOR",
    "MOVE_COLOR",
    "CHECK_COLOR",
    "LASTMOVE_COLOR",
    "BG_COLOR",
    "PANEL_COLOR",
    "ACCENT_COLOR",
    "SQUARE",
    "BOARD_PX",
    "AI_PIECE_CD_MS",
    "AUTO_NEXT_MS",
    "ChessAI",
    "ChessGame",
    "ChessGUI",
    "sq_name",
    "main",
]
