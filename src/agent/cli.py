from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from agent.cache_manager import CacheManager
from agent.ingestion import ingest_multiple_zips_to_duckdb, ingest_report_payloads_to_duckdb, ingest_zip_to_duckdb
from agent.models import QueryRequest
from agent.query_engine import QueryEngine
from agent.schema_summary import build_schema_summaries, schema_summaries_to_json_payload
from agent.settings import load_app_config, load_settings
from agent.zoho_client import ZohoConfigError, ZohoCreatorClient

app = typer.Typer(help="Zoho Creator terminal AI agent")
console = Console()


def _default_config_payload(app_name: str, reports: list[dict[str, Any]]) -> dict[str, Any]:
    allowed_tables = sorted({r["table_name"] for r in reports})
    return {
        "app_name": app_name,
        "reports": reports,
        "allowed_tables": allowed_tables,
        "join_hints": [],
        "business_definitions": {},
        "refresh": {"default_stale_after_hours": 24},
        "query": {"evidence_row_cap": 30},
        "schema_summary": {"sample_values_cap": 10, "profile_columns_cap": 50},
    }


def _question_requests_table(question: str) -> bool:
    q = question.lower()
    table_terms = ["table", "tabular", "rows", "row-wise", "as rows", "grid"]
    return any(term in q for term in table_terms)


@app.command("bootstrap-config")
def bootstrap_config(
    output: Path = typer.Option(Path("config/app.yaml"), "--output", help="Output YAML path"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite output if it exists"),
) -> None:
    """Generate config/app.yaml automatically from Zoho Creator app metadata."""
    settings = load_settings()
    client = ZohoCreatorClient(settings)

    if output.exists() and not overwrite:
        raise typer.BadParameter(
            f"{output} already exists. Use --overwrite to replace it."
        )

    try:
        discovered = client.list_reports()
    except ZohoConfigError as exc:
        raise typer.BadParameter(str(exc)) from exc
    except RuntimeError as exc:
        raise typer.BadParameter(
            f"Zoho metadata discovery failed: {exc}. "
            "Check ZOHO_CREATOR_BASE_URL/ZOHO_BASE_URL and app permissions."
        ) from exc

    if not discovered:
        raise typer.BadParameter(
            "No reports discovered from Zoho API. Check app permissions and endpoints."
        )

    payload = _default_config_payload(
        app_name=settings.zoho_app_link_name or "your_app_name",
        reports=discovered,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False, allow_unicode=False)

    console.print(f"[green]Generated config[/green] at {output}")
    console.print(f"[green]Reports discovered:[/green] {len(discovered)}")


@app.command()
def sync(
    config: Path = typer.Option(Path("config/app.yaml"), exists=True, help="App config YAML"),
    from_zip: list[Path] | None = typer.Option(None, "--from-zip", help="One or more local bulk ZIP files"),
) -> None:
    """Sync data into DuckDB using Zoho Creator v2.1 API or local ZIPs."""
    settings = load_settings()
    app_config = load_app_config(config)
    cache = CacheManager(Path(".cache") / app_config.app_name)

    if from_zip:
        zip_paths = [p.resolve() for p in from_zip]
        if len(zip_paths) == 1:
            snapshot = ingest_zip_to_duckdb(zip_paths[0], cache.db_path, app_config, source="local_zip")
        else:
            snapshot = ingest_multiple_zips_to_duckdb(zip_paths, cache.db_path, app_config, source="local_zip_multi")
    else:
        client = ZohoCreatorClient(settings)
        report_payloads: dict[str, list[dict]] = {}
        for report in app_config.report_models:
            console.print(f"[cyan]Fetching report data (v2.1)[/cyan] {report.report_link_name}")
            try:
                rows = client.fetch_report_rows(report.report_link_name)
            except ZohoConfigError as exc:
                raise typer.BadParameter(str(exc)) from exc
            report_payloads[report.report_link_name] = rows
        snapshot = ingest_report_payloads_to_duckdb(
            report_payloads=report_payloads,
            db_path=cache.db_path,
            app_config=app_config,
            source="zoho_v2_1_data",
        )

    cache.write_snapshot(snapshot)

    summaries = build_schema_summaries(cache.db_path, app_config)
    payload = schema_summaries_to_json_payload(summaries, app_config.app_name)
    cache.write_schema_summary(payload)

    console.print("[green]Sync complete[/green]")
    console.print(json.dumps(snapshot.model_dump(mode="json"), indent=2, default=str))


@app.command()
def status(config: Path = typer.Option(Path("config/app.yaml"), exists=True)) -> None:
    """Show cache and schema summary status."""
    app_config = load_app_config(config)
    cache = CacheManager(Path(".cache") / app_config.app_name)

    snap = cache.read_snapshot()
    if not snap:
        console.print("No sync metadata found. Run `agent sync` first.")
        raise typer.Exit(code=1)

    table = Table(title="Sync Status")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("App", snap.app_name)
    table.add_row("Synced At", str(snap.synced_at))
    table.add_row("Source", snap.source)
    table.add_row("Tables", ", ".join(sorted(snap.row_counts.keys())))
    console.print(table)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Natural-language question"),
    config: Path = typer.Option(Path("config/app.yaml"), exists=True),
    max_rows: int = typer.Option(30, help="Max evidence rows"),
    table: bool = typer.Option(False, "--table/--no-table", help="Show evidence table output"),
) -> None:
    """Ask one question and get bullet-point summary (table optional)."""
    settings = load_settings()
    app_config = load_app_config(config)
    cache = CacheManager(Path(".cache") / app_config.app_name)

    if not cache.db_path.exists():
        console.print("No local DuckDB found. Run `agent sync` first.")
        raise typer.Exit(code=1)

    schema_summary = cache.read_schema_summary()
    engine = QueryEngine(
        settings=settings,
        db_path=cache.db_path,
        schema_summary=schema_summary,
        allowed_tables=app_config.allowed_tables,
        business_definitions=app_config.business_definitions,
    )

    with console.status("[cyan]Analyzing data and generating answer...[/cyan]", spinner="dots"):
        answer = engine.answer(QueryRequest(question=question, max_evidence_rows=max_rows))
    cache.write_last_answer(answer.model_dump(mode="json"))

    console.print("\n[bold]Summary[/bold]")
    console.print(answer.summary)

    show_table = table or _question_requests_table(question)
    if show_table:
        evidence = Table(title="Evidence")
        for col in answer.evidence_columns:
            evidence.add_column(str(col))
        for row in answer.evidence_rows:
            evidence.add_row(*[str(row.get(col, "")) for col in answer.evidence_columns])
        console.print(evidence)


@app.command()
def chat(config: Path = typer.Option(Path("config/app.yaml"), exists=True)) -> None:
    """Start interactive terminal chat."""
    console.print("Type a question, or `exit` to quit.")
    while True:
        q = typer.prompt("agent>")
        if q.strip().lower() in {"exit", "quit"}:
            break
        ask(question=q, config=config)


@app.command()
def explain() -> None:
    """Show the last generated SQL and model used."""
    cache = CacheManager(Path(".agent_state"))
    payload = cache.read_last_answer()
    if not payload:
        console.print("No previous answer found. Run `agent ask` first.")
        raise typer.Exit(code=1)

    console.print("[bold]Last SQL[/bold]")
    console.print(payload.get("sql", ""))
    console.print(f"[bold]Model:[/bold] {payload.get('model', '')}")


if __name__ == "__main__":
    app()
