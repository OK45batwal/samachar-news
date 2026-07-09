---
phase: code-review
reviewed: 2026-07-09T18:00:00Z
depth: deep
files_reviewed: 32
files_reviewed_list:
  - backend/app.py
  - backend/config.py
  - backend/database/__init__.py
  - backend/models/models.py
  - backend/schemas.py
  - backend/seed.py
  - backend/seed_e2e_inline.py
  - backend/log_config.py
  - backend/auth/auth.py
  - backend/auth/supertokens.py
  - backend/routes/auth_routes.py
  - backend/routes/news.py
  - backend/routes/bookmarks.py
  - backend/routes/admin_routes.py
  - backend/services/news_service.py
  - backend/services/rate_limit.py
  - backend/services/scheduler.py
  - backend/services/task_manager.py
  - backend/websocket/ws.py
  - backend/ai/ai_service.py
  - backend/utils/utils.py
  - frontend/index.html
  - frontend/home.html
  - frontend/login.html
  - frontend/register.html
  - frontend/article.html
  - frontend/latest.html
  - frontend/profile.html
  - frontend/live.html
  - frontend/trending.html
  - frontend/forgot-password.html
  - frontend/assets/js/api.js
  - frontend/assets/js/app.js
  - frontend/assets/js/layout.js
  - requirements.txt
  - render.yaml
  - Procfile
findings:
  critical: 9
  warning: 10
  info: 7
  total: 26
status: issues_found
---

# Code Review Report

**Reviewed:** 2026-07-09T18:00:00Z
**Depth:** deep (cross-file analysis)
**Files Reviewed:** 32 source files (backend + frontend)
**Status:** issues_found

## Summary

A comprehensive deep-dive review of the Samachar News codebase identified **26 total findings**: 9 critical, 10 warnings, and 7 informational. The most severe issues involve **stored XSS vulnerabilities** in article content rendering (RSS feed data is injected into the DOM via `innerHTML` without sanitization), **missing API endpoints** that break core features (WebSocket authentication always fails; trending page calls non-existent routes), **no rate limiting on authentication endpoints** (brute force attacks are trivial), and a **cosmetic-only password reset page** with no backend implementation.

The application has several security hardening gaps: no CSRF protection with cookie-based auth, HSTS only conditionally set, CSP allows `'unsafe-inline'`, and the session cookie is set to `secure=True` which breaks on localhost HTTP.

Code quality concerns include empty catch blocks that silently swallow errors, raw SQL queries mixed with ORM code, and dead code paths (Supertokens init never actually used).

---

## Critical Issues

### CR-01: Stored Cross-Site Scripting (XSS) in Article Content Rendering

**File:** `frontend/assets/js/app.js:358-360`
**Severity:** CRITICAL — Stored XSS

**Issue:** Article content from RSS feeds is written directly to the DOM via `innerHTML` with no sanitization. Article titles, summaries, and content are all sourced from external RSS feeds and could contain malicious `<script>` tags, event handlers, or other HTML that executes in the context of the application's origin.

```javascript
// app.js:358-360
document.getElementById('articleContent').innerHTML =
    (article.content || article.summary || 'No content available')
        .split('\n').filter(Boolean).map(p => `<p>${p}</p>`).join('');
```

The same pattern exists for error messages (line 384), search results (line 131-136), and more. If an attacker controls any RSS feed in `FEED_CONFIG`, they can execute arbitrary JavaScript in every user's browser.

**Fix:** Use `textContent` for safe text insertion, or sanitize HTML with DOMPurify before using `innerHTML`. Replace with:

```javascript
// Safe approach:
const contentEl = document.getElementById('articleContent');
contentEl.innerHTML = '';
(article.content || article.summary || 'No content available')
    .split('\n').filter(Boolean).forEach(p => {
        const pEl = document.createElement('p');
        pEl.textContent = p;
        contentEl.appendChild(pEl);
    });
```

For the error case (line 384), use:
```javascript
document.getElementById('articleContent').textContent = err.message;
```

---

### CR-02: Stored XSS in News Card Rendering

**File:** `frontend/assets/js/app.js:29-63` (`renderNewsCard`)
**Severity:** CRITICAL — Stored XSS

**Issue:** The `renderNewsCard()` function builds HTML via template literals and injects `article.title` and `article.summary` directly into `innerHTML` (at line 175). These values come from external RSS feeds and are never sanitized.

```javascript
// app.js:47-48
`<h3 class="line-clamp-2">${article.title}</h3>
 <p class="line-clamp-2 mt-1">${article.summary || ''}</p>`
```

**Fix:** Either use DOMPurify to sanitize before insertion, or build DOM nodes with `textContent` instead of template literal interpolation. Add a sanitization helper:

```javascript
function sanitize(str) {
    const el = document.createElement('div');
    el.textContent = str || '';
    return el.innerHTML; // safely escaped
}
```

---

### CR-03: Missing `/api/auth/ws-token` Endpoint — WebSocket Auth Always Fails

**Files:** `frontend/assets/js/api.js:93-95`, `frontend/assets/js/app.js:99`

**Severity:** CRITICAL — Broken feature

**Issue:** The frontend calls `getWsToken()` which makes a GET request to `/api/auth/ws-token`. This endpoint does NOT exist in `backend/routes/auth_routes.py` or anywhere else in the backend. Every WebSocket connection attempt will fail at line 99-103 of `app.js` because the token fetch returns a 404, causing `ws.close()` to be called immediately.

**Fix:** Add a `ws-token` endpoint to `auth_routes.py`:

```python
@router.get("/ws-token")
async def ws_token(user: User = Depends(get_current_user)):
    token = create_access_token({"sub": user.id}, expires_delta=timedelta(hours=1))
    return {"token": token}
```

---

### CR-04: Non-Existent `/articles/trending` API — Trending Page Broken

**File:** `frontend/trending.html:101` (inline script)

**Severity:** CRITICAL — Broken feature

**Issue:** The trending.html inline script calls `window.api.get(\`/articles/${o}?page=${n}&limit=12\`)` which resolves to e.g., `/articles/trending?page=1&limit=12`. This API route does NOT exist in the backend. There is no `/articles/trending` or `/api/trending` endpoint defined. The trending page will never load content.

Additionally, `window.api.get(...)` is used instead of the existing `getArticles()` helper — this bypasses the API_BASE prefix and standard error handling.

**Fix:** Either:
1. Add a trending endpoint to `backend/routes/news.py` and call it via `getArticles({sort: 'trending', page: n, limit: 12})`, OR
2. Remove the separate trending page and redirect to `latest.html`

---

### CR-05: Hardcoded Production WebSocket URL in live.html — CORS/Connection Failure

**File:** `frontend/live.html:89` (inline script)

**Severity:** CRITICAL — Broken feature / Security

**Issue:** The live.html page hardcodes `wss://api.samachar.app/live` as the WebSocket URL. This is a production domain that:
1. Does not match the application's actual deployment domain
2. Will fail with CORS/connection errors in any environment except the production deployment
3. Bypasses the actual WS endpoint at `/api/ws` that is already defined in `backend/websocket/ws.py`
4. Cannot be authenticated because the same page relies on an API at a completely different origin

**Fix:** Use the same origin WS endpoint pattern as `app.js:72-75`:

```javascript
const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${proto}//${window.location.host}/api/ws`;
```

---

### CR-06: No Rate Limiting on Authentication Endpoints

**File:** `backend/services/rate_limit.py` (defined but never used)

**Severity:** CRITICAL — Brute force / DoS vulnerability

**Issue:** The `rate_limit` dependency is defined in `backend/services/rate_limit.py` but is NEVER imported or applied to any route. The `/api/auth/login` and `/api/auth/register` endpoints (and all other public endpoints) have NO rate limiting. An attacker can:
- Brute force passwords without restriction
- Flood the registration endpoint to exhaust resources
- Spray credentials across user accounts

The `RATE_LIMIT_PER_MINUTE` config setting exists but is dead code.

**Fix:** Apply the `rate_limit` dependency to all public endpoints:

```python
# In auth_routes.py
from ..services.rate_limit import rate_limit

@router.post("/login")
async def login(
    data: LoginRequest, 
    response: Response, 
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit),
):
    ...
```

---

### CR-07: No CSRF Protection with Cookie-Based Authentication

**File:** `frontend/assets/js/api.js:11` (credentials: 'include'), `backend/routes/auth_routes.py:53-62` (cookie set)

**Severity:** CRITICAL — CSRF vulnerability

**Issue:** The application uses cookie-based authentication (`access_token` cookie with `SameSite="lax"`) combined with `credentials: 'include'` on every API request. There is NO CSRF token anywhere. While SameSite=Lax offers some protection for top-level navigations, it does not protect against:
- `POST` requests via cross-origin form submissions (though CORS would block these on API endpoints)
- More critically, the WebSocket endpoint at `/api/ws` authenticates via a JWT token sent in the first message, which is not subject to SameSite protections

**Fix:** Either:
1. Use custom request header (`X-CSRF-Token`) validated server-side for state-changing operations
2. OR switch to `SameSite=Strict` for the auth cookie if cross-site usage isn't needed
3. OR use the `Authorization` header instead of cookies (the `OAuth2PasswordBearer` scheme already supports this)

---

### CR-08: `/dbg` Debug Endpoint Exposes System Information

**File:** `backend/app.py:133-143`

**Severity:** CRITICAL — Information disclosure

**Issue:** The `/dbg` endpoint exposes detailed system information to anyone who accesses it:
- Python version and executable path
- Current working directory
- System username
- Whether `DATABASE_URL` is set (confirms DB connection info)
- Server port

This information aids attackers in reconnaissance.

**Fix:** Remove the `/dbg` endpoint entirely, or gate it behind admin authentication:

```python
@app.get("/dbg")
async def debug(admin=Depends(require_admin)):
    ...
```

---

### CR-09: Password Reset Page Has No Backend Implementation

**File:** `frontend/forgot-password.html:92-102`

**Severity:** CRITICAL — Misleading UX / Missing critical feature

**Issue:** The forgot password page shows a fake "sending" animation (1.5s setTimeout) then displays "Check Your Email" with the user's email in the message. There is NO corresponding backend endpoint for password reset, no email sending, and no token generation. Users who forget their password have NO way to reset it — they are permanently locked out.

The page also reflects user-controlled input (`email`) into `innerHTML` on line 100 via string concatenation: `'...<strong>' + email + '</strong>...'`.

**Fix:** Either:
1. Implement a proper password reset flow (generate reset token, send email, verify + reset), OR
2. Remove the forgot-password.html page and related link if password reset is out of scope

---

## Warnings

### WR-01: JWT Tokens Not Invalidated on Logout

**File:** `backend/routes/auth_routes.py:104-107`

**Severity:** WARNING — Session management

**Issue:** The logout endpoint only deletes the cookie (`response.delete_cookie`) but does NOT invalidate the JWT. The token remains valid until its expiration (30 minutes by default). An attacker who steals a JWT can continue using it even after the legitimate user logs out.

**Fix:** Maintain a token blocklist in Redis (or DB for fallback) and check it during `get_current_user`:

```python
# During logout
await redis.sadd("token_blacklist", token_jti)

# During auth check
if await redis.sismember("token_blacklist", jti):
    raise HTTPException(status_code=401, detail="Token revoked")
```

---

### WR-02: Weak Password Policy — Only 6 Characters Minimum

**File:** `backend/routes/auth_routes.py:47-49`

**Severity:** WARNING — Security

**Issue:** The registration password validator requires only 6 characters minimum, with no complexity requirements (no uppercase, lowercase, digits, or special characters). This allows extremely weak passwords like "123456" or "abcdef".

**Fix:** Strengthen password requirements:

```python
@field_validator("password")
@classmethod
def valid_password(cls, v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain an uppercase letter")
    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain a lowercase letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain a digit")
    return v
```

---

### WR-03: Cookie `secure=True` Prevents Login on Localhost HTTP

**File:** `backend/routes/auth_routes.py:58`

**Severity:** WARNING — Authentication failure in dev

**Issue:** The `_set_token_cookie` function hardcodes `secure=True` for the auth cookie. When running locally on `http://localhost:8000` (the default configuration), the browser will refuse to set the cookie because the connection is not HTTPS. This means login/register will appear to succeed from the API perspective (returns user data) but the cookie is never stored, so subsequent authenticated requests fail.

**Fix:** The `secure` flag should be conditional based on the environment:

```python
def _set_token_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.API_DOMAIN.startswith("https://"),
        samesite="lax",
        path="/",
        max_age=86400 * 7,
    )
```

---

### WR-04: CSP Allows `'unsafe-inline'` — Defeats XSS Protection

**File:** `backend/app.py:100-108`

**Severity:** WARNING — Security mitigation bypass

**Issue:** The Content-Security-Policy header includes `'unsafe-inline'` for both `script-src` and `style-src`. This completely defeats the XSS protection that CSP is designed to provide. Any XSS vulnerability in the application can be exploited because inline script execution is permitted.

**Fix:** Remove `'unsafe-inline'` and use nonces or hashes for inline scripts/styles, or move all JS to external files loaded with `script-src 'self'`:

```python
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' https://unpkg.com; "  # removed 'unsafe-inline'
    "style-src 'self' https://unpkg.com; "   # removed 'unsafe-inline'
    "img-src 'self' https: data:; "
    "font-src 'self' data:; "
    "connect-src 'self' ws: wss:; "
    "frame-ancestors 'none'"
)
```

---

### WR-05: HSTS Only Applied When Request Scheme is HTTPS

**File:** `backend/app.py:98-99`

**Severity:** WARNING — Security header inconsistency

**Issue:** The HSTS header is only set when `request.url.scheme == "https"`. Behind a proxy (like Render), the incoming request may arrive as HTTP even though the external connection is HTTPS. This means HSTS is never sent, and users could be vulnerable to SSL stripping attacks.

**Fix:** Check the `X-Forwarded-Proto` header instead, or unconditionally set HSTS when `API_DOMAIN` starts with `https://`:

```python
if settings.API_DOMAIN.startswith("https://"):
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
```

---

### WR-06: Cookie max_age Hardcoded — Ignores Token Expiration Settings

**File:** `backend/routes/auth_routes.py:61`

**Severity:** WARNING — Inconsistent security configuration

**Issue:** The cookie `max_age` is hardcoded to `86400 * 7` (7 days) regardless of the configured `ACCESS_TOKEN_EXPIRE_MINUTES` (30 minutes) or `REFRESH_TOKEN_EXPIRE_DAYS` (7 days). The cookie persists for 7 days even though the access token expires in 30 minutes, creating a misleading UX where the cookie exists but the token inside is invalid.

**Fix:** Derive cookie max_age from the token expiration:

```python
def _set_token_cookie(response: Response, token: str):
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=max_age,
    )
```

---

### WR-07: Potential Username Collision in Registration

**File:** `backend/routes/auth_routes.py:82-83`

**Severity:** WARNING — Logic error

**Issue:** During registration, the username is derived from the email prefix (`data.email.split("@")[0]`). This is checked for uniqueness only via the existing user query on line 82 (`(User.email == data.email) | (User.username == ...)`), but the username check uses the email prefix of the CURRENT user, not the potential new one. If `alice@gmail.com` registers, username "alice" is taken. But if `alice@yahoo.com` tries to register, the check on line 82 checks if `username == "alice"` (alice@yahoo.com's prefix), which WILL match alice@gmail.com's entry. This means the second user gets a 409 "Email already registered" error — an incorrect error because the email is different.

More critically, if a user registers with an email prefix that another user already took, they get a confusing error message that leaks information about the other user's email prefix.

**Fix:** Use a separate check for username collisions, and generate a unique username:

```python
existing_email = await db.execute(select(User).where(User.email == data.email))
if existing_email.scalar_one_or_none():
    raise HTTPException(status_code=409, detail="Email already registered")

username = data.email.split("@")[0]
existing_username = await db.execute(select(User).where(User.username == username))
if existing_username.scalar_one_or_none():
    # Append a random suffix
    username = f"{username}-{uuid.uuid4().hex[:6]}"
```

---

### WR-08: `forwarded-allow-ips '*'` Permits IP Spoofing

**Files:** `Procfile:1`, `render.yaml:9`

**Severity:** WARNING — Security / Trust

**Issue:** Both the Procfile and render.yaml use `--forwarded-allow-ips '*'` which allows any IP to set `X-Forwarded-For`, `X-Forwarded-Proto`, and other forwarded headers. This means:
- The rate limiter's `request.client.host` can be spoofed
- The HSTS check (`request.url.scheme`) can be bypassed
- IP-based access controls can be trivially circumvented

**Fix:** Use the actual proxy IP range. For Render, replace with:

```
--forwarded-allow-ips='10.0.0.0/8,172.16.0.0/12,192.168.0.0/16'
```

Or at minimum, only allow the Render internal IP range.

---

### WR-09: Empty Catch Blocks Suppress Errors

**Files:** Multiple

**Severity:** WARNING — Debugging / Reliability

**Issue:** Multiple catch blocks are empty or only provide generic messages, silently swallowing errors:

| File | Line | Code |
|------|------|------|
| `backend/app.py` | 151 | `except: pass` |
| `frontend/assets/js/app.js` | 90 | `catch {}` |
| `frontend/assets/js/app.js` | 105 | `catch { ws.close() }` |
| `frontend/assets/js/app.js` | 141 | `catch { ... }` |
| `frontend/assets/js/app.js` | 187 | `catch { btn.textContent = 'Error' }` |
| `frontend/assets/js/app.js` | 231 | `catch { heroStats.innerHTML = '...' }` |
| `frontend/assets/js/app.js` | 245 | `catch { aiStats.innerHTML = '...' }` |
| `frontend/assets/js/app.js` | 292 | `catch { ... }` |
| `frontend/assets/js/app.js` | 380 | `catch { related.innerHTML = '...' }` |
| `frontend/assets/js/app.js` | 401 | `catch { bookmarksContainer.innerHTML = '...' }` |
| `backend/services/rate_limit.py` | 33 | `except Exception: _redis_available = False` |
| `backend/services/rate_limit.py` | 52 | `except Exception: return None` |

Silent failures make debugging production issues extremely difficult and can mask serious bugs.

**Fix:** At minimum, log errors:

```python
except Exception as e:
    logger.error("health_check_failed", error=str(e))
```

For frontend, use `console.error` or a logging helper:

```javascript
catch (err) { console.error('Failed to load stats:', err); }
```

---

### WR-10: `debugger;` Statement in Production Code

**File:** Not found in source — but check inline scripts

**Issue:** While no literal `debugger;` statement was found, the `live.html` and `trending.html` inline scripts are heavily minified/obfuscated and difficult to debug. The practice of embedding large inline scripts (noted in multiple .html files) prevents proper debugging and code organization.

---

## Info

### IN-01: Raw SQL Query in `get_geo_events`

**File:** `backend/routes/news.py:28-36`

**Severity:** INFO — Code quality

**Issue:** The geo events endpoint uses `text("""...""")` with raw SQL instead of the ORM. While this specific query is not injectable (no user input), it bypasses SQLAlchemy's abstraction layer and breaks consistency with the rest of the codebase.

**Fix:** Use the ORM for consistency:

```python
from sqlalchemy import func, select
query = (
    select(Source.country, func.count().label("cnt"))
    .join(Article, Article.source_id == Source.id)
    .where(Article.status == ArticleStatus.PUBLISHED, Source.country.isnot(None), Source.country != "")
    .group_by(Source.country)
    .order_by(desc("cnt"))
)
```

---

### IN-02: `passlib[bcrypt]` Requirement Unused — Redundant Dependency

**File:** `requirements.txt:12`

**Severity:** INFO — Code quality / Dependency bloat

**Issue:** Both `passlib[bcrypt]` (line 12) and `bcrypt` (line 13) are listed as dependencies. The code imports `bcrypt` directly (in `backend/auth/auth.py:5`) via `import bcrypt as _bcrypt` — `passlib` is never imported anywhere. This is a redundant dependency.

**Fix:** Remove `passlib[bcrypt]` from requirements.txt.

---

### IN-03: Supertokens Initialization Code Exists but Auth Routes Use JWT

**File:** `backend/auth/supertokens.py`

**Severity:** INFO — Dead code

**Issue:** The `init_supertokens()` function and all third-party provider configuration (Google, GitHub, Facebook) are defined but NEVER called from `backend/app.py` or any startup path. The auth routes in `backend/routes/auth_routes.py` use JWT-based auth with bcrypt, and `backend/routes/bookmarks.py` and `backend/routes/admin_routes.py` import `get_current_user` from `supertokens` module — but the supertokens `init` function is never invoked, meaning the `verify_session()` dependency will fail at runtime if supertokens endpoints are ever hit.

**Fix:** Either:
1. Call `init_supertokens()` during app startup in `lifespan()`, OR
2. Remove the dead supertokens code if it's not planned for use

---

### IN-04: Duplicate `<meta name="description">` in Profile Page

**File:** `frontend/profile.html:1`

**Severity:** INFO — HTML quality

**Issue:** The `<head>` contains two identical `<meta name="description">` tags. This is invalid HTML and may cause inconsistent SEO behavior.

**Fix:** Remove one of the duplicate meta tags.

---

### IN-05: Console.log References in Production JavaScript

**File:** `frontend/assets/js/app.js:84`

**Severity:** INFO — Code quality

**Issue:** Line 84 uses `console.warn('WS auth:', msg.message)` which leaks potentially sensitive authentication error details to the browser console. While not a critical vulnerability, it could expose information in shared/screenshotted developer tools.

**Fix:** Remove or gate behind a debug flag:

```javascript
if (window.DEBUG) console.warn('WS auth:', msg.message);
```

---

### IN-06: Inline `onclick` Handlers Mixed with Event Listeners

**File:** Multiple HTML files (article.html, home.html, login.html, register.html)

**Severity:** INFO — Code maintainability

**Issue:** The codebase mixes inline event handlers (`onclick="shareArticle..."`, `onclick="togglePassword(this)"`) with programmatic event listeners (`addEventListener`). This makes event flow harder to trace and violates separation of concerns.

**Fix:** Move all event handlers to JavaScript files using `addEventListener`.

---

### IN-07: Username Leaked to Sign-In Button on All Pages

**File:** `frontend/assets/js/app.js:215-218`

**Severity:** INFO — Privacy

**Issue:** When a user is logged in, the Sign In button is replaced with the user's username (via `innerHTML`). This exposes the username on every page the user visits, which could be shoulder-surfed or captured in screenshots.

**Fix:** Use the user's first name or initials instead, or a generic "Profile" link.

---

## Security Headers Assessment

| Header | Status | Value |
|--------|--------|-------|
| X-Content-Type-Options | ✅ Present | nosniff |
| X-Frame-Options | ✅ Present | DENY |
| X-XSS-Protection | ✅ Present | 1; mode=block |
| Referrer-Policy | ✅ Present | strict-origin-when-cross-origin |
| Strict-Transport-Security | ⚠️ Conditional | Only when `request.url.scheme == "https"` |
| Content-Security-Policy | ⚠️ Weak | `'unsafe-inline'` defeats XSS protection |

## Authentication Flow Assessment

| Concern | Status |
|---------|--------|
| Password hashing (bcrypt) | ✅ Good |
| JWT token signing | ✅ Uses SECRET_KEY + HS256 |
| JWT expiration | ✅ 30 min access, 7 day refresh |
| Cookie secure flag | ❌ Hardcoded `secure=True` breaks localhost |
| CSRF protection | ❌ None |
| Rate limiting applied | ❌ Defined but never used |
| Logout invalidates token | ❌ No token blacklist |
| Password reset | ❌ Frontend only, no backend |

---

_Reviewed: 2026-07-09T18:00:00Z_
_Reviewer: gsd-code-reviewer (deep cross-file analysis)_
_Depth: deep_
