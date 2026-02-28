## Zoho Creator AI Agent

An AI agent that ingests Zoho Creator bulk exports into DuckDB and answers questions using LangChain.  
Zoho live sync uses Creator API v2.1 metadata and report data endpoints for structured data access.  
The system builds intelligent schema summaries to understand your app structure.  
Only small, relevant data slices are used when generating answers.  
Designed to be secure, modular, and ready for future expansion.

## FastAPI + Streamlit Layer

A deployable API and sample local chatbot UI are available in `apps/zoho_agent_service`.

Run API:

```bash
uvicorn apps.zoho_agent_service.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Run Streamlit UI:

```bash
streamlit run apps/zoho_agent_service/ui/streamlit_app.py
```
