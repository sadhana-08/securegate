# Security Testing Methodology — SecureGate

This document explains the approach and standards used to test SecureGate,
and maps the project's testing activities to recognized industry
frameworks: the OWASP Web Security Testing Guide (WSTG) and the OWASP
Application Security Verification Standard (ASVS).

## 1. Testing Approach

Testing was performed in three complementary ways:

1. **Manual exploitation** of intentionally vulnerable, isolated lab apps
   (Phases 6–8), to understand each vulnerability class hands-on.
2. **Manual interception and retesting** using Burp Suite Community
   Edition (Phase 9), confirming the same attacks fail against the
   hardened secure app.
3. **Automated regression testing** using Pytest (Phase 10), so these
   security properties are re-verified automatically on every code change.

All testing was conducted exclusively against `127.0.0.1` (localhost).
Nothing in this project was tested against, or should ever be run against,
any publicly reachable system.

## 2. OWASP Web Security Testing Guide (WSTG) Mapping

| WSTG Category | Test performed | Phase |
|---|---|---|
| WSTG-ATHN (Authentication Testing) | Tested for weak password storage, credential guessing resistance, user enumeration | 8, 9, 10 |
| WSTG-SESS (Session Management Testing) | Tested session token predictability, cookie flags, session fixation, logout invalidation | 8, 9, 10 |
| WSTG-INPV (Input Validation Testing) | Tested SQL injection (auth bypass, UNION extraction) and XSS (reflected, stored) | 6, 7, 9, 10 |
| WSTG-IDNT (Identity Management Testing) | Tested registration validation, duplicate account prevention | 2, 10 |
| WSTG-CONF (Configuration Testing) | Verified security headers (CSP, X-Content-Type-Options, X-Frame-Options), CORS allowlist | 3, 9, 10 |
| WSTG-ERRH (Error Handling Testing) | Verified generic error messages, no stack trace leakage | 3, 10 |

## 3. OWASP ASVS Mapping (Level 1–2 controls demonstrated)

| ASVS Area | Requirement (paraphrased) | Where implemented |
|---|---|---|
| V2: Authentication | Passwords stored using an approved hashing algorithm | `backend/app/auth.py` — Werkzeug (PBKDF2) |
| V2: Authentication | Generic error messages for failed authentication | `backend/app/auth.py` |
| V2: Authentication | Rate limiting on authentication endpoints | `backend/app/db.py` — `login_attempts` table |
| V3: Session Management | Session tokens are generated using a secure method | Flask's signed session implementation |
| V3: Session Management | Cookies set with Secure, HttpOnly, SameSite | `backend/app/__init__.py` config |
| V4: Access Control | Enforce authorization on every request, not just authentication | `backend/app/auth.py` profile endpoints (user id from session, not request) |
| V5: Validation, Sanitization | All input validated server-side | `backend/app/validation.py` |
| V5: Validation, Sanitization | Output encoding prevents injection into other contexts | React's default escaping; no `dangerouslySetInnerHTML` |
| V7: Error Handling and Logging | Do not leak sensitive information in error responses | `backend/app/__init__.py` error handlers |
| V9: Communications | CSRF protection on state-changing requests | `backend/app/auth.py` CSRF token validation |
| V14: Configuration | Security headers configured | `backend/app/__init__.py` `after_request` |

## 4. Test Environment

- All testing performed on `127.0.0.1`, never a public network.
- Secure app: ports 5000 (backend) and 5173 (frontend).
- Vulnerability labs: ports 5001 (SQLi), 5002 (XSS), 5003 (broken auth),
  each gated behind a `SECUREGATE_LAB=1` environment variable and a
  localhost-only bind check.
- Tools used: Burp Suite Community Edition 2026.10.1, curl, Pytest.

## 5. Limitations

- Burp Suite Community Edition does not include the Scanner (automated
  vulnerability scanning) or unrestricted Intruder, available only in the
  Professional edition. Testing here relied on manual Proxy interception
  and Repeater, which is sufficient for a scoped, known set of
  vulnerabilities but is not a substitute for a full automated scan in a
  professional engagement.
- This methodology covers the three vulnerability classes built into this
  project (SQL Injection, XSS, Broken Authentication). It does not
  constitute a comprehensive penetration test of the entire OWASP Top 10.