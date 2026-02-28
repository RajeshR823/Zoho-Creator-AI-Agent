from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ColumnSummary(BaseModel):
    name: str
    dtype: str
    nullable: bool
    distinct_count_estimate: int | None = None
    min_value: Any | None = None
    max_value: Any | None = None
    sample_values: list[Any] = Field(default_factory=list)


class SchemaSummary(BaseModel):
    table_name: str
    description: str | None = None
    row_count: int
    key_columns: list[str] = Field(default_factory=list)
    columns: list[ColumnSummary] = Field(default_factory=list)
    join_hints: list[str] = Field(default_factory=list)
    generated_at: datetime


class QueryRequest(BaseModel):
    question: str
    max_evidence_rows: int = 30
    conversation_context: list[str] = Field(default_factory=list)


class ValidatedSQL(BaseModel):
    sql: str
    is_safe: bool
    reason: str | None = None


class AgentAnswer(BaseModel):
    question: str
    summary: str
    sql: str
    evidence_rows: list[dict[str, Any]] = Field(default_factory=list)
    evidence_columns: list[str] = Field(default_factory=list)
    generated_at: datetime
    model: str


class SyncSnapshot(BaseModel):
    app_name: str
    synced_at: datetime
    row_counts: dict[str, int]
    schema_hashes: dict[str, str]
    source: str


@dataclass
class AppReport:
    name: str
    report_link_name: str
    table_name: str
    description: str = ""
    key_columns: list[str] | None = None
