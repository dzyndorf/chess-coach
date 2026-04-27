from __future__ import annotations

from typing import Any

import chess

from .config import MAIA2_DEVICE, MAIA2_MODEL_TYPE

try:
    from maia2 import inference, model
except ImportError:  # pragma: no cover
    inference = None  # type: ignore[assignment]
    model = None  # type: ignore[assignment]


def maia_rating_from_elo(elo: int) -> int:
    """Map user Elo to nearest Maia network bucket (1100..1900)."""
    rounded = int(round(elo / 100.0) * 100)
    return max(1100, min(1900, rounded))


class MaiaEngine:
    """Maia-2 wrapper for rating-conditioned human move probabilities."""

    def __init__(
        self,
        *,
        target_elo: int,
        model_type: str | None = None,
        device: str | None = None,
    ) -> None:
        self.target_elo = maia_rating_from_elo(target_elo)
        if model is None or inference is None:
            raise ImportError("maia2 is not installed. Run: pip install maia2")

        selected_type = model_type or MAIA2_MODEL_TYPE
        selected_device = device or MAIA2_DEVICE
        self.maia_model = model.from_pretrained(type=selected_type, device=selected_device)
        self.inference_helper = inference.prepare()

    def __enter__(self) -> "MaiaEngine":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        # Maia-2 python API does not require explicit process teardown.
        return None

    def analyze_top_lines(self, board: chess.Board, multipv: int = 3) -> dict[str, Any]:
        move_probs, win_prob = inference.inference_each(
            self.maia_model,
            self.inference_helper,
            board.fen(),
            elo_self=self.target_elo,
            elo_oppo=self.target_elo,
        )

        if not move_probs:
            return {"cp": 0, "top_lines": [], "maia_rating": self.target_elo, "win_prob": win_prob}

        top_lines: list[dict[str, Any]] = []
        top_candidates = sorted(move_probs.items(), key=lambda item: item[1], reverse=True)[:multipv]
        for move_uci, probability in top_candidates:
            pv_board = board.copy()
            move = chess.Move.from_uci(move_uci)
            if move not in pv_board.legal_moves:
                continue
            san = pv_board.san(move)
            top_lines.append(
                {
                    "cp": 0,
                    "pv_san": san,
                    "pv_uci": move_uci,
                    "human_probability": float(probability),
                }
            )

        return {
            "cp": 0,
            "top_lines": top_lines,
            "maia_rating": self.target_elo,
            "win_prob": float(win_prob),
        }
