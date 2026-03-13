import cartography.intel.gcp.gke
import cartography.intel.gcp.labels
import tests.data.gcp.gke
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_NUMBER = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "https://container.googleapis.com/v1/projects/test-cluster/locations/europe-west2/clusters/test-cluster"


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


def test_gke_cluster_labels(neo4j_session):
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

    # Load GKE clusters
    data = tests.data.gcp.gke.GKE_RESPONSE
    cartography.intel.gcp.gke.load_gke_clusters(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Sync labels from transformed cluster data
    clusters = cartography.intel.gcp.gke.transform_gke_clusters(data)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_NUMBER,
    }
    cartography.intel.gcp.labels.sync_labels(
        neo4j_session,
        clusters,
        "gke_cluster",
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Verify GCPLabel nodes were created
    assert check_nodes(neo4j_session, "GCPLabel", ["key", "value"]) >= {
        ("env", "dev"),
        ("team", "platform"),
    }

    # Verify LABELED relationships from GKECluster to GCPLabel
    assert check_rels(
        neo4j_session,
        "GKECluster",
        "id",
        "GCPLabel",
        "key",
        "LABELED",
        rel_direction_right=True,
    ) == {
        (TEST_CLUSTER_ID, "env"),
        (TEST_CLUSTER_ID, "team"),
    }
