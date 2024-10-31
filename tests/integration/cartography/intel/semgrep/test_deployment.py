from unittest.mock import patch

import cartography.intel.semgrep.deployment
import tests.data.semgrep.sca
from cartography.intel.semgrep.deployment import sync_deployment
from tests.integration.cartography.intel.semgrep.test_findings import TEST_UPDATE_TAG
from tests.integration.util import check_nodes


@patch.object(
    cartography.intel.semgrep.deployment,
    "get_deployment",
    return_value=tests.data.semgrep.sca.DEPLOYMENTS,
)
def test_sync_deployment(mock_get_deployment, neo4j_session):
    # Arrange
    semgrep_app_token = "your_semgrep_app_token"
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # # Act
    sync_deployment(neo4j_session, semgrep_app_token, TEST_UPDATE_TAG, common_job_parameters)

    # Assert

    assert check_nodes(
        neo4j_session,
        "SemgrepDeployment",
        ["id", "name", "slug"],
    ) == {("123456", "Org", "org")}
