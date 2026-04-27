from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# Gemini (Google AI Studio / Vertex-style key via LANGCHAIN): use GOOGLE_API_KEY or GEMINI_API_KEY
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
# Default to Gemini 1.5 Flash; override with e.g. gemini-1.5-pro
GOOGLE_GENAI_MODEL = os.getenv("GOOGLE_GENAI_MODEL", "gemini-1.5-flash")
# gemini | openai — when unset, Gemini is used if GOOGLE_API_KEY is set, else OpenAI if OPENAI_API_KEY is set
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/local/bin/stockfish")
ENGINE_DEPTH = int(os.getenv("ENGINE_DEPTH", "15"))
MAIA2_MODEL_TYPE = os.getenv("MAIA2_MODEL_TYPE", "rapid")
MAIA2_DEVICE = os.getenv("MAIA2_DEVICE", "cpu")
