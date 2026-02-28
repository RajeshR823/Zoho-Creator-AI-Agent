# Zoho Creator AI Agent - Production API Documentation

## Base URL

- Production: `https://<your-render-service>.onrender.com`
- Local: `http://127.0.0.1:8000`

## Interactive API Docs

- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`
- OpenAPI spec: `GET /openapi.json`

## Endpoints

### 1) Health

- Method: `GET`
- Path: `/health`
- Purpose: basic liveness check

Example response:

```json
{
  "ok": true
}
```

### 2) Status

- Method: `GET`
- Path: `/status`
- Purpose: readiness and sync metadata

Example response:

```json
{
  "ready": true,
  "app_name": "hospital-management-system",
  "synced_at": "2026-03-01 10:15:00+00:00",
  "source": "zoho_v2_1_data",
  "tables": ["patients_report", "doctors_report"],
  "row_counts": {
    "patients_report": 100,
    "doctors_report": 10
  }
}
```

### 3) Chat

- Method: `POST`
- Path: `/chat`
- Purpose: ask natural-language questions against synced Zoho data

Request body:

```json
{
  "question": "Give me details about Dr. Sarah Lee",
  "session_id": "tenant-a-user-1",
  "max_rows": 20
}
```

Request fields:

- `question` (string, required)
- `session_id` (string, optional, default: `default`)
- `max_rows` (int, optional, default: `30`, min: `1`, max: `200`)

Success response (`200`):

```json
{
  "question": "Give me details about Dr. Sarah Lee",
  "summary": "- Doctor name: Dr. Sarah Lee\n- Specialization: Cardiology",
  "sql": "SELECT ...",
  "evidence_rows": [
    {
      "doctor_name": "Dr. Sarah Lee",
      "specialization": "Cardiology"
    }
  ],
  "evidence_columns": ["doctor_name", "specialization"],
  "generated_at": "2026-03-01T10:16:00.000000Z",
  "model": "mistralai/mistral-7b-instruct:free"
}
```

### 4) Clear Session

- Method: `POST`
- Path: `/session/clear`
- Purpose: clear conversation context for one session

Request body:

```json
{
  "session_id": "tenant-a-user-1"
}
```

Success response:

```json
{
  "ok": true,
  "session_id": "tenant-a-user-1"
}
```

## Error Model

Common response:

```json
{
  "detail": "<error message>"
}
```

Typical status codes:

- `400`: question processing error (unsafe SQL, missing DB sync, model/provider errors)
- `405`: wrong HTTP method (example: `GET /chat`)
- `422`: invalid request body
- `500`: unhandled server error

## cURL Examples

Health:

```bash
curl http://127.0.0.1:8000/health
```

Status:

```bash
curl http://127.0.0.1:8000/status
```

Chat:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "give me list of patient record and summarize the problem",
    "session_id": "demo-user-1",
    "max_rows": 20
  }'
```

Clear session:

```bash
curl -X POST http://127.0.0.1:8000/session/clear \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo-user-1"}'
```

## Render Free Deployment

This repo includes `render.yaml` for one-click deployment.

### Steps

1. Push code to GitHub.
2. In Render, create service from repo.
3. Render detects `render.yaml`.
4. Set secret env vars in Render dashboard:
   - `OPENROUTER_API_KEY`
   - `ZOHO_CLIENT_ID`
   - `ZOHO_CLIENT_SECRET`
   - `ZOHO_REFRESH_TOKEN`
   - `ZOHO_ACCOUNT_OWNER`
   - `ZOHO_APP_LINK_NAME`
5. Deploy service.
6. Open `/docs` on your Render URL.

## Security and Multi-User Notes

- Current sample has no auth middleware.
- Add API key or JWT for production exposure.
- Session state is in-memory; use Redis/DB for multi-instance reliability.
- DuckDB cache is local filesystem; free instances may reset storage.

## Known Production Constraints (Free Tier)

- Cold starts can increase first-request latency.
- Ephemeral disk may lose local cache between restarts.
- Add startup sync or external persistent storage for stable behavior.
