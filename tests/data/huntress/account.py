"""Huntress API v1 `GET /v1/account` response."""

from typing import Any

ACCOUNT: dict[str, Any] = {
    "id": 1000,
    "name": "Springfield Nuclear Power Plant",
    "subdomain": "springfield",
    "status": "enabled",
    "support_type": "not_applicable",
    "neighborhood_watch": {"edr": 0, "sat": 0, "ispm": 0, "itdr": 0, "siem": 0},
    "billing_address": None,
    "shipping_address": None,
}
