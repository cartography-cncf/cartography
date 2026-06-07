from unittest.mock import patch

import requests

import cartography.intel.subimage.team
import tests.data.subimage.team
import tests.data.subimage.tenant
from cartography.intel.subimage.team import load_team_members
from cartography.intel.subimage.tenant import load_tenants
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = "tenant-abc-123"


def _ensure_local_neo4j_has_test_tenant(neo4j_session):
    load_tenants(
        neo4j_session,
        tests.data.subimage.tenant.SUBIMAGE_TENANT_TRANSFORMED,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_team_members(neo4j_session):
    _ensure_local_neo4j_has_test_tenant(neo4j_session)
    load_team_members(
        neo4j_session,
        tests.data.subimage.team.SUBIMAGE_TEAM_MEMBERS,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.subimage.team,
    "get",
    return_value=tests.data.subimage.team.SUBIMAGE_TEAM_MEMBERS,
)
def test_load_subimage_team_members(mock_api, neo4j_session):
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "TENANT_ID": TEST_TENANT_ID,
        "BASE_URL": "https://app.example.com",
    }
    _ensure_local_neo4j_has_test_tenant(neo4j_session)

    # Act
    cartography.intel.subimage.team.sync(
        neo4j_session,
        api_session,
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert nodes exist
    expected_nodes = {
        ("member-001", "alice@example.com"),
        ("member-002", "bob@example.com"),
    }
    assert (
        check_nodes(neo4j_session, "SubImageTeamMember", ["id", "email"])
        == expected_nodes
    )

    # Assert rels to tenant
    expected_rels = {
        ("member-001", TEST_TENANT_ID),
        ("member-002", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "SubImageTeamMember",
            "id",
            "SubImageTenant",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
