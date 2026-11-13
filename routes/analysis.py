"""
Description: 
This file contains the routes for the analysis pages of the application.

Responsibilities:
- Provide a route for monthly analysis of user transactions

Dependencies:
- Flask
"""

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from models.transaction import Transaction
from services.monte_carlo import MIN_HISTORY_MONTHS, forecast_months
from services.monthly_analysis import analyze_monthly

from services.income_stability import income_stability

analysis_bp = Blueprint(
    "analysis",
    __name__
)

@analysis_bp.route("/analysis/monthly")
@login_required
def monthly_analysis():
    # Fields are encrypted in the database, so they can't be grouped in
    # SQL. Load through the model (which decrypts) and group in Python.
    transactions = (
        Transaction.query
        .filter_by(
            user_id=current_user.id
        )
        .all()
    )
    analysis = analyze_monthly(
        transactions
    )
    forecast = forecast_months(
        analysis["months"]
    )
    stability = income_stability(
        analysis["months"]
    )
    return render_template(
        "monthly_analysis.html",
        forecast=forecast,
        stability=stability,
        min_history_months=MIN_HISTORY_MONTHS,
        **analysis
    )
