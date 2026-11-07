import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Added by Copilot on 11/7/26 using HydraFusion  experimental model -- Aidan P.
    # Database config
    # Postgres URL expected, add ssl if needed
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    # check DB URL
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("DATABASE_URL must be configured")
    # ensure SSL for Postgres
    if SQLALCHEMY_DATABASE_URI.startswith(("postgres://", "postgresql://")):
        if "sslmode=" not in SQLALCHEMY_DATABASE_URI:
            separator = "&" if "?" in SQLALCHEMY_DATABASE_URI else "?"
            SQLALCHEMY_DATABASE_URI += f"{separator}sslmode=require"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key config, must be set in env, used for encryption
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be configured")

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"