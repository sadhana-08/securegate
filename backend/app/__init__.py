import hmac
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, request, session
from werkzeug.exceptions import HTTPException

from app.auth import api_bp, auth_bp
from app.db import register_db_teardown


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY must be set in the environment or .env file.")

    app.config.from_mapping(
        DEBUG=os.getenv("FLASK_DEBUG", "0") == "1",
        SECRET_KEY=secret_key,
        DATABASE=os.path.join(app.instance_path, "securegate.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1",
    )
    if test_config is not None:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    register_db_teardown(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    @app.before_request
    def enforce_csrf():
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None
        if request.endpoint is None:
            return None
        if request.endpoint == "api.update_profile" and "user_id" not in session:
            return None

        expected_token = session.get("csrf_token")
        supplied_token = request.headers.get("X-CSRF-Token", "")
        if (
            not isinstance(expected_token, str)
            or not supplied_token
            or not hmac.compare_digest(expected_token, supplied_token)
        ):
            abort(403)
        return None

    @app.after_request
    def add_security_headers(response):
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"

        response.vary.add("Origin")
        allowed_origins = {
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        }
        origin = request.headers.get("Origin")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, X-CSRF-Token"
            )
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, OPTIONS"
            )
        return response

    error_messages = {
        400: "Bad request.",
        401: "Authentication required.",
        403: "Request forbidden.",
        404: "Resource not found.",
        405: "Method not allowed.",
        500: "Internal server error.",
    }

    def json_error(error):
        status_code = error.code if isinstance(error, HTTPException) else 500
        return jsonify(error=error_messages[status_code]), status_code

    for status_code in error_messages:
        app.register_error_handler(status_code, json_error)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    return app
