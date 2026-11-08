from flask import (Blueprint, abort, redirect, render_template, request, url_for)
from flask_login import current_user, login_required

from extensions import db
from models.transaction import Transaction
from services.categorizer import CATEGORIES

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)

def calculate_summary(transactions):
    income = sum(
        t.amount
        for t in transactions
        if t.amount > 0
    )
    expenses = sum(
        t.amount
        for t in transactions
        if t.amount < 0
    )
    net_balance = income + expenses
    transaction_count = len(transactions)
    return {
        "income": income,
        "expenses": expenses,
        "net_balance": net_balance,
        "transaction_count":
            transaction_count
    }

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    transactions = (
        Transaction.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(Transaction.id)
        .all()
    )
    summary = calculate_summary(
        transactions
    )
    return render_template(
        "dashboard.html",
        transactions=transactions,
        categories=CATEGORIES,
        **summary
    )

@dashboard_bp.route(
    "/transactions/<int:transaction_id>/category",
    methods=["POST"]
)
@login_required
def update_category(transaction_id):
    # Only find the transaction if it belongs to the logged-in user,
    # so users cannot edit each other's transactions.
    transaction = (
        Transaction.query
        .filter_by(
            id=transaction_id,
            user_id=current_user.id
        )
        .first_or_404()
    )

    new_category = request.form.get(
        "category",
        ""
    ).strip()

    if new_category not in CATEGORIES:
        abort(400)

    transaction.category = new_category
    db.session.commit()

    # Return to the same row instead of the top of the page.
    return redirect(
        url_for("dashboard.dashboard")
        + f"#transaction-{transaction.id}"
    )
