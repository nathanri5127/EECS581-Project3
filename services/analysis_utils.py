"""Shared helpers for the Sprint 2 analysis services."""
import pandas as pd

FRAME_COLUMNS = ["date", "description", "amount", "category"]


def transactions_to_frame(transactions): # Author: Claude Sonnet 5.5 supervised by Fabrizio Falcón
    """Turn Transaction rows into a DataFrame with real datetimes.

    Dates are stored as the raw strings from the uploaded CSV, so some of
    them may be unreadable (for example "2026-09-31"). Those rows are
    dropped and counted so the page can tell the user.

    Returns (dataframe, number_of_skipped_rows).
    """
    rows = [
        {
            "date": t.date,
            "description": t.description,
            "amount": float(t.amount),
            "category": t.category or "Uncategorized",
        }
        for t in transactions
    ]
    df = pd.DataFrame(rows, columns=FRAME_COLUMNS)
    if df.empty:
        return df, 0

    parsed = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    skipped = int(parsed.isna().sum())
    df = df.assign(date=parsed).dropna(subset=["date"])
    return df.reset_index(drop=True), skipped
