"""
Monthly income/expense analysis.

Groups a user's transactions by calendar month and computes, for each
month, total income, total expenses, and net (income - expenses). Also
computes the average monthly income and expenses across the months that
have transactions, and flags months where expenses exceeded income.

Amounts follow the same convention as the dashboard: positive amounts are
income, negative amounts are expenses. Expenses are reported here as a
positive magnitude so they can be compared directly against income.
"""
import calendar
import re
from datetime import date, datetime
from decimal import Decimal

ZERO = Decimal("0")
CENT = Decimal("0.01")

# Dates come from uploaded CSVs and are stored as text, so the format
# depends on the bank. We only need the year and month to group them.
# ISO-style: 2026-10-01, 2026/10/01, 2026-10-01 00:00:00
_YEAR_FIRST = re.compile(r"^\s*(\d{4})[-/.](\d{1,2})(?:[-/.]\d{1,2})?\b")
# US-style: 10/01/2026, 10-01-2026
_MONTH_FIRST = re.compile(r"^\s*(\d{1,2})[-/.]\d{1,2}[-/.](\d{4})\b")


def parse_month(value):
    """
    Return (year, month) for a transaction date, or None if the date
    can't be understood.

    Accepts date/datetime objects and common text formats. Only the year
    and month are read, so a bad day (e.g. "2026-09-31") still groups
    into the right month instead of being dropped.
    """
    if value is None:
        return None

    if isinstance(value, (date, datetime)):
        return (value.year, value.month)

    text = str(value)

    match = _YEAR_FIRST.match(text)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
    else:
        match = _MONTH_FIRST.match(text)
        if not match:
            return None
        month, year = int(match.group(1)), int(match.group(2))

    if not 1 <= month <= 12:
        return None

    return (year, month)


def _to_decimal(amount):
    if isinstance(amount, Decimal):
        return amount
    # str() avoids float artifacts like 0.1 -> 0.1000000000000000055...
    return Decimal(str(amount))


def analyze_monthly(transactions):
    """
    Build the monthly analysis for a list of transactions.

    Each transaction only needs `.date` and `.amount` attributes, so this
    works with Transaction model instances (which decrypt those fields
    on load) as well as simple test objects.

    Returns a dict:
        months:          list of per-month dicts, oldest first
        average_income:  Decimal, mean income over months with data
        average_expenses: Decimal, mean expenses over months with data
        deficit_count:   number of months where expenses > income
        unparsed_count:  transactions skipped due to unreadable dates
    """
    buckets = {}
    unparsed_count = 0

    for transaction in transactions:
        key = parse_month(transaction.date)
        if key is None:
            unparsed_count += 1
            continue

        amount = _to_decimal(transaction.amount)
        bucket = buckets.setdefault(
            key,
            {"income": ZERO, "expenses": ZERO, "count": 0}
        )
        if amount > 0:
            bucket["income"] += amount
        elif amount < 0:
            bucket["expenses"] += -amount
        bucket["count"] += 1

    months = []
    for (year, month) in sorted(buckets):
        bucket = buckets[(year, month)]
        income = bucket["income"]
        expenses = bucket["expenses"]
        months.append({
            "year": year,
            "month": month,
            "label": f"{calendar.month_name[month]} {year}",
            "income": income,
            "expenses": expenses,
            "net": income - expenses,
            "transaction_count": bucket["count"],
            "is_deficit": expenses > income,
        })

    if months:
        average_income = (
            sum((m["income"] for m in months), ZERO) / len(months)
        ).quantize(CENT)
        average_expenses = (
            sum((m["expenses"] for m in months), ZERO) / len(months)
        ).quantize(CENT)
    else:
        average_income = ZERO
        average_expenses = ZERO

    return {
        "months": months,
        "average_income": average_income,
        "average_expenses": average_expenses,
        "deficit_count": sum(1 for m in months if m["is_deficit"]),
        "unparsed_count": unparsed_count,
    }
