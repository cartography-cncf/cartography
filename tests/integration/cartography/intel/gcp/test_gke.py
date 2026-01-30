import cartography.intel.gcp.gke
import tests.data.gcp.gke

TEST_PROJECT_NUMBER = "000000000000"
TEST_UPDATE_TAG = 123456789


def test_load_gke_clusters(neo4j_session):
    data = tests.data.gcp.gke.GKE_RESPONSE
    cartography.intel.gcp.gke.load_gke_clusters(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        # flake8: noqa
        "https://container.googleapis.com/v1/projects/test-cluster/locations/europe-west2/clusters/test-cluster",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GKECluster) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_gke_clusters_relationships(neo4j_session):
    # Create Test GCPProject
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: $PROJECT_NUMBER})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = $UPDATE_TAG
        """,
        PROJECT_NUMBER=TEST_PROJECT_NUMBER,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load Test GKE Clusters
    data = tests.data.gcp.gke.GKE_RESPONSE
    cartography.intel.gcp.gke.load_gke_clusters(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (
            TEST_PROJECT_NUMBER,
            "https://container.googleapis.com/v1/projects/test-cluster/locations/europe-west2/clusters/test-cluster",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GKECluster) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected
