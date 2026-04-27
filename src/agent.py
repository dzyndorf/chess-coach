from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import chess
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from .config import ENGINE_DEPTH
from .engine_handler import ChessEngine
from .maia_handler import MaiaEngine
from .state_schema import CoachGraphState

COACH_PROMPT = """You are a Grandmaster chess coach.
Translate engine evaluations into practical advice that exactly matches the student's level.

Rules by Elo:
- 800: focus on hanging pieces, simple checks, and castling safety.
- 1400: focus on tactical patterns, basic positional binds, and piece activity.
- 2000: focus on prophylaxis, pawn structure, and strategic imbalances.

Dual-engine coaching rules:
- Compare Stockfish top move vs Maia top move for this student's rating.
- If they match, treat it as "humanly optimal".
- If they differ and Maia eval is significantly worse, mark it as "human trap".
- In "human trap" cases, explain why Maia's move is tempting but flawed.

Return STRICT JSON with keys:
- positives: list of strings
- negatives: list of strings
- plan: list of exactly 3 strings
- maia_insight: short string
Do not include any text outside JSON.
"""


CoachState = CoachGraphState


def _first_move_uci(lines: list[dict[str, Any]]) -> str:
    if not lines:
        return ""
    pv_uci = lines[0].get("pv_uci", "")
    return pv_uci.split()[0] if pv_uci else ""


def _compare_stockfish_vs_maia(state: CoachState) -> dict[str, Any]:
    sf = state.get("engine_result", {})
    maia = state.get("maia_result") or {}
    sf_lines = sf.get("top_lines", [])
    maia_lines = maia.get("top_lines", [])
    sf_move = _first_move_uci(sf_lines)
    maia_move = _first_move_uci(maia_lines)
    sf_cp = int(sf.get("cp", 0))
    maia_cp = int(maia.get("cp", sf_cp))
    cp_gap = sf_cp - maia_cp

    if not maia:
        return {
            "label": "maia_unavailable",
            "stockfish_move": sf_move,
            "maia_move": "",
            "cp_gap": 0,
            "notes": "Maia engine not configured; only Stockfish used.",
        }
    if sf_move and maia_move and sf_move == maia_move:
        return {
            "label": "humanly_optimal",
            "stockfish_move": sf_move,
            "maia_move": maia_move,
            "cp_gap": cp_gap,
            "notes": "Maia and Stockfish agree on the top move.",
        }
    if cp_gap >= 120:
        return {
            "label": "human_trap",
            "stockfish_move": sf_move,
            "maia_move": maia_move,
            "cp_gap": cp_gap,
            "notes": "Maia candidate appears tempting but loses substantial eval.",
        }
    return {
        "label": "playable_human_choice",
        "stockfish_move": sf_move,
        "maia_move": maia_move,
        "cp_gap": cp_gap,
        "notes": "Different move choice but eval gap is not severe.",
    }


def evaluate_position(
    state: CoachState,
    engine: ChessEngine,
    maia_engine: MaiaEngine | None,
) -> CoachState:
    board = state["board"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        sf_future = pool.submit(engine.analyze_top_lines, board, ENGINE_DEPTH, 3)
        maia_future = (
            pool.submit(maia_engine.analyze_top_lines, board, 3) if maia_engine else None
        )
        sf_result = sf_future.result()
        maia_result = maia_future.result() if maia_future else None

    if maia_result and maia_result.get("top_lines"):
        maia_move_uci = _first_move_uci(maia_result["top_lines"])
        maia_result["cp"] = engine.evaluate_move_cp(board, maia_move_uci, depth=max(10, ENGINE_DEPTH - 3))

    next_state: CoachState = {"engine_result": sf_result, "maia_result": maia_result}
    next_state["comparison_result"] = _compare_stockfish_vs_maia(next_state)
    return next_state


def _fallback_summary(state: CoachState) -> dict[str, Any]:
    elo = state.get("user_elo", 1200)
    cp = int(state.get("engine_result", {}).get("cp", 0))
    top_lines = state.get("engine_result", {}).get("top_lines", [])
    comparison = state.get("comparison_result", {})
    maia_label = comparison.get("label", "maia_unavailable")
    maia_note = comparison.get("notes", "No Maia insight.")

    if elo < 1200:
        positives = ["Look for forcing checks to keep the initiative."]
        negatives = ["Scan for hanging pieces before every move."]
        plan = [
            "Count attackers and defenders on loose pieces.",
            "If your king is uncastled, prioritize castling soon.",
            f"Compare your move with engine idea: {top_lines[0]['pv_san'] if top_lines else 'N/A'}.",
        ]
    elif elo < 1800:
        positives = ["Use active piece placement to pressure key squares."]
        negatives = ["Avoid tactical oversights in overloaded positions."]
        plan = [
            "Evaluate candidate tactical motifs (forks, pins, discovered attacks).",
            "Improve your least active piece toward the center.",
            f"Test the top line sequence: {top_lines[0]['pv_san'] if top_lines else 'N/A'}.",
        ]
    else:
        positives = ["Assess long-term imbalances before concrete operations."]
        negatives = ["Watch prophylactic resources for your opponent."]
        plan = [
            "Map pawn-structure breaks for both sides.",
            "Make a prophylactic move that limits counterplay.",
            f"Use the engine line as a strategic benchmark: {top_lines[0]['pv_san'] if top_lines else 'N/A'}.",
        ]

    return {
        "current_evaluation_cp": cp,
        "key_positives": positives,
        "key_negatives": negatives,
        "recommended_3_step_plan": plan[:3],
        "maia_classification": maia_label,
        "maia_insight": maia_note,
    }


def generate_coaching_advice(state: CoachState, llm: BaseChatModel | None) -> CoachState:
    if llm is None:
        return {"coaching_summary": _fallback_summary(state)}

    payload = {
        "elo": state.get("user_elo", 1200),
        "fen": state.get("input_fen", ""),
        "move_history": state.get("move_history", []),
        "engine_result": state.get("engine_result", {}),
        "maia_result": state.get("maia_result", {}),
        "comparison_result": state.get("comparison_result", {}),
    }
    response = llm.invoke([SystemMessage(content=COACH_PROMPT), HumanMessage(content=json.dumps(payload))])
    try:
        parsed = json.loads(str(response.content))
        summary = {
            "current_evaluation_cp": int(state.get("engine_result", {}).get("cp", 0)),
            "key_positives": parsed.get("positives", []),
            "key_negatives": parsed.get("negatives", []),
            "recommended_3_step_plan": parsed.get("plan", [])[:3],
            "maia_classification": state.get("comparison_result", {}).get("label", "unknown"),
            "maia_insight": parsed.get("maia_insight", ""),
        }
    except (json.JSONDecodeError, TypeError, ValueError):
        summary = _fallback_summary(state)
    return {"coaching_summary": summary}


def user_interaction(state: CoachState) -> CoachState:
    return state


def build_agent_graph(
    engine: ChessEngine,
    llm: BaseChatModel | None,
    maia_engine: MaiaEngine | None = None,
):
    graph = StateGraph(CoachState)
    graph.add_node(
        "evaluate_position",
        lambda state: evaluate_position(state, engine, maia_engine),
    )
    graph.add_node("generate_coaching_advice", lambda state: generate_coaching_advice(state, llm))
    graph.add_node("user_interaction", user_interaction)

    graph.add_edge(START, "evaluate_position")
    graph.add_edge("evaluate_position", "generate_coaching_advice")
    graph.add_edge("generate_coaching_advice", "user_interaction")
    graph.add_edge("user_interaction", END)
    return graph.compile()

