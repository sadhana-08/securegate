# Vulnerability Assessment Report — SecureGate (Sample)

## Report Metadata

- **Application:** SecureGate Student Portal
- **Assessment date:** November 2026
- **Assessor:** SADHANA S
- **Scope:** Local vulnerability labs (`127.0.0.1:5001`, `5002`, `5003`)
  and the secure application (`127.0.0.1:5000`, `5173`)
- **Tools used:** Burp Suite Community Edition 2026.10.1, curl, Pytest

## Executive Summary

This assessment examined SecureGate, a student portal built with a React
frontend and a Flask REST API. Three isolated, intentionally vulnerable
lab applications were built to demonstrate SQL Injection, Cross-Site
Scripting, and Broken Authentication, and each vulnerability was then
verified as remediated in the production-intended secure application. All
12 identified weaknesses were successfully mitigated and confirmed through
manual retesting (Burp Suite) and an automated regression suite (17
passing Pytest tests, re-run on every commit via GitHub Actions). No open
findings remain in the secure application as of this assessment.

## Scope and Methodology

Testing covered the isolated vulnerability labs and the secure
application, all running exclusively on localhost. See
`testing-methodology.md` for the full WSTG/ASVS mapping. Methodology
combined manual exploitation of the labs, manual interception and
retesting via Burp Suite, and automated Pytest regression tests.

## Findings Summary Table

| ID | Title | OWASP Top 10 Category | CWE ID | Severity | Status |
|---|---|---|---|---|---|
| F-01 | SQL injection authentication bypass | A03:2021 – Injection | CWE-89 | Critical | Fixed |
| F-02 | SQL injection UNION-based data extraction | A03:2021 – Injection | CWE-89 | Critical | Fixed |
| F-03 | Reflected XSS | A03:2021 – Injection | CWE-79 | High | Fixed |
| F-04 | Stored XSS | A03:2021 – Injection | CWE-79 | High | Fixed |
| F-05 | Plaintext password storage | A02:2021 – Cryptographic Failures | CWE-256 | Critical | Fixed |
| F-06 | Predictable session identifiers | A07:2021 – Auth Failures | CWE-330 | High | Fixed |
| F-07 | No session regeneration on login | A07:2021 – Auth Failures | CWE-384 | Medium | Fixed |
| F-08 | Insecure cookie flags | A05:2021 – Security Misconfiguration | CWE-1004 | Medium | Fixed |
| F-09 | Logout doesn't invalidate session | A07:2021 – Auth Failures | CWE-613 | Medium | Fixed |
| F-10 | No login rate limiting | A07:2021 – Auth Failures | CWE-307 | Medium | Fixed |
| F-11 | User enumeration via verbose errors | A07:2021 – Auth Failures | CWE-203 | Low | Fixed |
| F-12 | Missing CSRF protection | A01:2021 – Broken Access Control | CWE-352 | High | Fixed |

## Detailed Findings

### F-01: SQL Injection — Authentication Bypass

- **Severity:** Critical
- **OWASP Top 10 Category:** A03:2021 – Injection
- **CWE ID:** CWE-89
- **Location:** `security/vulnerability-labs/sqli-lab/app.py`, `/api/lab/login`

**Description**

The login endpoint built its SQL query using Python f-strings, directly
embedding user-supplied input into the query text.

**Proof of Concept**
POST /api/lab/login
{“username”: “demo_lab_alex’ -- “, “password”: “anything”}

Resulting query: `SELECT ... WHERE username = 'demo_lab_alex' --' AND password = 'anything'`
— the `--` comments out the password check entirely.

**Impact**

Complete authentication bypass; an attacker can log in as any known
username with no valid password.

**Remediation**

Replaced with a parameterized query (see `remediation.md`, section 1).

**Retest Result**

The identical payload sent to the secure app's `/api/auth/login` returns
`401 Unauthorized` with a generic error message (evidence:
`security/reports/evidence/02-sqli-retest-blocked.png`).

---

### F-03: Reflected Cross-Site Scripting

- **Severity:** High
- **OWASP Top 10 Category:** A03:2021 – Injection
- **CWE ID:** CWE-79
- **Location:** `security/vulnerability-labs/xss-lab/app.py`, `/search`

**Description**

The search endpoint inserted the `q` query parameter directly into an HTML
response with no escaping.

**Proof of Concept**
GET /search?q=<script>document.title='hacked'</script>

The browser tab title changed to "hacked," confirming script execution.

**Impact**

An attacker could craft a malicious link; if a victim clicked it while
authenticated, a real payload could steal session cookies or perform
actions on the victim's behalf.

**Remediation**

The secure frontend renders all values through React's default text
interpolation; `dangerouslySetInnerHTML` is never used (see
`remediation.md`, section 2).

**Retest Result**

The same payload, submitted as a profile field in the secure app, is
displayed as literal visible text with no tab-title change (evidence:
`security/reports/evidence/01-xss-retest-rendered-as-text.png`).

---

### F-11: User Enumeration via Verbose Errors

- **Severity:** Low
- **OWASP Top 10 Category:** A07:2021 – Identification and Authentication Failures
- **CWE ID:** CWE-203
- **Location:** `security/vulnerability-labs/auth-lab/app.py`, `/api/lab/login`

**Description**

The login endpoint returned a distinct `404 "No account with that
username"` for nonexistent usernames versus a `401 "That password is
incorrect"` for existing usernames with a wrong password, allowing an
attacker to enumerate valid accounts.

**Proof of Concept**
POST /api/lab/login {“username”:”nobody_real”,”password”:”x”} → 404
POST /api/lab/login {“username”:”demo_lab_alex”,”password”:”x”} → 401

**Impact**

An attacker can build a list of valid usernames without guessing any
passwords, narrowing the target list for a subsequent credential-guessing
attack.

**Remediation**

The secure app returns an identical message and status code for both
cases (see `remediation.md`, section 8).

**Retest Result**

Confirmed byte-identical responses (`401`, same error text, same
`Content-Length: 53`) for both a nonexistent username and a wrong password
against a real username (evidence:
`security/reports/evidence/04-enum-test-fake-user.png` and
`05-enum-test-wrong-password.png`).

---

### F-12: Missing CSRF Protection

- **Severity:** High
- **OWASP Top 10 Category:** A01:2021 – Broken Access Control
- **CWE ID:** CWE-352
- **Location:** Demonstrated by contrast — none of the isolated labs implement CSRF protection.

**Description**

None of the lab applications validate any form of anti-CSRF token,
meaning a malicious site could trigger authenticated actions on a victim's
behalf if the victim were logged in and visited it.

**Impact**

An attacker-controlled page could silently submit requests (e.g. a
profile change) using the victim's existing session cookie.

**Remediation**

The secure app issues and validates a CSRF token on every state-changing
request (see `remediation.md`, section 9).

**Retest Result**

A valid login request with a tampered `X-CSRF-Token` header is rejected
with `403 Forbidden`, even though the credentials themselves were correct
(evidence: `security/reports/evidence/03-csrf-invalid-token-blocked.png`).

---

[Additional findings F-02, F-04 through F-10 follow the same format and
are fully documented in `vulnerability-comparison-table.md` and
`remediation.md`, with supporting evidence in `security/reports/evidence/`
and automated coverage in `backend/tests/test_security_regressions.py`.]

## Overall Risk Rating

All 12 findings identified during this assessment have been remediated in
the secure application and verified through both manual retesting and an
automated regression suite (17/17 tests passing). The secure application
demonstrates resistance to SQL Injection, Cross-Site Scripting, and the
full range of Broken Authentication weaknesses tested. As this remains a
local educational project, production deployment would require additional
hardening noted in `threat-model.md`, section 9 (Residual Risk).
