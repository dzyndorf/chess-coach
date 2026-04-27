from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/local/bin/stockfish")
ENGINE_DEPTH = int(os.getenv("ENGINE_DEPTH", "15"))
MAIA2_MODEL_TYPE = os.getenv("MAIA2_MODEL_TYPE", "rapid")
MAIA2_DEVICE = os.getenv("MAIA2_DEVICE", "cpu")
