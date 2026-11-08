from decimal import Decimal

from sqlalchemy import text

from extensions import db
from models.transaction import Transaction


def add_transactions(user, rows):
    for date_value, description, amount in rows:
        db.session.add(Transaction(
            user_id=user.id,
            date=date_value,
            description=description,
            amount=Decimal(str(amount)),
            category=None,
        ))
    db.session.commit()


def test_requires_login(client):
    response = client.get("/analysis/monthly")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_empty_state(client, make_user, login):
    login(make_user("alice"))
    response = client.get("/analysis/monthly")
    assert response.status_code == 200
    assert b"No transactions to analyze yet" in response.data


def test_shows_monthly_totals_and_flags_deficit(client, make_user, login):
    alice = make_user("alice")
    add_transactions(alice, [
        ("2026-10-01", "Paycheck", 5000),
        ("2026-10-02", "Rent", -1000),
        ("2026-11-01", "Paycheck", 1000),
        ("2026-11-02", "Rent", -1200),
    ])
    login(alice)

    html = client.get("/analysis/monthly").get_data(as_text=True)

    assert "October 2026" in html
    assert "November 2026" in html
    assert "$5000.00" in html        # October income
    assert "$4000.00" in html        # October net
    assert "-$200.00" in html        # November net
    assert "$3000.00" in html        # average income
    assert "-$1100.00" in html       # average expenses
    assert html.count("Expenses exceeded income") == 1
    assert "1 of 2" in html


def test_only_shows_current_users_transactions(client, make_user, login):
    alice = make_user("alice")
    bob = make_user("bob")
    add_transactions(alice, [("2026-10-01", "Paycheck", 1234)])
    add_transactions(bob, [("2026-07-01", "Bonus", 9999)])
    login(alice)

    html = client.get("/analysis/monthly").get_data(as_text=True)

    assert "October 2026" in html
    assert "$1234.00" in html
    assert "July 2026" not in html
    assert "9999" not in html


def test_reports_unreadable_dates(client, make_user, login):
    alice = make_user("alice")
    add_transactions(alice, [
        ("2026-10-01", "Paycheck", 100),
        ("NOT A TRANSACTION", "junk", -10000),
    ])
    login(alice)

    html = client.get("/analysis/monthly").get_data(as_text=True)

    assert "1 transaction" in html
    assert "unreadable date" in html


def test_reads_through_encrypted_model(app, make_user):
    alice = make_user("alice")
    add_transactions(alice, [("2026-10-01", "Paycheck", 5000)])

    # Stored column values are ciphertext, not the plaintext date/amount...
    raw_date, raw_amount = db.session.execute(
        text("SELECT date, amount FROM transactions")
    ).one()
    assert b"2026-10-01" not in bytes(raw_date)
    assert b"5000" not in bytes(raw_amount)

    # ...and the model decrypts them back for the analysis.
    loaded = Transaction.query.filter_by(user_id=alice.id).one()
    assert loaded.date == "2026-10-01"
    assert loaded.amount == Decimal("5000")


def test_forecast_needs_enough_history(client, make_user, login):
    alice = make_user("alice")
    add_transactions(alice, [
        ("2026-10-01", "Paycheck", 1000),
        ("2026-11-01", "Paycheck", 1000),
    ])
    login(alice)

    html = client.get("/analysis/monthly").get_data(as_text=True)

    assert "6-Month Forecast" in html
    assert "At least 3 months of transactions are" in html


def test_forecast_shown_with_enough_history(client, make_user, login):
    alice = make_user("alice")
    add_transactions(alice, [
        ("2026-08-01", "Paycheck", 3000),
        ("2026-08-02", "Rent", -2000),
        ("2026-09-01", "Paycheck", 3000),
        ("2026-09-02", "Rent", -2000),
        ("2026-10-01", "Paycheck", 3000),
        ("2026-10-02", "Rent", -2000),
    ])
    login(alice)

    html = client.get("/analysis/monthly").get_data(as_text=True)

    assert "10000 simulated futures" in html
    # Every month nets +$1000, so the forecast is certain.
    assert "0%" in html
    assert html.count("$6000.00") == 3


def test_dashboard_links_to_monthly_analysis(client, make_user, login):
    login(make_user("alice"))
    html = client.get("/dashboard").get_data(as_text=True)
    assert 'href="/analysis/monthly"' in html
