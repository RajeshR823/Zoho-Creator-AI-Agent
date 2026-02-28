from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import duckdb
from langchain_openai import ChatOpenAI
import requests

from agent.models import AgentAnswer, QueryRequest
from agent.settings import Settings
from agent.sql_safety import validate_select_only_sql


class SupportsInvoke(Protocol):
    def invoke(self, input: Any) -> Any: ...


def _stringify_response(response: Any) -> str:
    if hasattr(response, "content"):
        return str(response.content)
    return str(response)


def build_sql_prompt(
    question: str,
    schema_summary: dict,
    allowed_tables: list[str],
    business_definitions: dict[str, str],
) -> str:
    return (
        "You are a SQL planner for DuckDB. Output ONLY SQL.\n"
        "Rules:\n"
        "- Use exactly one SELECT statement.\n"
        "- Never use INSERT/UPDATE/DELETE/DDL/PRAGMA.\n"
        "- Use only allowed tables.\n"
        "- Prefer explicit column names and deterministic ordering.\n\n"
        f"Allowed tables: {allowed_tables}\n"
        f"Business definitions: {json.dumps(business_definitions)}\n"
        f"Schema summary: {json.dumps(schema_summary)}\n\n"
        f"Question: {question}\n"
        "SQL:"
    )


def build_answer_prompt(question: str, sql: str, rows: list[dict[str, Any]], row_cap: int) -> str:
    compact_rows = rows[:row_cap]
    return (
        "You are a user-facing assistant. Answer using only provided data.\n"
        "Do not fabricate information.\n"
        "Do NOT mention technical words like SQL, query, row, table, capped, result set, schema, or database.\n"
        "Write simple and clear facts that a non-technical user can understand.\n\n"
        f"Question: {question}\n"
        f"SQL used: {sql}\n"
        f"Rows (capped): {json.dumps(compact_rows, default=str)}\n\n"
        "Return ONLY bullet points.\n"
        "Format rules:\n"
        "- 4 to 8 bullets.\n"
        "- Each line must start with '- '.\n"
        "- No markdown table.\n"
        "- No paragraph text outside bullets.\n"
    )


class QueryEngine:
    def __init__(
        self,
        settings: Settings,
        db_path: Path,
        schema_summary: dict,
        allowed_tables: list[str],
        business_definitions: dict[str, str],
        llm: SupportsInvoke | None = None,
    ) -> None:
        self.settings = settings
        self.db_path = db_path
        self.schema_summary = schema_summary
        self.allowed_tables = allowed_tables
        self.business_definitions = business_definitions
        self.llm = llm or ChatOpenAI(
            model=settings.openrouter_model,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0,
        )

    def _build_llm(self, model: str) -> SupportsInvoke:
        return ChatOpenAI(
            model=model,
            openai_api_key=self.settings.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0,
        )

    def _discover_available_mistral_model(self) -> str | None:
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                timeout=20,
                headers={
                    "Authorization": f"Bearer {self.settings.openrouter_api_key}"
                }
                if self.settings.openrouter_api_key
                else None,
            )
            response.raise_for_status()
            payload = response.json()
            models = payload.get("data", [])
            ids = [m.get("id") for m in models if isinstance(m, dict) and m.get("id")]
            preferred = [
                "mistralai/mistral-7b-instruct",
                "mistralai/mistral-7b-instruct:free",
            ]
            for candidate in preferred:
                if candidate in ids:
                    return candidate
            for model_id in ids:
                if isinstance(model_id, str) and model_id.startswith("mistralai/") and model_id.endswith(":free"):
                    return model_id
            for model_id in ids:
                if isinstance(model_id, str) and model_id.startswith("mistralai/"):
                    return model_id
        except Exception:
            return None
        return None

    def _discover_available_free_models(self, limit: int = 8) -> list[str]:
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                timeout=20,
                headers={
                    "Authorization": f"Bearer {self.settings.openrouter_api_key}"
                }
                if self.settings.openrouter_api_key
                else None,
            )
            response.raise_for_status()
            payload = response.json()
            models = payload.get("data", [])
            ids = [m.get("id") for m in models if isinstance(m, dict) and m.get("id")]
            free_models = [m for m in ids if isinstance(m, str) and m.endswith(":free")]

            # Prefer mistral family first, then any free model.
            mistral_first = [m for m in free_models if m.startswith("mistralai/")]
            others = [m for m in free_models if not m.startswith("mistralai/")]
            ordered = mistral_first + others
            return ordered[:limit]
        except Exception:
            return []

    def _invoke_llm(self, prompt: str) -> Any:
        try:
            return self.llm.invoke(prompt)
        except Exception as exc:
            msg = str(exc).lower()
            if (
                "model_not_available" in msg
                or "non-serverless model" in msg
                or "provider returned error" in msg
                or "no endpoints found" in msg
            ):
                tried_models: list[str] = []

                # Retry configured family first.
                candidates: list[str] = []
                if self.settings.openrouter_model != "mistralai/mistral-7b-instruct:free":
                    candidates.append("mistralai/mistral-7b-instruct:free")

                discovered_mistral = self._discover_available_mistral_model()
                if discovered_mistral and discovered_mistral not in candidates:
                    candidates.append(discovered_mistral)

                for model_id in self._discover_available_free_models(limit=8):
                    if model_id not in candidates:
                        candidates.append(model_id)

                for model_id in candidates:
                    fallback = self._build_llm(model_id)
                    try:
                        return fallback.invoke(prompt)
                    except Exception:
                        tried_models.append(model_id)
                        continue
                raise RuntimeError(
                    "OpenRouter model invocation failed for configured and fallback models. "
                    f"Tried fallbacks: {tried_models}. Original error: {exc}"
                ) from exc
            raise

    def generate_sql(self, request: QueryRequest) -> str:
        prompt = build_sql_prompt(
            question=request.question,
            schema_summary=self.schema_summary,
            allowed_tables=self.allowed_tables,
            business_definitions=self.business_definitions,
        )
        sql = _stringify_response(self._invoke_llm(prompt)).strip()
        # Strip markdown fences if model returns them.
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql

    def execute_safe_query(self, sql: str, max_rows: int) -> tuple[list[dict[str, Any]], list[str]]:
        validation = validate_select_only_sql(sql, allowed_tables=self.allowed_tables)
        if not validation.is_safe:
            raise ValueError(f"Unsafe SQL blocked: {validation.reason}")

        conn = duckdb.connect(str(self.db_path), read_only=True)
        limited_sql = f"SELECT * FROM ({validation.sql.rstrip(';')}) AS subquery LIMIT {max_rows}"
        cursor = conn.execute(limited_sql)
        cols = [d[0] for d in cursor.description]
        rows_raw = cursor.fetchall()
        rows = [dict(zip(cols, row)) for row in rows_raw]
        conn.close()
        return rows, cols

    def answer(self, request: QueryRequest) -> AgentAnswer:
        sql = self.generate_sql(request)
        rows, cols = self.execute_safe_query(sql=sql, max_rows=request.max_evidence_rows)
        answer_prompt = build_answer_prompt(
            question=request.question,
            sql=sql,
            rows=rows,
            row_cap=request.max_evidence_rows,
        )
        summary_raw = _stringify_response(self._invoke_llm(answer_prompt)).strip()
        summary = self._ensure_bullet_points(summary_raw)
        summary = self._remove_technical_bullets(summary)
        summary = self._dedupe_bullets(summary)
        return AgentAnswer(
            question=request.question,
            summary=summary,
            sql=sql,
            evidence_rows=rows,
            evidence_columns=cols,
            generated_at=datetime.now(UTC),
            model=self.settings.openrouter_model,
        )

    @staticmethod
    def _ensure_bullet_points(text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        bullets = [line for line in lines if line.startswith("- ")]
        if bullets:
            return "\n".join(bullets)
        if not lines:
            return "- No data available to summarize."
        # Fallback formatting if model ignores bullet instruction.
        normalized: list[str] = []
        for line in lines:
            if line.startswith("• "):
                normalized.append("- " + line[2:].strip())
            elif line.startswith("* "):
                normalized.append("- " + line[2:].strip())
            else:
                normalized.append(f"- {line}")
        return "\n".join(normalized)

    @staticmethod
    def _remove_technical_bullets(text: str) -> str:
        banned_terms = {
            "sql",
            "query",
            "row",
            "rows",
            "table",
            "capped",
            "result set",
            "schema",
            "database",
        }
        kept: list[str] = []
        for line in text.splitlines():
            lower = line.lower()
            if any(term in lower for term in banned_terms):
                continue
            kept.append(line)
        if not kept:
            return "- Matching details found for your request.\n- Ask for a specific field like blood group, diagnosis, or visit date."
        return "\n".join(kept)

    @staticmethod
    def _normalize_bullet_for_compare(line: str) -> set[str]:
        clean = line.lower().strip()
        if clean.startswith("- "):
            clean = clean[2:]
        clean = clean.replace("years of age", "years old")
        clean = clean.replace("b positive", "b+")
        clean = clean.replace("a positive", "a+")
        clean = clean.replace("ab positive", "ab+")
        clean = clean.replace("o positive", "o+")
        clean = clean.replace("a negative", "a-")
        clean = clean.replace("ab negative", "ab-")
        clean = clean.replace("o negative", "o-")
        clean = re.sub(r"[^a-z0-9+\\-\\s]", " ", clean)
        tokens = [t for t in clean.split() if t not in {"is", "the", "her", "his", "their", "she", "he"}]
        return set(tokens)

    @staticmethod
    def _jaccard(a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    @staticmethod
    def _fact_signature(line: str) -> tuple[str, str] | None:
        clean = line.lower()
        clean = clean.replace("b positive", "b+").replace("a positive", "a+").replace("ab positive", "ab+").replace("o positive", "o+")
        clean = clean.replace("a negative", "a-").replace("ab negative", "ab-").replace("o negative", "o-")
        clean = clean.replace("years of age", "years old")

        blood = re.search(r"blood group.*?([abo]{1,2}[+-])", clean)
        if blood:
            return ("blood_group", blood.group(1))

        age = re.search(r"\b(\d{1,3})\s+years old\b", clean)
        if age:
            return ("age", age.group(1))
        return None

    @classmethod
    def _dedupe_bullets(cls, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        unique: list[str] = []
        sigs: list[set[str]] = []
        fact_sigs: set[tuple[str, str]] = set()
        for line in lines:
            fact = cls._fact_signature(line)
            if fact and fact in fact_sigs:
                continue
            sig = cls._normalize_bullet_for_compare(line)
            if any(cls._jaccard(sig, existing) >= 0.55 for existing in sigs):
                continue
            unique.append(line)
            sigs.append(sig)
            if fact:
                fact_sigs.add(fact)
        if not unique:
            return "- Matching details found."
        return "\n".join(unique)
