from openclaw_client import generate_tweet_options
from x_client import post_tweet


def run_pipeline(source_text: str, approve_fn, notify_fn=None):
    """Run the tweet pipeline: generate → approve → post.

    Args:
        source_text: Text to generate tweets from.
        approve_fn: Callable(options: list[str]) -> int | None
        notify_fn: Optional callable(message: str) for status updates.
    """
    def notify(msg):
        if notify_fn:
            notify_fn(msg)

    notify(f"Source text received ({len(source_text)} chars). Generating tweet options...")
    options = generate_tweet_options(source_text)

    if not options:
        notify("No tweet options returned.")
        return None

    selected = approve_fn(options)
    if selected is None:
        notify("Cancelled.")
        return None

    tweet_text = options[selected]
    notify(f"Posting tweet ({len(tweet_text)} chars)...")

    result = post_tweet(tweet_text)
    tweet_id = result["data"]["id"]
    notify(f"Posted! Tweet ID: {tweet_id}")
    return tweet_id
