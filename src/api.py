from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .backend_logic import (
    CoachChatRequest,
    CoachRequest,
    CoachToolRequest,
    analyze_position,
    coach_chat,
    coach_tool_action,
)

app = FastAPI(title="Chess Coach API")


@app.post("/coach")
def coach(request: CoachRequest) -> dict:
    try:
        return analyze_position(request)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/coach/chat")
def coach_chat_endpoint(request: CoachChatRequest) -> dict:
    try:
        return coach_chat(request)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/coach/tool")
def coach_tool_endpoint(request: CoachToolRequest) -> dict:
    try:
        return coach_tool_action(request)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc
