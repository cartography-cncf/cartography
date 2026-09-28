"""
Captured from the live Netlify API on 2026-07-30 against a Free-plan team.
Ids, names, emails and domains are replaced with stable fakes.

The plaintext connection strings are kept in the fixture on purpose so the tests can
assert that they never reach the graph.
"""

from typing import Any

NETLIFY_DATABASE_BRANCHES: list[dict[str, Any]] = [
    {
        "branch_id": "production",
        "compute": {
            "autoscaling_limit_max_cu": 0.25,
            "autoscaling_limit_min_cu": 0.25,
            "current_state": "active",
            "last_active": "2026-07-30T16:20:50Z",
            "suspend_timeout_seconds": 300,
        },
        "connection_string": "postgresql://netlifydb_readonly:ElXmQJhA8559cktljB3sWQK-woJPfvbc@ep-soft-sea-aydccu4t.c-5.us-east-2.db.netlify.com/netlifydb?sslmode=require",
        "connection_strings": {
            "netlifydb_readonly": "postgresql://netlifydb_readonly:ElXmQJhA8559cktljB3sWQK-woJPfvbc@ep-soft-sea-aydccu4t.c-5.us-east-2.db.netlify.com/netlifydb?sslmode=require"
        },
        "created_at": "2026-07-30T16:20:45Z",
        "logical_size_bytes": 0,
        "name": "production",
        "state": "ready",
        "updated_at": "2026-07-30T16:20:48Z",
    }
]
