"""Seasonal spending patterns (Sprint 2).

Looks at how spending (or income) changes across the calendar: by month
of the year, by season, and by category. Seasons use the northern
hemisphere calendar (Winter = Dec-Feb, Spring = Mar-May, Summer = Jun-Aug,
Fall = Sep-Nov).

A "seasonal index" is a month's (or season's) average divided by the
overall monthly average. 1.00 is typical, 1.30 is 30% above typical.
"""

# Author Claude Sonnet 5.5 supervised and tested by Fabrizio Falcón
import calendar

import pandas as pd

from services.analysis_utils import transactions_to_frame

SEASON_OF_MONTH = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Fall", 10: "Fall", 11: "Fall",
}
SEASON_ORDER = ["Winter", "Spring", "Summer", "Fall"]

HIGH_INDEX = 1.15   # 15% or more above the usual month
LOW_INDEX = 0.85    # 15% or more below the usual month
TOP_CATEGORIES = 6


def _label(index):
    if index is None:
        return None
    if index >= HIGH_INDEX:
        return "High"
    if index <= LOW_INDEX:
        return "Low"
    return "Normal"


def _empty(skipped, kind):
    return {
        "has_data": False,
        "kind": kind,
        "skipped": skipped,
        "months_covered": 0,
        "has_full_year": False,
        "overall_monthly_average": 0.0,
        "months": [],
        "seasons": [],
        "categories": [],
        "peak_months": [],
        "low_months": [],
        "notes": [],
    }


def analyze_seasonal_patterns(transactions, kind="expense"):
    """Analyze seasonal patterns in spending (kind="expense") or income
    (kind="income")."""
    df, skipped = transactions_to_frame(transactions)
    if df.empty:
        return _empty(skipped, kind)
    all_periods = set(df["date"].dt.to_period("M"))

    sign = -1 if kind == "expense" else 1
    df = df[df["amount"] * sign > 0].copy()
    if df.empty:
        return _empty(skipped, kind)
    df["value"] = df["amount"].abs()
    df["period"] = df["date"].dt.to_period("M")

    # One total per calendar month across the whole date range. Months with
    # no matching transactions count as 0 instead of being left out.
    full_range = pd.period_range(df["period"].min(), df["period"].max(),
                                 freq="M")
    monthly = (df.groupby("period")["value"].sum()
                 .reindex(full_range, fill_value=0.0))
    months_covered = len(monthly)
    overall_avg = float(monthly.mean())

    month_number = monthly.index.month
    month_season = [SEASON_OF_MONTH[m] for m in month_number]

    # By calendar month (Jan..Dec), averaged over every year we have.
    months = []
    for m in range(1, 13):
        mask = month_number == m
        observed = int(mask.sum())
        avg = float(monthly[mask].mean()) if observed else None
        index = (avg / overall_avg) if (observed and overall_avg) else None
        months.append({
            "number": m,
            "name": calendar.month_abbr[m],
            "average": avg,
            "observations": observed,
            "index": index,
            "label": _label(index),
        })

    # By season.
    seasons = []
    for season in SEASON_ORDER:
        mask = pd.Series(month_season) == season
        observed = int(mask.sum())
        avg = float(monthly.values[mask.values].mean()) if observed else None
        index = (avg / overall_avg) if (observed and overall_avg) else None
        seasons.append({
            "name": season,
            "average": avg,
            "observations": observed,
            "index": index,
            "label": _label(index),
        })

    # By category: average monthly amount in each season, for the biggest
    # categories, plus which season is the peak.
    categories = []
    top = (df.groupby("category")["value"].sum()
             .sort_values(ascending=False).head(TOP_CATEGORIES).index)
    for category in top:
        cat_monthly = (df[df["category"] == category]
                       .groupby("period")["value"].sum()
                       .reindex(full_range, fill_value=0.0))
        cat_avg = float(cat_monthly.mean())
        by_season = {}
        for season in SEASON_ORDER:
            mask = (pd.Series(month_season) == season).values
            by_season[season] = (float(cat_monthly.values[mask].mean())
                                 if mask.any() else None)
        observed = {s: v for s, v in by_season.items() if v is not None}
        peak = max(observed, key=observed.get)
        peak_ratio = (observed[peak] / cat_avg) if cat_avg else None
        if peak_ratio is None or peak_ratio < HIGH_INDEX:
            peak = None  # flat category, no real peak
        categories.append({
            "category": category,
            "total": float(df[df["category"] == category]["value"].sum()),
            "monthly_average": cat_avg,
            "by_season": by_season,
            "peak_season": peak,
            "peak_ratio": peak_ratio,
        })

    has_full_year = months_covered >= 12
    notes = []
    if not has_full_year:
        notes.append(
            f"Your data covers {months_covered} month"
            f"{'s' if months_covered != 1 else ''}. With less than 12 months "
            "these numbers show what you spent in each month, but they "
            "cannot confirm a true yearly pattern yet."
        )
    empty_months = months_covered - len(all_periods)
    if empty_months > 0:
        notes.append(
            f"{empty_months} month{'s' if empty_months != 1 else ''} in this "
            "range have no transactions at all and are counted as $0, which "
            "pulls the averages down. If that is just a gap in your uploads, "
            "add the missing statements for more accurate results."
        )
    notes.append(
        "The first and last months of an export are often partial, which can "
        "make them look lower than they really were."
    )

    observed_months = [m for m in months if m["index"] is not None]
    return {
        "has_data": True,
        "kind": kind,
        "skipped": skipped,
        "months_covered": months_covered,
        "has_full_year": has_full_year,
        "overall_monthly_average": overall_avg,
        "months": months,
        "seasons": seasons,
        "categories": categories,
        "peak_months": [m["name"] for m in observed_months
                        if m["label"] == "High"],
        "low_months": [m["name"] for m in observed_months
                       if m["label"] == "Low"],
        "notes": notes,
    }
