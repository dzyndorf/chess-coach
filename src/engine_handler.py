from __future__ import annotations

from pathlib import Path
from typing import Any

import chess
import chess.engine

from .config import PROJECT_ROOT, STOCKFISH_PATH


class ChessEngine:
    """Thin wrapper around a Stockfish UCI process."""

    def __init__(self, engine_path: str | None = None) -> None:
        configured = Path(engine_path or STOCKFISH_PATH)
        if not configured.is_absolute():
            configured = PROJECT_ROOT / configured
        self.engine_path = str(configured)
        self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)

    def __enter__(self) -> "ChessEngine":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        self.engine.quit()

    @staticmethod
    def _score_to_cp(score: chess.engine.PovScore | None) -> int:
        if score is None:
            return 0
        cp = score.white().score(mate_score=100000)
        return int(cp if cp is not None else 0)

    def analyze_top_lines(
        self,
        board: chess.Board,
        depth: int = 15,
        multipv: int = 3,
    ) -> dict[str, Any]:
        """Return a position eval and top principal variations."""
        infos = self.engine.analyse(
            board,
            chess.engine.Limit(depth=depth),
            multipv=multipv,
        )
        if not isinstance(infos, list):
            infos = [infos]

        top_lines: list[dict[str, Any]] = []
        for info in infos[:multipv]:
            pv_moves = info.get("pv", [])
            pv_board = board.copy()
            pv_san: list[str] = []
            for move in pv_moves:
                pv_san.append(pv_board.san(move))
                pv_board.push(move)

            top_lines.append(
                {
                    "cp": self._score_to_cp(info.get("score")),
                    "pv_san": " ".join(pv_san),
                    "pv_uci": " ".join(move.uci() for move in pv_moves),
                }
            )

        return {
            "cp": top_lines[0]["cp"] if top_lines else 0,
            "top_lines": top_lines,
        }

    def evaluate_move_cp(self, board: chess.Board, move_uci: str, depth: int = 12) -> int:
        """Evaluate a specific move by applying it and analyzing resulting position."""
        probe = board.copy()
        try:
            probe.push(chess.Move.from_uci(move_uci))
        except ValueError:
            return 0
        info = self.engine.analyse(probe, chess.engine.Limit(depth=depth))
        return self._score_to_cp(info.get("score"))
