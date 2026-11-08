import os
import sys

from cryptography.fernet import Fernet

# config.py reads these at import time, so they must be set before the
# app is imported. Assigned (not setdefault) so tests never touch the
# real database configured in .env.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["FERNET_KEY"] = Fernet.generate_key().decode("ascii")

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import pytest
from werkzeug.security import generate_password_hash

from app import app as flask_app
from extensions import db
from models.user import User


@pytest.fixture
def app():
    flask_app.config.update(
        TESTING=True,
        # The test client talks plain HTTP, so secure-only cookies would
        # never be sent back and the login session would be lost.
        SESSION_COOKIE_SECURE=False,
    )
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    def _make_user(username):
        user = User(
            username=username,
            password_hash=generate_password_hash("password")
        )
        db.session.add(user)
        db.session.commit()
        return user
    return _make_user


@pytest.fixture
def login(client):
    def _login(user):
        with client.session_transaction() as session:
            session["_user_id"] = str(user.id)
            session["_fresh"] = True
    return _login
