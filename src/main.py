import sys

from approval import choose_tweet_option
from pipeline import run_pipeline


def main():
    if len(sys.argv) > 1:
        source_text = " ".join(sys.argv[1:])
    else:
        print("Enter source text (end with Ctrl-D):\n")
        source_text = sys.stdin.read().strip()

    if not source_text:
        print("No source text provided. Exiting.")
        sys.exit(1)

    result = run_pipeline(
        source_text=source_text,
        approve_fn=choose_tweet_option,
        notify_fn=print,
    )

    if result is None:
        sys.exit(0)


if __name__ == "__main__":
    main()
