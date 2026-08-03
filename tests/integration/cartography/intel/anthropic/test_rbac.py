import copy
from unittest.mock import patch

import requests

import cartography.intel.anthropic.rbac
import tests.data.anthropic.rbac
from tests.integration.cartography.intel.anthropic.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.cartography.intel.anthropic.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"


def _ensure_local_neo4j_has_test_rbac_groups(neo4j_session):
    groups = copy.deepcopy(tests.data.anthropic.rbac.ANTHROPIC_RBAC_GROUPS)
    for group in groups:
        cartography.intel.anthropic.rbac.transform_group(
            group,
            tests.data.anthropic.rbac.ANTHROPIC_RBAC_GROUP_MEMBERS[group["id"]],
        )
    cartography.intel.anthropic.rbac.load_groups(
        neo4j_session,
        groups,
        TEST_ORG_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.anthropic.rbac,
    "get_group_members",
    side_effect=lambda _session, _url, group_id: (
        tests.data.anthropic.rbac.ANTHROPIC_RBAC_GROUP_MEMBERS[group_id]
    ),
)
@patch.object(
    cartography.intel.anthropic.rbac,
    "get_groups",
    return_value=copy.deepcopy(tests.data.anthropic.rbac.ANTHROPIC_RBAC_GROUPS),
)
@patch.object(
    cartography.intel.anthropic.rbac,
    "get_role_permissions",
    side_effect=lambda _session, _url, role_id: (
        tests.data.anthropic.rbac.ANTHROPIC_RBAC_ROLE_PERMISSIONS[role_id]
    ),
)
@patch.object(
    cartography.intel.anthropic.rbac,
    "get_roles",
    return_value=copy.deepcopy(tests.data.anthropic.rbac.ANTHROPIC_RBAC_ROLES),
)
def test_load_anthropic_rbac(
    mock_roles, mock_permissions, mock_groups, mock_members, neo4j_session
):
    """
    Ensure that RBAC roles, their permissions, and groups get loaded and linked
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    cartography.intel.anthropic.rbac.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert roles exist
    assert check_nodes(neo4j_session, "AnthropicRbacRole", ["id", "name"]) == {
        ("rbac_role_016J8xVtKpDq3Wy9ZmN2hR4s", "Project Editor"),
        ("rbac_role_02Tf7NqWrBz5Xk1LcPd8Ju6M", "Plant Supervisor"),
    }

    # Assert groups exist, with source_type distinguishing SCIM-synced groups
    assert check_nodes(
        neo4j_session, "AnthropicRbacGroup", ["id", "name", "source_type"]
    ) == {
        ("rbac_group_012rppKaSVsmTo6NqRDXQXNF", "Engineering", "direct"),
        ("rbac_group_03Yh4MjXsQe7Rv2BnKt9Wz5D", "Safety Inspectors", "scim"),
    }

    # Assert permissions get a synthetic id built from role, action and resource,
    # since the API returns none
    assert check_nodes(
        neo4j_session,
        "AnthropicRbacRolePermission",
        ["id", "action", "resource_type"],
    ) == {
        (
            f"rbac_role_016J8xVtKpDq3Wy9ZmN2hR4s/chat/organization/{TEST_ORG_ID}",
            "chat",
            "organization",
        ),
        (
            "rbac_role_016J8xVtKpDq3Wy9ZmN2hR4s/use/connector_tool/"
            "conn_01ReactorTelemetry/read_sensor",
            "use",
            "connector_tool",
        ),
        (
            "rbac_role_02Tf7NqWrBz5Xk1LcPd8Ju6M/capability_access_all/"
            f"organization/{TEST_ORG_ID}",
            "capability_access_all",
            "organization",
        ),
    }

    # Assert each permission hangs off its role
    assert check_rels(
        neo4j_session,
        "AnthropicRbacRole",
        "id",
        "AnthropicRbacRolePermission",
        "action",
        "GRANTS",
        rel_direction_right=True,
    ) == {
        ("rbac_role_016J8xVtKpDq3Wy9ZmN2hR4s", "chat"),
        ("rbac_role_016J8xVtKpDq3Wy9ZmN2hR4s", "use"),
        ("rbac_role_02Tf7NqWrBz5Xk1LcPd8Ju6M", "capability_access_all"),
    }

    # Assert the group with roles holds them. The group whose roles came back null
    # gets no edge: null means the data was unavailable, and inventing an edge would
    # be worse than reporting none.
    assert check_rels(
        neo4j_session,
        "AnthropicRbacGroup",
        "id",
        "AnthropicRbacRole",
        "id",
        "HAS_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "rbac_group_012rppKaSVsmTo6NqRDXQXNF",
            "rbac_role_016J8xVtKpDq3Wy9ZmN2hR4s",
        ),
    }

    # Assert members are linked
    assert check_rels(
        neo4j_session,
        "AnthropicUser",
        "id",
        "AnthropicRbacGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (
            "user_EneequohSheesh3Ohtaefu8we2aite",
            "rbac_group_012rppKaSVsmTo6NqRDXQXNF",
        ),
        (
            "user_Oov3aYewo6ZuoGh8thaiV1uNoy1aXe",
            "rbac_group_03Yh4MjXsQe7Rv2BnKt9Wz5D",
        ),
    }

    # Assert everything is scoped to the org
    for label in (
        "AnthropicRbacRole",
        "AnthropicRbacGroup",
        "AnthropicRbacRolePermission",
    ):
        assert {
            org_id
            for _, org_id in check_rels(
                neo4j_session,
                label,
                "id",
                "AnthropicOrganization",
                "id",
                "RESOURCE",
                rel_direction_right=False,
            )
        } == {TEST_ORG_ID}
