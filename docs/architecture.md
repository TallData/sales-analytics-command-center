# Architecture

## PR 1 boundary

The data foundation deliberately resembles a controlled monthly batch environment. Python creates deterministic source extracts, Parquet provides immutable monthly snapshots, DuckDB provides local schemas, QA gates the load, and dbt source declarations establish the contract for later transformations.

```text
Synthetic source generation
  -> data/raw/YYYY-MM/*.parquet
  -> source QA (halt on critical failure)
  -> raw DuckDB tables + audit.ingestion_runs
  -> dbt sources
```

The generator creates approximately 116,000 applications across January through August 2026, 2,500 providers, 68 sales representatives, four regions, and twenty territories. The data is sized for a laptop and CI.

## Attribution boundary

Digital application intake does not contain `provider_id` or `sales_rep_id`. Candidate provider context is used only inside the synthetic generator to produce a separate assignment event. Downstream analytics must resolve current assignment state from that event stream and must preserve unresolved applications.

## Snapshot and lineage strategy

Each month contains the nine source files defined in the data dictionary. Generated binaries are excluded from Git because they are deterministic build products. Ingestion adds `source_month` lineage based on the containing directory and records row counts in `audit.ingestion_runs`.

## Controls

Critical checks cover file receipt, identifiers, relationships, accepted values, nonnegative amounts, date ordering, duplicates, row-count variance, financial totals, and assignment-rate monitoring. A failure stops ingestion before any analytical model can refresh.

## Deferred work

PR 2 will implement staging, current assignment resolution, attributed applications, intermediate metrics, marts, and dbt tests. Forecasts and action scoring belong to PR 3. Streamlit belongs to PR 4.
