# SAS-to-Open-Source Mapping

| Traditional monthly concept | Project equivalent |
|---|---|
| SAS `LIBNAME` | DuckDB schema |
| SAS DATA step | Python generation/ingestion and dbt staging |
| `PROC SQL` | dbt SQL on DuckDB |
| `PROC SUMMARY` / `MEANS` | dbt aggregate models |
| `%MACRO` | dbt macro or focused Python function |
| SAS batch scheduler | GitHub Actions |
| SAS permanent dataset | Parquet monthly snapshot and DuckDB table |
| `PROC REPORT` | Streamlit, introduced in PR 4 |

This mapping does not claim one-to-one feature parity. It demonstrates understanding of a controlled monthly analytics production process using a modern, local, open-source stack.
