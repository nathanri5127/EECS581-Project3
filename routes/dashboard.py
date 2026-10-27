from flask import Blueprint, render_template
from flask_login import current_user, login_required

from models.transaction import Transaction

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
        .all()
    )
    summary = calculate_summary(
        transactions
    )
    return render_template(
        "dashboard.html",
        transactions=transactions,
        **summary
    )