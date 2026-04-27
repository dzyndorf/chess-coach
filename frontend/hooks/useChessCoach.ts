"use client";

import { useCallback, useMemo, useState } from "react";
import { Chess, Move } from "chess.js";

export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
}

interface CoachPayload {
  fen: string;
  pgn: string;
  user_query: string;
  user_rating: number;
  reasoning_rules: string[];
}

const START_FEN = new Chess().fen();

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function buildPositionsAndMoves(pgn: string) {
  const replay = new Chess();
  replay.loadPgn(pgn);
  const moves = replay.history({ verbose: true }) as Move[];
  const positions: string[] = [new Chess().fen()];
  const tracker = new Chess();
  for (const move of moves) {
    tracker.move(move);
    positions.push(tracker.fen());
  }
  return { moves, positions };
}

export function useChessCoach() {
  const [userRating, setUserRating] = useState(1400);
  const [pgnInput, setPgnInput] = useState("");
  const [loadedPgn, setLoadedPgn] = useState("");
  const [moves, setMoves] = useState<Move[]>([]);
  const [positions, setPositions] = useState<string[]>([START_FEN]);
  const [currentPly, setCurrentPly] = useState(0);
  const [manualFen, setManualFen] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [pendingMessage, setPendingMessage] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [highlightedSquares, setHighlightedSquares] = useState<string[]>([]);

  const currentFen = manualFen ?? positions[currentPly] ?? START_FEN;
  const currentMoveNumber = currentPly;

  const loadPgn = useCallback(() => {
    setError(null);
    try {
      const game = new Chess();
      game.loadPgn(pgnInput.trim());
      const normalizedPgn = game.pgn();
      const { moves: parsedMoves, positions: parsedPositions } = buildPositionsAndMoves(
        normalizedPgn
      );
      setLoadedPgn(normalizedPgn);
      setMoves(parsedMoves);
      setPositions(parsedPositions);
      setCurrentPly(parsedMoves.length);
      setManualFen(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load PGN.");
    }
  }, [pgnInput]);

  const goToPly = useCallback(
    (ply: number) => {
      const clamped = Math.max(0, Math.min(ply, moves.length));
      setCurrentPly(clamped);
      setManualFen(null);
    },
    [moves.length]
  );

  const goStart = useCallback(() => goToPly(0), [goToPly]);
  const goEnd = useCallback(() => goToPly(moves.length), [goToPly, moves.length]);
  const goBack = useCallback(() => goToPly(currentPly - 1), [goToPly, currentPly]);
  const goForward = useCallback(() => goToPly(currentPly + 1), [goToPly, currentPly]);

  const onPieceDrop = useCallback((sourceSquare: string, targetSquare: string) => {
    const game = new Chess(currentFen);
    const move = game.move({
      from: sourceSquare,
      to: targetSquare,
      promotion: "q",
    });
    if (!move) {
      return false;
    }
    setManualFen(game.fen());
    return true;
  }, [currentFen]);

  const extractSquares = useCallback((text: string): string[] => {
    const matches = text.toLowerCase().match(/\b[a-h][1-8]\b/g) ?? [];
    return Array.from(new Set(matches));
  }, []);

  const handleCoachInquiry = useCallback(async () => {
    const trimmed = pendingMessage.trim();
    if (!trimmed || isThinking) return;

    const userMsg: ChatMessage = { id: uid(), role: "user", content: trimmed };
    setChatMessages((prev) => [...prev, userMsg]);
    setPendingMessage("");
    setIsThinking(true);
    setError(null);

    const payload: CoachPayload = {
      fen: currentFen,
      pgn: loadedPgn || pgnInput,
      user_query: trimmed,
      user_rating: userRating || 1400,
      reasoning_rules: [
        "Offer one concrete position-improvement action.",
        "Name one attack target or one defensive vulnerability.",
        "Avoid centipawns, opening theory labels, and deep engine lines.",
        "If a move is bad, explain why in human strategic terms.",
      ],
    };

    try {
      const response = await fetch("/api/coach-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Coach request failed (${response.status}).`);
      }

      const data = (await response.json()) as { reply?: string };
      const assistantText = data.reply ?? "I reviewed the position but got an empty response.";
      setHighlightedSquares(extractSquares(assistantText));
      setChatMessages((prev) => [...prev, { id: uid(), role: "assistant", content: assistantText }]);
    } catch {
      const fallback = `I can see move ${currentMoveNumber} with FEN ${currentFen}. I would re-check tactical threats and king safety before committing.`;
      setHighlightedSquares(extractSquares(fallback));
      setChatMessages((prev) => [...prev, { id: uid(), role: "assistant", content: fallback }]);
      setError("Backend unavailable. Displaying local fallback reply.");
    } finally {
      setIsThinking(false);
    }
  }, [
    pendingMessage,
    isThinking,
    currentFen,
    loadedPgn,
    pgnInput,
    currentMoveNumber,
    userRating,
    extractSquares,
  ]);

  const groupedMoves = useMemo(() => {
    const rows: Array<{ moveNumber: number; white?: Move; black?: Move }> = [];
    for (let i = 0; i < moves.length; i += 2) {
      rows.push({
        moveNumber: Math.floor(i / 2) + 1,
        white: moves[i],
        black: moves[i + 1],
      });
    }
    return rows;
  }, [moves]);

  return {
    userRating,
    setUserRating,
    pgnInput,
    setPgnInput,
    loadedPgn,
    loadPgn,
    moves,
    groupedMoves,
    currentPly,
    currentFen,
    goToPly,
    goStart,
    goEnd,
    goBack,
    goForward,
    onPieceDrop,
    chatMessages,
    pendingMessage,
    setPendingMessage,
    handleCoachInquiry,
    isThinking,
    error,
    highlightedSquares,
  };
}
