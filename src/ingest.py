"""Validate and ingest monthly Parquet snapshots into DuckDB."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from src.config import MONTHS, RAW_ROOT, SOURCE_NAMES, WAREHOUSE_PATH
from src.qa import run_qa


def ingest(
    input_root: Path = RAW_ROOT, warehouse_path: Path = WAREHOUSE_PATH
) -> Path:
    report = run_qa(input_root=input_root, write_report=True)
    if report["status"] != "PASS":
        raise RuntimeError("Source validation failed; warehouse refresh halted")
    warehouse_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(warehouse_path)) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
        connection.execute("CREATE SCHEMA IF NOT EXISTS audit")
        for source in SOURCE_NAMES:
            files = [
                str(input_root / month / f"{source}.parquet") for month in MONTHS
            ]
            file_list = ", ".join(
                "'" + path.replace("'", "''") + "'" for path in files
            )
            connection.execute(
                f"""
                CREATE OR REPLACE TABLE raw.{source} AS
                SELECT *, regexp_extract(filename, '(2026-[0-9]{{2}})', 1) AS source_month
                FROM read_parquet(
                    [{file_list}], filename=true, union_by_name=true
                )
                """
            )
        connection.execute(
            """
            CREATE OR REPLACE TABLE audit.ingestion_runs AS
            SELECT current_timestamp AS loaded_at, source_month, source_name, row_count
            FROM (
                SELECT source_month, 'applications' AS source_name, count(*) AS row_count
                FROM raw.applications GROUP BY 1
                UNION ALL
                SELECT source_month, 'application_assignment_events', count(*)
                FROM raw.application_assignment_events GROUP BY 1
                UNION ALL
                SELECT source_month, 'financed_sales', count(*)
                FROM raw.financed_sales GROUP BY 1
            )
            """
        )
    return warehouse_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=RAW_ROOT)
    parser.add_argument("--warehouse", type=Path, default=WAREHOUSE_PATH)
    args = parser.parse_args()
    print(f"Ingested validated snapshots into {ingest(args.input_root, args.warehouse)}")


if __name__ == "__main__":
    main()
