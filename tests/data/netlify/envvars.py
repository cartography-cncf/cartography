"""
Captured from the live Netlify API on 2026-07-30 against a Free-plan team.
Ids, names, emails and domains are replaced with stable fakes.

The secret value arrives already masked by Netlify; it is dropped on ingest anyway.
"""

from typing import Any

NETLIFY_SITE_ENV_VARS: list[dict[str, Any]] = [
    {
        "is_secret": False,
        "key": "CARTO_PUBLIC",
        "scopes": ["builds", "functions", "post_processing", "runtime"],
        "updated_at": "2026-07-30T16:19:38Z",
        "updated_by": {
            "avatar_url": "https://secure.gravatar.com/avatar/00000000000000000000000000000000?s=30",
            "email": "alice@example.com",
            "full_name": "Alice Example",
            "id": "5f5a5d7053c60b4be4c8784b",
        },
        "values": [
            {
                "context": "production",
                "id": "9c5333bb-5436-4528-9d13-657a5d84e2d7",
                "role": "",
                "value": "hello",
            }
        ],
    },
    {
        "is_secret": True,
        "key": "CARTO_SECRET",
        "scopes": ["builds", "functions", "runtime"],
        "updated_at": "2026-07-30T16:20:18Z",
        "updated_by": {
            "avatar_url": "https://secure.gravatar.com/avatar/00000000000000000000000000000000?s=30",
            "email": "alice@example.com",
            "full_name": "Alice Example",
            "id": "5f5a5d7053c60b4be4c8784b",
        },
        "values": [
            {
                "context": "production",
                "id": "cef83b97-3907-48ae-89f6-d290d6c7fff3",
                "role": "",
                "value": "****************cr3t",
            }
        ],
    },
]
