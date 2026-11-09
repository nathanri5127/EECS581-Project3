"""
Description:
Creates shared Flask extensions that can be imported
throughout the application.

Responsibilities:
- Create SQLAlchemy instance
- Prevent circular imports

Dependencies:
- Flask-SQLAlchemy
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()