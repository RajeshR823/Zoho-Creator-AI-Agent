# Zoho Agent Service (FastAPI + Streamlit)

This folder contains:

- FastAPI app for deployable API endpoints
- Streamlit chatbot UI for local usage

## Endpoints

- `GET /health`
- `GET /status`
- `POST /chat`
- `POST /session/clear`

## Run locally

1. Install deps from project root:

```bash
pip install -e '.[dev]'
```

2. Start API server from project root:

```bash
uvicorn apps.zoho_agent_service.api.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Start Streamlit UI from project root:

```bash
streamlit run apps/zoho_agent_service/ui/streamlit_app.py
```

## Environment

Optional variables:

- `APP_CONFIG_PATH` (default: `config/app.yaml`)
- `API_BASE_URL` for Streamlit (default: `http://127.0.0.1:8000`)
- `CHAT_SESSION_ID` for Streamlit (default: `demo-session`)

## Deploy notes

- Run API behind a reverse proxy/load balancer.
- Keep `.env` secrets on server only.
- Session store is in-memory in this sample; replace with Redis/DB for multi-instance deploy.

## Render deployment

- Blueprint file: `render.yaml` (repo root)
- Production API doc: `apps/zoho_agent_service/docs/production-api.md`
