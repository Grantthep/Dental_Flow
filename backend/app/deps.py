def current_user_id() -> int | None:
    # shortcut: no auth yet, so audit rows have user_id = NULL; Member 3 replaces this with the JWT user.
    return None
