# Remediation Documentation

This document details exactly how each vulnerability class demonstrated in
the labs was remediated in the secure SecureGate application, with
before/after code and the verification method used to confirm the fix.

---

## 1. SQL Injection (Authentication Bypass & Data Extraction)

**Vulnerable pattern (lab):**

```python
query = f"SELECT id, username, full_name FROM users WHERE username = '{username}' AND password = '{password}'"
row = db.execute(query).fetchone()
```

**Remediation:**

```python
row = db.execute(
    "SELECT id, username, password_hash, full_name FROM users WHERE username = ?",
    (username,),
).fetchone()
```

**Why this works:** the `?` placeholder ensures user input is always
treated as data, never as part of the SQL command structure, regardless of
what characters it contains.

**Verification:** `backend/tests/test_security_regressions.py` includes an
automated test sending a `' -- ` style payload to the login endpoint and
asserting a `401` response, re-run on every push via
`.github/workflows/tests.yml`. Manually confirmed via Burp Suite Repeater
(Phase 9 evidence).

---

## 2. Cross-Site Scripting (Reflected & Stored)

**Vulnerable pattern (lab):**

```python
body = f"<p>You searched for: {q}</p>"
```

**Remediation:** the real frontend never constructs HTML by string
concatenation. All user-supplied values are rendered through React's
default JSX text interpolation (`{value}`), which escapes special
characters automatically. `dangerouslySetInnerHTML` is never used anywhere
in the codebase.

**Why this works:** the browser receives HTML-escaped text, so a payload
like `<script>` is displayed as the literal characters, never parsed as
markup or executed as code.

**Verification:** manually confirmed in-browser (Phase 9) — a profile
field containing `<script>document.title='hacked'</script>` is displayed
as literal text with no tab-title change. The backend test suite confirms
the API itself stores and returns the value unchanged as plain JSON text
(the escaping happens at the render layer, not the storage layer).

---

## 3. Plaintext Password Storage

**Vulnerable pattern (lab):**

```python
CREATE TABLE users (..., password TEXT)
if row["password"] != password: ...
```

**Remediation:**

```python
from werkzeug.security import generate_password_hash, check_password_hash

password_hash = generate_password_hash(password)        # at registration
check_password_hash(row["password_hash"], password)     # at login
```

**Why this works:** `generate_password_hash` uses a salted, computationally
expensive hashing algorithm (PBKDF2 by default in Werkzeug). Even with
full database access, an attacker cannot recover the original password
directly from the hash.

**Verification:** `backend/tests/test_security_regressions.py` confirms no
API response (registration, login, `/api/me`, `/api/profile`) ever
includes a `password` or `password_hash` field.

---

## 4. Predictable Sessions & Session Fixation

**Vulnerable pattern (lab):** sequential integer counters as session IDs,
reused across logins.

**Remediation:** Flask's built-in signed session mechanism is used,
backed by a `SECRET_KEY` loaded from environment configuration with no
hardcoded fallback. A new session is established on every successful
login.

**Verification:** manually confirmed via Burp Suite (Phase 9) — each login
response sets a fresh `Set-Cookie: session=...` value, structurally
distinct from a simple counter.

---

## 5. Insecure Cookie Flags

**Vulnerable pattern (lab):**

```python
resp.set_cookie("lab_session", session_id)
```

**Remediation:**

```python
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "false") == "true",
)
```

**Why this works:** `HttpOnly` prevents JavaScript (including an XSS
payload) from reading the cookie via `document.cookie`. `SameSite=Lax`
restricts the cookie from being sent on most cross-site requests,
mitigating CSRF. `Secure` (enabled in production) ensures the cookie is
only sent over HTTPS.

**Verification:** confirmed via Burp Suite response headers (Phase 9
evidence) and the automated test suite (Phase 10).

---

## 6. Session Not Invalidated on Logout

**Vulnerable pattern (lab):** logout only deletes the client-side cookie;
the server-side session record is never removed.

**Remediation:**

```python
@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    resp = make_response(jsonify({"status": "logged_out"}))
    resp.delete_cookie("session")
    return resp
```

**Verification:** automated test confirms `/api/me` returns `401` after
logout, using the same (now-invalid) cookie.

---

## 7. No Login Rate Limiting

**Remediation:** a `login_attempts` table tracks failed attempts per
username/IP within a rolling 15-minute window. After 5 failures, further
attempts return `429` until the window resets.

**Verification:** automated test performs 6 failed logins and asserts the
sixth returns `429`. Also manually confirmed in Phase 9's hands-on
testing.

---

## 8. User Enumeration via Verbose Errors

**Vulnerable pattern (lab):** distinct messages for "no such user" vs.
"wrong password."

**Remediation:**

```python
return jsonify({"error": "Invalid username/email or password."}), 401
```

The exact same message and status code are returned regardless of which
part of the credential pair was wrong.

**Verification:** confirmed via Burp Suite Repeater, sending both a
nonexistent username and a real username with a wrong password, and
observing byte-identical responses (Phase 9 evidence). Also covered by the
automated test suite.

---

## 9. Missing CSRF Protection

**Remediation:** a `GET /api/csrf-token` endpoint issues a token tied to
the session. Every state-changing request (register, login, logout,
profile update) must include a matching `X-CSRF-Token` header, validated
server-side with a constant-time comparison.

**Verification:** confirmed via Burp Suite Repeater — a request with an
invalid token is rejected with `403` even when the credentials themselves
are valid (Phase 9 evidence). Automated tests confirm both a missing and
an invalid token are rejected.