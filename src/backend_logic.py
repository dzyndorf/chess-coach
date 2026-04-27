from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, model_validator

from langchain_core.messages import HumanMessage, SystemMessage

from .llm_factory import build_chat_llm
from .main import run_coach


class CoachRequest(BaseModel):
    elo: int = Field(..., ge=100, le=3200)
    fen: str | None = None
    pgn: str | None = None

    @model_validator(mode="after")
    def validate_input(self) -> "CoachRequest":
        if not self.fen and not self.pgn:
            raise ValueError("Either fen or pgn must be supplied.")
        return self


class CoachChatRequest(BaseModel):
    fen: str
    pgn: str | None = None
    user_query: str = Field(..., min_length=1)
    user_rating: int = Field(1400, ge=100, le=3200)


class CoachToolRequest(BaseModel):
    fen: str
    pgn: str | None = None
    user_rating: int = Field(1400, ge=100, le=3200)
    tool: str = Field(..., min_length=1)


def analyze_position(request: CoachRequest) -> dict[str, Any]:
    return run_coach(fen=request.fen, pgn=request.pgn, elo=request.elo)


def _fallback_chat_response(request: CoachChatRequest, quick_summary: dict[str, Any]) -> str:
    positives = quick_summary.get("key_positives", [])
    negatives = quick_summary.get("key_negatives", [])
    plan = quick_summary.get("recommended_3_step_plan", [])
    return (
        f"Plan focus: {plan[0] if plan else 'Improve your least active piece and king safety first.'}\n"
        f"Target idea: {positives[0] if positives else 'Pressure central squares and weak pawns.'}\n"
        f"Risk check: {negatives[0] if negatives else 'Avoid drifting into tactical shots around your king.'}"
    )


def coach_chat(request: CoachChatRequest) -> dict[str, str]:
    quick = run_coach(fen=request.fen, pgn=request.pgn, elo=request.user_rating)
    summary = quick.get("coaching_summary", {})
    llm = build_chat_llm()
    if llm is None:
        return {"reply": _fallback_chat_response(request, summary)}

    prompt = {
        "user_query": request.user_query,
        "fen": request.fen,
        "pgn": request.pgn or "",
        "user_rating": request.user_rating,
        "summary": summary,
        "policy": {
            "focus": "One concrete improvement + one target/vulnerability",
            "style": "Plain terms only, no centipawns, no deep engine lines",
            "bad_move_logic": "Explain why tempting moves fail strategically",
        },
    }
    system = (
        "You are a strategic chess coach. Respond in plain human language. "
        "Always provide one concrete improvement action and one attacking/defensive theme."
    )
    response = llm.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(content=json.dumps(prompt)),
        ]
    )
    text = response.content if isinstance(response.content, str) else str(response.content)
    return {"reply": text}


def coach_tool_action(request: CoachToolRequest) -> dict[str, str]:
    data = run_coach(fen=request.fen, pgn=request.pgn, elo=request.user_rating)
    summary = data.get("coaching_summary", {})
    positives = summary.get("key_positives", [])
    negatives = summary.get("key_negatives", [])
    plan = summary.get("recommended_3_step_plan", [])
    tool = request.tool.lower()

    if tool == "analysis":
        message = f"Position snapshot: {summary.get('maia_insight', 'No Maia insight available.')}."
    elif tool == "themes":
        message = positives[0] if positives else "Theme: improve piece activity and central control."
    elif tool == "insights":
        message = negatives[0] if negatives else "Insight: avoid creating new weaknesses while attacking."
    elif tool == "explore":
        message = plan[1] if len(plan) > 1 else "Explore candidate moves that improve your worst piece."
    elif tool == "review":
        message = plan[2] if len(plan) > 2 else "Review whether your last move improved king safety and coordination."
    else:
        message = "Unknown tool. Choose analysis, themes, insights, explore, or review."
    return {"message": message}
