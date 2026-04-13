from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import load_containers
from cartography.intel.kubernetes.pods import load_pods
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.pods import KUBERNETES_CONTAINER_DATA
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_IMAGE_SHA = "my-image-sha"


def test_container_has_image_rels(neo4j_session):
    neo4j_session.run(
        "MERGE (img:ECRImage {id: $d, digest: $d}) SET img.lastupdated = $tag",
        d=TEST_IMAGE_SHA,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (img:GitLabContainerImage {id: $d, digest: $d}) SET img.lastupdated = $tag",
        d=TEST_IMAGE_SHA,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        "MERGE (img:GCPArtifactRegistryContainerImage {id: $d, digest: $d}) SET img.lastupdated = $tag",
        d=TEST_IMAGE_SHA,
        tag=TEST_UPDATE_TAG,
    )

    load_kubernetes_cluster(neo4j_session, KUBERNETES_CLUSTER_DATA, TEST_UPDATE_TAG)
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_1_NAMESPACES_DATA,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_NAMES[0],
        KUBERNETES_CLUSTER_IDS[0],
    )
    load_pods(
        neo4j_session,
        KUBERNETES_PODS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_containers(
        neo4j_session,
        KUBERNETES_CONTAINER_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    expected_rels = {
        ("my-pod-container", TEST_IMAGE_SHA),
        ("my-service-pod-container", TEST_IMAGE_SHA),
    }

    assert (
        check_rels(
            neo4j_session,
            "KubernetesContainer",
            "name",
            "ECRImage",
            "digest",
            "HAS_IMAGE",
        )
        == expected_rels
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesContainer",
            "name",
            "GitLabContainerImage",
            "digest",
            "HAS_IMAGE",
        )
        == expected_rels
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesContainer",
            "name",
            "GCPArtifactRegistryContainerImage",
            "digest",
            "HAS_IMAGE",
        )
        == expected_rels
    )
