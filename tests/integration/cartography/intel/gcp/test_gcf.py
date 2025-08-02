import pytest
from unittest.mock import patch, MagicMock
import neo4j

import cartography.intel.gcp.gcf as gcf
from cartography.client.core.tx import load
from cartography.models.gcp.iam import GCPServiceAccountSchema

# --- Test Data (Mock GCP API Response) ---
GCP_FUNCTIONS_RESPONSE = {
    "functions": [
        {
            "name": "projects/test-project/locations/us-central1/functions/function-1",
            "displayName": "Function One",
            "state": "ACTIVE",
            "runtime": "python310",
            "entryPoint": "hello_world_http",
            "httpsTrigger": {
                "url": "https://us-central1-test-project.cloudfunctions.net/function-1",
            },
            "createTime": "2023-01-01T10:00:00Z",
            "updateTime": "2023-01-01T10:00:00Z",
            "serviceAccountEmail": "service-1@test-project.iam.gserviceaccount.com",
        },
        {
            "name": "projects/test-project/locations/us-east1/functions/function-2",
            "displayName": "Function Two",
            "state": "ACTIVE",
            "runtime": "nodejs16",
            "entryPoint": "handler_event",
            "eventTrigger": {
                "eventType": "google.cloud.pubsub.topic.v1.messagePublished",
                "resource": "projects/test-project/topics/my-topic",
            },
            "createTime": "2023-02-01T11:00:00Z",
            "updateTime": "2023-02-01T11:00:00Z",
            "serviceAccountEmail": "service-2@test-project.iam.gserviceaccount.com",
        },
    ],
}

@patch('cartography.intel.gcp.gcf.get_gcp_cloud_functions')
def test_gcp_functions_load_and_relationships(
    mock_get_functions: MagicMock,
    neo4j_session: neo4j.Session,
):
    """
    Test that we can correctly load GCP Cloud Functions and their relationships.
    """
    # Arrange: Configure the mock
    mock_get_functions.return_value = GCP_FUNCTIONS_RESPONSE["functions"]
    project_id = "test-project"
    update_tag = 123456789

    # Arrange: Create the parent GCPProject node
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id: $PROJECT_ID})
        SET p.lastupdated = $UPDATE_TAG
        """,
        PROJECT_ID=project_id,
        UPDATE_TAG=update_tag,
    )

    # Arrange: Pre-load the GCPServiceAccount nodes that the functions run as
    sa1_email = "service-1@test-project.iam.gserviceaccount.com"
    sa2_email = "service-2@test-project.iam.gserviceaccount.com"
    # NOTE: Our GCF model links to Service Accounts by their email, so we set the `id` here to be the email.
    sa_properties_1 = {"id": sa1_email, "email": sa1_email, "projectId": project_id}
    sa_properties_2 = {"id": sa2_email, "email": sa2_email, "projectId": project_id}
    load(
        neo4j_session,
        GCPServiceAccountSchema(),
        [sa_properties_1, sa_properties_2],
        lastupdated=update_tag,
        projectId=project_id,
    )

    # Act: Call the main sync function
    gcf.sync(
        neo4j_session,
        None,  # The client is not used because the `get` function is patched
        project_id,
        update_tag,
        {"UPDATE_TAG": update_tag, "PROJECT_ID": project_id},
    )

    # Assert 1: Check that the Cloud Function nodes were created.
    expected_nodes = {
        "projects/test-project/locations/us-central1/functions/function-1",
        "projects/test-project/locations/us-east1/functions/function-2",
    }
    nodes = neo4j_session.run("MATCH (n:GCPCloudFunction) RETURN n.id")
    actual_nodes = {n['n.id'] for n in nodes}
    assert actual_nodes == expected_nodes

    # Assert 2: Check for the relationship to the project.
    # The relationship is (GCPProject)-[:RESOURCE]->(GCPCloudFunction)
    rels_to_project = neo4j_session.run(
        """
        MATCH (p:GCPProject{id:$PROJECT_ID})-[:RESOURCE]->(f:GCPCloudFunction)
        RETURN count(f) AS rel_count
        """,
        PROJECT_ID=project_id,
    )
    assert rels_to_project.single()['rel_count'] == 2

    # Assert 3: Check for the relationship to the service account.
    # The relationship is (GCPCloudFunction)-[:RUNS_AS]->(GCPServiceAccount)
    rels_to_sa = neo4j_session.run(
        """
        MATCH (f:GCPCloudFunction)-[:RUNS_AS]->(sa:GCPServiceAccount)
        WHERE f.project_id = $PROJECT_ID
        RETURN count(sa) as rel_count
        """,
        PROJECT_ID=project_id,
    )
    assert rels_to_sa.single()['rel_count'] == 2