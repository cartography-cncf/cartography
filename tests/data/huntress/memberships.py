"""Huntress API v1 `Membership` responses.

A membership carries either an account or an organization, never both, and Homer holds
two of them so the transform has to fold several grants into one user.
"""

from typing import Any

MEMBERSHIPS: list[dict[str, Any]] = [
    {
        "id": 5001,
        "permissions": "Admin",
        "account": {"id": 1000, "name": "Springfield Nuclear Power Plant"},
        "organization": None,
        "user": {
            "id": 6001,
            "email": "homer@springfield.example.com",
            "name": "Homer Simpson",
        },
        "created_at": "2026-01-05T09:20:00 UTC",
        "updated_at": "2026-01-05T09:20:00 UTC",
    },
    {
        "id": 5002,
        "permissions": "Read-only",
        "account": None,
        "organization": {"id": 2001, "name": "Springfield Elementary"},
        "user": {
            "id": 6002,
            "email": "marge@springfield.example.com",
            "name": "Marge Simpson",
        },
        "created_at": "2026-01-06T10:00:00 UTC",
        "updated_at": "2026-01-06T10:00:00 UTC",
    },
    {
        "id": 5003,
        "permissions": "Security Engineer",
        "account": None,
        "organization": {"id": 2002, "name": "Shelbyville Elementary"},
        "user": {
            "id": 6001,
            "email": "homer@springfield.example.com",
            "name": "Homer Simpson",
        },
        "created_at": "2026-01-09T08:30:00 UTC",
        "updated_at": "2026-01-09T08:30:00 UTC",
    },
]
