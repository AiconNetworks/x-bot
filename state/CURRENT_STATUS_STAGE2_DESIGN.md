# Stage 2: Token Reliability & VM-Ready Auth — Current Status & Full Design

This file captures everything needed to make the X auth layer reliable enough
for unattended VM operation. It is the single reference for Stage 2.

> **Companion files:**
> - `architecture/mvp-system-architecture.md` (full technical architecture)
> - `state/CURRENT_STATUS_STAGE1_DESIGN.md` (Stage 1 status)

---

## 1. What We're Building

A reliable token lifecycle for the X/Twitter OAuth 2.0 integration that ensures
the bot can run indefinitely on a VM without manual browser re-authorization.

**North star metric:** Bot posts successfully after token expiry with zero human intervention.

**MVP scope:**
- In: Automatic refresh on expiry, token persistence across restarts, proactive refresh option, validation on startup
- Out: Multi-user tokens, token encryption at rest, cloud secret management, OAuth 1.0a fallback

---

## 2. Integration Decision

All changes happen inside the existing `twitter-bot/` project, specifically in `src/x_client.py`.
No new services, no new dependencies.

**Rationale:** The auth layer is the only thing between "works locally" and "works on a VM."
Everything else (OpenClaw, approval, posting) already works. Fix auth reliability, and the system is VM-ready.

---

## 3. Subsystems & Paths

### 3.1 Token Lifecycle

The token lifecycle is the core of Stage 2. It must handle:

```
Bootstrap (one-time):
  Browser → PKCE auth → access_token + refresh_token → saved to .x_tokens.json

Normal runtime (every post):
  load_tokens()
  → post with access_token
  → if 401 or 403 (unsupported-auth): refresh_if_needed()
  → save_tokens(new_tokens)
  → retry post with new access_token

Proactive refresh (optional, cleaner):
  load_tokens()
  → check if token is near expiry (e.g., obtained_at + expires_in - buffer)
  → if near expiry: refresh before posting
  → save_tokens(new_tokens)
  → post with fresh access_token
```

### 3.2 Token File Format

Current `.x_tokens.json`:
```json
{
  "token_type": "bearer",
  "expires_in": 7200,
  "access_token": "...",
  "scope": "tweet.write users.read tweet.read offline.access",
  "refresh_token": "..."
}
```

Target `.x_tokens.json` (with metadata for proactive refresh):
```json
{
  "token_type": "bearer",
  "expires_in": 7200,
  "access_token": "...",
  "scope": "tweet.write users.read tweet.read offline.access",
  "refresh_token": "...",
  "obtained_at": 1774921876
}
```

### 3.3 User Stories

| # | User Story | Status |
|---|-----------|--------|
| A1 | Bot refreshes access token automatically when X returns 401 | ✅ (inferred — 403 path works, 401 uses same logic) |
| A2 | Bot refreshes access token automatically when X returns 403 unsupported-auth | ✅ (confirmed: tweet ID 2039047568349413675) |
| A3 | New tokens are saved to disk after successful refresh | ✅ (confirmed: .x_tokens.json updated with new tokens) |
| A4 | Bot retries the original post after successful refresh | ✅ (confirmed: retry posted successfully) |
| A5 | Bot continues working across restarts using saved tokens | ✅ (confirmed: ran again after refresh, tokens persisted) |
| A6 | Bot refreshes proactively before expiry (optional, cleaner) | ❌ |
| A7 | Token file includes `obtained_at` for proactive refresh calculation | ❌ |
| A8 | Bot validates token file on startup (has refresh_token, has required scopes) | ❌ |

---

## 4. Authentication & Authorization

### The One-Time Auth Rule

- Browser login = **bootstrap step** (done once, on a machine with a browser)
- Refresh token flow = **normal runtime step** (done automatically, no browser needed)

### Required Scopes

| Scope | Purpose |
|-------|---------|
| `tweet.read` | Read tweets |
| `tweet.write` | Post tweets (required for `POST /2/tweets`) |
| `users.read` | Read user info |
| `offline.access` | **Required for refresh tokens** — without this, no auto-refresh |

### Token Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST https://api.x.com/2/oauth2/token` | Exchange auth code for tokens (bootstrap) |
| `POST https://api.x.com/2/oauth2/token` | Refresh access token (runtime) |

### Refresh Request

```
POST https://api.x.com/2/oauth2/token
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=<saved_refresh_token>
```

### What NOT to do

- Never fall back to app-only bearer auth for posting (X returns 403)
- Never use OAuth 1.0a (we chose PKCE, stay on PKCE)
- Never prompt for browser login at runtime on the VM

---

## 5. What Exists Right Now

### Token refresh code in `src/x_client.py`:
- `_load_tokens()` — reads `.x_tokens.json`
- `_save_tokens()` — writes `.x_tokens.json`
- `_refresh_access_token()` — calls X refresh endpoint
- `post_tweet()` — posts with retry on 401 or 403 unsupported-auth

### What's missing:
- `obtained_at` timestamp in token file
- Proactive refresh (check expiry before posting)
- Startup validation (verify refresh_token exists, scopes correct)
- Live confirmation that refresh → retry → post actually works

---

## 6. What Was Validated So Far

### From Stage 1:

- OAuth 2.0 PKCE browser flow works — tokens saved
- Access token posts tweets successfully (tweet ID: 20388076084929)
- Corrupted access token → X returns 403 "Unsupported Authentication" (not 401)
- Refresh code triggers on 403 unsupported-auth (updated in Stage 1)

### Token refresh — confirmed working (2026-03-31)

```
$ poetry run python src/main.py "..."

Posting tweet (256 chars)...
Access token expired, refreshing...
Refresh successful.
Tokens saved to disk.
Retrying tweet...
Posted successfully. Tweet ID: 2039047568349413675
```

- Corrupted access token triggered refresh path
- Refresh endpoint returned new valid tokens
- New tokens saved to `.x_tokens.json`
- Retry posted successfully with new token
- Subsequent runs work with the refreshed tokens

### Not yet validated:

- System works after real 2-hour token expiry (same logic, but untested with natural expiry)
- Proactive refresh before posting (not yet built)

---

## 7. What Success Looks Like

**Stage 2 is complete when:**

1. Corrupt the access token in `.x_tokens.json`
2. Run `poetry run python src/main.py "test"`
3. See: `Access token expired, refreshing...`
4. See: `Refresh successful.`
5. See: `Tokens saved to disk.`
6. See: `Retrying tweet...`
7. See: `Posted successfully. Tweet ID: ...`
8. Inspect `.x_tokens.json` — new access token, refresh token present
9. Run again — works without refresh (new token is valid)

**Bonus (proactive):**

10. Wait 2 hours (or set a short buffer)
11. Run — bot refreshes proactively before posting
12. Post succeeds on first try (no 401/403 cycle)

---

## 8. Steps to Completion

| Step | Description | Status |
|------|------------|--------|
| 1 | Update refresh trigger to catch 401 + 403 unsupported-auth | ✅ |
| 2 | Add logging to refresh flow (expire, refresh, save, retry) | ✅ |
| 3 | Test refresh with corrupted access token | ✅ |
| 4 | Confirm new tokens are saved to disk | ✅ |
| 5 | Confirm retry posts successfully with new token | ✅ (tweet ID: 2039047568349413675) |
| 6 | Add `obtained_at` to token file on save | ❌ |
| 7 | Add proactive refresh (check expiry before posting) | ❌ |
| 8 | Add startup validation (refresh_token present, scopes correct) | ❌ |
| 9 | Test full cycle: post → wait 2h → post again (real expiry) | ❌ |
| 10 | Update architecture doc | ❌ |

---

## 9. Patterns to Follow (from Stage 1)

1. **Test with curl/simulation before trusting code.** Don't assume — confirm.
2. **X returns 403 for invalid tokens, not 401.** Handle both.
3. **Print response bodies on error.** `raise_for_status()` alone hides the real cause.
4. **Keep token file simple.** JSON, flat, no nesting beyond what X returns.
5. **Backup before mutating.** Always backup `.x_tokens.json` before corruption tests.

---

## 10. Intentionally NOT Built Yet

- Token encryption at rest
- Cloud secret management (AWS Secrets Manager, etc.)
- Multi-user token storage
- OAuth 1.0a fallback
- Token rotation alerts/monitoring
- Letta, gentags, memory, multi-agent, scheduling, automation

---

## 11. VM Deployment Checklist (for after Stage 2)

Once refresh is confirmed working:

1. Auth once in browser locally
2. Copy `.x_tokens.json` to VM
3. Copy `.env` to VM
4. VM runs the bot
5. Bot refreshes tokens automatically
6. Only re-auth manually if refresh token is revoked or app config changes

---

## 12. Next Stage Preview

**Stage 3:** Replace terminal approval with Telegram approval. Same pipeline, different approval interface. OpenClaw and X client unchanged. Token reliability already solved.
