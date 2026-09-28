import re
from datetime import datetime
from typing import Any

from dateutil.parser import isoparse

_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)


def unwrap_value(value: Any) -> Any:
    """Unwrap a value from Orca's Serving Layer field envelope."""
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


def field_value(data: dict[str, Any], key: str) -> Any:
    """Return an Orca field, unwrapping its value envelope."""
    return unwrap_value(data[key]) if key in data else None


def require_nonempty_string(value: Any, field: str) -> str:
    """Return a normalized required string or reject the malformed field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    return value.strip()


def optional_nonempty_string(value: Any, field: str) -> str | None:
    """Normalize an optional string while rejecting malformed present values."""
    if value is None:
        return None
    return require_nonempty_string(value, field)


def optional_string(value: Any, field: str) -> str | None:
    """Return an optional string or reject a malformed present value."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def optional_number(value: Any, field: str) -> int | float | None:
    """Return an optional number or reject a malformed present value."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    return value


def require_object(value: Any, field: str) -> dict[str, Any]:
    """Return a required JSON object or reject the malformed field."""
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def empty_target_context() -> dict[str, str | None]:
    """Return the target fields shared by Orca finding types."""
    return {
        "target_orca_inventory_id": None,
        "target_orca_asset_unique_id": None,
        "target_provider_id": None,
        "target_arn": None,
        "target_cloud_provider": None,
        "target_cloud_account_id": None,
        "target_region": None,
        "target_name": None,
        "target_type": None,
    }


def inventory_target_context(
    value: Any,
    field: str,
) -> dict[str, str | None]:
    """Extract exact target context from a related Orca Inventory object."""
    inventory = require_object(value, field)
    raw_data = inventory.get("data")
    data = inventory if raw_data is None else require_object(raw_data, f"{field}.data")
    sources = (inventory,) if data is inventory else (inventory, data)

    def first_value(*keys: str) -> Any:
        for source in sources:
            for key in keys:
                if key in source:
                    candidate = unwrap_value(source[key])
                    if candidate is not None:
                        return candidate
        return None

    raw_context = {
        "target_orca_inventory_id": first_value(
            "id",
        ),
        "target_orca_asset_unique_id": first_value(
            "AssetUniqueId",
            "asset_unique_id",
        ),
        "target_provider_id": first_value(
            "UiUniqueField",
        ),
        "target_arn": first_value("Arn"),
        "target_cloud_provider": first_value("CloudProvider"),
        "target_cloud_account_id": first_value(
            "CloudAccountId",
        ),
        "target_region": first_value("Region"),
        "target_name": first_value("name", "Name"),
        "target_type": first_value("type", "Type"),
    }
    return {
        key: optional_nonempty_string(raw_value, f"{field}.{key}")
        for key, raw_value in raw_context.items()
    }


def canonical_cve_ids(*values: Any) -> list[str]:
    """Return the distinct canonical CVE identifiers in Orca fields."""
    candidates: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            candidates.append(value)
            continue
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            candidates.extend(value)
            continue
        raise ValueError("Orca CVE fields must contain strings")

    return sorted(
        {
            candidate.strip().upper()
            for candidate in candidates
            if _CVE_RE.fullmatch(candidate.strip())
        },
    )


def parse_datetime(value: Any, field: str) -> datetime | None:
    """Parse an optional Orca RFC 3339 timestamp into a Neo4j-safe datetime."""
    if value is None:
        return None
    normalized = require_nonempty_string(value, field)
    try:
        timestamp = isoparse(normalized)
    except ValueError as exc:
        raise ValueError(f"{field} must be an RFC 3339 timestamp") from exc
    if timestamp.tzinfo is None:
        raise ValueError(f"{field} must include a UTC offset")
    return timestamp
