from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"
FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures"
WAREHOUSE_PATH = PROJECT_ROOT / "warehouse" / "sales_analytics.duckdb"
QA_OUTPUT_ROOT = PROJECT_ROOT / "qa_output"

MONTHS = tuple(f"2026-{month:02d}" for month in range(1, 9))
SOURCE_NAMES = (
    "provider_master",
    "sales_rep_master",
    "applications",
    "application_assignment_events",
    "provider_location_reference",
    "financed_sales",
    "provider_activity",
    "sales_goals",
    "pipeline",
)

BASE_SEED = 20260117
