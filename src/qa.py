"""Source-level quality controls that halt ingestion on critical failures."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import MONTHS, QA_OUTPUT_ROOT, RAW_ROOT, SOURCE_NAMES


def _check(
    results: list[dict[str, Any]], name: str, failures: int, detail: str
) -> None:
    results.append(
        {
            "check": name,
            "status": "PASS" if failures == 0 else "FAIL",
            "failures": int(failures),
            "detail": detail,
        }
    )


def _months_for_root(input_root: Path) -> list[str]:
    found = (
        sorted(path.name for path in input_root.iterdir() if path.is_dir())
        if input_root.exists()
        else []
    )
    return list(MONTHS) if all(month in found for month in MONTHS) else found


def run_qa(
    input_root: Path = RAW_ROOT, write_report: bool = True
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    direct_snapshot = any(
        (input_root / f"{source}.parquet").exists() for source in SOURCE_NAMES
    )
    months = (
        [input_root.name.removeprefix("bad-")] if direct_snapshot else _months_for_root(input_root)
    )
    missing = [
        str((input_root if direct_snapshot else input_root / month) / f"{source}.parquet")
        for month in months
        for source in SOURCE_NAMES
        if not (
            (input_root if direct_snapshot else input_root / month) / f"{source}.parquet"
        ).exists()
    ]
    if not months:
        missing.append(f"No monthly directories found under {input_root}")
    _check(
        results,
        "monthly_source_files_present",
        len(missing),
        "; ".join(missing[:5]) or "all expected files present",
    )
    if missing:
        report = _report(input_root, months, results)
        if write_report:
            _write_report(report)
        return report

    prior_count: int | None = None
    for month in months:
        folder = input_root if direct_snapshot else input_root / month
        providers = pd.read_parquet(folder / "provider_master.parquet")
        reps = pd.read_parquet(folder / "sales_rep_master.parquet")
        applications = pd.read_parquet(folder / "applications.parquet")
        assignments = pd.read_parquet(
            folder / "application_assignment_events.parquet"
        )
        sales = pd.read_parquet(folder / "financed_sales.parquet")
        locations = pd.read_parquet(folder / "provider_location_reference.parquet")

        for frame, column, label in (
            (providers, "provider_id", "provider_id"),
            (reps, "sales_rep_id", "sales_rep_id"),
            (applications, "application_id", "application_id"),
            (sales, "transaction_id", "transaction_id"),
        ):
            _check(
                results,
                f"{month}_{label}_unique",
                int(frame[column].duplicated().sum()),
                "duplicate identifiers",
            )
        attribution_columns = {"provider_id", "sales_rep_id"}.intersection(
            applications.columns
        )
        _check(
            results,
            f"{month}_raw_application_has_no_attribution",
            len(attribution_columns),
            "raw applications must not carry authoritative attribution",
        )
        _check(
            results,
            f"{month}_provider_rep_relationship",
            int((~providers["sales_rep_id"].isin(reps["sales_rep_id"])).sum()),
            "provider rows reference unknown reps",
        )
        _check(
            results,
            f"{month}_location_provider_relationship",
            int((~locations["provider_id"].isin(providers["provider_id"])).sum()),
            "location rows reference unknown providers",
        )
        _check(
            results,
            f"{month}_assignment_application_relationship",
            int(
                (~assignments["application_id"].isin(applications["application_id"])).sum()
            ),
            "assignment rows reference unknown applications",
        )
        bad_provider = assignments["assigned_provider_id"].notna() & ~assignments[
            "assigned_provider_id"
        ].isin(providers["provider_id"])
        _check(
            results,
            f"{month}_assignment_provider_relationship",
            int(bad_provider.sum()),
            f"{int(bad_provider.sum())} assignment records reference unknown providers",
        )
        _check(
            results,
            f"{month}_sales_application_relationship",
            int((~sales["application_id"].isin(applications["application_id"])).sum()),
            "transactions reference unknown applications",
        )
        nonnegative = int(
            applications[["requested_amount", "approved_amount"]].lt(0).sum().sum()
            + sales["financed_amount"].lt(0).sum()
        )
        _check(
            results,
            f"{month}_nonnegative_amounts",
            nonnegative,
            "negative financial amounts",
        )
        _check(
            results,
            f"{month}_approval_flag_values",
            int((~applications["approval_flag"].isin(("Y", "N"))).sum()),
            "accepted values are Y/N",
        )
        _check(
            results,
            f"{month}_assignment_status_values",
            int(
                (
                    ~assignments["assignment_status"].isin(
                        ("assigned", "manual_review", "unallocated")
                    )
                ).sum()
            ),
            "invalid status",
        )
        _check(
            results,
            f"{month}_assignment_confidence_range",
            int((~assignments["assignment_confidence"].between(0, 1)).sum()),
            "confidence outside [0,1]",
        )
        assignment_dates = assignments.merge(
            applications[["application_id", "application_date"]], on="application_id"
        )
        _check(
            results,
            f"{month}_assignment_date_sequence",
            int(
                (
                    assignment_dates["assignment_date"]
                    < assignment_dates["application_date"]
                ).sum()
            ),
            "assignment before application",
        )
        transaction_dates = sales.merge(
            applications[["application_id", "application_date"]], on="application_id"
        )
        _check(
            results,
            f"{month}_transaction_date_sequence",
            int(
                (
                    transaction_dates["transaction_date"]
                    < transaction_dates["application_date"]
                ).sum()
            ),
            "transaction before application",
        )
        month_end = pd.Timestamp(month + "-01") + pd.offsets.MonthEnd(0)
        _check(
            results,
            f"{month}_no_future_transaction_dates",
            int((transaction_dates["transaction_date"] > month_end).sum()),
            "transaction occurs after the reporting month",
        )
        _check(
            results,
            f"{month}_duplicate_application_detection",
            int(
                applications.duplicated(
                    subset=["application_date", "customer_zip", "requested_amount"]
                ).sum()
            ),
            "possible duplicate applications",
        )
        approved_total = applications["approved_amount"].sum()
        financed_total = sales["financed_amount"].sum()
        _check(
            results,
            f"{month}_financial_control_total",
            int(financed_total > approved_total),
            f"financed={financed_total:.2f}, approved={approved_total:.2f}",
        )
        count = len(applications)
        variance_failure = int(
            prior_count is not None and abs(count / prior_count - 1) > 0.15
        )
        _check(
            results,
            f"{month}_row_count_variance",
            variance_failure,
            f"applications={count}",
        )
        prior_count = count
        assignment_rate = assignments["assignment_status"].eq("assigned").mean()
        _check(
            results,
            f"{month}_assignment_rate_monitoring",
            int(not 0.80 <= assignment_rate <= 1.0),
            f"assignment_rate={assignment_rate:.4f}",
        )

    report = _report(input_root, months, results)
    if write_report:
        _write_report(report)
    return report


def _report(
    input_root: Path, months: list[str], results: list[dict[str, Any]]
) -> dict[str, Any]:
    failed = [result for result in results if result["status"] == "FAIL"]
    return {
        "run_at": datetime.now(UTC).isoformat(),
        "input_root": str(input_root),
        "months": months,
        "status": "FAIL" if failed else "PASS",
        "tests_passed": len(results) - len(failed),
        "tests_failed": len(failed),
        "results": results,
    }


def _write_report(report: dict[str, Any]) -> None:
    QA_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (QA_OUTPUT_ROOT / "latest.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=RAW_ROOT)
    parser.add_argument("--expect-failure", action="store_true")
    args = parser.parse_args()
    report = run_qa(args.input_root)
    print(
        f"DATA QUALITY {report['status']}: "
        f"{report['tests_passed']} passed, {report['tests_failed']} failed"
    )
    for result in report["results"]:
        if result["status"] == "FAIL":
            print(f"- {result['detail']}")
    if args.expect_failure:
        if report["status"] != "FAIL":
            raise SystemExit("Expected controlled fixture to fail")
        return
    if report["status"] != "PASS":
        raise SystemExit(
            "Monthly production refresh halted. No dashboard marts refreshed."
        )


if __name__ == "__main__":
    main()
