#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""リアルタイムチェス ランチャー。

実装は役割別に `chess` パッケージへ分割:
- chess.constants: 駒絵文字・色・サイズ
- chess.game: 対局ロジック (ChessGame)
- chess.ai: AI思考 (ChessAI)
- chess.gui: UI (ChessGUI) + 起動 main()

実行: python chess.py / python -m chess
"""

from chess import ChessAI, ChessGame, ChessGUI, main, sq_name

__all__ = ["ChessAI", "ChessGame", "ChessGUI", "main", "sq_name"]

if __name__ == "__main__":
    main()
