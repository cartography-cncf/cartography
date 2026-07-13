from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.applications
import tests.data.workos.applications
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
    """Ensure the WorkOSOrganization node exists for relationship testing."""
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
    cartography.intel.workos.applications,
    "get_applications",
    return_value=tests.data.workos.applications.WORKOS_APPLICATIONS,
)
def test_load_workos_applications(mock_api, neo4j_session):
    """
    Ensure that Connect applications actually get loaded.
    """
    # Arrange
    _ensure_local_neo4j_has_test_environment(neo4j_session)
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKOS_CLIENT_ID": TEST_CLIENT_ID,
    }

    # Act
    cartography.intel.workos.applications.sync(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Assert applications exist
    expected_nodes = {
        ("conn_app_01HXYZ1111111111AAAAAAAA", "Springfield Portal", None),
        ("conn_app_02HXYZ2222222222BBBBBBBB", "Squishee Inventory Sync", "m2m"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "WorkOSApplication",
            ["id", "name", "application_type"],
        )
        == expected_nodes
    )

    # Assert applications are linked to the environment
    expected_env_rels = {
        ("conn_app_01HXYZ1111111111AAAAAAAA", TEST_CLIENT_ID),
        ("conn_app_02HXYZ2222222222BBBBBBBB", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSApplication",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_env_rels
    )

    # Assert M2M application is linked to its organization (OAuth app has no org)
    expected_org_rels = {
        ("conn_app_02HXYZ2222222222BBBBBBBB", "org_02HXYZ0987654321ZYXWVUTSRQ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSApplication",
            "id",
            "WorkOSOrganization",
            "id",
            "BELONGS_TO",
            rel_direction_right=True,
        )
        == expected_org_rels
    )
