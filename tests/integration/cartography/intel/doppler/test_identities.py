from unittest.mock import patch

import requests

import cartography.intel.doppler.groups
import cartography.intel.doppler.members
import cartography.intel.doppler.projects
import cartography.intel.doppler.roles
import cartography.intel.doppler.service_accounts
import cartography.intel.doppler.users
import cartography.intel.doppler.workplace
import tests.data.doppler.doppler as data
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_WORKPLACE_ID = "wp1"


def _common():
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.doppler.com/v3",
        "WORKPLACE_ID": TEST_WORKPLACE_ID,
    }


@patch.object(
    cartography.intel.doppler.members,
    "get",
    return_value=data.PROJECT_MEMBERS,
)
@patch.object(
    cartography.intel.doppler.service_accounts,
    "get",
    return_value=(
        data.SERVICE_ACCOUNTS,
        data.SERVICE_ACCOUNT_TOKENS,
        data.SERVICE_ACCOUNT_IDENTITIES,
    ),
)
@patch.object(
    cartography.intel.doppler.groups,
    "get",
    return_value=(data.GROUPS, data.GROUP_MEMBERSHIPS),
)
@patch.object(cartography.intel.doppler.users, "get", return_value=data.USERS)
@patch.object(
    cartography.intel.doppler.roles,
    "get",
    return_value=(data.WORKPLACE_ROLES, data.PROJECT_ROLES),
)
@patch.object(cartography.intel.doppler.projects, "get", return_value=data.PROJECTS)
@patch.object(cartography.intel.doppler.workplace, "get", return_value=data.WORKPLACE)
def test_doppler_identities(
    mock_wp,
    mock_proj,
    mock_roles,
    mock_users,
    mock_groups,
    mock_sa,
    mock_members,
    neo4j_session,
):
    # Arrange
    api_session = requests.Session()
    common = _common()

    # Act
    cartography.intel.doppler.workplace.sync(neo4j_session, api_session, common)
    project_slugs = cartography.intel.doppler.projects.sync(
        neo4j_session, api_session, common
    )
    cartography.intel.doppler.roles.sync(neo4j_session, api_session, common)
    cartography.intel.doppler.users.sync(neo4j_session, api_session, common)
    cartography.intel.doppler.groups.sync(neo4j_session, api_session, common)
    cartography.intel.doppler.service_accounts.sync(neo4j_session, api_session, common)
    cartography.intel.doppler.members.sync(
        neo4j_session, api_session, project_slugs, common
    )

    # Assert: user flattened + UserAccount label + RESOURCE edge
    assert check_nodes(neo4j_session, "DopplerWorkplaceUser", ["id", "email"]) == {
        ("u1", "alice@acme.io")
    }
    assert check_nodes(neo4j_session, "UserAccount", ["id"]) >= {("u1",)}

    # Assert: user MEMBER_OF group
    assert check_rels(
        neo4j_session,
        "DopplerWorkplaceUser",
        "id",
        "DopplerGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {("u1", "g1")}

    # Assert: service account HAS_ROLE workplace role, HAS_TOKEN, HAS_IDENTITY
    assert check_rels(
        neo4j_session,
        "DopplerServiceAccount",
        "id",
        "DopplerWorkplaceRole",
        "id",
        "HAS_ROLE",
        rel_direction_right=True,
    ) == {("sa1", "admin")}
    assert check_rels(
        neo4j_session,
        "DopplerServiceAccount",
        "id",
        "DopplerServiceAccountToken",
        "id",
        "HAS_TOKEN",
        rel_direction_right=True,
    ) == {("sa1", "sat1")}
    assert check_rels(
        neo4j_session,
        "DopplerServiceAccount",
        "id",
        "DopplerServiceAccountIdentity",
        "id",
        "HAS_IDENTITY",
        rel_direction_right=True,
    ) == {("sa1", "sai1")}

    # Assert: project membership MatchLinks for all three member types
    assert check_rels(
        neo4j_session,
        "DopplerWorkplaceUser",
        "id",
        "DopplerProject",
        "slug",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {("u1", "backend")}
    assert check_rels(
        neo4j_session,
        "DopplerGroup",
        "id",
        "DopplerProject",
        "slug",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {("g1", "backend")}
    assert check_rels(
        neo4j_session,
        "DopplerServiceAccount",
        "id",
        "DopplerProject",
        "slug",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {("sa1", "backend")}
