from collections.abc import Iterable
from urllib.parse import urlparse


def normalize_hostname(value: str | None) -> str | None:
    """Return a lowercase hostname without surrounding whitespace or trailing dots."""
    if value is None:
        return None

    normalized = value.strip().rstrip(".").lower()
    return normalized or None


def normalize_hostname_values(values: Iterable[str] | None) -> list[str]:
    """Normalize each hostname and omit empty results."""
    if values is None:
        return []

    return [normalized for value in values if (normalized := normalize_hostname(value))]


def hostname_from_url(value: str | None) -> str | None:
    """Return the normalized hostname from an absolute URL."""
    if value is None:
        return None
    return normalize_hostname(urlparse(value.strip()).hostname)
