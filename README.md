# Runway Financial

## Secure data configuration

User passwords are stored as Werkzeug password hashes and are never stored in
plaintext. Transaction date, description, amount, and category values are
encrypted with Fernet before SQLAlchemy writes them to the database.

Copy `.env.example` to `.env` and replace every placeholder with a unique
random value. `FERNET_KEY` is encryption key material: keep it in a secrets
manager, do not commit it, and keep a protected backup. Losing it makes
encrypted transaction data unrecoverable. `DATABASE_URL` must point to a
database with TLS enabled; PostgreSQL connections automatically request
`sslmode=require`.

After installing dependencies, apply migrations:

```text
flask db upgrade
```

The encryption migration reads existing plaintext transaction values and
encrypts them before removing the plaintext columns. Set `FERNET_KEY` before
running it.
