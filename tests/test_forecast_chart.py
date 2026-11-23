## Test that the forecast charts are hidden if there is not enough history.
# Co-Authored by Claude code using Opus5.5 on 11/21/26, verified by Aidan
## More tests for the forecast charts are in test_forecast_chart.py, which tests the chart generation functions directly.
import calendar
from decimal import Decimal

import pytest

from services.forecast_chart import (
    HISTORY_MONTHS_SHOWN,
    PLOT_BOTTOM,
    PLOT_LEFT,
    PLOT_RIGHT,
    PLOT_TOP,
    cumulative_chart,
    forecast_charts,
    money,
    money_label,
    monthly_chart,
    nice_ticks,
)
from services.monte_carlo import forecast_months

## Test that the forecast charts are hidden if there is not enough history.
def month(year, month_number, income, expenses):
    income, expenses = Decimal(str(income)), Decimal(str(expenses))
    return {
        "year": year,
        "month": month_number,
        "label": f"{calendar.month_name[month_number]} {year}",
        "income": income,
        "expenses": expenses,
        "net": income - expenses,
    }


def varied_history():
    return [
        month(2026, 7, 3000, 2500),
        month(2026, 8, 2000, 2600),
        month(2026, 9, 4000, 1800),
        month(2026, 10, 2500, 2400),
    ]


# --- forecast bands from the Monte Carlo service ---------------------------
# The following tests check that the forecast_months() function produces the expected bands and totals for various histories. They also check that the labels for the forecast months are generated correctly based on the last month of history.
def test_bands_labelled_after_last_history_month():
    history = [month(2026, 10, 100, 50), month(2026, 11, 100, 50), month(2026, 12, 100, 50)]
    bands = forecast_months(history, months=3)["bands"]
    assert [b["label"] for b in bands] == ["January 2027", "February 2027", "March 2027"]

# If the last month of history is not available, fall back to generic labels.
def test_bands_fall_back_to_generic_labels():
    history = [{"income": 100, "expenses": 50}] * 3
    bands = forecast_months(history, months=2)["bands"]
    assert [b["label"] for b in bands] == ["Month 1", "Month 2"]

# The following tests check that the forecast_months() function produces the expected bands and totals for various histories. They also check that the labels for the forecast months are generated correctly based on the last month of history.
def test_bands_for_certain_history():
    history = [month(2026, m, 3000, 2000) for m in (8, 9, 10)]
    bands = forecast_months(history)["bands"]
    assert len(bands) == 6
    for i, b in enumerate(bands, start=1):
        assert b["net_low"] == b["net_typical"] == b["net_high"] == 1000
        assert b["cumulative_low"] == b["cumulative_typical"] == b["cumulative_high"] == 1000 * i

# The following tests check that the forecast_months() function produces the expected bands and totals for various histories. They also check that the labels for the forecast months are generated correctly based on the last month of history.
def test_bands_ordered_and_last_cumulative_matches_totals():
    result = forecast_months(varied_history())
    for b in result["bands"]:
        assert b["net_low"] <= b["net_typical"] <= b["net_high"]
        assert b["cumulative_low"] <= b["cumulative_typical"] <= b["cumulative_high"]
    last = result["bands"][-1]
    assert last["cumulative_low"] == result["bad_case_total"]
    assert last["cumulative_typical"] == result["typical_total"]
    assert last["cumulative_high"] == result["good_case_total"]


# --- helpers ----------------------------------------------------------------
# The following tests check that the helper functions for generating chart geometry and labels work as expected. They verify that the chart points, ranges, and labels are positioned correctly based on the forecast data.
@pytest.mark.parametrize("low, high", [(0, 6000), (-3000, 0), (-650, 4200), (5, 5), (0, 0)])
def test_nice_ticks_cover_range_and_are_even(low, high):
    ticks = nice_ticks(low, high)
    assert ticks[0] <= low and ticks[-1] >= high
    assert ticks[0] < ticks[-1]
    steps = {round(b - a, 6) for a, b in zip(ticks, ticks[1:])}
    assert len(steps) == 1

# The following tests check that the helper functions for generating chart geometry and labels work as expected. They verify that the chart points, ranges, and labels are positioned correctly based on the forecast data.
def test_money_labels():
    assert money_label(0) == "$0"
    assert money_label(1500) == "$1.5k"
    assert money_label(-2000) == "-$2k"
    assert money_label(-250) == "-$250"
    assert money(-1234.5) == "-$1,234.50"
    assert money(6000) == "$6,000.00"


# --- chart geometry ---------------------------------------------------------
# The following tests check that the chart geometry functions produce the expected SVG coordinates and paths for the cumulative and monthly charts. They verify that the points, ranges, and bands are positioned correctly based on the forecast data.
def test_cumulative_chart_geometry():
    forecast = forecast_months(varied_history())
    chart = cumulative_chart(forecast)

    # "Now" plus one label per future month, spanning the full plot width.
    assert len(chart["x_labels"]) == 7
    assert chart["x_labels"][0] == {"x": PLOT_LEFT, "label": "Now"}
    assert chart["x_labels"][-1]["x"] == PLOT_RIGHT
    assert chart["x_labels"][1]["label"] == "Nov 2026"

    assert len(chart["points"]) == 6
    for point in chart["points"]:
        assert PLOT_TOP <= point["y"] <= PLOT_BOTTOM
    assert PLOT_TOP <= chart["zero_y"] <= PLOT_BOTTOM
    assert chart["band_path"].startswith("M") and chart["band_path"].endswith("Z")
    assert "typical" in chart["points"][0]["tooltip"]

# The following tests check that the chart geometry functions produce the expected SVG coordinates and paths for the cumulative and monthly charts. They verify that the points, ranges, and bands are positioned correctly based on the forecast data.
def test_cumulative_chart_higher_values_drawn_higher():
    history = [month(2026, m, 3000, 2000) for m in (8, 9, 10)]
    chart = cumulative_chart(forecast_months(history))
    ys = [p["y"] for p in chart["points"]]
    # SVG y grows downward, so a rising total means falling y.
    assert ys == sorted(ys, reverse=True)
    assert all(y < chart["zero_y"] for y in ys)

# The following tests check that the chart geometry functions produce the expected SVG coordinates and paths for the cumulative and monthly charts. They verify that the points, ranges, and bands are positioned correctly based on the forecast data.
def test_monthly_chart_bars_and_ranges():
    history = varied_history()
    chart = monthly_chart(history, forecast_months(history))

    assert len(chart["bars"]) == 4
    assert len(chart["ranges"]) == 6
    # August was a deficit; the rest were surpluses.
    assert [b["negative"] for b in chart["bars"]] == [False, True, False, False]
    # Surplus bars sit above the zero line, deficit bars below it.
    zero = chart["zero_y"]
    assert chart["bars"][0]["y"] + chart["bars"][0]["height"] == pytest.approx(zero)
    assert chart["bars"][1]["y"] == zero
    for r in chart["ranges"]:
        assert r["y"] <= r["typical_y"] <= r["y"] + r["height"]
        assert PLOT_TOP <= r["y"] and r["y"] + r["height"] <= PLOT_BOTTOM
    # Divider sits between the last bar and the first forecast range.
    assert chart["bars"][-1]["center"] < chart["divider_x"] < chart["ranges"][0]["center"]

# Test that the monthly chart limits the number of history months shown.
def test_monthly_chart_limits_history_shown():
    history = [month(2026 + (m - 1) // 12, (m - 1) % 12 + 1, 3000, 2000) for m in range(1, 13)]
    chart = monthly_chart(history, forecast_months(history))
    assert len(chart["bars"]) == HISTORY_MONTHS_SHOWN
    assert (chart["bars"][-1]["label"], chart["bars"][-1]["year"]) == ("Dec", "2026")

# Test that the forecast charts are hidden if there is not enough history.
def test_forecast_charts_none_without_forecast():
    assert forecast_charts([], None) is None
    charts = forecast_charts(varied_history(), forecast_months(varied_history()))
    assert set(charts) == {"cumulative", "monthly"}

# Test that the monthly chart uses short month names for the history bars, and full month names for the forecast ranges.
def test_short_month_names_split_too():
    history = [month(2027, m, 3000, 2000) for m in (3, 4, 5)]
    chart = monthly_chart(history, forecast_months(history))
    assert (chart["bars"][-1]["label"], chart["bars"][-1]["year"]) == ("May", "2027")
