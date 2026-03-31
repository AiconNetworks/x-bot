import json

import requests
from config import OPENCLAW_URL, OPENCLAW_TOKEN

AGENT_ID = "main"


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

    # Parse the output text from the OpenResponses response.
    # The response shape will need adjusting once we see the actual output.
    output_text = data.get("output", "")
    if isinstance(output_text, list):
        # If output is a list of message objects, extract text from the last one
        for item in reversed(output_text):
            if isinstance(item, dict) and "content" in item:
                content = item["content"]
                if isinstance(content, list):
                    output_text = content[0].get("text", "")
                else:
                    output_text = content
                break

    options = json.loads(output_text)
    return options[:3]
