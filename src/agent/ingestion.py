from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from agent.models import SyncSnapshot
from agent.settings import AppConfig


def _sanitize_table_name(name: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in name.lower())
    return safe.strip("_") or "table"


def _hash_schema(conn: duckdb.DuckDBPyConnection, table_name: str) -> str:
    rows = conn.execute(f"DESCRIBE {table_name}").fetchall()
    signature = "|".join(str(row) for row in rows)
    return hashlib.sha256(signature.encode("utf-8")).hexdigest()


def _load_file_into_table(conn: duckdb.DuckDBPyConnection, file_path: Path, table_name: str) -> None:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        conn.execute(
            f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto(?, header=true)",
            [str(file_path)],
        )
    elif suffix == ".json":
        conn.execute(
            f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_json_auto(?)",
            [str(file_path)],
        )
    else:
        raise ValueError(f"Unsupported extracted file type: {file_path}")


def _ingest_extracted_dir(
    extracted: Path,
    conn: duckdb.DuckDBPyConnection,
    app_config: AppConfig,
) -> tuple[dict[str, int], dict[str, str]]:
    row_counts: dict[str, int] = {}
    schema_hashes: dict[str, str] = {}

    configured_table_map = {r.table_name: r for r in app_config.report_models}

    for file_path in sorted(extracted.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in {".csv", ".json"}:
            continue

        raw_name = _sanitize_table_name(file_path.stem)
        table_name = raw_name
        if raw_name in configured_table_map:
            table_name = raw_name

        _load_file_into_table(conn, file_path, table_name)
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        row_counts[table_name] = int(row_count)
        schema_hashes[table_name] = _hash_schema(conn, table_name)

    return row_counts, schema_hashes


def ingest_zip_to_duckdb(zip_path: Path, db_path: Path, app_config: AppConfig, source: str = "bulk_zip") -> SyncSnapshot:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    extracted = db_path.parent / "_extract"
    if extracted.exists():
        shutil.rmtree(extracted)
    extracted.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extracted)

    conn = duckdb.connect(str(db_path), read_only=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS __sync_snapshots (
            synced_at TIMESTAMP,
            app_name VARCHAR,
            source VARCHAR,
            row_counts_json JSON,
            schema_hashes_json JSON
        )
        """
    )

    row_counts, schema_hashes = _ingest_extracted_dir(extracted=extracted, conn=conn, app_config=app_config)

    sync = SyncSnapshot(
        app_name=app_config.app_name,
        synced_at=datetime.now(UTC),
        row_counts=row_counts,
        schema_hashes=schema_hashes,
        source=source,
    )

    conn.execute(
        "INSERT INTO __sync_snapshots VALUES (?, ?, ?, ?, ?)",
        [
            sync.synced_at,
            sync.app_name,
            sync.source,
            sync.row_counts,
            sync.schema_hashes,
        ],
    )
    conn.close()
    return sync


def ingest_multiple_zips_to_duckdb(
    zip_paths: list[Path],
    db_path: Path,
    app_config: AppConfig,
    source: str = "bulk_zip_multi",
) -> SyncSnapshot:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path), read_only=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS __sync_snapshots (
            synced_at TIMESTAMP,
            app_name VARCHAR,
            source VARCHAR,
            row_counts_json JSON,
            schema_hashes_json JSON
        )
        """
    )

    all_rows: dict[str, int] = {}
    all_hashes: dict[str, str] = {}
    base_extract = db_path.parent / "_extract"
    if base_extract.exists():
        shutil.rmtree(base_extract)
    base_extract.mkdir(parents=True, exist_ok=True)

    for idx, zip_path in enumerate(zip_paths):
        step_extract = base_extract / f"zip_{idx}"
        step_extract.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(step_extract)
        rows, hashes = _ingest_extracted_dir(step_extract, conn, app_config)
        all_rows.update(rows)
        all_hashes.update(hashes)

    sync = SyncSnapshot(
        app_name=app_config.app_name,
        synced_at=datetime.now(UTC),
        row_counts=all_rows,
        schema_hashes=all_hashes,
        source=source,
    )
    conn.execute(
        "INSERT INTO __sync_snapshots VALUES (?, ?, ?, ?, ?)",
        [sync.synced_at, sync.app_name, sync.source, sync.row_counts, sync.schema_hashes],
    )
    conn.close()
    return sync


def ingest_report_payloads_to_duckdb(
    report_payloads: dict[str, list[dict]],
    db_path: Path,
    app_config: AppConfig,
    source: str = "zoho_v2_1_data",
) -> SyncSnapshot:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path), read_only=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS __sync_snapshots (
            synced_at TIMESTAMP,
            app_name VARCHAR,
            source VARCHAR,
            row_counts_json JSON,
            schema_hashes_json JSON
        )
        """
    )

    row_counts: dict[str, int] = {}
    schema_hashes: dict[str, str] = {}
    temp_dir = db_path.parent / "_api_extract"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    for report in app_config.report_models:
        rows = report_payloads.get(report.report_link_name, [])
        json_path = temp_dir / f"{report.table_name}.json"
        json_path.write_text(json.dumps(rows), encoding="utf-8")
        _load_file_into_table(conn, json_path, report.table_name)
        row_count = conn.execute(f"SELECT COUNT(*) FROM {report.table_name}").fetchone()[0]
        row_counts[report.table_name] = int(row_count)
        schema_hashes[report.table_name] = _hash_schema(conn, report.table_name)

    sync = SyncSnapshot(
        app_name=app_config.app_name,
        synced_at=datetime.now(UTC),
        row_counts=row_counts,
        schema_hashes=schema_hashes,
        source=source,
    )
    conn.execute(
        "INSERT INTO __sync_snapshots VALUES (?, ?, ?, ?, ?)",
        [sync.synced_at, sync.app_name, sync.source, sync.row_counts, sync.schema_hashes],
    )
    conn.close()
    return sync
