def build_headers(
    *,
    api_key: str | None = None,
) -> dict[str, str]:
    if api_key:
        return {
            "x-api-key": api_key,
            "Content-Type": "application/json",
        }

    raise ValueError(
        "JumpCloud auth is not configured. Provide jumpcloud_api_key (x-api-key auth).",
    )
