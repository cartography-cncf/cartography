from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.api_keys
import tests.data.workos.api_keys
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
    """Ensure the WorkOSOrganization nodes exist for relationship testing."""
    neo4j_session.run(
        """
        MERGE (o:WorkOSOrganization{id: $org_id})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $update_tag, o.name = $name
        """,
        org_id="org_01HXYZ1234567890ABCDEFGHIJ",
        name="Springfield Nuclear Power Plant",
        update_tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (o:WorkOSOrganization{id: $org_id})
        ON CREATE SET o.firstseen = timestamp()
        SET o.lastupdated = $update_tag, o.name = $name
        """,
        org_id="org_02HXYZ0987654321ZYXWVUTSRQ",
        name="Kwik-E-Mart",
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.workos.api_keys,
    "get",
    return_value=tests.data.workos.api_keys.WORKOS_API_KEYS,
)
def test_load_workos_api_keys(mock_api, neo4j_session):
    """
    Ensure that API keys actually get loaded.
    """
    # Arrange
    _ensure_local_neo4j_has_test_environment(neo4j_session)
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    client = MagicMock()
    org_ids = [
        "org_01HXYZ1234567890ABCDEFGHIJ",
        "org_02HXYZ0987654321ZYXWVUTSRQ",
    ]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKOS_CLIENT_ID": TEST_CLIENT_ID,
    }

    # Act
    cartography.intel.workos.api_keys.sync(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # Assert API keys exist
    expected_nodes = {
        ("api_key_01HXYZ1111111111AAAAAAAA", "Reactor Monitoring Key"),
        ("api_key_02HXYZ2222222222BBBBBBBB", "Squishee Machine Key"),
    }
    assert (
        check_nodes(neo4j_session, "WorkOSAPIKey", ["id", "name"])
        == expected_nodes
    )

    # Assert API keys are linked to the environment
    expected_env_rels = {
        ("api_key_01HXYZ1111111111AAAAAAAA", TEST_CLIENT_ID),
        ("api_key_02HXYZ2222222222BBBBBBBB", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSAPIKey",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_env_rels
    )

    # Assert API keys are linked to their owning organizations
    expected_org_rels = {
        ("api_key_01HXYZ1111111111AAAAAAAA", "org_01HXYZ1234567890ABCDEFGHIJ"),
        ("api_key_02HXYZ2222222222BBBBBBBB", "org_02HXYZ0987654321ZYXWVUTSRQ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSAPIKey",
            "id",
            "WorkOSOrganization",
            "id",
            "OWNS",
            rel_direction_right=False,
        )
        == expected_org_rels
    )
