import sqlite3

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import execute, query_one
from app.validation import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    validate_registration,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _json_object():
    if not request.is_json:
        return None
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _public_user(user):
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "created_at": user["created_at"],
    }


@auth_bp.post("/register")
def register():
    data = _json_object()
    if data is None:
        return jsonify(error="Request body must be a JSON object."), 400

    errors = validate_registration(data)
    if errors:
        return jsonify(error="Validation failed.", details=errors), 400

    username = data["username"].strip()
    email = data["email"].strip().lower()
    full_name = data["full_name"].strip()
    password_hash = generate_password_hash(data["password"])

    try:
        result = execute(
            """
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, full_name),
        )
    except sqlite3.IntegrityError:
        return jsonify(error="Username or email is already registered."), 409

    user = query_one(
        """
        SELECT id, username, email, full_name, created_at
        FROM users
        WHERE id = ?
        """,
        (result.lastrowid,),
    )
    return jsonify(message="Registration successful.", user=_public_user(user)), 201


@auth_bp.post("/login")
def login():
    data = _json_object()
    if (
        data is None
        or not isinstance(data.get("identifier"), str)
        or not isinstance(data.get("password"), str)
    ):
        return jsonify(error="Identifier and password are required."), 400

    identifier = data["identifier"].strip()
    password = data["password"]
    if (
        not identifier
        or len(identifier) > 254
        or not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH
    ):
        session.clear()
        return jsonify(error="Invalid username/email or password."), 401

    user = query_one(
        """
        SELECT id, username, email, password_hash, full_name, created_at
        FROM users
        WHERE username = ? OR email = ?
        """,
        (identifier, identifier.lower()),
    )
    if user is None or not check_password_hash(user["password_hash"], password):
        session.clear()
        return jsonify(error="Invalid username/email or password."), 401

    session.clear()
    session["user_id"] = user["id"]
    return jsonify(message="Login successful.", user=_public_user(user)), 200


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify(message="Logged out."), 200
