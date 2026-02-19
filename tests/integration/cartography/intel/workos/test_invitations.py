from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.invitations
import tests.data.workos.invitations
from tests.integration.cartography.intel.workos.test_organizations import (
    _ensure_local_neo4j_has_test_environment,
)
from tests.integration.cartography.intel.workos.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.cartography.intel.workos.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLIENT_ID = "client_1234567890abcdef"


@patch.object(
    cartography.intel.workos.invitations,
    "get",
    return_value=tests.data.workos.invitations.WORKOS_INVITATIONS,
)
def test_load_workos_invitations(mock_api, neo4j_session):
    """
    Ensure that invitations actually get loaded
    """
    # Arrange
    _ensure_local_neo4j_has_test_environment(neo4j_session)
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    client = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKOS_CLIENT_ID": TEST_CLIENT_ID,
    }

    # Act
    cartography.intel.workos.invitations.sync(
        neo4j_session,
        client,
        common_job_parameters,
    )

    # Assert Invitations exist
    expected_nodes = {
        ("inv_01HXYZ1234567890ABCDEFGHIJ", "bsimpson@springfield.com"),
    }
    assert (
        check_nodes(neo4j_session, "WorkOSInvitation", ["id", "email"])
        == expected_nodes
    )

    # Assert invitations are linked to the environment
    expected_rels = {
        ("inv_01HXYZ1234567890ABCDEFGHIJ", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSInvitation",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert invitations are linked to organizations
    expected_rels = {
        ("inv_01HXYZ1234567890ABCDEFGHIJ", "org_01HXYZ1234567890ABCDEFGHIJ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSInvitation",
            "id",
            "WorkOSOrganization",
            "id",
            "FOR_ORGANIZATION",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert invitations are linked to inviter users
    expected_rels = {
        ("inv_01HXYZ1234567890ABCDEFGHIJ", "user_01HXYZ1234567890ABCDEFGHIJ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSInvitation",
            "id",
            "WorkOSUser",
            "id",
            "INVITED_BY",
            rel_direction_right=True,
        )
        == expected_rels
    )
