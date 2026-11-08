from extensions import db
from services.encryption import EncryptedDecimal, EncryptedString

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Encryption for sensitive fields added on 11/7/2026
    # Github Copilot using HydraFusion added this -- Aidan P.
    # Encrypted columns for date, description, amount, category for data security
    date = db.Column(
        EncryptedString(),
        nullable=False
    )

    description = db.Column(
        EncryptedString(),
        nullable=False
    )

    amount = db.Column(
        EncryptedDecimal(),
        nullable=False
    )

    category = db.Column(
        EncryptedString(),
        nullable=True
    )