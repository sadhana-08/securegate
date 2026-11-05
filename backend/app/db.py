import sqlite3
import time
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


def login_rate_limited(bucket_keys, max_attempts, window_seconds):
    cutoff = time.time() - window_seconds
    rows = get_db().execute(
        """
        SELECT bucket_key, COUNT(*) AS attempt_count
        FROM login_attempts
        WHERE bucket_key IN (?, ?) AND attempted_at > ?
        GROUP BY bucket_key
        """,
        (*bucket_keys, cutoff),
    ).fetchall()
    return any(row["attempt_count"] >= max_attempts for row in rows)


def record_failed_login(bucket_keys):
    connection = get_db()
    now = time.time()
    try:
        connection.execute(
            "DELETE FROM login_attempts WHERE attempted_at <= ?",
            (now - 15 * 60,),
        )
        connection.executemany(
            "INSERT INTO login_attempts (bucket_key, attempted_at) VALUES (?, ?)",
            ((bucket_key, now) for bucket_key in bucket_keys),
        )
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise


def clear_login_attempts(bucket_keys):
    execute(
        "DELETE FROM login_attempts WHERE bucket_key IN (?, ?)",
        tuple(bucket_keys),
    )


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
