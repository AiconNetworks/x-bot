import json
import re

import requests
from config import OPENCLAW_URL, OPENCLAW_TOKEN

AGENT_ID = "main"


def _extract_text(data: dict) -> str:
    """Extract the text content from an OpenResponses response."""
    output = data["output"]
    for item in reversed(output):
        if isinstance(item, dict) and "content" in item:
            content = item["content"]
            if isinstance(content, list):
                return content[0]["text"]
            return content
    return ""


def _parse_options(text: str) -> list[str]:
    """Parse tweet options from response text.

    Handles JSON arrays or numbered lines like '1) ...' / '1. ...'.
    """
    text = text.strip()

    # Try JSON array first
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed]
    except json.JSONDecodeError:
        pass

    # Fall back to numbered lines: 1) ... or 1. ...
    lines = re.split(r'\n?\d+[).]\s*', text)
    options = [line.strip().strip('"') for line in lines if line.strip()]
    return options


def generate_tweet_options(source_text: str) -> list[str]:
    """Ask OpenClaw to generate 3 tweet options from source text."""
    response = requests.post(
        f"{OPENCLAW_URL}/v1/responses",
        headers={
            "Authorization": f"Bearer {OPENCLAW_TOKEN}",
            "Content-Type": "application/json",
            "x-openclaw-agent-id": AGENT_ID,
        },
        json={
            "model": "openclaw",
            "input": (
                "You are a tweet writer. Given the following source text, "
                "generate exactly 3 tweet options. Each tweet must be under "
                "280 characters. Return only a JSON array of 3 strings, "
                "no other text.\n\n"
                f"Source text:\n{source_text}"
            ),
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    text = _extract_text(data)
    options = _parse_options(text)
    return options[:3]
