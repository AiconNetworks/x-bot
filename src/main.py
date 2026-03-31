import sys

from openclaw_client import generate_tweet_options
from approval import choose_tweet_option
from x_client import post_tweet


def main():
    # Step 1: Get source text
    if len(sys.argv) > 1:
        source_text = " ".join(sys.argv[1:])
    else:
        print("Enter source text (end with Ctrl-D):\n")
        source_text = sys.stdin.read().strip()

    if not source_text:
        print("No source text provided. Exiting.")
        sys.exit(1)

    print(f"\nSource text received ({len(source_text)} chars).")

    # Step 2: Generate tweet options via OpenClaw
    print("Generating tweet options...")
    options = generate_tweet_options(source_text)

    if not options:
        print("No tweet options returned. Exiting.")
        sys.exit(1)

    # Step 3: Approval
    selected = choose_tweet_option(options)
    if selected is None:
        print("Cancelled.")
        sys.exit(0)

    tweet_text = options[selected]

    # Step 4: Post to X
    print(f"\nPosting tweet ({len(tweet_text)} chars)...")
    result = post_tweet(tweet_text)
    print(f"Posted successfully. Tweet ID: {result['data']['id']}")


if __name__ == "__main__":
    main()
