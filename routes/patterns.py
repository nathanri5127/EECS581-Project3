from flask import Blueprint, render_template
from flask_login import current_user, login_required

from models.transaction import Transaction
from services.recurring_analysis import find_recurring_expenses
from services.seasonal_analysis import analyze_seasonal_patterns

patterns_bp = Blueprint(
    "patterns",
    __name__
)


@patterns_bp.route("/analysis/recurring-seasonal") # make a new path; Author : Fabrizio Falcon
@login_required
def patterns():
    transactions = (
        Transaction.query
        .filter_by(
            user_id=current_user.id
        )
        .all()
    )
    return render_template(
        "patterns.html",
        recurring=find_recurring_expenses(transactions),
        seasonal=analyze_seasonal_patterns(transactions)
    )
