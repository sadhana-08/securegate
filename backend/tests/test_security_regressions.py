import pytest

from app.db import query_one


def test_login_rejects_sql_injection_payload(login_user):
    response = login_user(identifier="' -- ")

    assert response.status_code == 401
    assert response.status_code != 500
    assert response.get_json()["error"] == "Invalid username/email or password."


def test_profile_script_text_is_stored_and_returned_as_json(
    app, authenticated_client, csrf_token
):
    script_text = '<script>alert("profile")</script>'
    response = authenticated_client.put(
        "/api/profile",
        json={"full_name": script_text},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert response.get_json()["full_name"] == script_text

    profile = authenticated_client.get("/api/profile")
    assert profile.status_code == 200
    assert profile.mimetype == "application/json"
    assert profile.get_json()["full_name"] == script_text


def test_profile_update_without_csrf_header_is_rejected(authenticated_client):
    response = authenticated_client.put(
        "/api/profile",
        json={"full_name": "Changed Name"},
    )

    assert response.status_code == 403


def test_profile_update_with_invalid_csrf_header_is_rejected(
    authenticated_client, csrf_token
):
    response = authenticated_client.put(
        "/api/profile",
        json={"full_name": "Changed Name"},
        headers={"X-CSRF-Token": f"{csrf_token}-invalid"},
    )

    assert response.status_code == 403


def test_user_id_parameter_cannot_view_or_edit_another_profile(
    app, authenticated_client, register_user, csrf_token
):
    owner_profile = authenticated_client.get("/api/profile").get_json()
    other_registration = register_user(
        username="other_user",
        email="other.user@example.com",
    )
    other_id = other_registration.get_json()["user"]["id"]
    assert other_id != owner_profile["id"]

    profile = authenticated_client.get(f"/api/profile?user_id={other_id}")
    assert profile.status_code == 200
    assert profile.get_json()["id"] == owner_profile["id"]

    update = authenticated_client.put(
        f"/api/profile?user_id={other_id}",
        json={"full_name": "Owner Updated", "user_id": other_id},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert update.status_code == 200
    assert update.get_json()["id"] == owner_profile["id"]

    with app.app_context():
        other_user = query_one(
            "SELECT full_name FROM users WHERE id = ?",
            (other_id,),
        )
    assert other_user["full_name"] == "Secure User"


@pytest.mark.parametrize("path", ["/api/me", "/api/profile"])
def test_profile_endpoints_require_authentication(client, path):
    response = client.get(path)

    assert response.status_code == 401


def test_session_cookie_is_httponly_and_secure_when_configured(
    app, register_user, login_user
):
    registration = register_user()
    assert registration.status_code == 201
    app.config["SESSION_COOKIE_SECURE"] = True

    response = login_user()

    assert response.status_code == 200
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "Secure" in cookie


def test_security_headers_are_present(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_authentication_and_profile_responses_never_expose_password_hashes(
    client, register_user, login_user
):
    registration = register_user()
    assert registration.status_code == 201
    login = login_user()
    assert login.status_code == 200

    responses = [
        registration,
        login,
        client.get("/api/me"),
        client.get("/api/profile"),
    ]
    for response in responses:
        assert response.status_code in {200, 201}
        assert "password_hash" not in response.get_data(as_text=True)


def test_internal_server_error_returns_only_generic_message(app, client):
    def fail_with_internal_details():
        raise RuntimeError("sensitive database implementation detail")

    app.add_url_rule(
        "/api/test-forced-error",
        endpoint="test_forced_error",
        view_func=fail_with_internal_details,
    )
    response = client.get("/api/test-forced-error")

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error."}
    body = response.get_data(as_text=True)
    assert "Traceback" not in body
    assert "sensitive database implementation detail" not in body


def test_wrong_password_and_unknown_username_have_same_response(
    register_user, login_user
):
    registration = register_user()
    assert registration.status_code == 201

    wrong_password = login_user(password="WrongPassword1!")
    unknown_username = login_user(
        identifier="unknown_user",
        password="WrongPassword1!",
    )

    assert wrong_password.status_code == unknown_username.status_code == 401
    assert wrong_password.get_json()["error"] == unknown_username.get_json()["error"]


@pytest.mark.parametrize(
    ("field", "duplicate_value"),
    [
        ("username", "secure_user"),
        ("email", "secure.user@example.com"),
    ],
)
def test_duplicate_registration_is_rejected(register_user, field, duplicate_value):
    first_registration = register_user()
    assert first_registration.status_code == 201

    duplicate_data = {
        "username": "second_user",
        "email": "second.user@example.com",
    }
    duplicate_data[field] = duplicate_value
    duplicate_registration = register_user(**duplicate_data)

    assert duplicate_registration.status_code == 409


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("email", "not-an-email"),
        ("password", "short"),
    ],
)
def test_registration_rejects_invalid_email_or_password(
    register_user, field, invalid_value
):
    response = register_user(**{field: invalid_value})

    assert response.status_code == 400
    assert field in response.get_json()["details"]


def test_sixth_failed_login_attempt_is_rate_limited(login_user):
    responses = [
        login_user(
            identifier="unknown_user",
            password="WrongPassword1!",
        )
        for _ in range(6)
    ]

    assert [response.status_code for response in responses] == [
        401,
        401,
        401,
        401,
        401,
        429,
    ]
