from __future__ import annotations

from src.main import run_coach

SAMPLE_FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 2 3"


def main() -> None:
    result = run_coach(fen=SAMPLE_FEN, pgn=None, elo=1400)
    summary = result["coaching_summary"]

    if not isinstance(summary.get("current_evaluation_cp"), int):
        raise AssertionError("Expected integer centipawn evaluation.")
    if len(summary.get("recommended_3_step_plan", [])) != 3:
        raise AssertionError("Expected exactly 3 recommended steps.")

    print("Board:")
    print(result["board"])
    print("\nCoaching Summary:")
    print(summary)
    print("\nPASS: Coach returned valid summary shape.")


if __name__ == "__main__":
    main()
