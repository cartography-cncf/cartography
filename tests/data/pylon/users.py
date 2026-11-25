from tests.data.pylon.roles import ADMIN_ROLE_ID
from tests.data.pylon.roles import MEMBER_ROLE_ID
from tests.data.pylon.roles import SECURITY_ROLE_ID

MARGE_ID = "b2c3d4e5-0000-4000-8000-000000000001"
HOMER_ID = "b2c3d4e5-0000-4000-8000-000000000002"
FRANK_ID = "b2c3d4e5-0000-4000-8000-000000000003"
ZAPIER_TOKEN_ID = "b2c3d4e5-0000-4000-8000-000000000004"
TRIAGE_BOT_ID = "b2c3d4e5-0000-4000-8000-000000000005"
OLD_TOKEN_ID = "b2c3d4e5-0000-4000-8000-000000000006"

PYLON_USERS = [
    {
        "id": MARGE_ID,
        "name": "Marge Simpson",
        "email": "mbsimpson@simpson.corp",
        "emails": ["mbsimpson@simpson.corp", "marge@simpson.corp"],
        "avatar_url": "https://example.com/marge.png",
        "is_deactivated": False,
        "status": "active",
        "role": {"id": ADMIN_ROLE_ID, "name": "Admin", "slug": "admin"},
        "role_id": ADMIN_ROLE_ID,
        "role_ids": [ADMIN_ROLE_ID, SECURITY_ROLE_ID],
        "roles": [
            {"id": ADMIN_ROLE_ID, "name": "Admin", "slug": "admin"},
            {"id": SECURITY_ROLE_ID, "name": "Security", "slug": "security"},
        ],
        "skills": None,
    },
    {
        "id": HOMER_ID,
        "name": "Homer Simpson",
        "email": "hjsimpson@simpson.corp",
        "emails": ["hjsimpson@simpson.corp"],
        "avatar_url": "https://example.com/homer.png",
        "is_deactivated": False,
        "status": "out_of_office",
        "role_id": MEMBER_ROLE_ID,
        "role_ids": [MEMBER_ROLE_ID],
        "roles": [{"id": MEMBER_ROLE_ID, "name": "Member", "slug": "member"}],
        "skills": None,
    },
    {
        "id": FRANK_ID,
        "name": "Frank Grimes",
        "email": "fgrimes@simpson.corp",
        "emails": ["fgrimes@simpson.corp"],
        "avatar_url": "",
        "is_deactivated": True,
        "status": "away",
        "role_ids": [MEMBER_ROLE_ID],
        "roles": [{"id": MEMBER_ROLE_ID, "name": "Member", "slug": "member"}],
        "skills": None,
    },
    # API tokens with their own identity and bots have no email address.
    {
        "id": ZAPIER_TOKEN_ID,
        "name": "Zapier - Write Back",
        "email": "",
        "emails": [],
        "avatar_url": "",
        "is_deactivated": False,
        "status": "active",
        "role_ids": [ADMIN_ROLE_ID],
        "roles": [{"id": ADMIN_ROLE_ID, "name": "Admin", "slug": "admin"}],
        "skills": None,
    },
    {
        "id": TRIAGE_BOT_ID,
        "name": "Triage Bot",
        "is_deactivated": False,
        "status": "active",
        "role_ids": [MEMBER_ROLE_ID],
        "roles": [{"id": MEMBER_ROLE_ID, "name": "Member", "slug": "member"}],
        "skills": None,
    },
    {
        "id": OLD_TOKEN_ID,
        "name": "Old Admin Token",
        "email": "",
        "emails": [],
        "is_deactivated": True,
        "status": "active",
        "role_ids": [ADMIN_ROLE_ID],
        "roles": [{"id": ADMIN_ROLE_ID, "name": "Admin", "slug": "admin"}],
        "skills": None,
    },
]
