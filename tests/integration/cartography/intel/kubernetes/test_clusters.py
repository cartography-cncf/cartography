# from cartography.intel.kubernetes.clusters import cleanup
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def test_load_clusters(neo4j_session):
    # Arrange
    data = KUBERNETES_CLUSTER_DATA

    # Act
    load_kubernetes_cluster(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        (KUBERNETES_CLUSTER_IDS[0],),
        (KUBERNETES_CLUSTER_IDS[1],),
    }
    assert check_nodes(neo4j_session, "KubernetesCluster", ["id"]) == expected_nodes
    assert check_nodes(
        neo4j_session,
        "KubernetesCluster",
        [
            "id",
            "api_server_url",
            "kubeconfig_tls_configuration_status",
            "kubeconfig_insecure_skip_tls_verify",
            "kubeconfig_has_certificate_authority_data",
            "kubeconfig_has_certificate_authority_file",
            "kubeconfig_has_client_certificate",
            "kubeconfig_has_client_key",
        ],
    ) == {
        (
            KUBERNETES_CLUSTER_IDS[0],
            "https://cluster-1.example.com",
            "valid_config",
            False,
            True,
            False,
            True,
            True,
        ),
        (
            KUBERNETES_CLUSTER_IDS[1],
            "https://cluster-2.example.com",
            "insecure_skip_tls",
            True,
            False,
            False,
            False,
            False,
        ),
    }


def test_kubernetes_cluster_maps_to_eks_cluster(neo4j_session):
    # Arrange: seed an EKSCluster whose arn matches cluster 1's external_id.
    # Cluster 2's external_id intentionally has no matching EKSCluster.
    cluster_1_arn = KUBERNETES_CLUSTER_DATA[0]["external_id"]
    neo4j_session.run(
        "MERGE (:EKSCluster {id: $arn, arn: $arn, lastupdated: $update_tag})",
        arn=cluster_1_arn,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    load_kubernetes_cluster(neo4j_session, KUBERNETES_CLUSTER_DATA, TEST_UPDATE_TAG)

    # Assert: MAPS_TO edge only for the cluster whose external_id matches.
    assert check_rels(
        neo4j_session,
        "EKSCluster",
        "arn",
        "KubernetesCluster",
        "id",
        "MAPS_TO",
    ) == {(cluster_1_arn, KUBERNETES_CLUSTER_IDS[0])}


# cleaning up the kubernetes cluster node is currently not supported
# def test_cluster_cleanup(neo4j_session):
#     # Arrange
#     data = KUBERNETES_CLUSTER_DATA
#     load_kubernetes_cluster(
#         neo4j_session,
#         data,
#         TEST_UPDATE_TAG,
#     )

#     # Act
#     common_job_parameters = {
#         "UPDATE_TAG": TEST_UPDATE_TAG + 1,
#     }
#     cleanup(
#         neo4j_session,
#         common_job_parameters,
#     )

#     # Assert
#     assert check_nodes(neo4j_session, "KubernetesCluster", ["id"]) == set()
