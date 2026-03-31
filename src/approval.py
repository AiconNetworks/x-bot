def choose_tweet_option(options: list[str]) -> int | None:
    """Display tweet options and let the user choose one.

    Returns the selected index (0-based) or None if cancelled.
    """
    print("\n--- Tweet Options ---\n")
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {option}\n")
    print("  0. Cancel\n")

    while True:
        choice = input("Choose an option: ").strip()
        if choice == "0":
            return None
        if choice in {str(i) for i in range(1, len(options) + 1)}:
            return int(choice) - 1
        print("Invalid choice. Try again.")
