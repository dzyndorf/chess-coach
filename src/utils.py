from __future__ import annotations

import io

import chess
import chess.pgn


def board_from_input(*, pgn: str | None = None, fen: str | None = None) -> tuple[chess.Board, list[str]]:
    """Build a board from either a PGN or FEN string and return SAN move history."""
    if pgn and pgn.strip():
        game = chess.pgn.read_game(io.StringIO(pgn))
        if game is None:
            raise ValueError("Could not parse PGN input.")
        board = game.board()
        move_history: list[str] = []
        for move in game.mainline_moves():
            move_history.append(board.san(move))
            board.push(move)
        return board, move_history

    if fen and fen.strip():
        return chess.Board(fen), []

    return chess.Board(), []


def render_board(board: chess.Board) -> str:
    """Return an ASCII board formatted for CLI output."""
    return str(board)
