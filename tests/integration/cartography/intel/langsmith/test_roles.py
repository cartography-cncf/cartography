from unittest.mock import patch

import cartography.intel.langsmith.roles
import tests.data.langsmith.roles
from tests.data.langsmith.organizations import LANGSMITH_ORG_ID
from tests.data.langsmith.roles import CUSTOM_ROLE_ID
from tests.data.langsmith.roles import ORG_ADMIN_ROLE_ID
from tests.integration.cartography.intel.langsmith.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_roles(neo4j_session):
    cartography.intel.langsmith.roles.load_roles(
        neo4j_session,
        cartography.intel.langsmith.roles.transform_permissions(
            tests.data.langsmith.roles.LANGSMITH_ROLES
        ),
        cartography.intel.langsmith.roles.transform_roles(
            tests.data.langsmith.roles.LANGSMITH_ROLES
        ),
        LANGSMITH_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.langsmith.roles,
    "get_roles",
    return_value=tests.data.langsmith.roles.LANGSMITH_ROLES,
)
def test_sync_langsmith_roles(mock_roles, neo4j_session):
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": LANGSMITH_ORG_ID,
    }

    cartography.intel.langsmith.roles.sync(
        neo4j_session, None, LANGSMITH_ORG_ID, common_job_parameters
    )

    # The permission catalog is derived from what the roles grant; the dedicated
    # /orgs/permissions endpoint is not reachable with a personal access token.
    assert check_nodes(
        neo4j_session, "LangSmithPermission", ["id", "access_scope"]
    ) == {
        ("organization:manage", "organization"),
        ("organization:read", "organization"),
        ("deployments:read", "workspace"),
        ("workspaces:read", "workspace"),
    }

    # A custom role is only distinguishable by display_name and the owning organization_id:
    # LangSmith stores every custom role under the system name CUSTOM.
    assert check_nodes(
        neo4j_session, "LangSmithRole", ["id", "name", "system_name", "is_custom"]
    ) == {
        (ORG_ADMIN_ROLE_ID, "Organization Admin", "ORGANIZATION_ADMIN", False),
        (
            tests.data.langsmith.roles.WORKSPACE_VIEWER_ROLE_ID,
            "Viewer",
            "WORKSPACE_VIEWER",
            False,
        ),
        (CUSTOM_ROLE_ID, "Deployment Auditor", "CUSTOM", True),
    }

    assert check_rels(
        neo4j_session,
        "LangSmithRole",
        "id",
        "LangSmithPermission",
        "id",
        "GRANTS",
        rel_direction_right=True,
    ) == {
        (ORG_ADMIN_ROLE_ID, "organization:manage"),
        (ORG_ADMIN_ROLE_ID, "organization:read"),
        (tests.data.langsmith.roles.WORKSPACE_VIEWER_ROLE_ID, "workspaces:read"),
        (CUSTOM_ROLE_ID, "workspaces:read"),
        (CUSTOM_ROLE_ID, "deployments:read"),
    }

    assert check_rels(
        neo4j_session,
        "LangSmithOrganization",
        "id",
        "LangSmithRole",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (LANGSMITH_ORG_ID, ORG_ADMIN_ROLE_ID),
        (LANGSMITH_ORG_ID, tests.data.langsmith.roles.WORKSPACE_VIEWER_ROLE_ID),
        (LANGSMITH_ORG_ID, CUSTOM_ROLE_ID),
    }
