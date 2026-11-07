# Threat Model — SecureGate

## 1. Overview

SecureGate is a student portal: registration, login, a dashboard, and
profile viewing/editing. This document identifies what we're protecting,
who might attack it, how, and what mitigates each threat. It follows a
simplified STRIDE approach, scoped to the system actually built in this
project.

## 2. Assets

| Asset | Description | Sensitivity |
|---|---|---|
| User credentials | Username, email, password hash | High |
| Session tokens | Signed cookies identifying a logged-in user | High |
| Profile data | Full name, email | Medium |
| Application availability | The service being reachable and responsive | Medium |

## 3. Actors

| Actor | Description | Trust level |
|---|---|---|
| Anonymous visitor | Hasn't registered or logged in | Untrusted |
| Registered student | Has an account, can log in | Semi-trusted (own data only) |
| Attacker | Malicious actor attempting to compromise the app | Untrusted, assumed hostile |
| Developer / admin | Has access to source code and server config | Trusted (out of scope for runtime threats) |

## 4. Trust Boundaries
[Browser] <--HTTPS/HTTP--> [React Frontend :5173] <--fetch--> [Flask API :5000] <--SQL--> [SQLite DB]

- **Browser ↔ Frontend:** untrusted network, anyone can intercept or modify
  traffic (mitigated by HTTPS in production; this local project runs over
  HTTP in dev).
- **Frontend ↔ Backend:** the backend must never trust that a request came
  from its own frontend just because it looks like it did — hence CORS,
  CSRF, and session validation all happen server-side.
- **Backend ↔ Database:** the backend is the only component that talks to
  the database. All queries must be parameterized.

## 5. Data Flow

1. Visitor submits registration form → Frontend sends JSON to
   `/api/auth/register` → Backend validates input → Backend hashes
   password → Backend inserts row into `users` table.
2. Visitor submits login form → Backend verifies credentials → Backend
   issues a signed session cookie → Frontend stores nothing itself (the
   browser holds the HttpOnly cookie, inaccessible to JavaScript).
3. Logged-in user requests `/api/profile` → Backend checks session →
   Backend looks up and returns only that user's row.
4. Logged-in user submits a profile edit → Frontend includes a CSRF token
   → Backend validates the token and the session → Backend updates only
   the authenticated user's row.

## 6. STRIDE Threat Analysis

| Threat category | Example in this app | Mitigation |
|---|---|---|
| **S**poofing | Attacker logs in as another user via SQL injection | Parameterized queries; password hashing (Phase 2) |
| **T**ampering | Attacker modifies a profile update to target another user's id | Server derives the user id from the session, never trusts a client-supplied id (Phase 3) |
| **R**epudiation | A user denies performing an action | Out of scope for this project (no audit log implemented); noted as a future enhancement |
| **I**nformation disclosure | Attacker extracts password hashes via UNION-based SQLi | Parameterized queries (Phase 2/6); password hashes never returned in any API response (Phase 10 test) |
| **D**enial of service | Attacker floods the login endpoint | Login rate limiting after 5 failed attempts (Phase 3) |
| **E**levation of privilege | Attacker forges a request to act as another user without logging in | Session validation + CSRF protection on all state-changing requests (Phase 3) |

## 7. Specific Threats Demonstrated in This Project

| ID | Threat | Where demonstrated | Where mitigated |
|---|---|---|---|
| T-01 | SQL injection authentication bypass | `security/vulnerability-labs/sqli-lab` | `backend/app/auth.py` (parameterized queries) |
| T-02 | SQL injection data extraction (UNION) | `security/vulnerability-labs/sqli-lab` | `backend/app/db.py` (parameterized queries) |
| T-03 | Reflected XSS | `security/vulnerability-labs/xss-lab` | React's default text rendering (no `dangerouslySetInnerHTML`) |
| T-04 | Stored XSS | `security/vulnerability-labs/xss-lab` | Same as T-03 |
| T-05 | Plaintext password storage | `security/vulnerability-labs/auth-lab` | Werkzeug password hashing (`backend/app/auth.py`) |
| T-06 | Predictable session identifiers | `security/vulnerability-labs/auth-lab` | Flask's signed, random session cookies |
| T-07 | Session fixation (no regeneration on login) | `security/vulnerability-labs/auth-lab` | Flask issues a fresh session on login |
| T-08 | Insecure cookie flags | `security/vulnerability-labs/auth-lab` | `HttpOnly`, `SameSite=Lax`, `Secure` (production) cookie flags |
| T-09 | Logout doesn't invalidate session | `security/vulnerability-labs/auth-lab` | Backend clears server-side session state on logout |
| T-10 | No login rate limiting | `security/vulnerability-labs/auth-lab` | 429 after 5 failed attempts in 15 minutes |
| T-11 | User enumeration via verbose errors | `security/vulnerability-labs/auth-lab` | Identical generic error for both cases |
| T-12 | Cross-site request forgery | Not a separate lab; tested directly against the secure app | CSRF token required on all state-changing requests |

## 8. Out of Scope

- Network-level attacks (DDoS, man-in-the-middle below the application
  layer) — this is a local educational project, not a deployed service.
- Physical security of the host machine.
- Social engineering of users.
- Multi-factor authentication (noted as a future enhancement).
- Audit logging / non-repudiation (noted as a future enhancement).

## 9. Residual Risk

Even with the above mitigations, this remains a student learning project,
not a production system. Before any real deployment, it would need: HTTPS
enforcement, a production-grade WSGI server (not Flask's dev server),
dependency vulnerability scanning, structured logging and monitoring, and
a formal secrets-management approach instead of a local `.env` file.