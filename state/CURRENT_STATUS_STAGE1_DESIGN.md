# Stage 1: MVP Tweet Pipeline — Current Status & Full Design

This file captures everything built, decided, and validated in Stage 1.
It is the single reference going forward.

> **Companion files:** `architecture/mvp-system-architecture.md` (full technical architecture)

---

## 1. What We're Building

A local command-line pipeline that takes source text, sends it to OpenClaw to generate 3 tweet candidates, presents them for manual approval in the terminal, and posts the selected tweet to X/Twitter via the v2 API.

**North star metric:** Can we go from source text to a live tweet on X in one command?

**MVP scope:**
- In: OpenClaw generation, terminal approval, X posting, OAuth 2.0 PKCE auth
- Out: Letta, gentags, memory, multi-agent, scheduling, automation, database, web UI, cloud deploy

---

## 2. Integration Decision

Everything lives in a single local Python project (`twitter-bot/`). No separate services, no containers, no cloud infra.

**Rationale:** The goal is to validate the core flow (generate → approve → post) with the fewest moving parts. OpenClaw already runs locally as a LaunchAgent. X API is called directly via HTTP. There is nothing to deploy.

---

## 3. Subsystems & Paths

### 3.1 OpenClaw Generation

OpenClaw Gateway runs locally on `127.0.0.1:18789`. The HTTP OpenResponses endpoint (`POST /v1/responses`) was enabled in config and confirmed working via curl.

**Flow:** Source text → prompt construction → POST /v1/responses → parse numbered tweet options

### 3.2 Terminal Approval

Simple numbered menu in the terminal. User picks 1/2/3 or 0 to cancel.

### 3.3 X Posting (OAuth 2.0 PKCE)

One-time browser-based authorization stores tokens in `.x_tokens.json`. Runtime loads tokens, posts via `POST https://api.x.com/2/tweets`, auto-refreshes on 401.

### 3.4 User Stories

| # | User Story | Status |
|---|-----------|--------|
| A1 | User provides source text via CLI arg or stdin | ✅ |
| A2 | System sends source text to OpenClaw and receives 3 tweet options | ✅ |
| A3 | System displays tweet options in terminal with numbered choices | ✅ |
| A4 | User selects a tweet or cancels | ✅ |
| A5 | System posts selected tweet to X via OAuth 2.0 | ✅ (confirmed, tweet ID: 20388076084929) |
| A6 | System prints success with tweet ID | ✅ |
| A7 | One-time OAuth 2.0 PKCE setup via browser | ✅ (tokens saved successfully) |
| A8 | Token auto-refresh on expiry | ✅ (confirmed: refresh → save → retry → tweet ID: 2039047568349413675) |

---

## 4. Authentication & Authorization

### OpenClaw
- Token-based auth via `Authorization: Bearer <token>`
- Token stored in `.env` as `OPENCLAW_TOKEN`
- Gateway config: `gateway.auth.mode: "token"`

### X/Twitter
- OAuth 2.0 Authorization Code with PKCE (user-context)
- Client ID + Client Secret in `.env`
- User access token + refresh token in `.x_tokens.json`
- Scopes: `tweet.read`, `tweet.write`, `users.read`, `offline.access`
- Callback URL: `http://127.0.0.1:3000/callback`

**Not being built:** No app-only bearer token auth. No OAuth 1.0a. No multi-user support.

---

## 5. What Exists Right Now

### Project files:
```
twitter-bot/
├── pyproject.toml                — Poetry config (python 3.11+, requests, python-dotenv)
├── .env                          — API keys and tokens (gitignored)
├── .x_tokens.json                — OAuth 2.0 user tokens (gitignored, created by setup)
├── .gitignore                    — excludes .env, .x_tokens.json, __pycache__, .venv
├── architecture/
│   └── mvp-system-architecture.md  — full technical architecture doc
├── state/
│   └── CURRENT_STATUS_STAGE1_DESIGN.md  — this file
└── src/
    ├── main.py                   — coordinator / entrypoint
    ├── config.py                 — env var loader (X_CLIENT_ID, X_CLIENT_SECRET, OPENCLAW_*)
    ├── openclaw_client.py        — OpenClaw HTTP client (POST /v1/responses)
    ├── approval.py               — terminal approval UX (choose 1/2/3/cancel)
    ├── x_client.py               — X posting client (OAuth 2.0 Bearer token)
    └── x_oauth_setup.py          — one-time PKCE authorization flow
```

### External dependencies:
- OpenClaw Gateway: running locally on `127.0.0.1:18789`, HTTP responses endpoint enabled
- X Developer App: OAuth 2.0 Client ID and Secret configured, callback URL registered

---

## 6. What Was Validated

### OpenClaw HTTP endpoint — confirmed working (2026-03-30)

```
$ curl -sS http://127.0.0.1:18789/v1/responses \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "x-openclaw-agent-id: main" \
  -d '{"model": "openclaw", "input": "Generate 3 short tweet options about gentags."}'

→ 200 OK, returned 3 tweet options in numbered format
```

### OAuth 2.0 PKCE setup — confirmed working (2026-03-30)

```
$ poetry run python src/x_oauth_setup.py
Opening browser for X authorization...

Waiting for callback on http://127.0.0.1:3000/callback ...
Authorization code received. Exchanging for tokens...
Tokens saved to /Users/infa/Documents/Personal/Aicons/twitter-bot/.x_tokens.json
Access token: SUh4X2V0MnNsWWVDaF9L...
Refresh token saved.

Done. You can now run the main app.
```

### End-to-end tweet posting — confirmed working (2026-03-30)

```
$ poetry run python src/main.py "post a thing about AI agents and reasoning..."

Source text received (109 chars).
Generating tweet options...

--- Tweet Options ---

  1. AI agents are getting more capable, but the real blocker is reliability...
  2. Hot take: the next big AI breakthrough isn't more reasoning...
  3. AI agents can "reason" all day...

Choose an option: 1

Posting tweet (203 chars)...
Posted successfully. Tweet ID: 20388076084929
```

### Token refresh path — partially validated (2026-03-30)

- Corrupted access token caused X to return 403 "Unsupported Authentication" (not 401)
- X treats invalid tokens as app-only auth attempts, returning 403 instead of 401
- Updated `x_client.py` to trigger refresh on both 401 and 403 with `unsupported-authentication`
- Refresh logic written but not yet confirmed end-to-end with a successful retry

---

## 7. What Success Looks Like

**Stage 1 is complete when:**

1. You run `poetry run python src/main.py "some source text"`
2. OpenClaw returns 3 tweet options
3. You pick one in the terminal
4. It posts to X and you see the tweet live
5. The script prints the tweet ID

That's it. One command, one tweet, confirmed on X.

---

## 8. Steps to Completion

| Step | Description | Status |
|------|------------|--------|
| 1 | Project scaffolding (pyproject, .env, .gitignore, file structure) | ✅ |
| 2 | Config loader (config.py) | ✅ |
| 3 | OpenClaw client (openclaw_client.py) | ✅ |
| 4 | Enable OpenClaw HTTP responses endpoint | ✅ |
| 5 | Curl test OpenClaw endpoint | ✅ |
| 6 | Terminal approval UX (approval.py) | ✅ |
| 7 | X OAuth 2.0 PKCE setup script (x_oauth_setup.py) | ✅ |
| 8 | Run PKCE setup, save tokens | ✅ |
| 9 | X posting client (x_client.py) with OAuth 2.0 | ✅ (code written) |
| 10 | Coordinator (main.py) | ✅ |
| 11 | End-to-end test: source text → live tweet on X | ✅ (tweet ID: 20388076084929) |
| 12 | Confirm token refresh works on expiry | ✅ (tweet ID: 2039047568349413675) |

---

## 9. What Worked — Patterns to Follow

1. **HTTP over WebSocket for MVP.** OpenClaw supports both, but HTTP is simpler and debuggable with curl. Use the simplest protocol that works.
2. **Enable, don't modify.** OpenClaw's HTTP endpoint was disabled by default. We enabled it via config rather than hacking internals.
3. **Curl before code.** Testing the endpoint with curl before writing the Python client confirmed the response shape and avoided guesswork.
4. **OAuth 2.0 PKCE with local callback.** One-time browser auth, tokens saved locally, auto-refresh on 401. No complex token management needed.
5. **Flexible parser.** The OpenClaw response parser handles both JSON arrays and numbered lines, since the model's output format isn't guaranteed.
6. **Thin coordinator.** `main.py` has zero business logic — it just calls components in order. Each component has one job and one interface.

---

## 10. Intentionally NOT Built Yet

- Letta
- Gentags / gentag memory blocks
- Multi-agent coordination
- Browser automation
- Scheduling / automation loops
- Database
- Web dashboard
- Autonomous posting
- Cloud deployment
- Telegram/Slack approval (replaces terminal later)

---

## 11. Next Stage Preview

**Stage 2:** Replace terminal approval with Telegram approval. Same pipeline, different approval interface. OpenClaw and X client unchanged.
