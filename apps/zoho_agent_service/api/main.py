from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from apps.zoho_agent_service.api.service import AgentService


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    session_id: str = Field(default="default")
    max_rows: int = Field(default=30, ge=1, le=200)


class AskResponse(BaseModel):
    question: str
    summary: str
    sql: str
    evidence_rows: list[dict]
    evidence_columns: list[str]
    generated_at: str
    model: str


class SessionRequest(BaseModel):
    session_id: str = Field(min_length=1)


def create_app() -> FastAPI:
    config_path = Path(os.getenv("APP_CONFIG_PATH", "config/app.yaml"))
    service = AgentService(config_path=config_path)

    app = FastAPI(
        title="Zoho Creator AI Agent API",
        version="0.1.0",
        description="Session-aware Q&A API over synced Zoho Creator data.",
    )

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/status")
    def status() -> dict:
        return service.status()

    @app.post("/chat", response_model=AskResponse)
    def chat(req: AskRequest) -> AskResponse:
        try:
            payload = service.ask(
                question=req.question,
                session_id=req.session_id,
                max_rows=req.max_rows,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return AskResponse.model_validate(payload)

    @app.post("/session/clear")
    def clear_session(req: SessionRequest) -> dict:
        service.clear_session(req.session_id)
        return {"ok": True, "session_id": req.session_id}

    return app


app = create_app()
