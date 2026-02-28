from pathlib import Path

import duckdb

from agent.schema_summary import build_schema_summaries
from agent.settings import AppConfig


def test_schema_summary_generation(tmp_path: Path) -> None:
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path), read_only=False)
    conn.execute("CREATE TABLE leads (id INTEGER, status VARCHAR, amount DOUBLE)")
    conn.execute("INSERT INTO leads VALUES (1, 'new', 10.5), (2, 'won', 20.0), (3, NULL, 5.0)")
    conn.close()

    cfg = AppConfig.model_validate(
        {
            "app_name": "app",
            "reports": [
                {
                    "name": "Leads",
                    "report_link_name": "All_Leads",
                    "table_name": "leads",
                    "description": "Lead table",
                    "key_columns": ["id"],
                }
            ],
            "allowed_tables": ["leads"],
        }
    )

    summaries = build_schema_summaries(db_path=db_path, app_config=cfg)
    assert len(summaries) == 1
    leads = summaries[0]
    assert leads.table_name == "leads"
    assert leads.row_count == 3
    assert any(c.name == "status" for c in leads.columns)
