from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.webhosting.hostings
from tests.data.scaleway.webhosting import SCALEWAY_WEBHOSTINGS
from tests.data.scaleway.webhosting import TEST_HOSTING_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.webhosting.hostings,
    "get",
    return_value=SCALEWAY_WEBHOSTINGS,
)
def test_load_scaleway_webhostings(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": TEST_ORG_ID}
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.webhosting.hostings.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "ScalewayWebHosting",
        ["id", "status", "region", "domain"],
    ) == {
        (TEST_HOSTING_ID, "ready", "fr-par", "example.com"),
    }
    assert check_rels(
        neo4j_session,
        "ScalewayWebHosting",
        "id",
        "ScalewayProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (TEST_HOSTING_ID, TEST_PROJECT_ID),
    }
