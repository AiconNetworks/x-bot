# Aicon MVP System Architecture

## Goal

Prove this flow end-to-end:

1. Give the system source text
2. Get 3 tweet options from OpenClaw
3. Choose one manually via terminal
4. Post the approved one to X

No Letta. No gentags. No memory system. No multi-agent logic. No scheduling. No automation.

---

## System Diagram

```
You
 │
 │ source text
 ▼
Coordinator (main.py)
 │
 ├──> OpenClaw (openclaw_client.py)
 │      └── POST /v1/responses → generates 3 tweet options
 │
 ├──> Approval Layer (approval.py)
 │      └── terminal prompt: choose 1 / 2 / 3 / cancel
 │
 └──> X Client (x_client.py)
        └── POST /2/tweets → posts approved tweet to X
```

---

## Components

### 1. Coordinator — `src/main.py`

Main entrypoint. Orchestrates the full flow:

- Reads source text from CLI args or stdin
- Calls OpenClaw for tweet options
- Presents options for approval
- Posts the selected tweet to X

No business logic lives here. It just wires the other components together.

### 2. OpenClaw Client — `src/openclaw_client.py`

Calls OpenClaw's HTTP OpenResponses endpoint.

**Interface:**
```python
generate_tweet_options(source_text: str) -> list[str]
```

**Connection details:**
- Endpoint: `POST http://127.0.0.1:18789/v1/responses`
- Auth: `Authorization: Bearer <OPENCLAW_TOKEN>`
- Headers: `x-openclaw-agent-id: main`
- Model: `"openclaw"`
- OpenClaw Gateway runs locally as a LaunchAgent on port 18789 (loopback only)
- The HTTP responses endpoint must be enabled in OpenClaw config: `gateway.http.endpoints.responses.enabled: true`

**Response format (confirmed via curl test):**
```json
{
  "id": "resp_...",
  "object": "response",
  "status": "completed",
  "model": "openclaw",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "1) tweet one\n\n2) tweet two\n\n3) tweet three"
        }
      ],
      "status": "completed"
    }
  ],
  "usage": {
    "input_tokens": ...,
    "output_tokens": ...,
    "total_tokens": ...
  }
}
```

Text extraction path: `data["output"][0]["content"][0]["text"]`

Parser handles both JSON arrays and numbered lines (`1) ...` / `1. ...`).

### 3. Approval Layer — `src/approval.py`

Simple terminal-based approval.

**Interface:**
```python
choose_tweet_option(options: list[str]) -> int | None
```

Displays numbered options, returns selected index (0-based) or `None` on cancel.

### 4. X Client — `src/x_client.py`

Posts tweets to X using OAuth 2.0 with PKCE and the Twitter v2 API.

**Interface:**
```python
post_tweet(text: str) -> dict
```

**Connection details:**
- Endpoint: `POST https://api.x.com/2/tweets`
- Auth: OAuth 2.0 Authorization Code with PKCE (user-context)
- Token is loaded from `.x_tokens.json` (created by the one-time setup script)
- Automatic token refresh using refresh token on 401

**Auth flow (one-time setup via `src/x_oauth_setup.py`):**
1. Opens X's authorize URL in browser with PKCE challenge
2. User logs in and approves the app
3. X redirects to `http://127.0.0.1:3000/callback` with authorization code
4. Script exchanges code for access token + refresh token
5. Tokens saved to `.x_tokens.json`

**Scopes:**
- `tweet.read`
- `tweet.write`
- `users.read`
- `offline.access` (for refresh tokens)

### 5. OAuth Setup — `src/x_oauth_setup.py`

One-time script to authorize the app with X.

Run once before first use:
```
poetry run python src/x_oauth_setup.py
```

Starts a local HTTP server on port 3000, opens the browser, receives the callback, exchanges the code, and saves tokens.

### 6. Config — `src/config.py`

Loads environment variables from `.env` via `python-dotenv`.

**Required env vars:**
```
X_CLIENT_ID        — Twitter OAuth 2.0 Client ID
X_CLIENT_SECRET    — Twitter OAuth 2.0 Client Secret
OPENCLAW_TOKEN     — OpenClaw Gateway auth token
```

**Optional:**
```
OPENCLAW_URL       — defaults to http://127.0.0.1:18789
```

---

## File Structure

```
twitter-bot/
  pyproject.toml          — Poetry project config
  .env                    — API keys and tokens (gitignored)
  .x_tokens.json          — OAuth 2.0 user tokens (gitignored, created by setup)
  .gitignore
  architecture/
    mvp-system-architecture.md  — this file
  src/
    main.py               — coordinator / entrypoint
    config.py             — env var loader
    openclaw_client.py    — OpenClaw HTTP client
    approval.py           — terminal approval UX
    x_client.py           — X/Twitter posting client (OAuth 2.0)
    x_oauth_setup.py      — one-time OAuth 2.0 PKCE authorization
```

---

## Dependencies

```
python = "^3.11"
python-dotenv = "^1.0.1"
requests = "^2.32.3"
```

Dev:
```
pytest = "^8.3.2"
ruff = "^0.6.9"
```

---

## OpenClaw Configuration

OpenClaw runs as a local LaunchAgent gateway. Relevant config in `~/.openclaw/openclaw.json`:

- Gateway port: `18789`
- Bind: `loopback` (127.0.0.1 only)
- Auth: token-based (`gateway.auth.mode: "token"`)
- HTTP responses endpoint: enabled (`gateway.http.endpoints.responses.enabled: true`)
- Default model: `openai-codex/gpt-5.2`
- Agent workspace: `~/.openclaw/workspace`

The gateway was restarted after enabling the HTTP endpoint. Confirmed working via curl on 2026-03-30.

---

## X/Twitter Configuration

- Auth method: OAuth 2.0 Authorization Code with PKCE
- Client ID and Client Secret stored in `.env`
- User access token and refresh token stored in `.x_tokens.json` after one-time setup
- Callback URL: `http://127.0.0.1:3000/callback` (must be registered in X Developer Portal)
- Token auto-refreshes on 401 using the refresh token

---

## Runtime Flow

### First time only:
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

### Every run:
```
Step 1:  poetry run python src/main.py "your source text"
Step 2:  main.py reads source text from args (or stdin)
Step 3:  openclaw_client.py → POST /v1/responses → returns 3 tweet candidates
Step 4:  approval.py prints options 1/2/3/0(cancel)
Step 5:  user selects one
Step 6:  x_client.py → POST /2/tweets with Bearer token → posts selected tweet
Step 7:  prints success or failure
```

---

## Responsibility Boundaries

| Component | Owns | Does NOT own |
|---|---|---|
| OpenClaw | Tweet generation, instruction following | Approval state, posting credentials, memory |
| Approval layer | Human confirmation | Generation, posting |
| X Client | Twitter API call, token management | Content decisions |
| X OAuth Setup | One-time authorization flow | Runtime posting |
| Coordinator | Workflow order, data passing | Business logic |

---

## Confirmed Working

- OpenClaw Gateway running on 127.0.0.1:18789
- HTTP responses endpoint enabled and tested via curl
- Response parsed successfully (numbered tweet format)
- All Python source files written and wired together
- OAuth 2.0 PKCE flow implemented with auto-refresh

## Not Yet Tested

- OAuth 2.0 PKCE authorization flow against live X
- Full end-to-end run (source text → tweet posted)
- Token refresh on expiry

---

## Intentionally NOT Built Yet

- Letta
- Gentags / gentag memory blocks
- Multi-agent coordination
- Browser automation
- Scheduling / automation loops
- Database
- Web dashboard
- Autonomous posting
- Cloud deployment

---

## Future Evolution Path

1. **Now:** OpenClaw + terminal approval + X posting (OAuth 2.0 PKCE)
2. **Next:** OpenClaw + Telegram approval + X posting
3. **Later:** Aicon reasoning layer + gentags + OpenClaw execution
4. **Final:** Full autonomous Aicon with memory, reasoning, and multi-channel output
