"""
Description:
Handles transaction file uploads and transaction
storage operations.

Responsibilities:
- Process uploaded CSV files
- Validate transaction uploads
- Create transaction records
- Store transaction data

Dependencies:
- Flask
- SQLAlchemy
- Pandas
"""

from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash
)
from flask_login import (
    login_required,
    current_user
)
from extensions import db
from models.transaction import Transaction
from services.csv_parser import parse_transactions

upload_bp = Blueprint(
    "upload",
    __name__
)

@upload_bp.route(
    "/upload-csv",
    methods=["POST"]
)
#handler function for uploading CSV files containing transaction data. 
#it processes the uploaded file, validates the transactions, and stores them in the database.
@login_required
def upload_csv():
    file = request.files["csv_file"]
    if not file:
        return "No file provided"
    try:
        transactions = parse_transactions(file)
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("dashboard.dashboard"))
    
    for transaction in transactions:
        new_transaction = Transaction(
            user_id=current_user.id,
            date=transaction["date"],
            description=transaction[
                "description"
            ],
            amount=transaction[
                "amount"
            ],
            category=transaction[
                "category"
            ]
        )

        db.session.add(
            new_transaction
        )
    db.session.commit()
    return redirect(
        url_for("dashboard.dashboard")
    )