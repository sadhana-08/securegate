import pytest

from app import create_app
from app.db import init_db


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "pytest-only-secret-key")
    test_app = create_app(
        {
            "TESTING": True,
            "PROPAGATE_EXCEPTIONS": False,
            "SECRET_KEY": "pytest-only-secret-key",
            "DATABASE": str(tmp_path / "securegate-test.sqlite3"),
            "SESSION_COOKIE_SECURE": False,
        }
    )
    with test_app.app_context():
        init_db()
    yield test_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def register_user(client):
    def _register_user(**overrides):
        data = {
            "username": "secure_user",
            "email": "secure.user@example.com",
            "password": "StrongPassword1!",
            "full_name": "Secure User",
        }
        data.update(overrides)
        csrf_token = client.get("/api/csrf-token").get_json()["csrf_token"]
        return client.post(
            "/api/auth/register",
            json=data,
            headers={"X-CSRF-Token": csrf_token},
        )

    return _register_user


@pytest.fixture
def login_user(client):
    def _login_user(identifier="secure_user", password="StrongPassword1!"):
        csrf_token = client.get("/api/csrf-token").get_json()["csrf_token"]
        return client.post(
            "/api/auth/login",
            json={"identifier": identifier, "password": password},
            headers={"X-CSRF-Token": csrf_token},
        )

    return _login_user


@pytest.fixture
def authenticated_client(client, register_user, login_user):
    registration = register_user()
    assert registration.status_code == 201
    login = login_user()
    assert login.status_code == 200
    return client


@pytest.fixture
def csrf_token(authenticated_client):
    response = authenticated_client.get("/api/csrf-token")
    assert response.status_code == 200
    return response.get_json()["csrf_token"]
