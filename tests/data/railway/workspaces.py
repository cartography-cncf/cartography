"""
Captured from the Railway public API (`workspace(workspaceId:)`) against a real Hobby
workspace, with identifiers and PII replaced by stable fakes.

`has2FAEnforcement` and `hasSAML` are Pro/Enterprise features and are therefore always false
in captured data; the fixture keeps the real values rather than inventing enabled ones.
"""

RAILWAY_WORKSPACE = {
    "id": "11111111-1111-1111-1111-111111111111",
    "name": "Example Workspace",
    "createdAt": "2026-07-27T17:24:42.964Z",
    "preferredRegion": "us-west2",
    "projectCount": 2,
    "has2FAEnforcement": False,
    "hasSAML": False,
    "plan": "HOBBY",
    "members": [
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "name": "Alice Example",
            "email": "alice@example.com",
            "role": "ADMIN",
            "twoFactorAuthEnabled": False,
        },
        # Hand-added: a personal workspace only ever has one ADMIN member, so a second
        # member is needed to exercise the non-owner role path.
        {
            "id": "23232323-2323-2323-2323-232323232323",
            "name": "Bob Example",
            "email": "bob@example.com",
            "role": "MEMBER",
            "twoFactorAuthEnabled": True,
        },
    ],
}
