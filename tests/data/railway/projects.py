"""
Captured from the Railway public API (`projects(workspaceId:)`) against a real Hobby
workspace, with identifiers and PII replaced by stable fakes.

The captured workspace had a single project and an empty `members` list (a personal
workspace has no per-project membership). A second project and synthetic members are added
by hand so tests can exercise per-project cleanup scoping and non-ADMIN roles.
"""

RAILWAY_PROJECTS = [
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "name": "cartography-fixture",
        "description": None,
        "isPublic": False,
        "isTempProject": False,
        "prDeploys": False,
        "createdAt": "2026-07-27T18:00:44.634Z",
        "updatedAt": "2026-07-27T18:00:44.634Z",
        "deletedAt": None,
        "workspaceId": "11111111-1111-1111-1111-111111111111",
        "subscriptionType": "trial",
        "members": [
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "email": "alice@example.com",
                "name": "Alice Example",
                "role": "ADMIN",
            },
            {
                "id": "23232323-2323-2323-2323-232323232323",
                "email": "bob@example.com",
                "name": "Bob Example",
                "role": "VIEWER",
            },
        ],
    },
    {
        "id": "34343434-3434-3434-3434-343434343434",
        "name": "cartography-fixture-public",
        "description": "A deliberately public project.",
        "isPublic": True,
        "isTempProject": False,
        "prDeploys": False,
        "createdAt": "2026-07-27T18:10:00.000Z",
        "updatedAt": "2026-07-27T18:10:00.000Z",
        "deletedAt": None,
        "workspaceId": "11111111-1111-1111-1111-111111111111",
        "subscriptionType": "trial",
        "members": [],
    },
]
