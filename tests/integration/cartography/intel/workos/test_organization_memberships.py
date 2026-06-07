from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.organization_memberships
import tests.data.workos.organization_memberships
from tests.integration.cartography.intel.workos.test_organizations import (
    _ensure_local_neo4j_has_test_environment,
)
from tests.integration.cartography.intel.workos.test_organizations import (
    _ensure_local_neo4j_has_test_organizations,
)
from tests.integration.cartography.intel.workos.test_roles import (
    _ensure_local_neo4j_has_test_roles,
)
from tests.integration.cartography.intel.workos.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLIENT_ID = "client_1234567890abcdef"


@patch.object(
    cartography.intel.workos.organization_memberships,
    "get",
    return_value=tests.data.workos.organization_memberships.WORKOS_ORGANIZATION_MEMBERSHIPS,
)
def test_load_workos_organization_memberships(mock_api, neo4j_session):
    """
    Ensure that organization memberships actually get loaded
    """
    # Arrange
    _ensure_local_neo4j_has_test_environment(neo4j_session)
    _ensure_local_neo4j_has_test_organizations(neo4j_session)
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_roles(neo4j_session)
    client = MagicMock()
    org_ids = ["org_01HXYZ1234567890ABCDEFGHIJ"]
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKOS_CLIENT_ID": TEST_CLIENT_ID,
    }

    # Act
    cartography.intel.workos.organization_memberships.sync(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # Assert OrganizationMemberships exist
    expected_nodes = {
        ("om_01HXYZ1234567890ABCDEFGHIJ",),
        ("om_02HXYZ0987654321ZYXWVUTSRQ",),
    }
    assert (
        check_nodes(neo4j_session, "WorkOSOrganizationMembership", ["id"])
        == expected_nodes
    )

    # Assert memberships are linked to the environment
    expected_rels = {
        ("om_01HXYZ1234567890ABCDEFGHIJ", TEST_CLIENT_ID),
        ("om_02HXYZ0987654321ZYXWVUTSRQ", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSOrganizationMembership",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert memberships are linked to users
    expected_rels = {
        ("user_01HXYZ1234567890ABCDEFGHIJ", "om_01HXYZ1234567890ABCDEFGHIJ"),
        ("user_02HXYZ0987654321ZYXWVUTSRQ", "om_02HXYZ0987654321ZYXWVUTSRQ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSUser",
            "id",
            "WorkOSOrganizationMembership",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert memberships are linked to organizations
    expected_rels = {
        ("om_01HXYZ1234567890ABCDEFGHIJ", "org_01HXYZ1234567890ABCDEFGHIJ"),
        ("om_02HXYZ0987654321ZYXWVUTSRQ", "org_01HXYZ1234567890ABCDEFGHIJ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSOrganizationMembership",
            "id",
            "WorkOSOrganization",
            "id",
            "IN",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert memberships are linked to roles
    expected_rels = {
        ("om_01HXYZ1234567890ABCDEFGHIJ", "admin"),
        ("om_02HXYZ0987654321ZYXWVUTSRQ", "member"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSOrganizationMembership",
            "id",
            "WorkOSRole",
            "slug",
            "WITH_ROLE",
            rel_direction_right=True,
        )
        == expected_rels
    )
