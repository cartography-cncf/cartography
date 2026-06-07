from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.pagerduty.services
import tests.data.pagerduty.services
from tests.integration.cartography.intel.pagerduty.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.cartography.intel.pagerduty.test_vendors import (
    _ensure_local_neo4j_has_test_vendors,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_services(neo4j_session):
    services = cartography.intel.pagerduty.services.transform_services(
        tests.data.pagerduty.services.GET_SERVICES_DATA,
    )
    cartography.intel.pagerduty.services.load_service_data(
        neo4j_session,
        services,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.pagerduty.services,
    "get_services",
    return_value=tests.data.pagerduty.services.GET_SERVICES_DATA,
)
@patch.object(
    cartography.intel.pagerduty.services,
    "get_integrations",
    return_value=tests.data.pagerduty.services.GET_INTEGRATIONS_DATA,
)
def test_load_service_data(mock_integrations, mock_services, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    _ensure_local_neo4j_has_test_teams(neo4j_session)
    _ensure_local_neo4j_has_test_vendors(neo4j_session)

    # Act
    cartography.intel.pagerduty.services.sync_services(
        neo4j_session, TEST_UPDATE_TAG, api_session, common_job_parameters
    )

    # Assert PagerDutyService nodes exist
    expected_nodes = {("PIJ90N7", "My Application Service")}
    assert (
        check_nodes(neo4j_session, "PagerDutyService", ["id", "name"]) == expected_nodes
    )
    # Assert PagerDutyIntegration nodes exist
    expected_nodes = {("PE1U9CH", "Email")}
    assert (
        check_nodes(neo4j_session, "PagerDutyIntegration", ["id", "name"])
        == expected_nodes
    )
    # Assert PagerDutyService are linked to Teams
    expected_rels = {
        ("PIJ90N7", "PQ9K7I8"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyService",
            "id",
            "PagerDutyTeam",
            "id",
            "ASSOCIATED_WITH",
            rel_direction_right=False,
        )
        == expected_rels
    )
    # Assert PagerDutyIntegration are linked to Services
    expected_rels = {
        ("PIJ90N7", "PE1U9CH"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyService",
            "id",
            "PagerDutyIntegration",
            "id",
            "HAS_INTEGRATION",
            rel_direction_right=True,
        )
        == expected_rels
    )
    # Assert PagerDutyIntegration are linked to vendor
    expected_rels = {
        ("PZQ6AUS", "PE1U9CH"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyVendor",
            "id",
            "PagerDutyIntegration",
            "id",
            "HAS_VENDOR",
            rel_direction_right=False,
        )
        == expected_rels
    )
