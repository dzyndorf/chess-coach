from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st
import streamlit.components.v1 as components
import chess
import chess.pgn
import chess.svg

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


def _init_state() -> None:
    if "sandbox_board" not in st.session_state:
        st.session_state.sandbox_board = chess.Board()
    if "sandbox_moves" not in st.session_state:
        st.session_state.sandbox_moves = []
    if "app_started" not in st.session_state:
        st.session_state.app_started = False
    if "selected_mode" not in st.session_state:
        st.session_state.selected_mode = "Sandbox"
    if "selected_skill" not in st.session_state:
        st.session_state.selected_skill = "Intermediate"
    if "latest_result" not in st.session_state:
        st.session_state.latest_result = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "tool_message" not in st.session_state:
        st.session_state.tool_message = ""


def _sync_sandbox_moves_from_board(board: chess.Board) -> None:
    """Rebuild SAN move list from the board's move stack (source of truth)."""
    replay = chess.Board()
    sans: list[str] = []
    for mv in board.move_stack:
        sans.append(replay.san(mv))
        replay.push(mv)
    st.session_state.sandbox_moves = sans


def _export_pgn(board: chess.Board, *, event: str = "Sandbox") -> str:
    game = chess.pgn.Game()
    game.headers["Event"] = event
    game.headers["Site"] = "Local"
    node = game
    replay = chess.Board()
    for mv in board.move_stack:
        node = node.add_variation(mv)
        replay.push(mv)
    exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
    return game.accept(exporter)


def _origin_squares(board: chess.Board) -> list[str]:
    """Squares with a piece for the side to move that have at least one legal move."""
    side = board.turn
    origins: set[str] = set()
    for mv in board.legal_moves:
        if board.piece_at(mv.from_square) and board.piece_at(mv.from_square).color == side:
            origins.add(chess.square_name(mv.from_square))
    return sorted(origins)


def _destination_squares(board: chess.Board, from_sq: str) -> list[str]:
    if from_sq == "—":
        return []
    try:
        from_i = chess.parse_square(from_sq)
    except ValueError:
        return []
    dests: set[str] = set()
    for mv in board.legal_moves:
        if mv.from_square == from_i:
            dests.add(chess.square_name(mv.to_square))
    return sorted(dests)


def _apply_sandbox_move(move_text: str) -> tuple[bool, str]:
    board: chess.Board = st.session_state.sandbox_board
    cleaned = move_text.strip()
    if not cleaned:
        return False, "Enter a SAN or UCI move."
    try:
        try:
            move = chess.Move.from_uci(cleaned)
            if move not in board.legal_moves:
                raise ValueError("Illegal UCI move in this position.")
            board.push(move)
        except ValueError:
            board.push_san(cleaned)
        _sync_sandbox_moves_from_board(board)
        return True, "Move applied."
    except Exception as exc:  # noqa: BLE001
        return False, f"Could not apply move: {exc}"


def _apply_click_move(board: chess.Board, from_sq: str, to_sq: str, promotion: str) -> tuple[bool, str]:
    if from_sq == "—" or to_sq == "—":
        return False, "Pick both From and To squares."
    try:
        from_i = chess.parse_square(from_sq)
        to_i = chess.parse_square(to_sq)
    except ValueError:
        return False, "Invalid square."

    prom_codes = {"Queen": "q", "Rook": "r", "Bishop": "b", "Knight": "n", "—": None}
    prom_ch = prom_codes.get(promotion)

    candidates = [m for m in board.legal_moves if m.from_square == from_i and m.to_square == to_i]
    if not candidates:
        return False, "That from/to pair is not legal here."
    chosen: chess.Move | None = None
    if len(candidates) == 1:
        chosen = candidates[0]
    else:
        if not prom_ch:
            return False, "This move needs a promotion — pick Queen/Rook/Bishop/Knight."
        promo_map = {"q": chess.QUEEN, "r": chess.ROOK, "b": chess.BISHOP, "n": chess.KNIGHT}
        want = promo_map.get(prom_ch)
        for m in candidates:
            if m.promotion == want:
                chosen = m
                break
        if chosen is None:
            return False, "Promotion choice does not match a legal promotion."

    board.push(chosen)
    _sync_sandbox_moves_from_board(board)
    return True, "Move applied."


def _post_to_backend(api_base_url: str, endpoint: str, payload: dict) -> dict:
    req = Request(
        url=f"{api_base_url}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=60) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def _inject_theme() -> None:
    st.markdown(
        """
<style>
    .stApp {
        background: radial-gradient(circle at top right, #1a2237 0%, #0a0f1b 35%, #070b14 100%);
        color: #e5e7eb;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 1280px !important;
    }
    div[data-testid="column"] {
        background: transparent;
    }
    .gold-title {
        color: #e6c27a;
        letter-spacing: 0.04em;
    }
    .dash-card {
        border: 1px solid rgba(230, 194, 122, 0.28);
        border-radius: 14px;
        padding: 14px;
        background: rgba(17, 24, 39, 0.78);
        min-height: 130px;
    }
    .panel {
        border: 1px solid rgba(230, 194, 122, 0.25);
        border-radius: 14px;
        background: rgba(10, 15, 27, 0.86);
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .title-chip {
        border: 1px solid rgba(230, 194, 122, 0.3);
        border-radius: 10px;
        padding: 10px 12px;
        background: rgba(17, 24, 39, 0.75);
        margin-bottom: 12px;
        font-size: 0.95rem;
    }
    .insight-card {
        border: 1px solid rgba(230, 194, 122, 0.22);
        border-radius: 12px;
        padding: 12px 14px;
        background: rgba(17, 24, 39, 0.65);
        margin-bottom: 10px;
        line-height: 1.45;
    }
    .insight-card b {
        color: #e6c27a;
        display: block;
        margin-bottom: 6px;
    }
    .board-wrap {
        display: flex;
        justify-content: center;
        align-items: flex-start;
        gap: 12px;
        flex-wrap: wrap;
    }
    .tools-stack {
        display: flex;
        flex-direction: column;
        gap: 6px;
        min-width: 110px;
    }
    .section-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        margin: 12px 0 6px 0;
    }
</style>
""",
        unsafe_allow_html=True,
    )


def _render_landing() -> None:
    st.markdown("<h1 class='gold-title'>Decision Dashboard</h1>", unsafe_allow_html=True)
    st.caption("Your journey. Smarter decisions. Stronger chess.")

    st.markdown("### Select Mode")
    mode_cols = st.columns(2, gap="large")
    mode_data = [
        ("Sandbox", "Explore positions, test ideas, and get AI guidance in a distraction-free environment."),
        ("Analyze Input", "Paste FEN/PGN and uncover actionable strategic insights."),
    ]
    for idx, (title, desc) in enumerate(mode_data):
        with mode_cols[idx]:
            st.markdown(
                f"<div class='dash-card'><h3>{title}</h3><p>{desc}</p></div>",
                unsafe_allow_html=True,
            )
            if st.button(
                f"Choose {title}",
                key=f"mode_{title}",
                use_container_width=True,
                type="primary" if st.session_state.selected_mode == title else "secondary",
            ):
                st.session_state.selected_mode = title

    st.markdown("### Your Skill Level")
    skill_map = {
        "Novice": 800,
        "Casual": 1100,
        "Intermediate": 1400,
        "Advanced": 1700,
        "Expert": 2000,
    }
    skill_blurbs = {
        "Novice": "You know the rules and movement, but often miss immediate threats.",
        "Casual": "You hunt for forks and pins. You want to stop blunders.",
        "Intermediate": "You understand coordination and are ready for plans.",
        "Advanced": "You play strategically and want deeper positional play.",
        "Expert": "You study theory and refine nuanced strategic decisions.",
    }
    skill_cols = st.columns(5, gap="small")
    for idx, (label, elo) in enumerate(skill_map.items()):
        with skill_cols[idx]:
            st.markdown(
                f"<div class='dash-card'><h4>{label}</h4><p>{skill_blurbs[label]}</p><p><b>Elo: {elo}</b></p></div>",
                unsafe_allow_html=True,
            )
            if st.button(
                f"Select {label}",
                key=f"skill_{label}",
                use_container_width=True,
                type="primary" if st.session_state.selected_skill == label else "secondary",
            ):
                st.session_state.selected_skill = label

    if st.button("Confirm & Begin Coaching", type="primary", use_container_width=True):
        st.session_state.app_started = True
        st.rerun()


def main() -> None:
    _init_state()
    _inject_theme()

    if not st.session_state.app_started:
        _render_landing()
        return

    st.markdown("<h1 class='gold-title' style='margin-bottom:0.25rem;'>Summit Chess · Coach</h1>", unsafe_allow_html=True)
    st.caption("Decision workspace — board on the right, reasoning on the left.")

    with st.sidebar:
        st.header("Settings")
        default_elo = {
            "Novice": 800,
            "Casual": 1100,
            "Intermediate": 1400,
            "Advanced": 1700,
            "Expert": 2000,
        }.get(st.session_state.selected_skill, 1400)
        elo = st.selectbox("User Elo", options=[800, 1100, 1400, 1700, 2000], index=[800, 1100, 1400, 1700, 2000].index(default_elo))
        api_base_url = st.text_input(
            "Backend URL",
            value="http://127.0.0.1:8000",
            help="FastAPI server base URL",
        ).rstrip("/")
        st.markdown("---")
        ui_mode = st.radio(
            "Mode",
            options=["Sandbox", "Analyze Input"],
            index=0 if st.session_state.selected_mode == "Sandbox" else 1,
        )
        st.write("Input format")
        input_type = st.radio("Position format", options=["FEN", "PGN"], label_visibility="collapsed")
        st.markdown("---")
        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state.app_started = False
            st.rerun()

    default_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 2 3"
    default_pgn = '[Event "Casual"] 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5'

    raw_position = ""
    if ui_mode == "Analyze Input":
        raw_position = st.text_area(
            "Paste a FEN or PGN string",
            value=default_fen if input_type == "FEN" else default_pgn,
            height=130,
        )

    if ui_mode == "Sandbox":
        board = st.session_state.sandbox_board
        fen_for_analysis = board.fen()
        pgn_for_analysis = None
    else:
        if raw_position.strip():
            try:
                board = _board_from_user_input(input_type, raw_position)
            except Exception as exc:
                st.error(f"Failed to parse input: {exc}")
                board = chess.Board()
        else:
            board = chess.Board()
        fen_for_analysis = raw_position if input_type == "FEN" and raw_position.strip() else board.fen()
        pgn_for_analysis = raw_position if input_type == "PGN" and raw_position.strip() else None

    # Top action bar (full width, avoids nested column chaos)
    act1, act2, act3 = st.columns([1, 1, 1], gap="small")
    with act1:
        analyze = st.button("Analyze Position", type="primary", use_container_width=True)
    with act2:
        rewind = st.button(
            "Rewind last move",
            use_container_width=True,
            disabled=(ui_mode != "Sandbox"),
            help="Only available in Sandbox mode.",
        )
        if rewind and ui_mode == "Sandbox" and st.session_state.sandbox_board.move_stack:
            st.session_state.sandbox_board.pop()
            _sync_sandbox_moves_from_board(st.session_state.sandbox_board)
            st.rerun()
    with act3:
        new_pos = st.button(
            "New position",
            use_container_width=True,
            disabled=(ui_mode != "Sandbox"),
            help="Only available in Sandbox mode.",
        )
        if new_pos and ui_mode == "Sandbox":
            st.session_state.sandbox_board = chess.Board()
            st.session_state.sandbox_moves = []
            st.session_state.latest_result = None
            st.session_state.chat_history = []
            st.session_state.tool_message = ""
            st.rerun()

    if analyze:
        payload = {"elo": elo, "fen": fen_for_analysis, "pgn": pgn_for_analysis}
        try:
            st.session_state.latest_result = _post_to_backend(api_base_url, "/coach", payload)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            st.error(f"Backend returned HTTP {exc.code}: {detail or exc.reason}")
        except URLError as exc:
            st.error(
                "Could not connect to backend. Start API with: "
                "`python -m uvicorn src.api:app --reload`"
                f"\n\nDetails: {exc.reason}"
            )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Backend request failed: {exc}")
        else:
            st.rerun()

    result = st.session_state.latest_result
    analysis_notice = "No analysis yet — click **Analyze Position** above."
    if result is not None:
        summary = result.get("coaching_summary", {})
        maia_class = summary.get("maia_classification", "maia_unavailable")
        analysis_notice = f"Alignment: {maia_class} · side to move: {'White' if board.turn else 'Black'}"

    # Single two-column workspace (coach left, board right) — no duplicate rows
    col_coach, col_board = st.columns([0.44, 0.56], gap="large")

    with col_coach:
        st.markdown(
            "<div class='panel'><h3 style='margin:0 0 4px 0;' class='gold-title'>AI Coach</h3>"
            "<p style='margin:0;color:#94a3b8;font-size:0.9rem;'>Your reasoning partner · Active</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"<div class='title-chip'>🧠 <b>Status</b> · {analysis_notice}</div>", unsafe_allow_html=True)

        player_note = st.text_input(
            "Your idea",
            placeholder="I played d4 to control the center and open lines for my pieces.",
            key="player_note_input",
        )

        if result is None:
            st.markdown(
                "<div class='insight-card'><b>Ready</b><br>"
                "Play moves on the right (sandbox), then run analysis. Insight cards appear here after the first analysis.</div>",
                unsafe_allow_html=True,
            )
        else:
            summary = result.get("coaching_summary", {})
            maia_insight = summary.get("maia_insight", "No Maia insight available.")
            plan = summary.get("recommended_3_step_plan", [])
            positives = summary.get("key_positives", [])
            negatives = summary.get("key_negatives", [])

            st.markdown(
                "<div class='insight-card'><b>The Intuition (Validation)</b><br>"
                f"{maia_insight}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='insight-card'><b>The Better Path</b><br>"
                f"{plan[0] if plan else 'Develop your least active piece first.'}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='insight-card'><b>Target / Vulnerability</b><br>"
                f"{positives[0] if positives else 'Look for central control and king safety first.'} "
                f"<br><span style='color:#fca5a5'>{negatives[0] if negatives else ''}</span></div>",
                unsafe_allow_html=True,
            )

        if player_note:
            st.markdown(
                f"<div class='insight-card'><b>Your note</b><br>{player_note}</div>",
                unsafe_allow_html=True,
            )

        st.markdown('<p class="section-label">Coach chat</p>', unsafe_allow_html=True)
        coach_q = st.text_input(
            "Message",
            placeholder="Ask a question or share your thoughts…",
            key="coach_query_text",
            label_visibility="collapsed",
        )
        send_row = st.columns([5, 1], gap="small")
        with send_row[1]:
            send_chat = st.button("Send", use_container_width=True, key="send_chat_btn")
        st.caption("Sends to `/coach/chat` with current FEN, optional PGN, and your rating.")

        if send_chat and coach_q.strip():
            st.session_state.chat_history.append(("You", coach_q.strip()))
            try:
                chat_payload = {
                    "fen": board.fen(),
                    "pgn": pgn_for_analysis,
                    "user_query": coach_q.strip(),
                    "user_rating": elo,
                }
                chat_res = _post_to_backend(api_base_url, "/coach/chat", chat_payload)
                st.session_state.chat_history.append(("Coach", chat_res.get("reply", "")))
            except Exception as exc:  # noqa: BLE001
                st.session_state.chat_history.append(("Coach", f"Chat error: {exc}"))
            st.session_state.coach_query_text = ""
            st.rerun()

        if st.session_state.chat_history:
            with st.container(border=True):
                for who, msg in st.session_state.chat_history[-12:]:
                    st.markdown(f"**{who}:** {msg}")

    with col_board:
        st.markdown('<p class="section-label">Position</p>', unsafe_allow_html=True)
        inner_b, inner_t = st.columns([1, 0.22], gap="small")
        with inner_b:
            arrow = None
            if result and result.get("engine_top_lines"):
                top_uci = result["engine_top_lines"][0].get("pv_uci", "")
                if len(top_uci) >= 4:
                    arrow = [(top_uci[:2], top_uci[2:4])]
            last_mv = board.peek() if board.move_stack else None
            svg = chess.svg.board(
                board=board,
                size=480,
                arrows=arrow or [],
                coordinates=True,
                lastmove=last_mv,
            )
            components.html(svg, height=500)
            st.caption(f"FEN · `{board.fen()[:50]}…`" if len(board.fen()) > 50 else f"FEN · `{board.fen()}`")
            if ui_mode != "Sandbox":
                st.caption("Board follows your FEN/PGN input (read-only). Switch to **Sandbox** in the sidebar to play moves.")

        with inner_t:
            st.markdown("**Tools**")
            for tool_name in ["Analysis", "Themes", "Insights", "Explore", "Review"]:
                if st.button(tool_name, key=f"tool_{tool_name}", use_container_width=True):
                    try:
                        tool_res = _post_to_backend(
                            api_base_url,
                            "/coach/tool",
                            {
                                "fen": board.fen(),
                                "pgn": pgn_for_analysis,
                                "user_rating": elo,
                                "tool": tool_name.lower(),
                            },
                        )
                        st.session_state.tool_message = tool_res.get("message", "")
                    except Exception as exc:  # noqa: BLE001
                        st.session_state.tool_message = f"Tool error: {exc}"
                    st.rerun()
            if st.session_state.tool_message:
                st.info(st.session_state.tool_message)

        if ui_mode == "Sandbox":
            sb = st.session_state.sandbox_board
            st.markdown('<p class="section-label">Play moves (interactive)</p>', unsafe_allow_html=True)
            st.caption(
                "Streamlit cannot drag pieces on the SVG board. Use **From → To** squares (or type SAN/UCI below). "
                "Moves update the PGN live."
            )
            origins = ["—"] + _origin_squares(sb)
            from_sq = st.selectbox("From square", origins, key="interactive_from_sq")
            to_opts = ["—"] + _destination_squares(sb, from_sq)
            to_sq = st.selectbox("To square", to_opts, key="interactive_to_sq")

            from_i = chess.parse_square(from_sq) if from_sq != "—" else None
            to_i = chess.parse_square(to_sq) if to_sq != "—" else None
            promos_needed = (
                from_i is not None
                and to_i is not None
                and len([m for m in sb.legal_moves if m.from_square == from_i and m.to_square == to_i]) > 1
            )
            promotion = "—"
            if promos_needed:
                promotion = st.selectbox(
                    "Promotion",
                    ["—", "Queen", "Rook", "Bishop", "Knight"],
                    key="interactive_promotion",
                )

            ic1, ic2 = st.columns([1, 1], gap="small")
            with ic1:
                if st.button("Apply move", use_container_width=True, type="primary", key="interactive_apply"):
                    ok, msg = _apply_click_move(sb, from_sq, to_sq, promotion)
                    if ok:
                        st.session_state.latest_result = None
                        st.rerun()
                    else:
                        st.error(msg)
            with ic2:
                if st.button("Clear From/To", use_container_width=True, key="interactive_clear"):
                    for _k in ("interactive_from_sq", "interactive_to_sq", "interactive_promotion"):
                        if _k in st.session_state:
                            del st.session_state[_k]
                    st.rerun()

            st.markdown('<p class="section-label">Or type a move</p>', unsafe_allow_html=True)
            c1, c2 = st.columns([2.5, 1], gap="small")
            with c1:
                move_text = st.text_input(
                    "SAN or UCI (e.g. e4, Nf3, e2e4)",
                    placeholder="e4",
                    key="sandbox_move_text",
                    label_visibility="collapsed",
                )
            with c2:
                if st.button("Play typed", use_container_width=True, key="typed_play"):
                    ok, msg = _apply_sandbox_move(move_text)
                    if ok:
                        st.session_state.sandbox_move_text = ""
                        st.session_state.latest_result = None
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown('<p class="section-label">Live game PGN</p>', unsafe_allow_html=True)
            st.code(_export_pgn(sb), language=None)

        st.markdown('<p class="section-label">Move list</p>', unsafe_allow_html=True)
        move_source = (
            st.session_state.sandbox_moves
            if ui_mode == "Sandbox"
            else ([m.uci() for m in board.move_stack] if board.move_stack else [])
        )
        if not move_source:
            st.caption("No moves yet.")
        else:
            rows = []
            for i in range(0, len(move_source), 2):
                white = move_source[i]
                black = move_source[i + 1] if i + 1 < len(move_source) else ""
                rows.append({"#": i // 2 + 1, "White": white, "Black": black})
            st.dataframe(rows, hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
