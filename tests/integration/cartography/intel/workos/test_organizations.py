from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.organizations
import tests.data.workos.organizations
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLIENT_ID = "client_1234567890abcdef"


def _ensure_local_neo4j_has_test_environment(neo4j_session):
    """Ensure the WorkOSEnvironment node exists."""
    neo4j_session.run(
        """
        MERGE (e:WorkOSEnvironment{id: $client_id})
        ON CREATE SET e.firstseen = timestamp()
        SET e.lastupdated = $update_tag
        """,
        client_id=TEST_CLIENT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_organizations(neo4j_session):
    transformed_orgs = cartography.intel.workos.organizations.transform(
        tests.data.workos.organizations.WORKOS_ORGANIZATIONS
    )
    cartography.intel.workos.organizations.load_organizations(
        neo4j_session,
        transformed_orgs,
        TEST_CLIENT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.workos.organizations,
    "get",
    return_value=tests.data.workos.organizations.WORKOS_ORGANIZATIONS,
)
def test_load_workos_organizations(mock_api, neo4j_session):
    """
    Ensure that organizations actually get loaded
    """
    # Arrange
    _ensure_local_neo4j_has_test_environment(neo4j_session)
    client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKOS_CLIENT_ID": TEST_CLIENT_ID,
    }

    # Act
    cartography.intel.workos.organizations.sync(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Assert Organizations exist
    expected_nodes = {
        ("org_01HXYZ1234567890ABCDEFGHIJ", "Springfield Nuclear Power Plant"),
        ("org_02HXYZ0987654321ZYXWVUTSRQ", "Kwik-E-Mart"),
    }
    assert (
        check_nodes(neo4j_session, "WorkOSOrganization", ["id", "name"])
        == expected_nodes
    )

    # Assert organizations are linked to the environment
    expected_rels = {
        ("org_01HXYZ1234567890ABCDEFGHIJ", TEST_CLIENT_ID),
        ("org_02HXYZ0987654321ZYXWVUTSRQ", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSOrganization",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
