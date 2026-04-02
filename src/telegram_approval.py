import time
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
POLL_TIMEOUT = 120  # seconds to wait for a reply


def send_message(text: str) -> dict:
    """Send a message to the configured Telegram chat."""
    response = requests.post(
        f"{API_BASE}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def _flush_updates():
    """Consume all pending updates so we only see new replies."""
    resp = requests.post(
        f"{API_BASE}/getUpdates",
        json={"timeout": 0},
        timeout=15,
    )
    resp.raise_for_status()
    results = resp.json().get("result", [])
    if results:
        last_id = results[-1]["update_id"]
        requests.post(
            f"{API_BASE}/getUpdates",
            json={"offset": last_id + 1, "timeout": 0},
            timeout=15,
        )


def _wait_for_reply() -> str | None:
    """Long-poll for a text reply from the authorized chat. Returns text or None on timeout."""
    deadline = time.time() + POLL_TIMEOUT

    while time.time() < deadline:
        remaining = max(1, int(deadline - time.time()))
        poll_time = min(remaining, 30)

        resp = requests.post(
            f"{API_BASE}/getUpdates",
            json={"timeout": poll_time},
            timeout=poll_time + 10,
        )
        resp.raise_for_status()
        results = resp.json().get("result", [])

        for update in results:
            msg = update.get("message", {})
            chat_id = msg.get("chat", {}).get("id")
            text = msg.get("text", "").strip()

            # Acknowledge this update
            requests.post(
                f"{API_BASE}/getUpdates",
                json={"offset": update["update_id"] + 1, "timeout": 0},
                timeout=15,
            )

            # Only accept messages from the authorized chat
            if chat_id == TELEGRAM_CHAT_ID and text:
                return text

    return None


def choose_tweet_option(options: list[str]) -> int | None:
    """Send tweet options to Telegram and wait for a selection.

    Returns selected index (0-based) or None on cancel/timeout.
    """
    lines = ["Tweet options:\n"]
    for i, option in enumerate(options, start=1):
        lines.append(f"{i}. {option}\n")
    lines.append("Reply 1, 2, 3 to select — or 0 to cancel.")

    _flush_updates()
    send_message("\n".join(lines))

    reply = _wait_for_reply()
    if reply is None:
        send_message("Timed out waiting for reply. Cancelled.")
        return None

    if reply == "0":
        return None

    valid = {str(i) for i in range(1, len(options) + 1)}
    if reply in valid:
        return int(reply) - 1

    send_message(f"Invalid choice: {reply}. Cancelled.")
    return None
