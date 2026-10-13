from typing import Any

# Synthetic raw API payloads for GET /api/v1/api-tokens.

API_TOKENS: list[dict[str, Any]] = [
    {
        "id": "00T-zone-restricted",
        "name": "SIEM integration",
        "clientName": "Okta API",
        "userId": "00u-svc-siem",
        "tokenWindow": "P30D",
        "created": "2026-01-01T00:00:00.000Z",
        "expiresAt": "2026-10-30T00:00:00.000Z",
        "lastUpdated": "2026-01-01T00:00:00.000Z",
        "network": {
            "connection": "ZONE",
            "include": ["nzo-corp"],
            "exclude": ["nzo-tor"],
        },
        "_link": {},
    },
    {
        "id": "00T-anywhere",
        "name": "Legacy script",
        "clientName": "Okta API",
        "userId": "00u-alice",
        "tokenWindow": "P30D",
        "created": "2025-06-01T00:00:00.000Z",
        "expiresAt": "2026-10-20T00:00:00.000Z",
        "lastUpdated": "2025-06-01T00:00:00.000Z",
        "network": {"connection": "ANYWHERE"},
    },
    {
        "id": "00T-no-network",
        "name": "Older token without a network condition",
        "clientName": "Okta API",
        "userId": "00u-alice",
        "tokenWindow": "P30D",
        "created": "2025-01-01T00:00:00.000Z",
        "expiresAt": "2026-10-10T00:00:00.000Z",
        "lastUpdated": "2025-01-01T00:00:00.000Z",
    },
]
