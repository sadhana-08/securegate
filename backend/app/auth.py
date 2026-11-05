import hashlib
import hmac
import secrets
import sqlite3

from flask import Blueprint, abort, current_app, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import (
    clear_login_attempts,
    execute,
    login_rate_limited,
    query_one,
    record_failed_login,
)
from app.validation import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    validate_email,
    validate_full_name,
    validate_registration,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
api_bp = Blueprint("api", __name__, url_prefix="/api")
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 15 * 60


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


def _login_bucket_keys(identifier):
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    normalized_identifier = identifier.strip().casefold()
    remote_address = request.remote_addr or "unknown"
    return (
        hmac.new(
            secret,
            f"username:{normalized_identifier}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest(),
        hmac.new(
            secret,
            f"ip:{remote_address}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest(),
    )


@api_bp.get("/csrf-token")
def csrf_token():
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    response = jsonify(csrf_token=token)
    response.headers["Cache-Control"] = "no-store"
    return response


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
        return jsonify(error="Invalid username/email or password."), 401

    bucket_keys = _login_bucket_keys(identifier)
    if login_rate_limited(
        bucket_keys,
        LOGIN_MAX_ATTEMPTS,
        LOGIN_WINDOW_SECONDS,
    ):
        return (
            jsonify(error="Too many login attempts. Try again in 15 minutes."),
            429,
            {"Retry-After": str(LOGIN_WINDOW_SECONDS)},
        )

    user = query_one(
        """
        SELECT id, username, email, password_hash, full_name, created_at
        FROM users
        WHERE username = ? OR email = ?
        """,
        (identifier, identifier.lower()),
    )
    if user is None or not check_password_hash(user["password_hash"], password):
        record_failed_login(bucket_keys)
        return jsonify(error="Invalid username/email or password."), 401

    session.clear()
    session["user_id"] = user["id"]
    clear_login_attempts(bucket_keys)
    return jsonify(message="Login successful.", user=_public_user(user)), 200


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify(message="Logged out."), 200


@api_bp.get("/me")
def me():
    user = _authenticated_user()
    return jsonify(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
    )


@api_bp.get("/profile")
def get_profile():
    user = _authenticated_user()
    return jsonify(_public_user(user))


@api_bp.put("/profile")
def update_profile():
    user = _authenticated_user()
    data = _json_object()
    if data is None:
        return jsonify(error="Request body must be a JSON object."), 400

    if "full_name" not in data and "email" not in data:
        return jsonify(error="Provide at least one editable profile field."), 400

    full_name = user["full_name"]
    email = user["email"]
    errors = {}
    if "full_name" in data:
        full_name_error = validate_full_name(data["full_name"])
        if full_name_error:
            errors["full_name"] = full_name_error
        else:
            full_name = data["full_name"].strip()
    if "email" in data:
        email_error = validate_email(data["email"])
        if email_error:
            errors["email"] = email_error
        else:
            email = data["email"].strip().lower()
    if errors:
        return jsonify(error="Validation failed.", details=errors), 400

    try:
        execute(
            "UPDATE users SET full_name = ?, email = ? WHERE id = ?",
            (full_name, email, user["id"]),
        )
    except sqlite3.IntegrityError:
        return jsonify(error="Email is already registered."), 409

    updated_user = query_one(
        """
        SELECT id, username, email, full_name, created_at
        FROM users
        WHERE id = ?
        """,
        (user["id"],),
    )
    return jsonify(_public_user(updated_user))


def _authenticated_user():
    user_id = session.get("user_id")
    if user_id is None:
        abort(401)
    user = query_one(
        """
        SELECT id, username, email, full_name, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    if user is None:
        session.clear()
        abort(401)
    return user
