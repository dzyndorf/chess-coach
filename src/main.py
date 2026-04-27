from __future__ import annotations

import argparse
import json
from typing import Callable

from langchain_openai import ChatOpenAI

from .agent import build_agent_graph
from .config import OPENAI_API_KEY, OPENAI_MODEL, STOCKFISH_PATH
from .engine_handler import ChessEngine
from .maia_handler import MaiaEngine
from .utils import board_from_input, render_board


def _build_llm() -> ChatOpenAI | None:
    if not OPENAI_API_KEY:
        return None
    return ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0)


def run_coach(*, fen: str | None, pgn: str | None, elo: int) -> dict:
    board, move_history = board_from_input(pgn=pgn, fen=fen)
    llm = _build_llm()
    maia_engine: MaiaEngine | None = None
    try:
        maia_engine = MaiaEngine(target_elo=elo)
    except Exception:
        maia_engine = None
    with ChessEngine(STOCKFISH_PATH) as engine:
        try:
            graph = build_agent_graph(engine=engine, llm=llm, maia_engine=maia_engine)
            final_state = graph.invoke(
                {
                    "input_fen": board.fen(),
                    "user_elo": elo,
                    "board": board,
                    "move_history": move_history,
                }
            )
        finally:
            if maia_engine is not None:
                maia_engine.close()
    return {
        "board": render_board(board),
        "coaching_summary": final_state["coaching_summary"],
        "engine_top_lines": final_state["engine_result"]["top_lines"],
        "maia_top_lines": (final_state.get("maia_result") or {}).get("top_lines", []),
        "maia_vs_stockfish": final_state.get("comparison_result", {}),
    }


def _print_result(result: dict) -> None:
    print("Board:")
    print(result["board"])
    print()
    print("Coaching Summary:")
    print(json.dumps(result["coaching_summary"], indent=2))
    print()
    print("Top Engine Lines:")
    print(json.dumps(result["engine_top_lines"], indent=2))
    if result.get("maia_top_lines"):
        print()
        print("Top Maia Lines:")
        print(json.dumps(result["maia_top_lines"], indent=2))
    if result.get("maia_vs_stockfish"):
        print()
        print("Maia vs Stockfish:")
        print(json.dumps(result["maia_vs_stockfish"], indent=2))


def interactive_session(input_fn: Callable[[str], str] = input) -> None:
    print("Interactive Chess Coach")
    print("Enter your Elo once, then analyze multiple positions.")
    print("Type 'quit' to exit.\n")

    while True:
        elo_raw = input_fn("Elo (e.g. 800, 1400, 2000): ").strip()
        if elo_raw.lower() in {"quit", "exit"}:
            return
        if elo_raw.isdigit():
            elo = int(elo_raw)
            break
        print("Please enter a numeric Elo.\n")

    while True:
        mode = input_fn("Input type [fen/pgn/quit]: ").strip().lower()
        if mode in {"quit", "exit"}:
            return
        if mode not in {"fen", "pgn"}:
            print("Choose 'fen', 'pgn', or 'quit'.\n")
            continue

        raw = input_fn(f"Paste {mode.upper()} string: ").strip()
        if raw.lower() in {"quit", "exit"}:
            return
        if not raw:
            print("Input cannot be empty.\n")
            continue

        fen = raw if mode == "fen" else None
        pgn = raw if mode == "pgn" else None

        try:
            result = run_coach(fen=fen, pgn=pgn, elo=elo)
        except Exception as exc:
            print(f"Error: {exc}\n")
            continue

        print()
        _print_result(result)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Conversational AI Chess Coach")
    parser.add_argument("--elo", type=int, help="Student Elo, e.g. 800/1400/2000")
    parser.add_argument("--fen", type=str, help="FEN string of the position")
    parser.add_argument("--pgn", type=str, help="PGN string of a game")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start a conversational CLI loop for repeated analysis.",
    )
    args = parser.parse_args()

    if args.interactive:
        interactive_session()
        return

    if args.elo is None:
        parser.error("Provide --elo for one-shot mode, or use --interactive.")

    if not args.fen and not args.pgn:
        parser.error("Provide either --fen/--pgn or use --interactive.")

    result = run_coach(fen=args.fen, pgn=args.pgn, elo=args.elo)
    _print_result(result)


if __name__ == "__main__":
    main()
