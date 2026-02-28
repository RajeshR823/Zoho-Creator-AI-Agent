# Install and Run Guide

## 1) System requirements

- Python 3.11+
- macOS/Linux terminal (Windows works with equivalent commands)

## 2) Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -V
```

## 3) Install project dependencies

```bash
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

This installs runtime libraries including:

- `duckdb`
- `langchain`
- `langchain-openai`
- `pydantic`
- `pydantic-settings`
- `python-dotenv`
- `PyYAML`
- `requests`
- `rich`
- `typer`
- plus dev dependency: `pytest`

## 4) Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set:

- `OPENROUTER_API_KEY=<your_openrouter_key>`
- Keep `OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free`
- `ZOHO_ACCOUNTS_URL=https://accounts.zoho.com` (or your region accounts domain)

For Zoho API sync, also set all `ZOHO_*` fields.

## 5) Configure app schema

Edit `config/app.yaml`:

- set your reports/forms
- set `table_name`
- set `allowed_tables`
- optional join hints and business definitions

Or auto-generate `config/app.yaml` from Zoho app metadata:

```bash
agent bootstrap-config --output config/app.yaml --overwrite
```

This calls Zoho Creator metadata/report APIs and fills `reports` + `allowed_tables`.

## 6) First sync options

### Option A: local ZIP (recommended first)

```bash
agent sync --from-zip /absolute/path/to/export.zip
```

You can pass multiple ZIPs:

```bash
agent sync --from-zip /abs/leads.zip --from-zip /abs/deals.zip
```

### Option B: live Zoho Creator API v2.1

```bash
agent sync
```

Requires all `ZOHO_*` values in `.env`. The app uses:
- `GET /creator/v2.1/meta/{owner}/{app}/reports`
- `GET /creator/v2.1/data/{owner}/{app}/report/{report_link_name}`

## 7) Run queries

```bash
agent status
agent ask "Top 5 stages by total amount"
agent chat
agent explain
```

## 8) What to run after `.env` is ready

```bash
cd /Users/rajeshr/Downloads/Learning/Projects/Summarizer
source .venv/bin/activate
```

Then run in sequence:

```bash
agent bootstrap-config --output config/app.yaml --overwrite
agent sync --from-zip /absolute/path/to/export.zip
agent status
agent ask "show top 10 records by amount"
agent chat
agent explain
```

## 9) Run tests

```bash
pytest -q
```

## 10) Troubleshooting

- If `agent` command is not found:
  - Ensure virtualenv is active and rerun `pip install -e '.[dev]'`.
- If model lock error appears:
  - Keep `.env` model exactly `mistralai/mistral-7b-instruct:free` (or `mistralai/mistral-7b-instruct`).
- If Zoho auth errors appear:
  - Use ZIP sync mode first and verify `.env` fields later.
