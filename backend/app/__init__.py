import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify

from app.auth import auth_bp
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

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    return app
