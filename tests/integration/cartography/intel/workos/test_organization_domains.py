from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.workos.organization_domains
import tests.data.workos.organization_domains
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


@patch.object(
    cartography.intel.workos.organization_domains,
    "get",
    return_value=tests.data.workos.organization_domains.WORKOS_ORGANIZATION_DOMAINS,
)
def test_load_workos_organization_domains(mock_api, neo4j_session):
    """
    Ensure that organization domains actually get loaded
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
    cartography.intel.workos.organization_domains.sync(
        neo4j_session,
        client,
        org_ids,
        common_job_parameters,
    )

    # Assert OrganizationDomains exist
    expected_nodes = {
        ("orgdom_01HXYZ1234567890ABCDEFGHIJ", "springfield.com"),
    }
    assert (
        check_nodes(neo4j_session, "WorkOSOrganizationDomain", ["id", "domain"])
        == expected_nodes
    )

    # Assert organization domains are linked to the environment
    expected_rels = {
        ("orgdom_01HXYZ1234567890ABCDEFGHIJ", TEST_CLIENT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSOrganizationDomain",
            "id",
            "WorkOSEnvironment",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )

    # Assert organization domains are linked to organizations
    expected_rels = {
        ("orgdom_01HXYZ1234567890ABCDEFGHIJ", "org_01HXYZ1234567890ABCDEFGHIJ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "WorkOSOrganizationDomain",
            "id",
            "WorkOSOrganization",
            "id",
            "DOMAIN_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
