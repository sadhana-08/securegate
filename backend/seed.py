import os

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import execute, query_one
from app.validation import validate_password


SEED_USERS = (
    ("demo_taylor", "taylor@example.invalid", "Taylor Example"),
    ("demo_morgan", "morgan@example.invalid", "Morgan Sample"),
)


def seed_users():
    password = os.getenv("SEED_PASSWORD", "")
    password_error = validate_password(password)
    if password_error:
        raise RuntimeError(f"Set SEED_PASSWORD to a strong throwaway value. {password_error}")

    password_hash = generate_password_hash(password)
    for username, email, full_name in SEED_USERS:
        existing_user = query_one(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
        )
        if existing_user is not None:
            print(f"Skipped existing synthetic user: {username}")
            continue

        execute(
            """
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, full_name),
        )
        print(f"Created synthetic user: {username}")


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        seed_users()
