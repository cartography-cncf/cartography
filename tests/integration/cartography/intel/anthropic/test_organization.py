from unittest.mock import patch

import requests

import cartography.intel.anthropic.organization
import tests.data.anthropic.organization
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"


def _ensure_local_neo4j_has_test_organization(neo4j_session):
    cartography.intel.anthropic.organization.load_organization(
        neo4j_session,
        tests.data.anthropic.organization.ANTHROPIC_ORGANIZATION,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.anthropic.organization,
    "get",
    return_value=tests.data.anthropic.organization.ANTHROPIC_ORGANIZATION,
)
def test_load_anthropic_organization(mock_api, neo4j_session):
    """
    Ensure that the organization gets loaded and its id is published for other syncs
    """
    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://api.anthropic.com/v1",
    }

    # Act
    org_id = cartography.intel.anthropic.organization.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
    )

    # Assert the org id is returned and published for the other syncs to scope on
    assert org_id == TEST_ORG_ID
    assert common_job_parameters["ORG_ID"] == TEST_ORG_ID

    # Assert Organization exists, with the name that only /organizations/me exposes
    assert check_nodes(neo4j_session, "AnthropicOrganization", ["id", "name"]) == {
        (TEST_ORG_ID, "Springfield Nuclear Power Plant"),
    }
