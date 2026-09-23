def normalize_azure_ad_device_id(value: str | None) -> str | None:
    """Normalize the Entra device join key; empty and zero IDs cannot identify a device."""
    normalized = (value or "").lower() or None
    return normalized if normalized != "00000000-0000-0000-0000-000000000000" else None
