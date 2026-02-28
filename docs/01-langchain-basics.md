# LangChain Basics (Stage 1)

This project uses LangChain only for:

1. SQL generation from natural language.
2. Final natural-language summary from capped SQL results.

Flow:

- Build prompt from schema summary + allowed tables + question.
- Model returns SQL.
- SQL validator enforces SELECT-only policy.
- DuckDB executes query in read-only mode.
- Model gets only capped result rows to write a summary.

Important: raw full tables are never sent to the model.
