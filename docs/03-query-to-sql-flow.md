# Query to SQL Safety Pattern

Safety controls:

- SQL must be a single SELECT statement.
- Blocked keywords include INSERT/UPDATE/DELETE/DDL/PRAGMA and more.
- Only configured `allowed_tables` can be referenced.
- DuckDB query execution uses read-only connection.

This keeps the terminal agent safe even if the model outputs unsafe SQL.
