from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from services.monthly_analysis import analyze_monthly, parse_month


def txn(date_value, amount):
    return SimpleNamespace(date=date_value, amount=Decimal(str(amount)))


@pytest.mark.parametrize("value, expected", [
    ("2026-10-01", (2026, 10)),
    ("2026/10/01", (2026, 10)),
    ("2026-10-01 00:00:00", (2026, 10)),
    ("2026-1-5", (2026, 1)),
    ("10/01/2026", (2026, 10)),
    ("1-5-2026", (2026, 1)),
    # Invalid day still identifies the month (appears in test_transactions.csv)
    ("2026-09-31", (2026, 9)),
    (date(2026, 3, 15), (2026, 3)),
])
def test_parse_month_valid(value, expected):
    assert parse_month(value) == expected


@pytest.mark.parametrize("value", [
    None, "", "NOT A DATE", "2026-13-01", "13/01/2026", "Oct 2026",
])
def test_parse_month_invalid(value):
    assert parse_month(value) is None


def test_empty_transactions():
    result = analyze_monthly([])
    assert result["months"] == []
    assert result["average_income"] == Decimal("0")
    assert result["average_expenses"] == Decimal("0")
    assert result["deficit_count"] == 0
    assert result["unparsed_count"] == 0


def test_groups_by_month_and_totals():
    result = analyze_monthly([
        txn("2026-10-01", 5000),
        txn("2026-10-02", -1000),
        txn("2026-10-15", -100.50),
        txn("2026-11-01", 2000),
        txn("2026-11-03", -2500),
    ])

    october, november = result["months"]

    assert october["label"] == "October 2026"
    assert october["income"] == Decimal("5000")
    assert october["expenses"] == Decimal("1100.50")
    assert october["net"] == Decimal("3899.50")
    assert october["transaction_count"] == 3
    assert october["is_deficit"] is False

    assert november["label"] == "November 2026"
    assert november["income"] == Decimal("2000")
    assert november["expenses"] == Decimal("2500")
    assert november["net"] == Decimal("-500")
    assert november["is_deficit"] is True

    assert result["deficit_count"] == 1


def test_months_sorted_chronologically_across_years():
    result = analyze_monthly([
        txn("2026-02-01", 10),
        txn("2025-12-01", 10),
        txn("2026-01-01", 10),
    ])
    keys = [(m["year"], m["month"]) for m in result["months"]]
    assert keys == [(2025, 12), (2026, 1), (2026, 2)]


def test_same_month_different_years_kept_separate():
    result = analyze_monthly([
        txn("2025-10-01", 100),
        txn("2026-10-01", 300),
    ])
    assert [m["income"] for m in result["months"]] == [
        Decimal("100"), Decimal("300")
    ]


def test_averages_over_months_with_data():
    result = analyze_monthly([
        txn("2026-01-10", 3000),
        txn("2026-01-11", -1000),
        txn("2026-02-10", 1000),
        txn("2026-02-11", -2000),
        txn("2026-03-10", 2000),
    ])
    # Income: 3000 + 1000 + 2000 = 6000 over 3 months
    assert result["average_income"] == Decimal("2000.00")
    # Expenses: 1000 + 2000 + 0 = 3000 over 3 months
    assert result["average_expenses"] == Decimal("1000.00")


def test_averages_rounded_to_cents():
    result = analyze_monthly([
        txn("2026-01-01", 100),
        txn("2026-02-01", 100),
        txn("2026-03-01", 101),
    ])
    assert result["average_income"] == Decimal("100.33")


def test_deficit_requires_expenses_strictly_greater():
    result = analyze_monthly([
        txn("2026-01-01", 500),
        txn("2026-01-02", -500),
    ])
    month = result["months"][0]
    assert month["net"] == Decimal("0")
    assert month["is_deficit"] is False


def test_expense_only_month_is_deficit():
    result = analyze_monthly([txn("2026-04-01", -20)])
    month = result["months"][0]
    assert month["income"] == Decimal("0")
    assert month["expenses"] == Decimal("20")
    assert month["is_deficit"] is True


def test_zero_amount_counted_but_not_totaled():
    result = analyze_monthly([txn("2026-04-01", 0)])
    month = result["months"][0]
    assert month["transaction_count"] == 1
    assert month["income"] == month["expenses"] == Decimal("0")


def test_unparseable_dates_skipped_and_counted():
    result = analyze_monthly([
        txn("2026-10-01", 100),
        txn("NOT A TRANSACTION", -10000),
    ])
    assert len(result["months"]) == 1
    assert result["months"][0]["expenses"] == Decimal("0")
    assert result["unparsed_count"] == 1


def test_float_amounts_do_not_drift():
    transactions = [
        SimpleNamespace(date="2026-05-01", amount=0.1),
        SimpleNamespace(date="2026-05-02", amount=0.2),
    ]
    result = analyze_monthly(transactions)
    assert result["months"][0]["income"] == Decimal("0.3")
