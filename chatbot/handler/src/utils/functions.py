def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """Mask sensitive data, showing only the last visible_chars characters."""
    if not value:
        return ""
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]
