from pathlib import Path

import duckdb
import pandas as pd
from pandas.testing import assert_frame_equal

from src.config import SOURCE_NAMES
from src.generate_synthetic_data import generate_bad_data_fixture, generate_month
from src.ingest import ingest
from src.qa import run_qa


def test_month_generation_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate_month("2026-08", first)
    generate_month("2026-08", second)
    for source in SOURCE_NAMES:
        assert_frame_equal(
            pd.read_parquet(first / "2026-08" / f"{source}.parquet"),
            pd.read_parquet(second / "2026-08" / f"{source}.parquet"),
        )


def test_applications_and_assignment_events_are_separate(tmp_path: Path) -> None:
    frames = generate_month("2026-08", tmp_path)
    assert "provider_id" not in frames["applications"].columns
    assert "sales_rep_id" not in frames["applications"].columns
    assignment_rate = (
        frames["application_assignment_events"]["assignment_status"]
        .eq("assigned")
        .mean()
    )
    assert 0.87 <= assignment_rate <= 0.91


def test_bad_fixture_has_exactly_17_unknown_provider_references(
    tmp_path: Path, monkeypatch,
) -> None:
    import src.generate_synthetic_data as generator

    monkeypatch.setattr(generator, "FIXTURE_ROOT", tmp_path)
    fixture = generate_bad_data_fixture()
    report = run_qa(fixture, write_report=False)
    relationship = next(
        result
        for result in report["results"]
        if result["check"].endswith("assignment_provider_relationship")
    )
    assert relationship["failures"] == 17
    assert report["status"] == "FAIL"


def test_ingest_builds_raw_tables(tmp_path: Path, monkeypatch) -> None:
    import src.ingest as ingest_module

    months = ("2026-01", "2026-02")
    for month in months:
        generate_month(month, tmp_path / "raw")
    monkeypatch.setattr(ingest_module, "MONTHS", months)
    warehouse = ingest(tmp_path / "raw", tmp_path / "warehouse.duckdb")
    with duckdb.connect(str(warehouse), read_only=True) as connection:
        count = connection.execute("select count(*) from raw.applications").fetchone()[0]
        assert count == 27_400
