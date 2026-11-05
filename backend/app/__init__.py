import os

from dotenv import load_dotenv
from flask import Flask, jsonify


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_mapping(
        DEBUG=os.getenv("FLASK_DEBUG", "0") == "1",
        SECRET_KEY=os.getenv("SECRET_KEY"),
    )

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    return app
