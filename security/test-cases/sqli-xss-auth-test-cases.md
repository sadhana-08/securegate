# Test Case Table

| ID | Objective | Steps | Expected result (vulnerable lab) | Expected result (secure app) |
|---|---|---|---|---|
| TC-01 | Auth bypass via SQLi | POST login with `username: "demo_lab_alex' -- "` | Login succeeds with no valid password | 401, generic failure |
| TC-02 | Data extraction via SQLi | GET search with UNION payload | Returns rows from `secrets` table | No extra data, literal search only |
| TC-03 | Reflected XSS | GET `/search?q=<script>...` | Script executes in browser | Payload shown as escaped text |
| TC-04 | Stored XSS | POST comment with `<script>...` | Script executes for every future viewer | Payload shown as escaped text |
| TC-05 | User enumeration | POST login with fake vs real username | Different error messages | Same generic message both times |
| TC-06 | No rate limiting | 10 rapid failed logins | All return 401, no lockout | 6th attempt returns 429 |
| TC-07 | Insecure cookie flags | Inspect `Set-Cookie` after login | No `HttpOnly`/`SameSite` | `HttpOnly`, `SameSite=Lax` present |
| TC-08 | Session survives logout | Call `/me` with old cookie after logout | Still returns user data | 401 after logout |
| TC-09 | CSRF protection | Resend a PUT profile request with no `X-CSRF-Token` | N/A (lab has no CSRF logic) | 403 forbidden |
| TC-10 | Security headers present | Inspect response headers | Minimal/no security headers (lab) | CSP, X-Frame-Options, nosniff, etc. present |