from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.salesforce.organization
import tests.data.salesforce.data as test_data
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_organization(neo4j_session):
    org = cartography.intel.salesforce.organization.transform(
        dict(test_data.SALESFORCE_ORGANIZATION)
    )
    cartography.intel.salesforce.organization.load_organization(
        neo4j_session, org, TEST_UPDATE_TAG
    )
    return org


@patch.object(
    cartography.intel.salesforce.organization,
    "get",
    return_value=dict(test_data.SALESFORCE_ORGANIZATION),
)
def test_sync_salesforce_organization(mock_get, neo4j_session):
    # Arrange
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Act
    cartography.intel.salesforce.organization.sync(
        neo4j_session, Mock(), common_job_parameters
    )

    # Assert the organization node exists with the Tenant label
    assert check_nodes(neo4j_session, "SalesforceOrganization", ["id", "name"]) == {
        (test_data.ORG_ID, "Simpson Corp"),
    }
    assert check_nodes(neo4j_session, "Tenant", ["id"]) == {(test_data.ORG_ID,)}
