# KnightAI

> A context-aware AI chess coach that helps players understand how to think through a position, not just receive the engine’s best move.

KnightAI is built around a simple belief:

**The best chess advice is not only correct. It is useful, understandable, and appropriate for the player’s level.**

Most chess engines can tell you the best move. KnightAI is designed to explain the reasoning behind the move in a way that feels closer to a coach than a computer evaluation.

It combines objective engine analysis from **Stockfish**, rating-aware human move prediction from **Maia-2**, and an **LLM reasoning layer** orchestrated with **LangGraph** to translate raw analysis into practical, plain-English coaching.

---

## Why This Project Exists

Modern AI tools are excellent at answer delivery.

In many situations, that is enough. If the goal is to automate a step, speed up a workflow, or solve something you do not care to deeply learn, getting the answer may be all you need.

But chess is different.

If the goal is to improve, build judgment, and get better over time, simply being handed the answer often falls short.

Most chess tools can show:

- The best move
- The engine evaluation
- The top continuation
- Whether a move was a blunder, mistake, or inaccuracy

But players often still need to understand:

- What should I have noticed?
- Why was my move risky?
- What was my opponent threatening?
- How could I find this idea in a real game?
- What should I look for next time?

KnightAI explores the gap between **engine output** and **human learning**.

The goal is to move from:

> “Here is the best move.”

to:

> “Here is how to think through the position.”

---

## Why Context Matters

Good coaching is not just about being correct.

It is about being useful for the person learning.

A beginner and an advanced player should not receive the same explanation for the same position.

For example, if a newer player reaches a Sicilian Defense position, an engine may recommend a sharp theory-heavy continuation. That move may be objectively strong, but it may not be useful coaching if the player is still missing basic threats, hanging pieces, or delaying development.

A good chess coach would adjust the advice.

For a newer player, the coaching may focus on:

- Develop your pieces
- Castle your king
- Avoid hanging material
- Check what your opponent is attacking
- Look for simple checks, captures, and threats

For a stronger player, the same position may lead to deeper discussion around:

- Candidate move comparison
- Positional tradeoffs
- Move-order precision
- Long-term planning
- Subtle advantages
- Engine-preferred moves that are difficult to find

That is the thought behind KnightAI:

**The best answer is not always the best coaching.**

---

## Why Memorization Does Not Scale

Chess improvement is not about memorizing every possible answer.

Memorization can help in the first few opening moves, but the game branches too quickly for memorization to be the main path to improvement.

By move 10, there can already be billions of possible game paths. Even after filtering out obviously bad moves, there are still far too many reasonable-looking options to learn by memorization.

A chess engine can calculate a move that creates an advantage 15 to 20 moves later. The engine may be right, but humans are not chess engines.

The real opportunity to improve is not memorizing what to play.

It is learning:

- What to notice
- What to think about
- Which threats matter
- Which candidate moves are realistic
- Why a natural move may fail
- How to reason through a position under pressure

KnightAI is designed around that learning opportunity.

---

## Meet the Coaching Team

KnightAI is not powered by a single model or a single answer engine.

It combines multiple tools, each playing a different coaching role.

### Stockfish: The Grandmaster Analyst

Stockfish provides the objective chess engine view.

It helps answer:

- What is the strongest move?
- What are the top candidate lines?
- Where does the evaluation shift?
- What tactical or positional opportunity exists?

Stockfish gives KnightAI the objective benchmark for best play.

### Maia-2: The Human Behavior Coach

Maia-2 estimates what a human player at a given rating level is likely to consider.

This matters because effective coaching often starts by understanding the player’s likely thought process.

Maia-2 helps identify moments where:

- The human-likely move is also strong
- The human-likely move is playable but not best
- The human-likely move is a tempting trap
- The engine move is correct but difficult to find

This helps KnightAI meet the player at their actual decision point.

### LLM Reasoning Layer: The Communication Coach

The LLM reasoning layer translates raw analysis into plain-English coaching.

Instead of dumping engine lines or centipawn evaluations, it helps explain:

- What the player should notice
- Why a move works
- Why a tempting move fails
- What concept matters most
- What the player should focus on next
- How the explanation should change based on skill level

This is the layer that turns raw analysis into a coaching conversation.

### LangGraph: The Coaching Coordinator

LangGraph coordinates the workflow between the tools.

It helps organize the steps between:

1. Reading the board position and player rating
2. Running Stockfish analysis
3. Running Maia-2 human-likely move prediction
4. Comparing objective best play against likely human play
5. Generating coaching that fits the player’s level

In simple terms:

**Stockfish** identifies what is best.  
**Maia-2** helps understand what a human might play.  
**The LLM** explains the lesson.  
**LangGraph** coordinates the coaching flow.

That combination allows KnightAI to behave less like a static engine report and more like an interactive coach.

---

## Core Architecture

### 1. Position and Game Context

KnightAI ingests chess context such as:

- `fen`
- `pgn`
- move history
- user rating / Elo
- board state
- analysis metadata

This allows the system to support both single-position analysis and broader game-review workflows.

### 2. Objective Engine Analysis

Stockfish provides the objective engine baseline:

- best move
- top candidate lines
- evaluation shifts
- principal variations
- tactical and positional opportunities

This gives the system a reliable view of best-play reality.

### 3. Human-Likely Move Prediction

Maia-2 provides rating-conditioned move probabilities.

Instead of only asking, “What is objectively best?” KnightAI can also ask:

“What is a player at this level likely to consider?”

This creates the opportunity to distinguish between:

- **Humanly optimal**: Maia-2 and Stockfish align
- **Human trap**: the natural human move is tempting but strategically flawed
- **Playable human choice**: the human-likely move is reasonable but not best

### 4. Coaching Response Generation

The LLM reasoning layer translates the analysis into practical coaching.

The response is designed to avoid:

- centipawn dumps
- computer-jargon tactical walls
- “book says so” explanations
- overly advanced theory for newer players

Instead, KnightAI aims to provide:

- one concrete improvement idea
- one relevant threat, target, or vulnerability
- one human explanation for why a move works or fails
- guidance calibrated to the player’s level

---

## Two Learning Modes

KnightAI is designed around two primary modes.

### Sandbox Mode

Sandbox Mode is for position-based exploration.

Users can:

- load or enter a position
- test ideas
- ask “what should I be thinking about here?”
- compare candidate moves
- get hints before the full answer
- ask follow-up questions
- explore why one move is better than another

This mode is intended to feel like a training environment where the player can pause, explore, and learn through interaction.

### Game Review Mode

Game Review Mode is for reviewing your own games, typically through PGN.

Users can:

- paste a full game
- review critical moments
- identify recurring mistakes
- understand where the game shifted
- learn from blunders, inaccuracies, and missed opportunities
- get coaching tied to real decisions from their own game

This makes the experience more personal and practical because the feedback is grounded in the user’s actual play.

---

## Feature Highlights

### Context-Aware Coaching

- Adapts explanation depth based on rating level
- Keeps beginner feedback focused on practical improvement
- Supports deeper analysis for stronger players
- Avoids overwhelming users with unnecessary theory

### Human-AI Alignment

- Compares Stockfish’s best move with Maia-2’s human-likely move
- Identifies whether a move is humanly optimal, playable, or a tempting trap
- Explains why natural moves may feel right before showing where they fail

### Interactive Coaching Flow

- Supports coaching-style follow-up questions
- Provides plain-English explanation instead of static engine output
- Designed to evolve from one-off analysis into a more stateful coaching experience

### FEN and PGN Support

- Analyze single positions using FEN
- Review games using PGN
- Preserve move history for broader context

---

## Tools & Technologies

### AI Reasoning and Orchestration

- LangGraph
- LangChain integrations
- OpenAI support
- Google Gemini support
- LLM-based reasoning and explanation

### Chess Analysis

- Stockfish
- Maia-2
- python-chess
- FEN / PGN parsing
- SAN and UCI move handling

### Backend and API

- Python
- FastAPI
- Uvicorn
- Pydantic
- python-dotenv

### Prototype / Product Layer

- Streamlit
- GitHub

### Frontend Direction

- Next.js 14
- Tailwind CSS
- Chess.js
- React-Chessboard
- Lucide-react

---

## Why This Architecture

I explored a few different ways to build the coaching experience.

A simple LLM-only approach was the fastest path to a conversational experience, but it created too much risk of generic or overly confident chess advice. For a reasoning-heavy product, the coaching needs to be grounded in actual board analysis, not just language generation.

A Stockfish-only approach provided strong objective analysis, but it felt too much like a traditional chess engine. It could identify the best move, but it did not solve the product problem of explaining the position in a way that matched the player’s skill level.

A static rules-based approach could help with beginner guidance like “develop your pieces” or “check for hanging pieces,” but it would not scale well across different positions, player levels, and follow-up questions.

That is why KnightAI uses a multi-tool architecture:

- **Stockfish** provides objective chess analysis
- **Maia-2** adds rating-aware human move prediction
- **The LLM reasoning layer** turns analysis into plain-English coaching
- **LangGraph** coordinates the workflow across tools and keeps the coaching flow structured

This approach better matches the product goal:

Not just producing the strongest move, but creating a coaching experience that understands the position, considers what a human player is likely to see, adapts to the user’s level, and helps the player build better reasoning over time.

---

## Why LangGraph

LangGraph made sense because KnightAI is not a single-prompt experience.

The system needs a workflow:

1. Read the board position and player rating
2. Run objective engine analysis
3. Run rating-aware human move prediction
4. Compare engine-best play against human-likely play
5. Generate level-appropriate coaching
6. Support follow-up questions and future stateful coaching

LangGraph provides a way to structure that flow as a graph of steps instead of one large prompt.

That matters because KnightAI can grow into a more interactive coach over time, with different paths for Sandbox Mode, Game Review Mode, hints, move comparison, and deeper analysis.

In simple terms, LangGraph helps turn the system from:

> “Ask the model a question.”

into:

> “Coordinate a coaching workflow.”

---

## Future MCP Direction

MCP is an area I’m exploring as a future direction for KnightAI.

The project already depends on multiple tools that could eventually live outside one tightly coupled application:

- Stockfish analysis
- Maia-2 human move prediction
- PGN parsing
- board-state utilities
- game databases
- opening explorers
- puzzle generators
- player history
- study-plan recommendations

MCP could provide a more modular way to expose those capabilities as reusable tools an AI system can call through a standardized interface.

That would make it easier to add or swap capabilities without rebuilding the full coaching workflow.

For example:

- Stockfish as an analysis tool
- Maia-2 as a human-move prediction tool
- PGN parser as a game-ingestion tool
- user history as a personalization tool
- study planner as a recommendation tool

For this project, **LangGraph coordinates the reasoning flow today**, while **MCP points toward a more modular future** where the coach can access a broader ecosystem of tools.

---

## Quickstart

Install dependencies:

```bash
pip install -r requirements.txt
