from agent.query_engine import QueryEngine, build_answer_prompt, build_sql_prompt


def test_sql_prompt_uses_schema_not_full_rows() -> None:
    schema_summary = {"tables": [{"table_name": "leads", "row_count": 1000000}]}
    prompt = build_sql_prompt(
        question="Count leads",
        schema_summary=schema_summary,
        allowed_tables=["leads"],
        business_definitions={},
    )
    assert "Schema summary" in prompt
    assert "row_count" in prompt


def test_answer_prompt_caps_rows() -> None:
    rows = [{"id": i} for i in range(100)]
    prompt = build_answer_prompt("How many?", "SELECT id FROM leads", rows, row_cap=10)
    assert '"id": 9' in prompt
    assert '"id": 10' not in prompt
    assert "Return ONLY bullet points" in prompt
    assert "Do NOT mention technical words" in prompt


def test_dedupe_bullets_merges_repeated_facts() -> None:
    text = "\n".join(
        [
            "- Sarah Wilson's blood group is B+.",
            "- Her blood group is B positive.",
            "- Sarah Wilson is 39 years old.",
            "- She is 39 years of age.",
        ]
    )
    deduped = QueryEngine._dedupe_bullets(text)
    lines = [x for x in deduped.splitlines() if x.strip()]
    assert len(lines) == 2
