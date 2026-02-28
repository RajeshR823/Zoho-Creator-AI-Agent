from __future__ import annotations

import re

from agent.models import ValidatedSQL

BLOCKED_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "MERGE",
    "COPY",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "REPLACE",
    "CALL",
}


def _has_multiple_statements(sql: str) -> bool:
    trimmed = sql.strip()
    if not trimmed:
        return False
    # Allow one trailing semicolon, but block additional statements.
    if trimmed.count(";") > 1:
        return True
    if ";" in trimmed[:-1]:
        return True
    return False


def _starts_with_select(sql: str) -> bool:
    cleaned = sql.strip().lstrip("(")
    return cleaned.upper().startswith("SELECT")


def validate_select_only_sql(sql: str, allowed_tables: list[str] | None = None) -> ValidatedSQL:
    normalized = sql.strip()
    if not normalized:
        return ValidatedSQL(sql=sql, is_safe=False, reason="SQL cannot be empty")

    if _has_multiple_statements(normalized):
        return ValidatedSQL(sql=sql, is_safe=False, reason="Multiple statements are not allowed")

    if not _starts_with_select(normalized):
        return ValidatedSQL(sql=sql, is_safe=False, reason="Only SELECT queries are allowed")

    upper_sql = normalized.upper()
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_sql):
            return ValidatedSQL(sql=sql, is_safe=False, reason=f"Blocked keyword detected: {keyword}")

    if allowed_tables:
        # Light guard: if FROM/JOIN references unknown identifiers, reject.
        referenced = re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", normalized, flags=re.IGNORECASE)
        for table in referenced:
            if table not in allowed_tables:
                return ValidatedSQL(
                    sql=sql,
                    is_safe=False,
                    reason=f"Table '{table}' is not in allowed_tables",
                )

    return ValidatedSQL(sql=normalized, is_safe=True, reason=None)
