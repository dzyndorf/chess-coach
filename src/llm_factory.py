from __future__ import annotations

from typing import TYPE_CHECKING

from .config import (
    GOOGLE_API_KEY,
    GOOGLE_GENAI_MODEL,
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel


def build_chat_llm() -> "BaseChatModel | None":
    """
    Return a LangChain chat model.

    ``LLM_PROVIDER``: unset / empty = auto (prefer Gemini if ``GOOGLE_API_KEY``, else OpenAI).
    ``gemini`` / ``google`` → Gemini only when ``GOOGLE_API_KEY`` is set.
    ``openai`` → OpenAI only when ``OPENAI_API_KEY`` is set.
    """
    provider = (LLM_PROVIDER or "").strip().lower()

    def _openai() -> "BaseChatModel | None":
        if not OPENAI_API_KEY:
            return None
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0)

    def _gemini(*, strict: bool) -> "BaseChatModel | None":
        if not GOOGLE_API_KEY:
            return None
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            if strict:
                raise ImportError(
                    "Gemini requires `langchain-google-genai`. Run: pip install langchain-google-genai"
                ) from exc
            return None
        return ChatGoogleGenerativeAI(
            model=GOOGLE_GENAI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0,
        )

    if provider == "openai":
        return _openai()
    if provider in {"gemini", "google"}:
        return _gemini(strict=True)

    # Auto
    g = _gemini(strict=False)
    if g is not None:
        return g
    return _openai()
