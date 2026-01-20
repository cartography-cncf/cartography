from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j

import cartography.intel.gcp.gcf as gcf
import tests.data.gcp.gcf
from cartography.client.core.tx import load
from cartography.models.gcp.iam import GCPServiceAccountSchema
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "test-project"
TEST_UPDATE_TAG = 123456789


def _create_base_nodes(neo4j_session: neo4j.Session) -> None:
    """
    Create the GCPProject and GCPServiceAccount nodes ahead of time.
    """
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id: $PROJECT_ID})
        SET p.lastupdated = $UPDATE_TAG
        """,
        PROJECT_ID=TEST_PROJECT_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    sa1_email = "service-1@test-project.iam.gserviceaccount.com"
    sa2_email = "service-2@test-project.iam.gserviceaccount.com"
    sa_properties_1 = {
        "uniqueId": "1111",
        "id": "1111",
        "email": sa1_email,
        "projectId": TEST_PROJECT_ID,
    }
    sa_properties_2 = {
        "uniqueId": "2222",
        "id": "2222",
        "email": sa2_email,
        "projectId": TEST_PROJECT_ID,
    }
    load(
        neo4j_session,
        GCPServiceAccountSchema(),
        [sa_properties_1, sa_properties_2],
        lastupdated=TEST_UPDATE_TAG,
        projectId=TEST_PROJECT_ID,
    )


@patch("cartography.intel.gcp.gcf.get_gcp_cloud_functions")
def test_gcp_functions_load_and_relationships(
    mock_get_functions: MagicMock,
    neo4j_session: neo4j.Session,
) -> None:
    """
    Test that we can correctly load GCP Cloud Functions and their relationships.
    """
    # Arrange
    mock_get_functions.return_value = tests.data.gcp.gcf.GCF_RESPONSE["functions"]
    _create_base_nodes(neo4j_session)

    # Act
    gcf.sync(
        neo4j_session,
        None,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "projectId": TEST_PROJECT_ID},
    )

    # Assert: Test that the nodes exist
    expected_nodes = {
        ("projects/test-project/locations/us-central1/functions/function-1",),
        ("projects/test-project/locations/us-east1/functions/function-2",),
    }
    assert check_nodes(neo4j_session, "GCPCloudFunction", ["id"]) == expected_nodes

    # Assert: Test that the (GCPProject)-[:RESOURCE]->(GCPCloudFunction) relationships exist
    expected_rels = {
        (
            TEST_PROJECT_ID,
            "projects/test-project/locations/us-central1/functions/function-1",
        ),
        (
            TEST_PROJECT_ID,
            "projects/test-project/locations/us-east1/functions/function-2",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPCloudFunction",
            "id",
            "RESOURCE",
        )
        == expected_rels
    )

    # Assert: Test that the (GCPCloudFunction)-[:RUNS_AS]->(GCPServiceAccount) relationships exist
    expected_rels_runs_as = {
        (
            "projects/test-project/locations/us-central1/functions/function-1",
            "service-1@test-project.iam.gserviceaccount.com",
        ),
        (
            "projects/test-project/locations/us-east1/functions/function-2",
            "service-2@test-project.iam.gserviceaccount.com",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GCPCloudFunction",
            "id",
            "GCPServiceAccount",
            "email",
            "RUNS_AS",
        )
        == expected_rels_runs_as
    )
