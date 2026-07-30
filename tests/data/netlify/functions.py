"""
Captured from the live Netlify API on 2026-07-30 against a Free-plan team.
Ids, names, emails and domains are replaced with stable fakes.

Note the abbreviated keys: the published OpenAPI spec is wrong about this endpoint.
"""

from typing import Any

NETLIFY_SITE_FUNCTIONS: list[dict[str, Any]] = [
    {
        "branch": None,
        "created_at": "2026-07-30T16:19:16.293Z",
        "functions": [
            {
                "a": "836076848574",
                "bd": {"bootstrapVersion": "2.16.0", "runtimeAPIVersion": 2},
                "c": "2026-07-30T16:19:22.860Z",
                "d": "cc20e993515e1cfd8a682ac7aa9a520cb82a9e946b9c9d636bbeb10169f50a95",
                "dn": None,
                "endpoint": "https://example-site.netlify.app/.netlify/functions/hello",
                "g": None,
                "id": "a461835758354215e6227926ae13db71a066e9aa9c570a981816fcb7c6ad8315",
                "im": "stream",
                "m": 1024,
                "n": "hello",
                "obl": "netlify-observability-extension",
                "oblv": 32,
                "oid": "005924409ed425960221b06af48d1aeabc378eb91ce26c856bc1b311b0e64ff1",
                "p": 10,
                "r": "nodejs24.x",
                "rg": "us-east-2",
                "s": 62033,
                "schedule": None,
            },
            {
                "a": "719837505512",
                "bd": {"bootstrapVersion": "2.16.0", "runtimeAPIVersion": 2},
                "c": "2026-07-30T16:19:22.946Z",
                "d": "7cb8fd4623842551b5ae66083edbf6cd2397724523f78396dd42032125757df2",
                "dn": None,
                "endpoint": "https://example-site.netlify.app/.netlify/functions/scheduled",
                "g": None,
                "id": "c44bc58c71339ffcfa5d9f85242bd5cd67985c59ba010a795ecb61fe8db5f880",
                "im": "stream",
                "m": 1024,
                "n": "scheduled",
                "obl": "netlify-observability-extension",
                "oblv": 32,
                "oid": "1b04d64e80e935a6e28cdde33c2d04137d35e81b7a0eed360d30ba1a38f44b6b",
                "p": 10,
                "r": "nodejs24.x",
                "rg": "us-east-2",
                "s": 62064,
                "schedule": "@daily",
            },
        ],
        "id": "357719e9d9d32974fd84fab69f0c064807c3685f",
        "log_type": "socketeer",
        "provider": "aws_lambda",
    }
]
