from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

from .main import run_coach

app = FastAPI(title="Chess Coach API")


class CoachRequest(BaseModel):
    elo: int = Field(..., ge=100, le=3200)
    fen: str | None = None
    pgn: str | None = None

    @model_validator(mode="after")
    def validate_input(self) -> "CoachRequest":
        if not self.fen and not self.pgn:
            raise ValueError("Either fen or pgn must be supplied.")
        return self


@app.post("/coach")
def coach(request: CoachRequest) -> dict:
    try:
        return run_coach(fen=request.fen, pgn=request.pgn, elo=request.elo)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc
