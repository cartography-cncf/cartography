from tests.data.pylon.users import FRANK_ID
from tests.data.pylon.users import HOMER_ID
from tests.data.pylon.users import MARGE_ID
from tests.data.pylon.users import TRIAGE_BOT_ID

SUPPORT_TEAM_ID = "c3d4e5f6-0000-4000-8000-000000000001"
SECURITY_TEAM_ID = "c3d4e5f6-0000-4000-8000-000000000002"

PYLON_TEAMS = [
    {
        "id": SUPPORT_TEAM_ID,
        "name": "Support",
        "users": [
            {"id": HOMER_ID, "email": "hjsimpson@simpson.corp"},
            {"id": FRANK_ID, "email": "fgrimes@simpson.corp"},
            {"id": TRIAGE_BOT_ID, "email": ""},
        ],
        "assignment_configuration": {
            "assignment_method": "routing",
            "assignable_user_statuses": [],
            "only_assign_if_user_active": True,
            "override_existing_assignee": False,
        },
        "schedule": None,
    },
    {
        "id": SECURITY_TEAM_ID,
        "name": "Security",
        "users": [
            {"id": MARGE_ID, "email": "mbsimpson@simpson.corp"},
        ],
        "assignment_configuration": {
            "assignment_method": "manual",
        },
    },
]
