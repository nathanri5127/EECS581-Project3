"""
Monte Carlo forecast of the next few months of net cash.

Adapted from the simulation in app/engine.py of runway-planner
(https://github.com/dillonfigueredo2169/runway-planner), Dillon
Figueredo's Hack Midwest project. That engine resamples past weekly pay
and subtracts bills/spending from a starting balance; this version works
on whole months, since that's how the monthly analysis groups data.

Plain-English summary:
  1. Look at the user's past months of income and expenses.
  2. For each future month, pick a random past month's income and,
     separately, a random past month's expenses (like the engine, which
     draws income and spending separately).
  3. Repeat 10,000 times.
  4. Count how often at least one month ends with negative net cash, and
     report typical (median), bad-case (10th percentile), and good-case
     (90th percentile) totals for the whole period.
  5. For each future month, report an 80% confidence interval of the
     running total so far: 80% of simulated futures land between the
     10th and 90th percentile
"""
import numpy as np

# Resampling one or two months just replays them, which isn't a forecast.
MIN_HISTORY_MONTHS = 3

# Percentiles for the bad case, typical case, and good case. 10 and 90
# leave 10% of outcomes on each side, so the range between them is an
# 80% confidence interval.
LOW_PERCENTILE = 10
HIGH_PERCENTILE = 90
CONFIDENCE_LEVEL = HIGH_PERCENTILE - LOW_PERCENTILE

def forecast_months(history, months=6, n=10_000, seed=7):
    """
    Simulate future months by resampling past monthly income and expenses.

    `history` is a list of dicts with "income" and "expenses" keys (the
    "months" list from services.monthly_analysis.analyze_monthly).
    Expenses are positive magnitudes.

    A fixed seed keeps the numbers stable when the page is refreshed, as
    in runway-planner.

    Returns None if there isn't enough history, otherwise a dict:
        months:                   number of future months simulated
        simulations:              number of simulated futures
        history_months:           how many past months were resampled
        negative_month_probability: share of simulations with at least one
                                  month where expenses exceed income
        typical_total:            median total net over the period
        bad_case_total:           10th percentile total net
        good_case_total:          90th percentile total net
        confidence_level:         width of the intervals, in percent (80)
        intervals:                one dict per future month with
                                  month (1 = next month) and low, median,
                                  high: the 10th, 50th, and 90th
                                  percentiles of total net up to and
                                  including that month
    """
    if months < 1 or n < 1:
        raise ValueError("months and n must be positive.")

    if len(history) < MIN_HISTORY_MONTHS:
        return None

    income = np.array([float(m["income"]) for m in history])
    expenses = np.array([float(m["expenses"]) for m in history])

    rng = np.random.default_rng(seed)

    # One row per simulated future, one column per future month.
    simulated_income = rng.choice(income, size=(n, months))
    simulated_expenses = rng.choice(expenses, size=(n, months))
    monthly_net = simulated_income - simulated_expenses

    any_negative = (monthly_net < 0).any(axis=1)
    total_net = monthly_net.sum(axis=1)

    # Running total after each month, per simulated future. Taking
    # percentiles down each column (axis=0) gives the spread of outcomes
    # after 1 month, 2 months, and so on.
    running_net = monthly_net.cumsum(axis=1)
    low, median, high = np.percentile(
        running_net,
        [LOW_PERCENTILE, 50, HIGH_PERCENTILE],
        axis=0
    )
    intervals = [
        {
            "month": i + 1,
            "low": round(float(low[i]), 2),
            "median": round(float(median[i]), 2),
            "high": round(float(high[i]), 2),
        }
        for i in range(months)
    ]

    return {
        "months": months,
        "simulations": n,
        "history_months": len(history),
        "negative_month_probability": round(float(any_negative.mean()), 4),
        "typical_total": round(float(np.median(total_net)), 2),
        "bad_case_total": round(float(np.percentile(total_net, LOW_PERCENTILE)), 2),
        "good_case_total": round(float(np.percentile(total_net, HIGH_PERCENTILE)), 2),
        "confidence_level": CONFIDENCE_LEVEL,
        "intervals": intervals,
    }
