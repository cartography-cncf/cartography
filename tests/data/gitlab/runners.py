"""Test data for GitLab runners module."""

TEST_GITLAB_URL = "https://gitlab.example.com"
TEST_ORG_ID = 10
TEST_GROUP_ID = 42
TEST_PROJECT_ID = 123

# Raw list-endpoint response (subset of fields). The real API also returns these
# fields on /api/v4/runners/all, /api/v4/groups/:id/runners, and
# /api/v4/projects/:id/runners.
GET_INSTANCE_RUNNERS_LIST = [
    {
        "id": 1001,
        "description": "shared-runner-1",
        "runner_type": "instance_type",
        "is_shared": True,
        "active": True,
        "paused": False,
        "online": True,
        "status": "online",
        "ip_address": "10.0.0.1",
    },
]

GET_GROUP_RUNNERS_LIST = [
    {
        "id": 2001,
        "description": "group-runner-1",
        "runner_type": "group_type",
        "is_shared": False,
        "active": True,
        "paused": False,
        "online": True,
        "status": "online",
        "ip_address": "10.0.1.1",
    },
]

GET_PROJECT_RUNNERS_LIST = [
    {
        "id": 3001,
        "description": "project-runner-untagged",
        "runner_type": "project_type",
        "is_shared": False,
        "active": True,
        "paused": False,
        "online": True,
        "status": "online",
        "ip_address": "10.0.2.1",
    },
]

# Detail-endpoint responses (/api/v4/runners/:id) keyed by runner id. These add
# the fields that are NOT present in the list endpoints (architecture, platform,
# tag_list, run_untagged, locked, access_level, maximum_timeout, contacted_at).
RUNNER_DETAILS = {
    1001: {
        "id": 1001,
        "description": "shared-runner-1",
        "runner_type": "instance_type",
        "is_shared": True,
        "active": True,
        "paused": False,
        "online": True,
        "status": "online",
        "ip_address": "10.0.0.1",
        "architecture": "amd64",
        "platform": "linux",
        "contacted_at": "2026-04-29T10:00:00Z",
        "tag_list": ["shared", "linux"],
        "run_untagged": True,
        "locked": False,
        "access_level": "not_protected",
        "maximum_timeout": 3600,
    },
    2001: {
        "id": 2001,
        "description": "group-runner-1",
        "runner_type": "group_type",
        "is_shared": False,
        "active": True,
        "paused": False,
        "online": True,
        "status": "online",
        "ip_address": "10.0.1.1",
        "architecture": "amd64",
        "platform": "linux",
        "contacted_at": "2026-04-29T10:01:00Z",
        "tag_list": ["group-only"],
        "run_untagged": False,
        "locked": True,
        "access_level": "ref_protected",
        "maximum_timeout": 1800,
    },
    3001: {
        "id": 3001,
        "description": "project-runner-untagged",
        "runner_type": "project_type",
        "is_shared": False,
        "active": True,
        "paused": False,
        "online": True,
        "status": "online",
        "ip_address": "10.0.2.1",
        "architecture": "arm64",
        "platform": "linux",
        "contacted_at": "2026-04-29T10:02:00Z",
        "tag_list": [],
        "run_untagged": True,
        "locked": False,
        "access_level": "not_protected",
        "maximum_timeout": None,
    },
}
