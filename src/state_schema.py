from __future__ import annotations

from typing import Any, TypedDict

import chess


class AlignmentData(TypedDict, total=False):
    best_move: str
    human_move: str
    is_aligned: bool
    human_prob: float
    error: str


class CoachGraphState(TypedDict, total=False):
    current_fen: str
    user_rating: int
    input_fen: str
    user_elo: int
    board: chess.Board
    move_history: list[str]
    engine_result: dict[str, Any]
    maia_result: dict[str, Any] | None
    comparison_result: dict[str, Any] | None
    coaching_summary: dict[str, Any]
    alignment_data: AlignmentData
