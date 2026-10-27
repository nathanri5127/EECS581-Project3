import pandas as pd

DATE_COLUMNS = [
    "date",
    "transaction date",
    "posted date"
]

DESCRIPTION_COLUMNS = [
    "description",
    "merchant",
    "transaction description"
]

AMOUNT_COLUMNS = [
    "amount",
    "transaction amount"
]

CATEGORY_COLUMNS = [
    "category",
    "expense category",
    "type"
]

def find_column(columns, aliases):
    for column in columns:
        if (column.lower().strip() in aliases):
            return column
    return None

def parse_transactions(file):
    df = pd.read_csv(file)

    date_col = find_column(
        df.columns,
        DATE_COLUMNS
    )

    description_col = find_column(
        df.columns,
        DESCRIPTION_COLUMNS
    )

    amount_col = find_column(
        df.columns,
        AMOUNT_COLUMNS
    )

    category_col = find_column(
        df.columns,
        CATEGORY_COLUMNS
    )

    if not date_col:
        raise Exception(
            "Date column missing"
        )

    if not description_col:
        raise Exception(
            "Description column missing"
        )

    if not amount_col:
        raise Exception(
            "Amount column missing"
        )

    transactions = []

    for _, row in df.iterrows():
        transactions.append({
            "date":
                row[date_col],

            "description":
                row[
                    description_col
                ],

            "amount":
                float(
                    row[
                        amount_col
                    ]
                ),

            "category":
                (
                    row[
                        category_col
                    ]
                    if category_col
                    else
                    "Uncategorized"
                )
        })
    return transactions