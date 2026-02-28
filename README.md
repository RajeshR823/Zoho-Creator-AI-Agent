# Zoho Creator Terminal AI Agent (Stage 1)

Terminal-only AI agent that ingests Zoho Creator bulk exports into DuckDB and answers questions with LangChain.
Zoho live sync now uses Creator API v2.1 metadata + report data endpoints.

## Guarantees

- LLM never receives full dataset; only schema summary and capped query rows.
- OpenRouter model is locked to `mistralai/mistral-7b-instruct` family (default: `mistralai/mistral-7b-instruct:free`).
- SQL execution is `SELECT`-only with explicit blocked operations.
- No LangGraph in Stage 1.

## Quickstart

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -V
```

2. Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

3. Configure environment:

```bash
cp .env.example .env
```

Edit `.env`:

- Set `OPENROUTER_API_KEY=<your_key>`
- Keep `OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free` (recommended default)
- Fill `ZOHO_*` values only when using direct Zoho sync

4. Update `config/app.yaml` with your app/report/table details.
   - This is a reusable mapping file, not a fixed schema.
   - You can point the same agent to any Zoho Creator app by changing this file (or using another config path).
   - Or auto-generate from Zoho metadata:
```bash
agent bootstrap-config --output config/app.yaml --overwrite
```

5. Sync data (recommended first run: local ZIP):

```bash
agent sync --from-zip /absolute/path/to/export.zip
```

If your Zoho credentials are configured, you can sync directly (v2.1 data endpoint):

```bash
agent sync
```

6. Check status:

```bash
agent status
```

7. Ask questions:

```bash
agent ask "Top 10 deals by amount this quarter"
agent ask "Top 10 deals by amount this quarter" --table
agent chat
agent explain
```

8. Run tests:

```bash
pytest -q
```

## Commands

- `agent sync`
- `agent status`
- `agent ask "..."`
- `agent chat`
- `agent explain`
- `agent bootstrap-config --output config/app.yaml --overwrite`

## What Next (After `.env` is ready)

Run from project root:

```bash
cd /Users/rajeshr/Downloads/Learning/Projects/Summarizer
source .venv/bin/activate
```

1. Sync data:
```bash
agent sync --from-zip /absolute/path/to/export.zip
```
or (if Zoho creds are configured):
```bash
agent sync
```

2. Verify sync:
```bash
agent status
```

3. Ask your first question:
```bash
agent ask "show top 10 records by amount"
```

4. Interactive terminal chat:
```bash
agent chat
```

5. Inspect generated SQL:
```bash
agent explain
```

## Common issues

- `command not found: agent`
  - Run `pip install -e '.[dev]'` again in the active virtualenv.
- `OPENROUTER_MODEL must be ...`
  - Set `OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free` in `.env`.
- Zoho config missing errors
  - Use ZIP mode first: `agent sync --from-zip /absolute/path/file.zip`.

## Additional docs

- [`docs/04-install-and-run.md`](docs/04-install-and-run.md)
