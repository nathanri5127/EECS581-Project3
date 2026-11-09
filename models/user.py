"""
Description:
Defines the User database model used for account
registration, authentication, and session management.

Responsibilities:
- Store account information
- Store password hashes
- Support Flask-Login user sessions

Dependencies:
- SQLAlchemy
- Flask-Login
"""

from extensions import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    transactions = db.relationship(
        "Transaction",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )