"""
Description:
Calculates the income stability score (0-100): how steady a user's
monthly income is.

Responsibilities:
- Score month-to-month income variation
- Label the score as Stable, Moderate, or Volatile

Dependencies:
- numpy
- services.monte_carlo (MIN_HISTORY_MONTHS)

Method:
  CV = std(monthly income) / mean(monthly income)
  score = 100 * (1 - CV), clamped to 0-100
  e.g. income 800, 1200, 800, 1200 -> CV 0.2 -> score 80
"""

#Author: Maxwell Phachanla + Claude Sonnet 5.5

import numpy as np

# Same minimum as the forecast, so both appear together.
from services.monte_carlo import MIN_HISTORY_MONTHS

# Lowest score for each label; below MODERATE_THRESHOLD is "Volatile".
STABLE_THRESHOLD = 80
MODERATE_THRESHOLD = 50


def stability_label(score):
    """Return the label for a 0-100 stability score."""
    if score >= STABLE_THRESHOLD:
        return "Stable"
    if score >= MODERATE_THRESHOLD:
        return "Moderate"
    return "Volatile"


def income_stability(months):
    """
    Score how consistent monthly income is.

    `months` is the "months" list from analyze_monthly.

    Returns None if there are fewer than MIN_HISTORY_MONTHS months,
    otherwise a dict with score, label, coefficient_of_variation,
    average_income, months_used, and months_without_income.
    """
    # Too little history to judge.
    if len(months) < MIN_HISTORY_MONTHS:
        return None

    # analyze_monthly returns Decimals; numpy needs floats.
    income = np.array([float(m["income"]) for m in months])
    mean = float(income.mean())
    months_without_income = int((income == 0).sum())

    # No income at all; also avoids dividing by zero below.
    if mean <= 0:
        return {
            "score": 0,
            "label": "Volatile",
            "coefficient_of_variation": None,
            "average_income": 0.0,
            "months_used": len(months),
            "months_without_income": months_without_income,
        }

    # Dividing by the mean makes the score independent of income level.
    cv = float(income.std()) / mean

    # Clamp so a CV above 1 scores 0 instead of going negative.
    score = int(round(100 * max(0.0, 1 - cv)))

    return {
        "score": score,
        "label": stability_label(score),
        "coefficient_of_variation": round(cv, 3),
        "average_income": round(mean, 2),
        "months_used": len(months),
        "months_without_income": months_without_income,
    }