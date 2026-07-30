"""
Railway API and project token fixtures.

Both are hand-written from the live GraphQL schema rather than captured: `apiTokens` returns
`Not Authorized` for tokens that are not account-scoped, and a freshly created project has
no project tokens. `displayToken` is Railway's own redacted prefix, so storing it is safe.
"""

from typing import Any

RAILWAY_API_TOKENS: list[dict[str, Any]] = [
    {
        "id": "a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1",
        "name": "ci-deploy",
        "displayToken": "rw_1a2b",
        "workspaceId": "11111111-1111-1111-1111-111111111111",
        "expiresAt": "2027-01-01T00:00:00.000Z",
    },
    {
        # A personal-scope token: workspaceId is null, so it reaches every workspace.
        "id": "a2a2a2a2-a2a2-a2a2-a2a2-a2a2a2a2a2a2",
        "name": "laptop",
        "displayToken": "rw_3c4d",
        "workspaceId": None,
        "expiresAt": None,
    },
    {
        # Belongs to a different workspace and must be filtered out of this sync.
        "id": "a3a3a3a3-a3a3-a3a3-a3a3-a3a3a3a3a3a3",
        "name": "other-workspace",
        "displayToken": "rw_5e6f",
        "workspaceId": "19191919-1919-1919-1919-191919191919",
        "expiresAt": None,
    },
]

RAILWAY_PROJECT_TOKENS: list[dict[str, Any]] = [
    {
        "id": "b1b1b1b1-b1b1-b1b1-b1b1-b1b1b1b1b1b1",
        "name": "production-deploy",
        "displayToken": "rw_7g8h",
        "projectId": "33333333-3333-3333-3333-333333333333",
        "environmentId": "44444444-4444-4444-4444-444444444444",
        "createdAt": "2026-07-27T18:05:00.000Z",
    },
]
