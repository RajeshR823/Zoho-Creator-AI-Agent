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
    upper = cleaned.upper()
    return upper.startswith("SELECT") or upper.startswith("WITH")


def _extract_cte_names(sql: str) -> set[str]:
    names = set(re.findall(r"\bWITH\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\b", sql, flags=re.IGNORECASE))
    names.update(re.findall(r",\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\b", sql, flags=re.IGNORECASE))
    return {n.lower() for n in names}


def _extract_from_join_sources(sql: str) -> list[tuple[str, bool]]:
    # Returns (source_token, is_function_like)
    pattern = re.compile(
        r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\s*(\()?",
        flags=re.IGNORECASE,
    )
    out: list[tuple[str, bool]] = []
    for match in pattern.finditer(sql):
        out.append((match.group(1), bool(match.group(2))))
    return out


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
        allowed_lower = {t.lower() for t in allowed_tables}
        cte_names = _extract_cte_names(normalized)
        for source, is_function in _extract_from_join_sources(normalized):
            if is_function:
                continue
            source_base = source.split(".")[-1].lower()
            if source_base in cte_names:
                continue
            if source.lower() not in allowed_lower and source_base not in allowed_lower:
                return ValidatedSQL(
                    sql=sql,
                    is_safe=False,
                    reason=f"Table '{source}' is not in allowed_tables",
                )

    return ValidatedSQL(sql=normalized, is_safe=True, reason=None)
