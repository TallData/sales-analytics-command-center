"""Generate deterministic monthly Parquet snapshots for a fictional portfolio."""

from __future__ import annotations

import argparse
import calendar
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import BASE_SEED, FIXTURE_ROOT, MONTHS, RAW_ROOT

REGION_TERRITORIES = {
    "Northeast": ("New England", "Metro New York", "Mid-Atlantic", "Allegheny", "Capital"),
    "Southeast": ("Carolinas", "Georgia", "Florida North", "Florida South", "Tennessee"),
    "Central": ("Great Lakes", "Ohio Valley", "Upper Midwest", "Plains", "Texas North"),
    "West": (
        "Pacific Northwest",
        "Northern California",
        "Southern California",
        "Mountain",
        "Desert",
    ),
}
REGION_STATES = {
    "Northeast": ("MA", "NY", "PA", "NJ", "MD"),
    "Southeast": ("NC", "GA", "FL", "SC", "TN"),
    "Central": ("IL", "OH", "MN", "MO", "TX"),
    "West": ("WA", "CA", "CA", "CO", "AZ"),
}
SPECIALTIES = ("Dental", "Veterinary", "Vision", "Audiology", "Cosmetic", "Specialty Healthcare")
SEGMENTS = ("Emerging", "Growth", "Established", "Strategic")
PRODUCTS = ("Standard Plan", "Extended Plan", "Promotional Plan")
FIRST_NAMES = ("Avery", "Blake", "Cameron", "Dakota", "Emery", "Frankie", "Harper", "Jordan")
LAST_NAMES = ("Brooks", "Chen", "Diaz", "Ellis", "Foster", "Gray", "Hayes", "Iqbal")


@dataclass(frozen=True)
class MonthProfile:
    applications: int
    assignment_rate: float
    manual_review_rate: float
    growth_factor: float


PROFILES = {
    "2026-01": MonthProfile(13_500, 0.970, 0.010, 1.00),
    "2026-02": MonthProfile(13_900, 0.972, 0.010, 1.02),
    "2026-03": MonthProfile(14_300, 0.975, 0.009, 1.04),
    "2026-04": MonthProfile(14_700, 0.971, 0.010, 1.06),
    "2026-05": MonthProfile(15_000, 0.969, 0.011, 1.05),
    "2026-06": MonthProfile(15_200, 0.968, 0.012, 1.03),
    "2026-07": MonthProfile(15_000, 0.930, 0.025, 1.00),
    "2026-08": MonthProfile(14_800, 0.890, 0.035, 0.96),
}


def _rng(label: str) -> np.random.Generator:
    """Return a stable generator independent of Python's randomized hash."""
    offset = sum((index + 1) * ord(char) for index, char in enumerate(label))
    return np.random.default_rng(BASE_SEED + offset)


def build_sales_reps() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    rep_number = 1
    for region_index, (region, territories) in enumerate(REGION_TERRITORIES.items()):
        for territory_index, territory in enumerate(territories):
            rep_count = 4 if territory_index < 2 else 3
            for slot in range(rep_count):
                first = FIRST_NAMES[(rep_number + slot) % len(FIRST_NAMES)]
                last = LAST_NAMES[(rep_number * 3 + slot) % len(LAST_NAMES)]
                rows.append(
                    {
                        "sales_rep_id": f"REP{rep_number:03d}",
                        "sales_rep_name": f"{first} {last}",
                        "region": region,
                        "territory": territory,
                        "manager_name": f"Manager {region_index + 1}",
                        "hire_date": pd.Timestamp("2019-01-01")
                        + pd.Timedelta(days=(rep_number * 41) % 2100),
                        "status": "active" if rep_number % 31 else "leave",
                    }
                )
                rep_number += 1
    return pd.DataFrame(rows)


def build_providers(reps: pd.DataFrame) -> pd.DataFrame:
    rng = _rng("providers")
    rows: list[dict[str, object]] = []
    reps_by_territory = {
        territory: frame["sales_rep_id"].tolist()
        for territory, frame in reps.groupby("territory")
    }
    territories = [
        (region, territory)
        for region, values in REGION_TERRITORIES.items()
        for territory in values
    ]
    for index in range(2_500):
        region, territory = territories[index % len(territories)]
        territory_index = REGION_TERRITORIES[region].index(territory)
        state = REGION_STATES[region][territory_index]
        specialty = SPECIALTIES[index % len(SPECIALTIES)]
        activation_date = pd.Timestamp("2017-01-01") + pd.Timedelta(
            days=int(rng.integers(0, 3280))
        )
        rows.append(
            {
                "provider_id": f"PRV{index + 1:05d}",
                "provider_name": f"{territory} {specialty} Center {index + 1:04d}",
                "provider_type": "Group" if index % 5 == 0 else "Independent",
                "specialty": specialty,
                "segment": SEGMENTS[
                    int(rng.choice(len(SEGMENTS), p=[0.30, 0.32, 0.25, 0.13]))
                ],
                "provider_zip": f"{(10000 + len(region) * 7000 + index * 37) % 90000 + 10000:05d}",
                "provider_state": state,
                "region": region,
                "territory": territory,
                "sales_rep_id": reps_by_territory[territory][
                    index % len(reps_by_territory[territory])
                ],
                "activation_date": activation_date,
                "status": "inactive" if index % 47 == 0 else "active",
                "employee_band": ("1-9", "10-24", "25-49", "50+")[index % 4],
                "annual_volume_band": ("Under $250K", "$250K-$1M", "$1M-$3M", "$3M+")
                [index % 4],
            }
        )
    return pd.DataFrame(rows)


def _month_dates(month: str, count: int, rng: np.random.Generator) -> pd.DatetimeIndex:
    year, month_number = map(int, month.split("-"))
    days = calendar.monthrange(year, month_number)[1]
    return pd.to_datetime(
        {
            "year": year,
            "month": month_number,
            "day": rng.integers(1, days + 1, size=count),
        }
    )


def _provider_weights(providers: pd.DataFrame, month: str) -> np.ndarray:
    base = providers["segment"].map(
        {"Emerging": 0.7, "Growth": 1.0, "Established": 1.3, "Strategic": 1.7}
    ).to_numpy(float)
    if month >= "2026-05":
        southeast = providers["region"].eq("Southeast").to_numpy()
        selected = providers["territory"].isin(
            ("Carolinas", "Georgia", "Florida North")
        ).to_numpy()
        base[southeast] *= 0.94
        base[selected] *= (
            0.88 if month == "2026-05" else 0.77 if month == "2026-06" else 0.69
        )
    return base / base.sum()


def generate_month(month: str, output_root: Path = RAW_ROOT) -> dict[str, pd.DataFrame]:
    profile = PROFILES.get(month, MonthProfile(14_800, 0.95, 0.02, 1.0))
    rng = _rng(month)
    reps = build_sales_reps()
    providers = build_providers(reps)
    count = profile.applications
    application_dates = _month_dates(month, count, rng)
    candidate_indexes = rng.choice(
        len(providers), size=count, p=_provider_weights(providers, month)
    )
    candidates = providers.iloc[candidate_indexes].reset_index(drop=True)
    requested = np.round(rng.lognormal(mean=8.0, sigma=0.55, size=count), 2)
    approval_probability = np.where(candidates["segment"].eq("Strategic"), 0.76, 0.68)
    approved = rng.random(count) < approval_probability
    approved_amount = np.where(
        approved, requested * rng.uniform(0.68, 1.0, size=count), 0.0
    ).round(2)
    converted = approved & (rng.random(count) < 0.48)
    intake_attributed = np.zeros(count, dtype=bool)
    intake_attributed[: count // 2] = True
    rng.shuffle(intake_attributed)
    applications = pd.DataFrame(
        {
            "application_id": [
                f"APP{month.replace('-', '')}{value:06d}" for value in range(1, count + 1)
            ],
            "application_date": application_dates,
            "application_month": month,
            "customer_zip": candidates["provider_zip"].to_numpy(),
            "customer_state": candidates["provider_state"].to_numpy(),
            # Intake attribution is a source-provided hint. The assignment event remains
            # the authoritative downstream state used by sales analytics.
            "provider_id": candidates["provider_id"].where(intake_attributed),
            "sales_rep_id": candidates["sales_rep_id"].where(intake_attributed),
            "requested_amount": requested,
            "approval_flag": np.where(approved, "Y", "N"),
            "approved_amount": approved_amount,
            "decline_flag": np.where(approved, "N", "Y"),
            "conversion_flag": np.where(converted, "Y", "N"),
            "digital_source": rng.choice(
                ("central_web", "central_mobile", "provider_qr"),
                size=count,
                p=(0.62, 0.30, 0.08),
            ),
        }
    )

    known_assignment_probability = 0.995
    unknown_assignment_probability = np.clip(
        2 * profile.assignment_rate - known_assignment_probability, 0, 1
    )
    assignment_probability = np.where(
        intake_attributed,
        known_assignment_probability,
        unknown_assignment_probability,
    )
    assigned = rng.random(count) < assignment_probability
    remaining = ~assigned
    manual_probability = profile.manual_review_rate / (1 - profile.assignment_rate)
    manual = remaining & (rng.random(count) < manual_probability)
    confidence = np.where(
        assigned,
        rng.beta(18, 2, size=count),
        np.where(
            manual,
            rng.uniform(0.55, 0.82, size=count),
            rng.uniform(0.05, 0.60, size=count),
        ),
    )
    methods = np.where(
        confidence >= 0.95,
        "exact_synthetic_match",
        np.where(confidence >= 0.90, "provider_session_match", "geographic_temporal_match"),
    )
    lag_days = np.where(
        assigned,
        rng.choice((0, 1, 2, 3), count, p=(0.55, 0.28, 0.12, 0.05)),
        0,
    )
    assignments = pd.DataFrame(
        {
            "assignment_event_id": [
                f"ASN{month.replace('-', '')}{value:06d}" for value in range(1, count + 1)
            ],
            "application_id": applications["application_id"],
            "assignment_date": pd.Series(application_dates)
            + pd.to_timedelta(lag_days, unit="D"),
            "assigned_provider_id": candidates["provider_id"].where(assigned),
            "assignment_method": pd.Series(methods).where(
                assigned, np.where(manual, "manual_review", "insufficient_evidence")
            ),
            "assignment_confidence": confidence.round(4),
            "assignment_status": np.where(
                assigned, "assigned", np.where(manual, "manual_review", "unallocated")
            ),
            "assigned_by": np.where(
                assigned & (confidence >= 0.9),
                "rules_engine",
                np.where(
                    assigned,
                    "system_match",
                    np.where(manual, "analyst_review", "rules_engine"),
                ),
            ),
        }
    )

    financed_mask = converted & assigned
    financed_count = int(financed_mask.sum())
    transaction_dates = pd.Series(
        applications.loc[financed_mask, "application_date"].to_numpy()
        + pd.to_timedelta(rng.integers(0, 8, size=financed_count), unit="D")
    ).clip(upper=pd.Timestamp(month + "-01") + pd.offsets.MonthEnd(0))
    financed_sales = pd.DataFrame(
        {
            "transaction_id": [
                f"TXN{month.replace('-', '')}{value:06d}"
                for value in range(1, financed_count + 1)
            ],
            "application_id": applications.loc[
                financed_mask, "application_id"
            ].to_numpy(),
            "transaction_date": transaction_dates,
            "financed_amount": (
                applications.loc[financed_mask, "approved_amount"].to_numpy()
                * rng.uniform(0.88, 1.0, size=financed_count)
            ).round(2),
            "product_type": rng.choice(
                PRODUCTS, size=financed_count, p=(0.50, 0.30, 0.20)
            ),
        }
    )

    assigned_counts = assignments.loc[assigned].groupby("assigned_provider_id").size()
    provider_activity = providers[["provider_id"]].copy()
    provider_activity.insert(0, "month", month)
    provider_activity["applications_count"] = (
        provider_activity["provider_id"].map(assigned_counts).fillna(0).astype(int)
    )
    active_probability = np.full(len(providers), 0.83)
    if month >= "2026-05":
        affected = providers["territory"].isin(
            ("Carolinas", "Georgia", "Florida North")
        ).to_numpy()
        active_probability[affected] -= (
            0.10 if month == "2026-05" else 0.18 if month == "2026-06" else 0.24
        )
    provider_activity["active_flag"] = np.where(
        rng.random(len(providers)) < active_probability, "Y", "N"
    )
    provider_activity["training_completed_flag"] = np.where(
        rng.random(len(providers)) < 0.71, "Y", "N"
    )
    provider_activity["rep_contact_count"] = rng.poisson(1.8, len(providers))
    provider_activity["days_since_last_transaction"] = np.where(
        provider_activity["applications_count"] > 0,
        rng.integers(0, 30, len(providers)),
        rng.integers(30, 180, len(providers)),
    )

    goals = reps[["sales_rep_id"]].copy()
    goals.insert(0, "month", month)
    goals["sales_goal"] = np.round(
        1_100_000 * profile.growth_factor * rng.uniform(0.82, 1.18, len(reps)), 2
    )
    goals["application_goal"] = rng.integers(205, 285, len(reps))
    goals["activation_goal"] = rng.integers(25, 42, len(reps))

    pipeline_count = 520
    pipe_provider_indexes = rng.choice(len(providers), pipeline_count, replace=False)
    pipe_providers = providers.iloc[pipe_provider_indexes].reset_index(drop=True)
    pipeline = pd.DataFrame(
        {
            "opportunity_id": [
                f"OPP{month.replace('-', '')}{value:05d}"
                for value in range(1, pipeline_count + 1)
            ],
            "month": month,
            "provider_id": pipe_providers["provider_id"],
            "sales_rep_id": pipe_providers["sales_rep_id"],
            "stage": rng.choice(
                ("Prospecting", "Qualified", "Proposal", "Commit"),
                pipeline_count,
                p=(0.25, 0.35, 0.25, 0.15),
            ),
            "estimated_volume": np.round(
                rng.lognormal(10.2, 0.65, pipeline_count), 2
            ),
            "probability": rng.choice((0.10, 0.35, 0.60, 0.85), pipeline_count),
            "expected_close_date": pd.Timestamp(month + "-01")
            + pd.to_timedelta(rng.integers(15, 90, pipeline_count), unit="D"),
            "initiative_type": rng.choice(
                ("New activation", "Reactivation", "Training", "Expansion"),
                pipeline_count,
            ),
        }
    )

    provider_locations = providers[
        [
            "provider_id",
            "provider_zip",
            "provider_state",
            "specialty",
            "sales_rep_id",
            "territory",
            "region",
        ]
    ].copy()
    provider_locations["active_flag"] = np.where(
        providers["status"].eq("active"), "Y", "N"
    )
    frames = {
        "provider_master": providers,
        "sales_rep_master": reps,
        "applications": applications,
        "application_assignment_events": assignments,
        "provider_location_reference": provider_locations,
        "financed_sales": financed_sales,
        "provider_activity": provider_activity,
        "sales_goals": goals,
        "pipeline": pipeline,
    }
    month_dir = output_root / month
    month_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_parquet(month_dir / f"{name}.parquet", index=False)
    return frames


def generate_all(output_root: Path = RAW_ROOT) -> None:
    for month in MONTHS:
        generate_month(month, output_root)


def generate_bad_data_fixture() -> Path:
    fixture = FIXTURE_ROOT / "bad-2026-09"
    generate_month("2026-09", FIXTURE_ROOT)
    generated = FIXTURE_ROOT / "2026-09"
    if fixture.exists():
        shutil.rmtree(fixture)
    generated.rename(fixture)
    path = fixture / "application_assignment_events.parquet"
    assignments = pd.read_parquet(path)
    assigned_rows = assignments.index[
        assignments["assignment_status"].eq("assigned")
    ][:17]
    assignments.loc[assigned_rows, "assigned_provider_id"] = [
        f"UNKNOWN{i:03d}" for i in range(1, 18)
    ]
    assignments.to_parquet(path, index=False)
    return fixture


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--month", help="Generate one month in YYYY-MM format")
    group.add_argument("--bad-data-fixture", action="store_true")
    group.add_argument("--clean", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.clean:
        for path in (RAW_ROOT, FIXTURE_ROOT):
            if path.exists():
                shutil.rmtree(path)
        return
    if args.bad_data_fixture:
        print(f"Created controlled failure fixture: {generate_bad_data_fixture()}")
        return
    if args.all:
        generate_all()
        print(f"Generated {len(MONTHS)} monthly snapshots in {RAW_ROOT}")
        return
    generate_month(args.month)
    print(f"Generated {args.month} in {RAW_ROOT / args.month}")


if __name__ == "__main__":
    main()
