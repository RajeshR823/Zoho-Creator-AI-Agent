# Zoho Bulk Ingestion

Stage 1 supports two sync modes:

1. `agent sync` with Zoho Bulk API (once credentials are set).
2. `agent sync --from-zip ...` for local ZIP files.

Ingestion steps:

- Download/export ZIP.
- Extract CSV/JSON files.
- Create/replace DuckDB tables.
- Record row counts + schema hashes.
- Build schema summary metadata.
