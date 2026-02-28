from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from threading import Lock

from agent.cache_manager import CacheManager
from agent.models import QueryRequest
from agent.query_engine import QueryEngine
from agent.settings import load_app_config, load_settings


class AgentService:
    """Thin service wrapper that provides session-aware question answering."""

    def __init__(self, config_path: Path, context_window: int = 6) -> None:
        self.settings = load_settings()
        self.app_config = load_app_config(config_path)
        self.cache = CacheManager(Path(".cache") / self.app_config.app_name)
        self.context_window = context_window
        self._sessions: dict[str, deque[str]] = defaultdict(lambda: deque(maxlen=self.context_window))
        self._lock = Lock()

    def _build_engine(self) -> QueryEngine:
        if not self.cache.db_path.exists():
            raise RuntimeError("No local DuckDB found. Run sync first.")
        schema_summary = self.cache.read_schema_summary()
        return QueryEngine(
            settings=self.settings,
            db_path=self.cache.db_path,
            schema_summary=schema_summary,
            allowed_tables=self.app_config.allowed_tables,
            business_definitions=self.app_config.business_definitions,
        )

    def ask(self, question: str, session_id: str | None = None, max_rows: int = 30) -> dict:
        sid = session_id or "default"
        with self._lock:
            history = list(self._sessions[sid])

        engine = self._build_engine()
        answer = engine.answer(
            QueryRequest(
                question=question,
                max_evidence_rows=max_rows,
                conversation_context=history,
            )
        )
        payload = answer.model_dump(mode="json")
        self.cache.write_last_answer(payload)

        with self._lock:
            self._sessions[sid].append(f"User: {question}")
            summary_line = answer.summary.splitlines()[0] if answer.summary else ""
            self._sessions[sid].append(f"Assistant: {summary_line}")

        return payload

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def status(self) -> dict:
        snap = self.cache.read_snapshot()
        if not snap:
            return {
                "ready": False,
                "message": "No sync metadata found. Run sync first.",
            }
        return {
            "ready": True,
            "app_name": snap.app_name,
            "synced_at": str(snap.synced_at),
            "source": snap.source,
            "tables": sorted(snap.row_counts.keys()),
            "row_counts": snap.row_counts,
        }
