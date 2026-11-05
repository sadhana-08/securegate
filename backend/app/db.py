import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            timeout=5,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def query_one(sql, parameters=()):
    return get_db().execute(sql, parameters).fetchone()


def query_all(sql, parameters=()):
    return get_db().execute(sql, parameters).fetchall()


def execute(sql, parameters=()):
    connection = get_db()
    try:
        cursor = connection.execute(sql, parameters)
        connection.commit()
        return cursor
    except sqlite3.Error:
        connection.rollback()
        raise


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    get_db().executescript(schema)
    get_db().commit()


def register_db_teardown(app):
    app.teardown_appcontext(close_db)
