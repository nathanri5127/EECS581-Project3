from extensions import db

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

    date = db.Column(
        db.String(50)
    )

    description = db.Column(
        db.String(255)
    )

    amount = db.Column(
        db.Float
    )

    category = db.Column(
        db.String(100)
    )