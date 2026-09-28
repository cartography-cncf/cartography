"""Raw Snowflake artifact repository payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/artifact-repositories`
returns them.
"""

from typing import Any

SNOWFLAKE_ARTIFACT_REPOSITORIES: list[dict[str, Any]] = [
    {
        "name": "DUFF_PYPI",
        "repository_type": "PIP",
        "api_integration": "DUFF_API",
        "owner": "PLANT_ENGINEER",
        "comment": "Packages the brewery publishes",
        "created_on": "2026-08-03T17:30:00.000+00:00",
    },
    {
        "name": "KWIK_E_PYPI",
        "repository_type": "PIP",
        "api_integration": None,
        "owner": "SHOPKEEPER",
        "comment": None,
        "created_on": "2026-08-03T17:31:00.000+00:00",
    },
]
