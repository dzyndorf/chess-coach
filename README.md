# Reasoning-Chess

> A LangGraph-powered Chess Coach that prioritizes human-style reasoning over raw engine evaluations.

Reasoning-Chess is built around a core belief: **the best chess advice is not only correct, but findable**.  
Instead of dumping engine lines, it aligns objective strength (Stockfish) with realistic player behavior (Maia-2) and translates that into practical, plain-English coaching.

---

## Why This Project Exists

Most chess tools optimize for absolute truth. Real players need something else:

- Advice they can actually execute in a real game.
- Explanations that sound like a coach, not a compiler.
- Guidance calibrated to rating-level thinking patterns.

Reasoning-Chess introduces **Human-AI Alignment in Chess**:
- **Stockfish** gives best-play reality.
- **Maia-2** predicts human-likely choices at rating context.
- **LLM Reasoning Layer** bridges the gap into strategic, understandable instruction.

---

## Core Architecture

### 1) The Reasoning Layer

The Reasoning Layer is the central intelligence bridge:

- Ingests board context (`fen`, `pgn`, move history, user rating).
- Compares **Stockfish best continuation** vs **Maia-2 likely move**.
- Produces actionable coaching that explains:
  - what improves the position now,
  - what target or vulnerability matters most,
  - why tempting human moves can fail.

This allows the system to distinguish between:
- **Humanly optimal**: Maia and Stockfish align.
- **Human trap**: Maia-favored move is understandable but strategically flawed.

### 2) Maia-2 Integration

Maia-2 provides rating-conditioned move probabilities (for example, the 1400 context):

- Predicts what a player at that strength is likely to consider.
- Surfaces "findable" plans, not just machine-perfect ones.
- Enables coaching that addresses *why a natural move feels right* before correcting it.

This improves learning quality by meeting players at their actual decision frontier.

### 3) Plain-English Coaching

Reasoning-Chess enforces a strict communication style:

- No centipawn dumps.
- No computer-jargon tactical walls.
- No "book says so" framing.

Every response aims to include:
- one concrete positional improvement,
- one attacking target or defensive weakness,
- one human explanation for risky ideas.

---

## Feature Highlights

### Stateful Analysis (LangGraph)

- Tracks board state, move history, user rating, and analysis metadata.
- Supports full-game context instead of one-off snapshots.
- Maintains coherent coaching progression across multiple inquiries.

### Dynamic Frontend Experience

- Next.js + Tailwind dark-mode interface.
- Responsive board experience with `react-chessboard`.
- Chat-first coaching flow designed for iterative exploration.
- Square-awareness hooks for highlighting referenced targets.

### Rating-Aware Logic

- Complexity and vocabulary adapt by Elo bands.
- Supports instructional depth from foundational habits to higher-order planning.
- Keeps feedback realistic to what the user can identify in practical play.

---

## Technical Stack

### Backend

- Python
- LangGraph
- Maia-2
- Stockfish
- FastAPI

### Frontend

- Next.js 14 (App Router)
- Tailwind CSS
- Chess.js
- React-Chessboard
- Lucide-react

---

## Quickstart

Install:

```bash
pip install -r requirements.txt
```

Create `.env`:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
STOCKFISH_PATH=/usr/local/bin/stockfish
ENGINE_DEPTH=15
MAIA2_MODEL_TYPE=rapid
MAIA2_DEVICE=cpu
```

Run CLI:

```bash
python -m src.main --interactive
```

Run API:

```bash
python -m uvicorn src.api:app --reload
```

---

## Example API Request

```bash
curl -X POST http://127.0.0.1:8000/coach \
  -H "Content-Type: application/json" \
  -d "{\"elo\": 1400, \"fen\": \"r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 2 3\"}"
```

---

## Project Identity

- **Suggested Name**: `Reasoning-Chess`  
- **Alternative Brand Name**: `Grandmaster.ai`  
- **Tagline**: *A LangGraph-powered Chess Coach that prioritizes human-style reasoning over raw engine evaluations.*
