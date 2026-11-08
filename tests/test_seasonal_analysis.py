from types import SimpleNamespace

from services.seasonal_analysis import analyze_seasonal_patterns


def tx(day, description, amount, category="Utilities"):
    return SimpleNamespace(
        date=day, description=description, amount=amount, category=category
    )


def year_of_spending(summer_amount=300, other_amount=100):
    """One expense per month for 2025, bigger in Jun-Aug."""
    txs = []
    for m in range(1, 13):
        amount = summer_amount if m in (6, 7, 8) else other_amount
        txs.append(tx(f"2025-{m:02d}-10", "Evergy", -amount))
    return txs


def test_finds_summer_peak():
    result = analyze_seasonal_patterns(year_of_spending())
    assert result["has_data"]
    assert result["has_full_year"]
    assert result["months_covered"] == 12
    assert result["peak_months"] == ["Jun", "Jul", "Aug"]
    summer = next(s for s in result["seasons"] if s["name"] == "Summer")
    winter = next(s for s in result["seasons"] if s["name"] == "Winter")
    assert summer["label"] == "High"
    assert winter["label"] == "Low"
    assert summer["average"] == 300


def test_category_peak_season():
    result = analyze_seasonal_patterns(year_of_spending())
    cat = result["categories"][0]
    assert cat["category"] == "Utilities"
    assert cat["peak_season"] == "Summer"


def test_short_history_warns():
    txs = [tx("2026-09-10", "Rent", -1000), tx("2026-10-10", "Rent", -1000)]
    result = analyze_seasonal_patterns(txs)
    assert not result["has_full_year"]
    assert any("less than 12 months" in n for n in result["notes"])


def test_empty_months_inside_range_count_as_zero():
    txs = [tx("2026-01-10", "A", -100), tx("2026-03-10", "B", -100)]
    result = analyze_seasonal_patterns(txs)
    feb = next(m for m in result["months"] if m["name"] == "Feb")
    assert result["months_covered"] == 3
    assert feb["average"] == 0.0


def test_months_without_data_are_none():
    result = analyze_seasonal_patterns([tx("2026-01-10", "A", -100)])
    mar = next(m for m in result["months"] if m["name"] == "Mar")
    assert mar["average"] is None and mar["index"] is None


def test_income_mode_and_expense_mode_are_separate():
    txs = [tx("2026-01-05", "Paycheck", 5000, "Income"),
           tx("2026-01-10", "Rent", -1000, "Rent")]
    spend = analyze_seasonal_patterns(txs)
    income = analyze_seasonal_patterns(txs, kind="income")
    assert spend["overall_monthly_average"] == 1000
    assert income["overall_monthly_average"] == 5000


def test_bad_dates_and_empty_input():
    assert not analyze_seasonal_patterns([])["has_data"]
    only_bad = analyze_seasonal_patterns([tx("2026-09-31", "X", -5)])
    assert not only_bad["has_data"] and only_bad["skipped"] == 1


def test_gap_months_trigger_a_note():
    txs = [tx("2026-01-10", "A", -100), tx("2026-04-10", "B", -100)]
    notes = analyze_seasonal_patterns(txs)["notes"]
    assert any("2 months in this range have no transactions" in n
               for n in notes)


def test_flat_category_has_no_peak_season():
    txs = [tx(f"2025-{m:02d}-01", "Rent", -1000, "Rent")
           for m in range(1, 13)]
    cat = analyze_seasonal_patterns(txs)["categories"][0]
    assert cat["peak_season"] is None
