"""
Tests for services/income_stability.py.

These call income_stability() directly with hand-made month data, so they
don't need the database or the Flask app.
"""
from decimal import Decimal

import pytest

from services.income_stability import (
    MODERATE_THRESHOLD,
    STABLE_THRESHOLD,
    income_stability,
    stability_label,
)
from services.monte_carlo import MIN_HISTORY_MONTHS


def month(income):
    """Build one month in the same shape analyze_monthly returns."""
    return {"income": Decimal(str(income))}


def test_not_enough_history_returns_none():
    # No months, and one month short of the minimum, both give no score.
    assert income_stability([]) is None
    assert income_stability([month(1000)] * (MIN_HISTORY_MONTHS - 1)) is None


def test_identical_income_scores_100():
    # Same paycheck every month: no variation at all.
    result = income_stability([month(2500)] * 4)
    assert result["score"] == 100
    assert result["label"] == "Stable"
    assert result["coefficient_of_variation"] == 0
    assert result["months_used"] == 4


def test_known_coefficient_of_variation():
    # Worked by hand: mean 1000, population std 200 -> CV 0.2 -> score 80.
    result = income_stability([month(800), month(1200), month(800), month(1200)])
    assert result["coefficient_of_variation"] == pytest.approx(0.2)
    assert result["score"] == 80
    assert result["label"] == "Stable"
    assert result["average_income"] == 1000


def test_steady_income_scores_higher_than_varying_income():
    # Small swings around $3000 vs. large swings between $500 and $4000.
    steady = income_stability([month(3000), month(3100), month(2900)])
    varying = income_stability([month(500), month(4000), month(1500)])
    assert steady["score"] > varying["score"]


def test_huge_swings_clamp_to_zero():
    # One big month and two empty ones gives CV > 1, which would be a
    # negative score without the clamp.
    result = income_stability([month(9000), month(0), month(0)])
    assert result["score"] == 0
    assert result["label"] == "Volatile"
    assert result["months_without_income"] == 2


def test_no_income_at_all_does_not_divide_by_zero():
    # Mean income is 0, so CV can't be computed; must not crash.
    result = income_stability([month(0)] * 3)
    assert result["score"] == 0
    assert result["label"] == "Volatile"
    assert result["coefficient_of_variation"] is None
    assert result["months_without_income"] == 3


def test_score_is_always_between_0_and_100():
    # A few unrelated income patterns, from tiny to very uneven.
    for incomes in ([1, 2, 3], [100, 0, 50, 0], [5000, 5001, 4999]):
        score = income_stability([month(i) for i in incomes])["score"]
        assert 0 <= score <= 100


# Each threshold should belong to the higher label, and one point below
# it to the next label down.
@pytest.mark.parametrize("score, label", [
    (100, "Stable"),
    (STABLE_THRESHOLD, "Stable"),
    (STABLE_THRESHOLD - 1, "Moderate"),
    (MODERATE_THRESHOLD, "Moderate"),
    (MODERATE_THRESHOLD - 1, "Volatile"),
    (0, "Volatile"),
])
def test_label_boundaries(score, label):
    assert stability_label(score) == label
