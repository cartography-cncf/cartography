from copy import deepcopy
from unittest.mock import Mock

from cartography.intel.jira.util import JiraClient
from tests.data.jira.access import API_RESPONSES
from tests.data.jira.access import CLOUD_ID
from tests.data.jira.access import GROUPS
from tests.data.jira.access import PROJECTS
from tests.data.jira.access import USERS


def api_client(cloud_id=CLOUD_ID):
    """Mock only the provider client boundary; exercise real orchestration and graph writes."""
    client = Mock(spec=JiraClient)
    client.cloud_id = cloud_id
    state = {
        "responses": deepcopy(API_RESPONSES),
        "users": deepcopy(USERS),
        "groups": deepcopy(GROUPS),
        "projects": deepcopy(PROJECTS),
        "memberships": {"group-1": deepcopy(USERS), "group-2": [deepcopy(USERS[0])]},
        "admin": [deepcopy(GROUPS[1])],
        "site-admin": [deepcopy(GROUPS[1])],
    }

    def pages(path, **params):
        if path == "users/search":
            return deepcopy(state["users"])
        if path == "group/bulk":
            return deepcopy(state[params.get("accessType", "groups")])
        if path == "group/member":
            assert params["includeInactiveUsers"] == "true"
            return deepcopy(state["memberships"][params["groupId"]])
        if path == "project/search":
            return deepcopy(state["projects"])
        raise AssertionError(path)

    client.pages.side_effect = pages
    client.get.side_effect = lambda path, **params: deepcopy(state["responses"][path])
    return client, state
