from datetime import date, timedelta
from types import SimpleNamespace

from services.recurring_analysis import (
    find_recurring_expenses,
    normalize_description,
)


def tx(day, description, amount, category="Uncategorized"):
    return SimpleNamespace(
        date=str(day), description=description,
        amount=amount, category=category
    )


def monthly(description, amount, start=date(2026, 1, 1), count=6):
    return [
        tx(date(start.year, start.month + i, start.day), description, amount)
        for i in range(count)
    ]


def test_normalize_description_merges_store_numbers():
    assert normalize_description("NETFLIX 12345") == "netflix"
    assert normalize_description("Netflix #98") == "netflix"
    assert normalize_description("Disney+") == "disney+"


def test_detects_monthly_fixed_expense():
    result = find_recurring_expenses(monthly("Rent", -1000.00))
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["frequency"] == "Monthly"
    assert item["amount_type"] == "Fixed"
    assert item["occurrences"] == 6
    assert round(item["monthly_cost"], 2) == 1000.00
    assert item["next_expected"] == date(2026, 7, 1)


def test_detects_weekly_and_biweekly():
    weekly = [tx(date(2026, 1, 3) + timedelta(days=7 * i), "Dillons", -80)
              for i in range(8)]
    biweekly = [tx(date(2026, 1, 2) + timedelta(days=14 * i), "Gym", -30)
                for i in range(6)]
    result = find_recurring_expenses(weekly + biweekly)
    freqs = {i["description"]: i["frequency"] for i in result["items"]}
    assert freqs == {"Dillons": "Weekly", "Gym": "Biweekly"}


def test_variable_amounts_are_flagged_variable():
    amounts = [-60, -75, -90, -110, -95, -70]
    txs = [tx(date(2026, 1 + i, 15), "Evergy Electric", a)
           for i, a in enumerate(amounts)]
    item = find_recurring_expenses(txs)["items"][0]
    assert item["amount_type"] == "Variable"


def test_ignores_irregular_and_too_few():
    irregular = [tx(d, "Chipotle", -12) for d in
                 [date(2026, 1, 3), date(2026, 1, 5), date(2026, 2, 20),
                  date(2026, 2, 21), date(2026, 4, 9)]]
    too_few = monthly("Hulu", -12, count=2)
    assert find_recurring_expenses(irregular + too_few)["items"] == []


def test_ignores_wildly_varying_amounts():
    txs = [tx(date(2026, 1 + i, 1), "Amazon", a)
           for i, a in enumerate([-5, -300, -20, -450, -8, -200])]
    assert find_recurring_expenses(txs)["items"] == []


def test_income_is_not_reported_as_expense():
    result = find_recurring_expenses(monthly("Paycheck", 5000))
    assert result["items"] == []


def test_bad_dates_are_skipped_not_fatal():
    txs = monthly("Rent", -1000) + [tx("2026-09-31", "Paycheck", 5000)]
    result = find_recurring_expenses(txs)
    assert result["skipped"] == 1
    assert len(result["items"]) == 1


def test_empty_input():
    result = find_recurring_expenses([])
    assert result["items"] == []
    assert result["monthly_total"] == 0.0
