from agent.sql_safety import validate_select_only_sql


def test_accepts_simple_select() -> None:
    result = validate_select_only_sql("SELECT * FROM leads", allowed_tables=["leads"])
    assert result.is_safe


def test_rejects_non_select() -> None:
    result = validate_select_only_sql("DELETE FROM leads", allowed_tables=["leads"])
    assert not result.is_safe
    assert "Only SELECT" in (result.reason or "")


def test_rejects_blocked_keyword() -> None:
    result = validate_select_only_sql("SELECT * FROM leads; DROP TABLE leads;", allowed_tables=["leads"])
    assert not result.is_safe


def test_rejects_unknown_table() -> None:
    result = validate_select_only_sql("SELECT * FROM deals", allowed_tables=["leads"])
    assert not result.is_safe
    assert "not in allowed_tables" in (result.reason or "")


def test_allows_unnest_function_source() -> None:
    sql = "SELECT d.doctor_name FROM doctors_report d JOIN UNNEST(d.specialization) AS s(v) ON true"
    result = validate_select_only_sql(sql, allowed_tables=["doctors_report"])
    assert result.is_safe


def test_allows_cte_alias_reference() -> None:
    sql = "WITH x AS (SELECT * FROM leads) SELECT * FROM x"
    result = validate_select_only_sql(sql, allowed_tables=["leads"])
    assert result.is_safe
