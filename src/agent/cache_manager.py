from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from agent.models import SyncSnapshot


class CacheManager:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.root / "sync_metadata.json"
        self.summary_file = self.root / "schema_summary.json"

    @property
    def db_path(self) -> Path:
        return self.root / "agent.duckdb"

    def write_snapshot(self, snapshot: SyncSnapshot) -> None:
        self.metadata_file.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")

    def read_snapshot(self) -> SyncSnapshot | None:
        if not self.metadata_file.exists():
            return None
        return SyncSnapshot.model_validate_json(self.metadata_file.read_text(encoding="utf-8"))

    def is_stale(self, stale_after_hours: int) -> bool:
        snap = self.read_snapshot()
        if snap is None:
            return True
        age = datetime.now(UTC) - snap.synced_at
        return age > timedelta(hours=stale_after_hours)

    def write_schema_summary(self, payload: dict) -> None:
        self.summary_file.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    def read_schema_summary(self) -> dict:
        if not self.summary_file.exists():
            return {}
        return json.loads(self.summary_file.read_text(encoding="utf-8"))

    def write_last_answer(self, payload: dict) -> None:
        state_dir = Path(".agent_state")
        state_dir.mkdir(exist_ok=True)
        (state_dir / "last_answer.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    def read_last_answer(self) -> dict | None:
        state_path = Path(".agent_state") / "last_answer.json"
        if not state_path.exists():
            return None
        return json.loads(state_path.read_text(encoding="utf-8"))
