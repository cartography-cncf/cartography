from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.security_center as security_center
from tests.data.azure.security_center import MOCK_ASSESSMENTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.security_center.get_assessments")
def test_sync_assessments(mock_get, neo4j_session):
    """
    Test that we can correctly sync Azure Security Assessment data and relationships.
    """
    # Arrange
    mock_get.return_value = MOCK_ASSESSMENTS

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    security_center.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes
    expected_nodes = {
        (
            "/subscriptions/00-00-00-00/providers/Microsoft.Security/assessments/00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000001",
        ),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureSecurityAssessment", ["id", "name"])
    assert actual_nodes == expected_nodes

    # Assert Relationships
    expected_rels = {
        (
            TEST_SUBSCRIPTION_ID,
            "/subscriptions/00-00-00-00/providers/Microsoft.Security/assessments/00000000-0000-0000-0000-000000000001",
        ),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureSecurityAssessment",
        "id",
        "HAS_ASSESSMENT",
    )
    assert actual_rels == expected_rels
