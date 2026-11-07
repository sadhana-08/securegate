# Burp Suite Testing Workflow

This document explains how to use Burp Suite Community Edition to manually
test the SecureGate labs and the secure app, entirely on localhost.

**Only ever point Burp at 127.0.0.1 ports used by this project (5000, 5001,
5002, 5003). Never scan or intercept traffic to any other site or network.**

---

## 1. Install and open Burp Suite Community Edition

Download from [portswigger.net/burp/communitydownload](https://portswigger.net/burp/communitydownload),
install, and open it. Choose **Temporary project** and the default settings
when prompted.

## 2. Configure the proxy listener

1. Go to the **Proxy** tab → **Proxy settings** (or **Options** in older
   versions).
2. Confirm a listener exists on `127.0.0.1:8080` (Burp's default). If not,
   add one.
3. Leave **Intercept is on** toggled for now (you'll use this shortly).

## 3. Configure your browser to use the Burp proxy

The easiest approach is a dedicated browser profile so normal browsing
isn't affected:

1. In Firefox: **Settings → General → Network Settings → Manual proxy
   configuration** → HTTP Proxy `127.0.0.1`, Port `8080`, and check "Also
   use this proxy for HTTPS."
2. Alternatively, Burp's built-in Chromium browser (**Proxy → Intercept →
   Open browser**) is pre-configured and the simplest option for this lab.

## 4. Install Burp's CA certificate (for HTTPS sites only)

Not required for this project, since everything runs on plain HTTP
(`127.0.0.1`), not HTTPS. Skip this step unless you extend the project
later to use HTTPS locally.

## 5. Intercepting a request

1. In Burp, go to **Proxy → Intercept**, make sure **Intercept is on**.
2. In your proxied browser, open `http://127.0.0.1:5173` (the secure
   frontend) or `http://127.0.0.1:5001` (the SQLi lab) and perform an
   action, like logging in.
3. The request pauses in Burp before reaching the server. You can inspect
   headers, cookies, and the body, then click **Forward** to let it
   through, or **Drop** to cancel it.

## 6. Sending a request to Repeater

Repeater lets you resend and edit a captured request repeatedly, ideal for
testing payloads:

1. Right-click an intercepted request → **Send to Repeater**.
2. Go to the **Repeater** tab, edit the request body or headers (for
   example, change a login's username field to an injection payload).
3. Click **Send** and inspect the response on the right.

## 7. Intruder (Community Edition limits)

Burp Community's Intruder is heavily rate-limited and not suited for real
brute-force testing, but it's still useful to see the concept:

1. Right-click a login request → **Send to Intruder**.
2. In the **Positions** tab, highlight the password field value and click
   **Add §** to mark it as the injection point.
3. In the **Payloads** tab, add a short list of test passwords.
4. Click **Start attack**. Community Edition throttles this heavily, so
   use it only to demonstrate the concept with a handful of payloads, not
   as a real brute-force tool.

## 8. Inspecting parameters and cookies

For any captured request, check:

- **Headers** tab: look at `Cookie`, `Content-Type`, `X-CSRF-Token`.
- **Response** tab, **Headers** sub-tab: check for `Set-Cookie` flags
  (`HttpOnly`, `SameSite`, `Secure`) and security headers (`Content-
  Security-Policy`, `X-Frame-Options`, etc.).

## 9. Authentication testing checklist

- Does the login response reveal whether a username or password was wrong
  (user enumeration)?
- Is the session cookie random-looking and unpredictable, or sequential?
- Does the cookie have `HttpOnly` and `SameSite` set?
- Does the session still work after logout (replay the old cookie)?
- Is there any rate limiting after repeated failed logins?

## 10. SQL Injection testing (against the isolated SQLi lab only, port 5001)

1. Intercept a request to `/api/lab/login` or `/api/lab/search`.
2. Send it to Repeater.
3. Edit the `username` or `name` field to include a payload such as
   `' -- ` or `' UNION SELECT ...`.
4. Compare the response against a normal request. A successful injection
   shows a login bypass, extra rows, or a database error revealing the
   query structure.

See `security/vulnerability-labs/sqli/README.md` for the exact payloads
already confirmed to work against this lab.

## 11. XSS testing (against the isolated XSS lab only, port 5002)

1. Intercept a request to `/search` or a POST to `/comments`.
2. In Repeater, change the `q` parameter or `body` field to a payload like
   `<script>document.title='test'</script>`.
3. Send, then open the resulting URL/page in the browser (Repeater's
   response viewer has a **Render** tab) to confirm the script executes.

See `security/vulnerability-labs/xss/README.md` for confirmed payloads.

## 12. Session security testing (against the broken-auth lab, port 5003)

1. Log in via Repeater and note the `Set-Cookie: lab_session=...` value.
2. Log in again and compare, is the new session ID just one higher than
   the last (sequential, predictable)?
3. Log out, then resend an earlier request using the old cookie value,
   does `/api/lab/me` still respond successfully?

## 13. Retesting after remediation (against the secure app, port 5000)

Repeat the same SQLi, XSS, and session tests from steps 10 to 12, but
targeted at the real secure backend endpoints (`/api/auth/login`,
`/api/profile`, etc.) instead of the lab ports. Confirm each attack that
worked against the lab now fails against the secure app:

- SQLi payloads are treated as literal text, no bypass, no extra rows.
- `<script>` payloads are returned as escaped text in the frontend, not
  executed.
- Session cookies show `HttpOnly` and `SameSite=Lax`.
- A request without a valid CSRF token is rejected with `403`.
- Old sessions don't work after logout.

## Evidence checklist

Save screenshots to `security/reports/evidence/`, named clearly, for
example:

- `01-sqli-login-bypass-lab.png`
- `02-sqli-union-extraction-lab.png`
- `03-sqli-retest-secure-app-blocked.png`
- `04-xss-reflected-lab.png`
- `05-xss-stored-lab.png`
- `06-xss-retest-secure-app-blocked.png`
- `07-auth-sequential-session-lab.png`
- `08-auth-logout-still-works-lab.png`
- `09-auth-retest-secure-app-cookie-flags.png`
- `10-burp-repeater-example.png`

**Do not commit Burp project files (`.burp` extension) to git.** Only
screenshots and this documentation belong in the repository.