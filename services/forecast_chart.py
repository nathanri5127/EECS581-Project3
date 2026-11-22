"""
Forecast visualization charts.

Turns the Monte Carlo forecast (services.monte_carlo.forecast_months) and
the monthly history (services.monthly_analysis.analyze_monthly) into the
coordinates the monthly analysis template draws as inline SVG. Keeping
the math here (instead of in the template or in JavaScript) means the
charts need no extra libraries and can be unit tested.

Two charts are built:
  1. Cumulative net fan chart: starting from $0 today, the typical
     (median) running total of net cash for each future month, with a
     shaded band between the bad case (10th percentile) and the good case
     (90th percentile).
  2. Monthly net chart: the actual net of recent past months as bars,
     followed by each future month's likely range (10th to 90th
     percentile) with a marker at the typical value.
"""
import math

WIDTH = 720
HEIGHT = 300
PAD_LEFT = 70
PAD_RIGHT = 40
PAD_TOP = 20
PAD_BOTTOM = 50

PLOT_LEFT = PAD_LEFT
PLOT_RIGHT = WIDTH - PAD_RIGHT
PLOT_TOP = PAD_TOP
PLOT_BOTTOM = HEIGHT - PAD_BOTTOM

# How many past months to show next to the forecast in the monthly chart.
HISTORY_MONTHS_SHOWN = 6


def nice_ticks(low, high, target=5):
    """
    Return evenly spaced, round tick values covering [low, high].

    The first and last ticks are the chart's axis limits, so every value
    in the range fits inside the plot.
    """
    if low > high:
        low, high = high, low
    if low == high:
        pad = abs(low) * 0.1 or 1
        low, high = low - pad, high + pad

    raw_step = (high - low) / max(target - 1, 1)
    magnitude = 10 ** math.floor(math.log10(raw_step))
    for multiple in (1, 2, 2.5, 5, 10):
        step = multiple * magnitude
        if step >= raw_step:
            break

    start = math.floor(low / step) * step
    end = math.ceil(high / step) * step
    count = int(round((end - start) / step))
    # round() avoids float noise like 0.30000000000000004 in labels.
    return [round(start + i * step, 10) for i in range(count + 1)]


def money_label(value):
    """Short axis label: 1500 -> "$1.5k", -200 -> "-$200", 0 -> "$0"."""
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1000:
        return f"{sign}${round(value / 1000, 1):g}k"
    return f"{sign}${round(value, 2):g}"


def money(value):
    """Full amount for tooltips: -1234.5 -> "-$1,234.50"."""
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def _y_axis(values):
    """Build ticks and a value -> y pixel function. Always includes $0."""
    ticks = nice_ticks(min(min(values), 0), max(max(values), 0))
    low, high = ticks[0], ticks[-1]

    def y(value):
        share = (value - low) / (high - low)
        return round(PLOT_BOTTOM - share * (PLOT_BOTTOM - PLOT_TOP), 2)

    tick_marks = [{"y": y(t), "label": money_label(t)} for t in ticks]
    return y, tick_marks


def _frame(y):
    return {
        "width": WIDTH,
        "height": HEIGHT,
        "plot_left": PLOT_LEFT,
        "plot_right": PLOT_RIGHT,
        "plot_top": PLOT_TOP,
        "plot_bottom": PLOT_BOTTOM,
        "zero_y": y(0),
    }


def _split_label(label):
    """ "December 2026" -> ("Dec", "2026"); other labels -> (label, "")."""
    parts = label.split(" ")
    if len(parts) == 2 and parts[0].isalpha() and parts[1].isdigit():
        return parts[0][:3], parts[1]
    return label, ""


def _short_label(label):
    """ "December 2026" -> "Dec 2026"; other labels pass through."""
    return " ".join(p for p in _split_label(label) if p)


def cumulative_chart(forecast):
    """
    Fan chart of running total net, starting at $0 "Now".

    Returns a dict with the SVG frame, y ticks, x labels, the band polygon
    path, the median line path, and one point per future month (with
    full-precision tooltip text).
    """
    bands = forecast["bands"]
    lows = [0] + [b["cumulative_low"] for b in bands]
    mids = [0] + [b["cumulative_typical"] for b in bands]
    highs = [0] + [b["cumulative_high"] for b in bands]
    labels = ["Now"] + [_short_label(b["label"]) for b in bands]

    y, ticks = _y_axis(lows + highs)
    step = (PLOT_RIGHT - PLOT_LEFT) / (len(labels) - 1)
    xs = [round(PLOT_LEFT + i * step, 2) for i in range(len(labels))]

    upper = [f"{x},{y(v)}" for x, v in zip(xs, highs)]
    lower = [f"{x},{y(v)}" for x, v in zip(xs, lows)]
    band_path = "M" + " L".join(upper + lower[::-1]) + " Z"
    median_path = "M" + " L".join(f"{x},{y(v)}" for x, v in zip(xs, mids))

    points = [
        {
            "x": xs[i + 1],
            "y": y(mids[i + 1]),
            "tooltip": (
                f"{b['label']}: typical {money(b['cumulative_typical'])} "
                f"(bad case {money(b['cumulative_low'])}, "
                f"good case {money(b['cumulative_high'])})"
            ),
        }
        for i, b in enumerate(bands)
    ]

    chart = _frame(y)
    chart.update({
        "ticks": ticks,
        "x_labels": [{"x": x, "label": l} for x, l in zip(xs, labels)],
        "band_path": band_path,
        "median_path": median_path,
        "points": points,
    })
    return chart


def monthly_chart(history, forecast):
    """
    Bars for recent actual monthly net, then forecast ranges per month.

    `history` is the "months" list from analyze_monthly. Returns a dict
    with the SVG frame, y ticks, a list of `bars` (past months) and a list
    of `ranges` (future months), each with its own x position and label.
    """
    past = history[-HISTORY_MONTHS_SHOWN:]
    bands = forecast["bands"]

    values = [float(m["net"]) for m in past]
    for b in bands:
        values += [b["net_low"], b["net_high"]]
    y, ticks = _y_axis(values)

    slots = len(past) + len(bands)
    slot_width = (PLOT_RIGHT - PLOT_LEFT) / slots
    bar_width = round(slot_width * 0.6, 2)

    def center(i):
        return round(PLOT_LEFT + (i + 0.5) * slot_width, 2)

    zero_y = y(0)
    bars = []
    for i, m in enumerate(past):
        net = float(m["net"])
        top = min(y(net), zero_y)
        bars.append({
            "x": round(center(i) - bar_width / 2, 2),
            "y": top,
            "width": bar_width,
            # Keep a hairline for $0 months so they're still visible.
            "height": max(round(abs(y(net) - zero_y), 2), 1),
            "center": center(i),
            "label": _split_label(m["label"])[0],
            "year": _split_label(m["label"])[1],
            "negative": net < 0,
            "tooltip": f"{m['label']} (actual): {money(net)}",
        })

    ranges = []
    for j, b in enumerate(bands):
        i = len(past) + j
        top = y(b["net_high"])
        ranges.append({
            "x": round(center(i) - bar_width / 2, 2),
            "y": top,
            "width": bar_width,
            "height": max(round(y(b["net_low"]) - top, 2), 1),
            "typical_y": y(b["net_typical"]),
            "center": center(i),
            "label": _split_label(b["label"])[0],
            "year": _split_label(b["label"])[1],
            "tooltip": (
                f"{b['label']} (forecast): typical {money(b['net_typical'])}, "
                f"likely between {money(b['net_low'])} and {money(b['net_high'])}"
            ),
        })

    chart = _frame(y)
    chart.update({
        "ticks": ticks,
        "bars": bars,
        "ranges": ranges,
        # Dashed divider between past and forecast.
        "divider_x": round(PLOT_LEFT + len(past) * slot_width, 2) if past else None,
    })
    return chart


def forecast_charts(history, forecast):
    """Both charts for the template, or None when there's no forecast."""
    if not forecast:
        return None
    return {
        "cumulative": cumulative_chart(forecast),
        "monthly": monthly_chart(history, forecast),
    }
