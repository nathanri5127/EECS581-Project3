from decimal import Decimal

import pytest

from services.monte_carlo import MIN_HISTORY_MONTHS, forecast_months


def month(income, expenses):
    return {"income": Decimal(str(income)), "expenses": Decimal(str(expenses))}


def test_not_enough_history_returns_none():
    history = [month(100, 50)] * (MIN_HISTORY_MONTHS - 1)
    assert forecast_months(history) is None
    assert forecast_months([]) is None


@pytest.mark.parametrize("kwargs", [{"months": 0}, {"n": 0}])
def test_rejects_non_positive_arguments(kwargs):
    with pytest.raises(ValueError):
        forecast_months([month(100, 50)] * 3, **kwargs)


def test_identical_surplus_months_are_deterministic():
    result = forecast_months([month(3000, 2000)] * 4)
    assert result["negative_month_probability"] == 0
    # 6 months x $1000 net every time
    assert result["typical_total"] == 6000
    assert result["bad_case_total"] == 6000
    assert result["good_case_total"] == 6000


def test_always_deficit_history():
    result = forecast_months([month(1000, 1500)] * 3)
    assert result["negative_month_probability"] == 1
    assert result["typical_total"] == -3000


def test_break_even_month_is_not_negative():
    result = forecast_months([month(500, 500)] * 3)
    assert result["negative_month_probability"] == 0
    assert result["typical_total"] == 0


def test_negative_month_probability_matches_theory():
    # Income is always 100; expenses are 50 or 150 with equal chance, so
    # each month is negative with p = 0.5 and at least one of 6 months is
    # negative with p = 1 - 0.5**6 = 0.984375.
    history = [month(100, 50), month(100, 150), month(100, 50), month(100, 150)]
    result = forecast_months(history, n=10_000)
    assert result["negative_month_probability"] == pytest.approx(0.984375, abs=0.01)


def test_percentiles_ordered_and_within_bounds():
    history = [month(3000, 2500), month(2000, 2600), month(4000, 1800)]
    result = forecast_months(history)

    assert (
        result["bad_case_total"]
        <= result["typical_total"]
        <= result["good_case_total"]
    )
    # Totals can't go beyond 6 x (lowest income - highest expenses) or
    # 6 x (highest income - lowest expenses).
    assert result["bad_case_total"] >= 6 * (2000 - 2600)
    assert result["good_case_total"] <= 6 * (4000 - 1800)


def test_income_and_expenses_resampled_independently():
    # If months were replayed as (income, expenses) pairs, net would always
    # be 0. Drawing them separately allows negative months.
    history = [month(100, 100), month(200, 200), month(300, 300)]
    result = forecast_months(history)
    assert 0 < result["negative_month_probability"] < 1


def test_same_seed_gives_same_result():
    history = [month(3000, 2500), month(2000, 2600), month(4000, 1800)]
    assert forecast_months(history, seed=1) == forecast_months(history, seed=1)


def test_reports_run_settings():
    result = forecast_months([month(100, 50)] * 5, months=4, n=500)
    assert result["months"] == 4
    assert result["simulations"] == 500
    assert result["history_months"] == 5
