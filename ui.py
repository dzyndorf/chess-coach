from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
import chess
import chess.svg

from src.main import run_coach
from src.utils import board_from_input

st.set_page_config(page_title="Chess Coach", page_icon="♟️", layout="wide")


def _card(title: str, body_md: str) -> None:
    st.markdown(
        f"""
<div style="
    border:1px solid #2b2b2b;
    border-radius:12px;
    padding:16px;
    margin-bottom:12px;
    background:#111827;
">
  <h4 style="margin-top:0;">{title}</h4>
  <div>{body_md}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _board_from_user_input(input_type: str, raw_text: str) -> chess.Board:
    if input_type == "FEN":
        return chess.Board(raw_text.strip())
    board, _ = board_from_input(pgn=raw_text.strip(), fen=None)
    return board


def main() -> None:
    st.title("Conversational AI Chess Coach")
    st.caption("Stockfish-backed analysis with Elo-adaptive coaching")

    with st.sidebar:
        st.header("Settings")
        elo = st.selectbox("User Elo", options=[800, 1400, 2000], index=1)
        st.markdown("---")
        st.write("Input mode")
        input_type = st.radio("Position format", options=["FEN", "PGN"], label_visibility="collapsed")

    default_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 2 3"
    default_pgn = '[Event "Casual"] 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5'
    raw_position = st.text_area(
        "Paste a FEN or PGN string",
        value=default_fen if input_type == "FEN" else default_pgn,
        height=150,
    )

    analyze = st.button("Get Coaching Summary", type="primary", use_container_width=True)

    if not analyze:
        return

    if not raw_position.strip():
        st.error("Please enter a valid FEN or PGN string.")
        return

    try:
        board = _board_from_user_input(input_type, raw_position)
        fen = raw_position if input_type == "FEN" else None
        pgn = raw_position if input_type == "PGN" else None
        result = run_coach(fen=fen, pgn=pgn, elo=elo)
    except Exception as exc:
        st.error(f"Failed to analyze position: {exc}")
        return

    left, right = st.columns([1, 1.2], gap="large")

    with left:
        st.subheader("Board")
        svg = chess.svg.board(board=board, size=520)
        components.html(svg, height=540)

    with right:
        st.subheader("Coaching Summary")
        summary = result.get("coaching_summary", {})
        eval_cp = summary.get("current_evaluation_cp", 0)
        positives = summary.get("key_positives", [])
        negatives = summary.get("key_negatives", [])
        plan = summary.get("recommended_3_step_plan", [])
        maia_class = summary.get("maia_classification", "maia_unavailable")
        maia_insight = summary.get("maia_insight", "No Maia insight available.")

        _card("Evaluation", f"**Current Evaluation (cp):** `{eval_cp}`")
        _card("Maia Classification", f"**Type:** `{maia_class}`\n\n{maia_insight}")
        _card(
            "Positives",
            "\n".join(f"- {item}" for item in positives) if positives else "- None detected.",
        )
        _card(
            "Negatives",
            "\n".join(f"- {item}" for item in negatives) if negatives else "- None detected.",
        )
        _card(
            "Recommended 3-Step Plan",
            "\n".join(f"{idx + 1}. {item}" for idx, item in enumerate(plan))
            if plan
            else "1. No plan generated.",
        )

    with st.expander("Show Engine Comparison Details"):
        st.markdown("**Stockfish Top 3**")
        st.json(result.get("engine_top_lines", []))
        st.markdown("**Maia Top 3**")
        st.json(result.get("maia_top_lines", []))
        st.markdown("**Maia vs Stockfish**")
        st.json(result.get("maia_vs_stockfish", {}))


if __name__ == "__main__":
    main()
