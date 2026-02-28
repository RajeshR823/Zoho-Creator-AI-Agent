# Zoho Creator AI Agent

This app connects **Zoho Creator** data with **LangChain** so users can ask questions in natural language and get answers.

## App idea

- Pull data from Zoho Creator
- Store and query data safely
- Let users ask questions like a chatbot
- Return simple answers from real data

## Tech used

- Zoho Creator API
- LangChain
- DuckDB
- FastAPI (API backend)
- Streamlit (chat UI)

## Configuration

Create a `.env` file from `.env.example` and set these values:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `ZOHO_CLIENT_ID`
- `ZOHO_CLIENT_SECRET`
- `ZOHO_REFRESH_TOKEN`
- `ZOHO_ACCOUNT_OWNER`
- `ZOHO_APP_LINK_NAME`
- `ZOHO_ACCOUNTS_URL` (default is fine)
- `ZOHO_BASE_URL` (default is fine)
- `ZOHO_CREATOR_BASE_URL` (default is fine)

Also check app config file:

- `config/app.yaml`

## Run

1. Install:

```bash
pip install -e '.[dev]'
```

2. Start API:

```bash
uvicorn apps.zoho_agent_service.api.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Start UI:

```bash
streamlit run apps/zoho_agent_service/ui/streamlit_app.py
```
