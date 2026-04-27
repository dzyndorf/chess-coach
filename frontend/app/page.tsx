"use client";

import { useEffect, useState } from "react";
import { Chessboard } from "react-chessboard";
import {
  Bot,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  MessageCircle,
  ScrollText,
  SendHorizontal,
  User,
} from "lucide-react";

import { useChessCoach } from "../hooks/useChessCoach";

type TabKey = "game" | "chat";

export default function ChessCoachPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("game");
  const [boardWidth, setBoardWidth] = useState(520);
  const {
    userRating,
    setUserRating,
    pgnInput,
    setPgnInput,
    loadedPgn,
    loadPgn,
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
  } = useChessCoach();

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        goBack();
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        goForward();
      } else if (event.key === "Home") {
        event.preventDefault();
        goStart();
      } else if (event.key === "End") {
        event.preventDefault();
        goEnd();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [goBack, goForward, goStart, goEnd]);

  useEffect(() => {
    const resize = () => {
      const width = window.innerWidth;
      if (width < 640) setBoardWidth(320);
      else if (width < 1024) setBoardWidth(420);
      else setBoardWidth(520);
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 lg:flex-row">
        <section className="w-full rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4 lg:w-3/5">
          <h1 className="mb-4 text-2xl font-semibold">Chess Coach</h1>
          <div className="flex justify-center">
            <Chessboard
              id="coach-board"
              position={currentFen}
              onPieceDrop={onPieceDrop}
              boardWidth={boardWidth}
              customSquareStyles={Object.fromEntries(
                highlightedSquares.map((sq) => [
                  sq,
                  { boxShadow: "inset 0 0 1px 4px rgba(56, 189, 248, 0.75)" },
                ])
              )}
              customDarkSquareStyle={{ backgroundColor: "#334155" }}
              customLightSquareStyle={{ backgroundColor: "#cbd5e1" }}
            />
          </div>

          <div className="mt-4 grid grid-cols-4 gap-2">
            <button onClick={goStart} className="nav-btn">
              <ChevronsLeft size={16} /> Start
            </button>
            <button onClick={goBack} className="nav-btn">
              <ChevronLeft size={16} /> Back
            </button>
            <button onClick={goForward} className="nav-btn">
              Forward <ChevronRight size={16} />
            </button>
            <button onClick={goEnd} className="nav-btn">
              End <ChevronsRight size={16} />
            </button>
          </div>
          <p className="mt-2 text-xs text-zinc-400">
            Keyboard: Left/Right arrows to navigate, Home/End for start/end.
          </p>
        </section>

        <aside className="w-full rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4 lg:w-2/5">
          <div className="mb-4 flex items-center justify-between">
            <div className="inline-flex rounded-lg bg-zinc-800 p-1">
              <button
                onClick={() => setActiveTab("game")}
                className={`tab-btn ${activeTab === "game" ? "tab-btn-active" : ""}`}
              >
                <ScrollText size={16} />
                Game Info
              </button>
              <button
                onClick={() => setActiveTab("chat")}
                className={`tab-btn ${activeTab === "chat" ? "tab-btn-active" : ""}`}
              >
                <MessageCircle size={16} />
                Coach Chat
              </button>
            </div>
            <select
              value={userRating}
              onChange={(e) => setUserRating(Number(e.target.value))}
              className="rounded-md border border-zinc-700 bg-zinc-900 px-2 py-1 text-sm"
            >
              <option value={800}>800</option>
              <option value={1400}>1400</option>
              <option value={2000}>2000</option>
            </select>
          </div>

          {error ? (
            <div className="mb-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-xs text-amber-200">
              {error}
            </div>
          ) : null}

          {activeTab === "game" ? (
            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm text-zinc-300">Paste PGN</label>
                <textarea
                  value={pgnInput}
                  onChange={(e) => setPgnInput(e.target.value)}
                  rows={6}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-sky-500"
                  placeholder='[Event "Casual"] 1. e4 e5 2. Nf3 Nc6 ...'
                />
                <button onClick={loadPgn} className="mt-2 rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium hover:bg-sky-500">
                  Load PGN
                </button>
              </div>

              <div>
                <h2 className="mb-2 text-sm font-medium text-zinc-300">Move List</h2>
                <div className="max-h-72 overflow-y-auto rounded-lg border border-zinc-800 bg-zinc-950 p-2 text-sm">
                  {groupedMoves.length === 0 ? (
                    <p className="text-zinc-500">Load a PGN to view moves.</p>
                  ) : (
                    groupedMoves.map((row, idx) => {
                      const whitePly = idx * 2 + 1;
                      const blackPly = idx * 2 + 2;
                      return (
                        <div key={row.moveNumber} className="mb-1 flex items-center gap-2">
                          <span className="w-8 text-zinc-500">{row.moveNumber}.</span>
                          <button
                            onClick={() => goToPly(whitePly)}
                            className={`rounded px-2 py-0.5 ${
                              currentPly === whitePly ? "bg-sky-600 text-white" : "hover:bg-zinc-800"
                            }`}
                          >
                            {row.white?.san ?? ""}
                          </button>
                          <button
                            onClick={() => goToPly(blackPly)}
                            className={`rounded px-2 py-0.5 ${
                              currentPly === blackPly ? "bg-sky-600 text-white" : "hover:bg-zinc-800"
                            }`}
                          >
                            {row.black?.san ?? ""}
                          </button>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-2 text-xs text-zinc-400">
                <p>Current FEN:</p>
                <p className="mt-1 break-all font-mono">{currentFen}</p>
                <p className="mt-2 text-zinc-500">Loaded PGN length: {loadedPgn.length} chars</p>
              </div>
            </div>
          ) : (
            <div className="flex h-[36rem] flex-col">
              <div className="flex-1 space-y-2 overflow-y-auto rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                {chatMessages.length === 0 ? (
                  <p className="text-sm text-zinc-500">Ask about this position, plan, or mistakes.</p>
                ) : (
                  chatMessages.map((msg) => (
                    <div key={msg.id} className={`flex items-start gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      {msg.role === "assistant" ? (
                        <div className="mt-1 rounded-full bg-zinc-800 p-1 text-zinc-300">
                          <Bot size={14} />
                        </div>
                      ) : null}
                      <div
                        className={`max-w-[88%] rounded-xl px-3 py-2 text-sm ${
                          msg.role === "user"
                            ? "bg-sky-600 text-white"
                            : "bg-zinc-800 text-zinc-100"
                        }`}
                      >
                        {msg.content}
                      </div>
                      {msg.role === "user" ? (
                        <div className="mt-1 rounded-full bg-sky-600 p-1 text-white">
                          <User size={14} />
                        </div>
                      ) : null}
                    </div>
                  ))
                )}
                {isThinking ? (
                  <div className="rounded-xl bg-zinc-800 px-3 py-2 text-sm text-zinc-300 animate-pulse">
                    Coach is analyzing the position...
                  </div>
                ) : null}
              </div>

              <div className="mt-3 flex gap-2">
                <input
                  value={pendingMessage}
                  onChange={(e) => setPendingMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void handleCoachInquiry();
                    }
                  }}
                  className="flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none focus:border-sky-500"
                  placeholder="Ask the coach about this position..."
                />
                <button
                  onClick={() => void handleCoachInquiry()}
                  disabled={isThinking}
                  className="inline-flex items-center gap-1 rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Send <SendHorizontal size={16} />
                </button>
              </div>
            </div>
          )}
        </aside>
      </div>

      <style jsx global>{`
        .nav-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 0.35rem;
          border-radius: 0.5rem;
          border: 1px solid rgb(63 63 70);
          background: rgb(24 24 27);
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
          transition: all 0.15s ease;
        }
        .nav-btn:hover {
          background: rgb(39 39 42);
        }
        .tab-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          border-radius: 0.45rem;
          padding: 0.4rem 0.7rem;
          font-size: 0.85rem;
          color: rgb(212 212 216);
        }
        .tab-btn-active {
          background: rgb(15 23 42);
          color: white;
        }
      `}</style>
    </main>
  );
}
