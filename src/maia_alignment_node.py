from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

import chess

from .config import MAIA2_DEVICE, MAIA2_MODEL_TYPE, STOCKFISH_PATH
from .engine_handler import ChessEngine
from .state_schema import CoachGraphState

try:
    from maia2 import inference, model
except ImportError:  # pragma: no cover
    inference = None  # type: ignore[assignment]
    model = None  # type: ignore[assignment]


def _score_to_pct(probability: float) -> float:
    return round(float(probability) * 100.0, 2)


class MaiaAlignmentNode:
    """LangGraph-compatible node for Maia-vs-Stockfish move alignment."""

    def __init__(
        self,
        *,
        stockfish_path: str | None = None,
        maia_model_type: str | None = None,
        maia_device: str | None = None,
    ) -> None:
        if model is None or inference is None:
            raise ImportError("maia2 is required for MaiaAlignmentNode. Install with: pip install maia2")
        self.stockfish_path = stockfish_path or STOCKFISH_PATH
        self.maia_model = model.from_pretrained(
            type=maia_model_type or MAIA2_MODEL_TYPE,
            device=maia_device or MAIA2_DEVICE,
        )
        self.inference_helper = inference.prepare()

    def __call__(self, state: CoachGraphState) -> dict[str, Any]:
        fen = state.get("current_fen") or state.get("input_fen") or ""
        user_rating = int(state.get("user_rating") or state.get("user_elo") or 1400)
        if not fen:
            return {"alignment_data": {"error": "Missing FEN in state."}}

        try:
            board = chess.Board(fen)
        except ValueError as exc:
            return {"alignment_data": {"error": f"Invalid FEN: {exc}"}}

        try:
            with ChessEngine(self.stockfish_path) as sf:
                with ThreadPoolExecutor(max_workers=2) as pool:
                    sf_future = pool.submit(sf.analyze_top_lines, board, 18, 1)
                    maia_future = pool.submit(
                        inference.inference_each,
                        self.maia_model,
                        self.inference_helper,
                        board.fen(),
                        user_rating,
                        user_rating,
                    )
                    sf_result = sf_future.result()
                    move_probs, _win_prob = maia_future.result()
        except Exception as exc:  # noqa: BLE001
            return {"alignment_data": {"error": f"Alignment analysis failed: {exc}"}}

        best_move = ""
        if sf_result.get("top_lines"):
            best_move = sf_result["top_lines"][0].get("pv_uci", "").split(" ")[0]

        human_move = ""
        human_prob_pct = 0.0
        if move_probs:
            human_move, human_prob = max(move_probs.items(), key=lambda item: item[1])
            human_prob_pct = _score_to_pct(human_prob)

        alignment_data = {
            "best_move": best_move,
            "human_move": human_move,
            "is_aligned": bool(best_move and human_move and best_move == human_move),
            "human_prob": human_prob_pct,
        }
        return {"alignment_data": alignment_data}
