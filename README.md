# Sales Analytics Command Center

> **This portfolio project uses 100% synthetic data.** It does not represent actual Synchrony or CareCredit data, systems, customers, providers, schemas, assignment rules, forecasts, or internal processes.

An open-source demonstration of a controlled monthly analytics foundation for a fictional Health & Wellness financing portfolio. PR 1 establishes reproducible monthly Parquet snapshots, separates digital application intake from downstream sales attribution, loads the snapshots into DuckDB, and produces auditable data-quality results.

## Why this project exists

The eventual command center will help sales and analytics leaders answer what happened, whether the apparent change is commercial or caused by incomplete attribution, where to act, what may happen next, and whether the data is trustworthy. This first increment concentrates on the trust and attribution foundations.

## Architecture

```text
deterministic Python generator
        |
        v
monthly immutable Parquet snapshots
        |
        +--> source validation + QA report
        |
        v
DuckDB raw schema + ingestion audit
        |
        v
dbt sources (analytics models arrive in PR 2)
```

Approximately 50% of applications arrive with provisional provider and sales-rep attribution from the intake source; the other 50% enter the unallocated pool. A separate `application_assignment_events` source records the authoritative downstream assignment outcome and confidence.

Unresolved applications move through an explainable allocation waterfall: validated intake attribution, fictional provider-session matching, and geographic + specialty + activity matching. Every attempt is retained, and exactly one event is marked as the current outcome.

## Stack

Python 3.11+, pandas, NumPy, PyArrow, DuckDB, pytest, Ruff, and dbt Core/dbt-duckdb source definitions.

## Quick start

```bash
make setup
make generate
make warehouse
make qa
make test
```

`make refresh` runs generation, ingestion, and QA together. To reproduce a single month:

```bash
python -m src.generate_synthetic_data --month 2026-09
```

Generated Parquet files, DuckDB databases, and QA outputs are local build artifacts and are intentionally excluded from Git. Every artifact can be reconstructed from the deterministic code and seed.

## Monthly process

1. Generate or receive the nine expected monthly source files.
2. Validate file presence, schema, relationships, dates, accepted values, and control totals.
3. Halt before warehouse refresh on critical failures.
4. Ingest validated snapshots into DuckDB with source-month lineage.
5. Publish a machine-readable QA report for downstream application use.

Run `make bad-data-demo` to create and validate an isolated September fixture containing exactly 17 unknown-provider assignment references. It is never included in the normal production path.

## Repository status

This branch is PR 1, the data foundation. dbt transformations, KPI marts, forecasting, opportunity scoring, and the Streamlit interface are intentionally deferred to later reviewed pull requests.

See [architecture](docs/architecture.md), [data dictionary](docs/data_dictionary.md), and [assignment framework](docs/assignment_framework.md).
