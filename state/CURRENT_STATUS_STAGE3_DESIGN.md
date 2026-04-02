# Stage 3: Telegram Approval — Current Status & Full Design

This file captures everything needed to replace terminal approval with Telegram-based
approval, making the bot usable from a phone while it runs unattended on the VM.

> **Companion files:**
> - `architecture/mvp-system-architecture.md` (full technical architecture)
> - `state/CURRENT_STATUS_STAGE2_DESIGN.md` (Stage 2 status)

---

## 1. What We're Building

A Telegram-based approval interface that replaces the terminal prompt. The bot sends
tweet options to a Telegram chat, the user replies with their choice, and the bot posts
the selected tweet to X.

**North star metric:** Approve and post a tweet from your phone while the bot runs on the VM.

**MVP scope:**
- In: Telegram bot sends options, receives choice, triggers X post
- Out: Inline keyboards, multi-user support, conversation threads, scheduling, autonomous mode

---

## 2. Integration Decision

Replace `approval.py` (terminal) with `telegram_approval.py` (Telegram). The coordinator
(`main.py`) switches which approval function it calls. Everything else stays the same —
OpenClaw generates tweets, X client posts them.

**Rationale:** The terminal is the only thing tying the bot to a local session. Replace it
with Telegram and the bot can run headless on a VM while you approve from anywhere.

---

## 3. How It Works

### Current flow (terminal):
```
source text → OpenClaw → terminal prompt (1/2/3/cancel) → X post
```

### New flow (Telegram):
```
source text → OpenClaw → Telegram message (options) → wait for reply (1/2/3/cancel) → X post
```

### Sequence:
```
1. main.py receives source text (CLI arg, stdin, or future trigger)
2. openclaw_client.py generates 3 tweet options
3. telegram_approval.py sends options to your Telegram chat
4. You reply 1, 2, 3, or 0 (cancel) from your phone
5. telegram_approval.py returns your choice
6. x_client.py posts the selected tweet
7. telegram_approval.py confirms success (or error) back to you
```

---

## 4. Telegram Bot Setup

### What exists:
- Telegram bot token: already in OpenClaw config (`8196742012:AAH...`)
- Bot was created via @BotFather

### What's needed:
- Your Telegram chat ID (so the bot knows where to send messages)
- The bot token in `.env`

### Getting your chat ID:
```
1. Message your bot on Telegram (any message)
2. Call: curl https://api.telegram.org/bot<TOKEN>/getUpdates
3. Find your chat ID in the response: result[0].message.chat.id
```

### Env vars to add to `.env`:
```
TELEGRAM_BOT_TOKEN=8196742012:AAH...
TELEGRAM_CHAT_ID=<your_chat_id>
```

---

## 5. Components

### 5.1 Telegram Approval — `src/telegram_approval.py` (new)

Replaces `approval.py` for Telegram-based approval.

**Interface:**
```python
def choose_tweet_option_telegram(options: list[str]) -> int | None
```

Same signature as `choose_tweet_option()` in `approval.py`. Returns selected index
(0-based) or `None` on cancel.

**Behavior:**
1. Send a message to your chat with numbered tweet options
2. Poll for your reply using `getUpdates` with a timeout
3. Parse the reply (1/2/3 → index, 0 → cancel)
4. Return the selection

**Telegram API calls:**
| Method | Purpose |
|--------|---------|
| `POST /bot<token>/sendMessage` | Send tweet options to your chat |
| `POST /bot<token>/getUpdates` | Long-poll for your reply |

**No webhook needed.** Polling (`getUpdates`) is simpler and doesn't require a public
URL or SSL cert. The bot calls `getUpdates` with `timeout=120` (long poll) and waits
for your reply. Good enough for MVP.

### 5.2 Coordinator update — `src/main.py`

Swap the approval import:
```python
# Before:
from approval import choose_tweet_option

# After:
from telegram_approval import choose_tweet_option_telegram as choose_tweet_option
```

Or use an env var / CLI flag to switch between terminal and Telegram mode, keeping
both available.

### 5.3 Config update — `src/config.py`

Add:
```python
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
```

### 5.4 Confirmation message (nice-to-have)

After posting to X, send a confirmation back to Telegram:
```
Posted! Tweet ID: 2039142826626171031
```

This closes the loop — you know it worked without checking X.

---

## 6. User Stories

| # | User Story | Status |
|---|-----------|--------|
| T1 | Bot sends tweet options to my Telegram chat | ❌ |
| T2 | I reply 1/2/3 and the bot posts the selected tweet | ❌ |
| T3 | I reply 0 and the bot cancels without posting | ❌ |
| T4 | Bot confirms success (or error) back to Telegram | ❌ |
| T5 | Bot ignores messages from other users (chat ID check) | ❌ |
| T6 | Bot times out gracefully if no reply within N minutes | ❌ |
| T7 | Terminal approval still works as fallback (CLI flag or env var) | ❌ |

---

## 7. Dependencies

New dependency:
```
# None — using requests directly against Telegram Bot API
# No python-telegram-bot library needed for MVP
```

The `requests` library (already installed) is enough. Telegram Bot API is simple
HTTP — `sendMessage` and `getUpdates` are just POST requests.

---

## 8. Security Considerations

- **Chat ID lock:** Only respond to messages from your chat ID. Ignore everything else.
- **Bot token in `.env`:** Same pattern as X credentials. Gitignored.
- **No webhook:** No public endpoint exposed. Polling only.
- **No stored messages:** Don't persist Telegram messages. Approval is ephemeral.

---

## 9. Steps to Completion

| Step | Description | Status |
|------|------------|--------|
| 1 | Get your Telegram chat ID | ❌ |
| 2 | Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to `.env` | ❌ |
| 3 | Add Telegram config to `src/config.py` | ❌ |
| 4 | Build `src/telegram_approval.py` (sendMessage + getUpdates polling) | ❌ |
| 5 | Test: bot sends options to Telegram | ❌ |
| 6 | Test: reply with selection, tweet posts | ❌ |
| 7 | Test: reply 0, bot cancels | ❌ |
| 8 | Add confirmation message after post | ❌ |
| 9 | Add chat ID security check | ❌ |
| 10 | Add timeout handling | ❌ |
| 11 | Wire into `main.py` (with terminal fallback) | ❌ |
| 12 | End-to-end test from phone → VM → X | ❌ |
| 13 | Update architecture doc | ❌ |

---

## 10. What Success Looks Like

1. Bot is running on the VM
2. You trigger it (manually for now — scheduling is a later stage)
3. Your phone buzzes with a Telegram message showing 3 tweet options
4. You reply "2"
5. Bot posts tweet option 2 to X
6. Bot sends you a confirmation: "Posted! Tweet ID: ..."
7. You check X — tweet is live

---

## 11. Patterns to Follow (from Stage 1 & 2)

1. **Keep the same interface.** `choose_tweet_option_telegram()` returns the same type as `choose_tweet_option()`.
2. **Use raw HTTP, not SDKs.** `requests` + Telegram Bot API is simpler than `python-telegram-bot` for MVP.
3. **Test with curl first.** Confirm `sendMessage` and `getUpdates` work before writing Python.
4. **Print response bodies on error.** Same as X client — don't hide error details.
5. **Don't over-build.** No inline keyboards, no conversation state, no database. Text messages and polling.

---

## 12. Intentionally NOT Built Yet

- Inline keyboard buttons (nicer UX, but text replies work fine for MVP)
- Webhook mode (needs public URL + SSL)
- Multi-user approval
- Scheduling / cron triggers
- Autonomous posting (no approval)
- Conversation threads / context
- Rate limiting
- Message queuing

---

## 13. Next Stage Preview

**Stage 4:** Trigger the pipeline automatically (cron, webhook, or event-based).
Right now you still run `main.py` manually. Stage 4 makes the bot truly autonomous —
it finds content, generates tweets, asks for approval via Telegram, and posts on schedule.
