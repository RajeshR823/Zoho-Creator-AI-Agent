from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

from agent.cache_manager import CacheManager
from agent.ingestion import ingest_zip_to_duckdb
from agent.models import QueryRequest
from agent.query_engine import QueryEngine
from agent.schema_summary import build_schema_summaries, schema_summaries_to_json_payload
from agent.settings import AppConfig, Settings


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeLLM:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, prompt: str) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            return _FakeResponse("SELECT stage, SUM(amount) AS total_amount FROM deals GROUP BY stage ORDER BY total_amount DESC")
        return _FakeResponse("Top stage is negotiation by total amount in the result sample.")


def _write_zip_with_csv(zip_path: Path) -> None:
    rows = [
        {"id": "1", "stage": "prospect", "amount": "100"},
        {"id": "2", "stage": "negotiation", "amount": "300"},
        {"id": "3", "stage": "negotiation", "amount": "200"},
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["id", "stage", "amount"])
    writer.writeheader()
    writer.writerows(rows)

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("deals.csv", buf.getvalue())


def test_sync_and_ask_end_to_end(tmp_path: Path) -> None:
    zip_path = tmp_path / "export.zip"
    _write_zip_with_csv(zip_path)

    cfg = AppConfig.model_validate(
        {
            "app_name": "test_app",
            "reports": [
                {
                    "name": "Deals",
                    "report_link_name": "All_Deals",
                    "table_name": "deals",
                    "description": "Deals data",
                    "key_columns": ["id"],
                }
            ],
            "allowed_tables": ["deals"],
            "query": {"evidence_row_cap": 5},
        }
    )

    cache = CacheManager(tmp_path / ".cache" / cfg.app_name)
    snapshot = ingest_zip_to_duckdb(zip_path=zip_path, db_path=cache.db_path, app_config=cfg)
    assert snapshot.row_counts["deals"] == 3

    summaries = build_schema_summaries(cache.db_path, cfg)
    summary_payload = schema_summaries_to_json_payload(summaries, cfg.app_name)
    cache.write_schema_summary(summary_payload)

    settings = Settings.model_validate(
        {
            "OPENROUTER_MODEL": "mistralai/mistral-7b-instruct",
            "OPENROUTER_API_KEY": "test",
        }
    )

    engine = QueryEngine(
        settings=settings,
        db_path=cache.db_path,
        schema_summary=summary_payload,
        allowed_tables=cfg.allowed_tables,
        business_definitions=cfg.business_definitions,
        llm=FakeLLM(),
    )

    answer = engine.answer(QueryRequest(question="Which stage has highest total amount?", max_evidence_rows=5))
    assert "SELECT" in answer.sql.upper()
    assert answer.evidence_rows
    assert answer.model == "mistralai/mistral-7b-instruct"
