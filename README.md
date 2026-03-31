# Aicon Twitter Bot (MVP)

Minimal end-to-end pipeline that generates tweet options from research text and posts an approved tweet to X.

This is the first working backbone of **Aicon**, validating the loop:

**text → options → human approval → post**

The system uses:

- OpenClaw for generation
- X API for posting
- local terminal approval for control

No memory layer yet. No automation yet.

---

# Goal

Prove the core interaction loop before building reasoning or memory systems.

Workflow:

1. provide source text (research idea, paragraph, note)
2. generate 3 tweet candidates
3. choose one manually
4. post the approved tweet to X

---

# Architecture

```
You
 │
 │ source text
 ▼
main.py (coordinator)
 │
 ├── openclaw_client.py
 │      POST /v1/responses
 │      → generates 3 tweet options
 │
 ├── approval.py
 │      terminal selection
 │
 └── x_client.py
        POST /2/tweets
```

Responsibilities:

| component      | role                    |
| -------------- | ----------------------- |
| OpenClaw       | generates tweet options |
| approval layer | human decision          |
| X client       | posts tweet             |
| coordinator    | connects everything     |

---

# Example run

```
poetry run python src/main.py "Gentags are discrete semantic attributes that improve consistency in constraint-sensitive decisions."
```

Output:

```
--- Tweet Options ---

1.
Gentags are discrete semantic attributes that improve consistency when decisions are constraint-sensitive.

2.
Gentags = discrete semantic attributes that boost consistency when decisions must satisfy constraints.

3.
Need consistency in constraint-sensitive decisions? Use gentags.

Choose an option:
```

After selecting:

```
Posting tweet...
Success.
```

---

# Installation

## 1. clone project

```
git clone <repo>
cd twitter-bot
```

## 2. install dependencies

```
poetry install
```

## 3. install and run OpenClaw

follow onboarding:

```
openclaw onboard --install-daemon
openclaw dashboard
```

confirm gateway running locally:

```
http://127.0.0.1:18789
```

---

# Configure OpenClaw HTTP endpoint

Edit:

```
~/.openclaw/openclaw.json
```

enable:

```
gateway.http.endpoints.responses.enabled = true
```

restart gateway:

```
openclaw restart
```

---

# Configure X OAuth 2.0

create an app in the X developer portal.

set:

App type:

```
Web App, Automated App or Bot
```

Callback URI:

```
http://127.0.0.1:3000/callback
```

Scopes required:

```
tweet.read
tweet.write
users.read
offline.access
```

---

# run one-time authentication

```
poetry run python src/x_oauth_setup.py
```

This will:

- open browser
- request permission
- save tokens to:

```
.x_tokens.json
```

---

# Environment variables

create `.env`:

```
OPENCLAW_URL=http://127.0.0.1:18789
OPENCLAW_TOKEN=...

X_CLIENT_ID=...
X_CLIENT_SECRET=...
```

`.x_tokens.json` is generated automatically.

---

# Running the bot

```
poetry run python src/main.py "text you want to tweet about"
```

---

# Project structure

```
twitter-bot/

src/
  main.py
  openclaw_client.py
  x_client.py
  x_oauth_setup.py
  approval.py
  config.py

.env
.x_tokens.json
pyproject.toml
```

---

# What this project intentionally does NOT include

no automation
no scheduling
no database
no memory layer
no gentags yet
no multi-agent logic
no browser automation

this is intentional.

the goal is to validate the publishing loop first.

---

# Future steps

planned evolution of the system:

1. improved prompt control for tweet style
2. telegram approval interface
3. source ingestion from notes/papers
4. gentag semantic state layer
5. reasoning layer (Aicon)
6. automation controls
7. VM deployment

---

# Cost considerations

X API currently charges per post (approx $0.01 per tweet depending on plan).

Because tweets require manual approval, cost is controlled.

---
