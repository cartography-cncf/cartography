from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.roles
import tests.data.workos.roles
from tests.integration.cartography.intel.workos.test_organizations import (
    _ensure_local_neo4j_has_test_environment,
)
from tests.integration.cartography.intel.workos.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLIENT_ID = "client_1234567890abcdef"


def _ensure_local_neo4j_has_test_roles(neo4j_session):
    # Transform expects a dict mapping org_id to list of roles
    roles_by_org = {
        "org_01HXYZ1234567890ABCDEFGHIJ": tests.data.workos.roles.WORKOS_ROLES
    }
    transformed_roles = cartography.intel.workos.roles.transform(roles_by_org)
    cartography.intel.workos.roles.load_roles(
        neo4j_session,
        transformed_roles,
        TEST_CLIENT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.workos.roles,
    "get",
    return_value=tests.data.workos.roles.WORKOS_ROLES,
)
def test_load_workos_roles(mock_api, neo4j_session):
    """
    Ensure that roles actually get loaded
    """
    # Arrange
    _ensure_local_neo4j_has_test_environment(neo4j_session)
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    client = MagicMock()
    org_ids = ["org_01HXYZ1234567890ABCDEFGHIJ"]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKOS_CLIENT_ID": TEST_CLIENT_ID,
    }

    # Act
    cartography.intel.workos.roles.sync(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # Assert Roles exist
    expected_nodes = {
        ("role_01HXYZ1234567890ABCDEFGHIJ", "admin"),
        ("role_02HXYZ0987654321ZYXWVUTSRQ", "member"),
    }
    assert check_nodes(neo4j_session, "WorkOSRole", ["id", "slug"]) == expected_nodes

    # Assert roles are linked to the environment
    expected_rels = {
        ("role_01HXYZ1234567890ABCDEFGHIJ", TEST_CLIENT_ID),
        ("role_02HXYZ0987654321ZYXWVUTSRQ", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSRole",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert roles are linked to the organization
    expected_rels = {
        ("role_01HXYZ1234567890ABCDEFGHIJ", "org_01HXYZ1234567890ABCDEFGHIJ"),
        ("role_02HXYZ0987654321ZYXWVUTSRQ", "org_01HXYZ1234567890ABCDEFGHIJ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSRole",
            "id",
            "WorkOSOrganization",
            "id",
            "HAS",
            rel_direction_right=False,
        )
        == expected_rels
    )
