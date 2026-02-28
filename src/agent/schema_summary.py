from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from agent.models import ColumnSummary, SchemaSummary
from agent.settings import AppConfig


def _to_python(value: object) -> object:
    if value is None:
        return None
    return value


def _column_profile(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    col: str,
    dtype: str,
    sample_cap: int,
) -> ColumnSummary:
    distinct = conn.execute(
        f"SELECT APPROX_COUNT_DISTINCT({col}) FROM {table}"
    ).fetchone()[0]

    nullable = conn.execute(
        f"SELECT COUNT(*) > COUNT({col}) FROM {table}"
    ).fetchone()[0]

    min_val = None
    max_val = None
    if any(t in dtype.upper() for t in ["INT", "DECIMAL", "DOUBLE", "FLOAT", "DATE", "TIME"]):
        min_val, max_val = conn.execute(
            f"SELECT MIN({col}), MAX({col}) FROM {table}"
        ).fetchone()

    sample_rows = conn.execute(
        f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL LIMIT {sample_cap}"
    ).fetchall()
    sample_values = [_to_python(r[0]) for r in sample_rows]

    return ColumnSummary(
        name=col,
        dtype=dtype,
        nullable=bool(nullable),
        distinct_count_estimate=int(distinct) if distinct is not None else None,
        min_value=_to_python(min_val),
        max_value=_to_python(max_val),
        sample_values=sample_values,
    )


def build_schema_summaries(db_path: Path, app_config: AppConfig) -> list[SchemaSummary]:
    conn = duckdb.connect(str(db_path), read_only=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS __schema_summary (
            table_name VARCHAR PRIMARY KEY,
            summary_json JSON,
            updated_at TIMESTAMP
        )
        """
    )

    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall() if not str(row[0]).startswith("__")]
    report_map = {r.table_name: r for r in app_config.report_models}

    summaries: list[SchemaSummary] = []
    for table in tables:
        row_count = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        describe = conn.execute(f"DESCRIBE {table}").fetchall()
        cols = []

        for idx, (col, dtype, *_rest) in enumerate(describe):
            if idx >= app_config.schema_summary.profile_columns_cap:
                break
            cols.append(
                _column_profile(
                    conn=conn,
                    table=table,
                    col=col,
                    dtype=dtype,
                    sample_cap=app_config.schema_summary.sample_values_cap,
                )
            )

        report = report_map.get(table)
        summary = SchemaSummary(
            table_name=table,
            description=report.description if report else None,
            row_count=row_count,
            key_columns=(report.key_columns or []) if report else [],
            columns=cols,
            join_hints=app_config.join_hints,
            generated_at=datetime.now(UTC),
        )
        summaries.append(summary)

        conn.execute(
            """
            INSERT INTO __schema_summary (table_name, summary_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(table_name) DO UPDATE SET
              summary_json=excluded.summary_json,
              updated_at=excluded.updated_at
            """,
            [summary.table_name, summary.model_dump_json(), summary.generated_at],
        )

    conn.close()
    return summaries


def schema_summaries_to_json_payload(summaries: list[SchemaSummary], app_name: str) -> dict:
    return {
        "app_name": app_name,
        "generated_at": datetime.now(UTC).isoformat(),
        "tables": [json.loads(item.model_dump_json()) for item in summaries],
    }
