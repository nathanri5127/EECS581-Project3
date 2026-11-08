"""Recurring expense detection (Sprint 2).

A recurring expense is a charge from the same merchant that shows up on a
regular schedule (weekly, biweekly, monthly, quarterly or yearly) with a
reasonably stable amount, like rent, Netflix or an electric bill.

The functions here take plain transaction objects (anything with
.date, .description, .amount and .category), so they can be tested
without a database.
"""

#Author Fabrizio Falcón + Claude Sonnet 5.5
import re
from collections import Counter

import pandas as pd

from services.analysis_utils import transactions_to_frame

# label, typical gap in days, allowed +/- days, charges per month,
# and how to step forward one period to predict the next charge.
FREQUENCIES = [
    {"label": "Weekly", "days": 7, "tolerance": 2,
     "per_month": 52 / 12, "step": pd.DateOffset(days=7)},
    {"label": "Biweekly", "days": 14, "tolerance": 3,
     "per_month": 26 / 12, "step": pd.DateOffset(days=14)},
    {"label": "Monthly", "days": 30, "tolerance": 5,
     "per_month": 1.0, "step": pd.DateOffset(months=1)},
    {"label": "Quarterly", "days": 91, "tolerance": 10,
     "per_month": 1 / 3, "step": pd.DateOffset(months=3)},
    {"label": "Yearly", "days": 365, "tolerance": 15,
     "per_month": 1 / 12, "step": pd.DateOffset(years=1)},
]

MIN_OCCURRENCES = 3        # need at least 3 charges to call it a pattern
MIN_REGULARITY = 0.6       # share of gaps that must fit the schedule
FIXED_VARIATION = 0.10     # amounts within ~10% count as "Fixed"
MAX_VARIATION = 0.35       # more variation than this is not a bill


def normalize_description(description):
    """Group "NETFLIX 1234" and "Netflix #5678" under one merchant key."""
    original = str(description).lower().strip()
    text = re.sub(r"[#*]?\d[\d\-/]*", " ", original)  # store numbers, refs
    text = re.sub(r"[^a-z&+' ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or original


def _match_frequency(gaps):
    """Return (frequency, regularity) for a list of day gaps, or (None, 0)."""
    median_gap = float(pd.Series(gaps).median())
    for freq in FREQUENCIES:
        if abs(median_gap - freq["days"]) <= freq["tolerance"]:
            fits = sum(
                1 for g in gaps
                if abs(g - freq["days"]) <= freq["tolerance"]
            )
            return freq, fits / len(gaps)
    return None, 0.0


def find_recurring_expenses(transactions, min_occurrences=MIN_OCCURRENCES):
    """Detect recurring expenses.

    Returns a dict:
      items          list of recurring expenses, biggest monthly cost first
      monthly_total  estimated recurring spend per month
      annual_total   monthly_total * 12
      skipped        rows ignored because the date could not be read
    """
    df, skipped = transactions_to_frame(transactions)
    result = {
        "items": [],
        "monthly_total": 0.0,
        "annual_total": 0.0,
        "skipped": skipped,
    }
    if df.empty:
        return result

    expenses = df[df["amount"] < 0].copy()
    if expenses.empty:
        return result

    expenses["spend"] = -expenses["amount"]
    expenses["key"] = expenses["description"].map(normalize_description)

    items = []
    for _, group in expenses.groupby("key"):
        if len(group) < min_occurrences:
            continue

        group = group.sort_values("date")
        gaps = group["date"].diff().dt.days.dropna().tolist()
        freq, regularity = _match_frequency(gaps)
        if freq is None or regularity < MIN_REGULARITY:
            continue

        mean_spend = float(group["spend"].mean())
        variation = float(group["spend"].std(ddof=0)) / mean_spend
        if variation > MAX_VARIATION:
            continue

        last_date = group["date"].iloc[-1]
        monthly_cost = mean_spend * freq["per_month"]
        items.append({
            "description": Counter(group["description"]).most_common(1)[0][0],
            "category": Counter(group["category"]).most_common(1)[0][0],
            "frequency": freq["label"],
            "occurrences": int(len(group)),
            "average_amount": mean_spend,
            "last_amount": float(group["spend"].iloc[-1]),
            "amount_type": "Fixed" if variation <= FIXED_VARIATION
                           else "Variable",
            "first_date": group["date"].iloc[0].date(),
            "last_date": last_date.date(),
            "next_expected": (last_date + freq["step"]).date(),
            "monthly_cost": monthly_cost,
            "annual_cost": monthly_cost * 12,
        })

    items.sort(key=lambda item: item["monthly_cost"], reverse=True)
    result["items"] = items
    result["monthly_total"] = sum(i["monthly_cost"] for i in items)
    result["annual_total"] = result["monthly_total"] * 12
    return result
