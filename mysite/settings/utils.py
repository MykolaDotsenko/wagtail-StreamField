import os


def env_list(name: str, *, default: tuple[str, ...] = ()) -> list[str]:
    """Return a comma-separated environment variable as a trimmed list."""
    raw_value = os.environ.get(name)
    if raw_value is None:
        return list(default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def env_bool(name: str, *, default: bool = False) -> bool:
    """Parse an explicit boolean environment variable."""
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(f"{name} must be one of: true/false, yes/no, on/off, 1/0")
