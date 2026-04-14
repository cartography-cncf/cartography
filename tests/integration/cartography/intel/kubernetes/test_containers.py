from copy import deepcopy

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import load_containers
from cartography.intel.kubernetes.pods import load_pods
from tests.data.gcp.artifact_registry import MOCK_DOCKER_IMAGES
from tests.data.gcp.artifact_registry import MOCK_PLATFORM_IMAGES
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.pods import KUBERNETES_CONTAINER_DATA
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def test_container_has_image_rels(neo4j_session):
    parent_image = MOCK_DOCKER_IMAGES[0]
    child_image = MOCK_PLATFORM_IMAGES[1]
    child_container_image_uri = (
        f"{parent_image['uri'].rsplit('@', 1)[0]}@{child_image['digest']}"
    )

    neo4j_session.run(
        """
        MERGE (img:GCPArtifactRegistryContainerImage {id: $id})
        SET img.digest = $digest,
            img.uri = $uri,
            img.media_type = $media_type,
            img.lastupdated = $tag
        """,
        id=parent_image["name"],
        digest=parent_image["name"].split("@", 1)[1],
        uri=parent_image["uri"],
        media_type=parent_image["mediaType"],
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (img:GCPArtifactRegistryContainerImage {id: $id})
        SET img.digest = $digest,
            img.uri = $uri,
            img.media_type = $media_type,
            img.lastupdated = $tag
        """,
        id=f"{parent_image['name'].rsplit('@', 1)[0]}@{child_image['digest']}",
        digest=child_image["digest"],
        uri=child_container_image_uri,
        media_type=child_image["media_type"],
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (img:GCPArtifactRegistryPlatformImage {id: $id})
        SET img.digest = $digest,
            img.architecture = $architecture,
            img.os = $os,
            img.media_type = $media_type,
            img.parent_artifact_id = $parent_artifact_id,
            img.lastupdated = $tag
        """,
        id=child_image["id"],
        digest=child_image["digest"],
        architecture=child_image["architecture"],
        os=child_image["os"],
        media_type=child_image["media_type"],
        parent_artifact_id=child_image["parent_artifact_id"],
        tag=TEST_UPDATE_TAG,
    )

    containers = deepcopy(KUBERNETES_CONTAINER_DATA)
    pods = deepcopy(KUBERNETES_PODS_DATA)

    # This container declares the parent image index in spec, while runtime status resolves
    # to the child digest. HAS_IMAGE should follow the runtime digest uniformly.
    containers[0]["image"] = parent_image["uri"]
    containers[0][
        "status_image_id"
    ] = f"{parent_image['uri'].rsplit('@', 1)[0]}@{child_image['digest']}"
    containers[0]["status_image_sha"] = child_image["digest"]
    pods[0]["containers"] = [containers[0]]

    # This container declares the child platform manifest directly in spec. It should
    # resolve to the same runtime digest-backed image relationships.
    containers[1]["image"] = child_container_image_uri
    containers[1]["status_image_id"] = containers[1]["image"]
    containers[1]["status_image_sha"] = child_image["digest"]
    pods[1]["containers"] = [containers[1]]

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
        pods,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_containers(
        neo4j_session,
        containers,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    assert check_rels(
        neo4j_session,
        "KubernetesContainer",
        "name",
        "GCPArtifactRegistryContainerImage",
        "digest",
        "HAS_IMAGE",
    ) == {
        ("my-pod-container", child_image["digest"]),
        ("my-service-pod-container", child_image["digest"]),
    }

    assert check_rels(
        neo4j_session,
        "KubernetesContainer",
        "name",
        "GCPArtifactRegistryPlatformImage",
        "digest",
        "HAS_IMAGE",
    ) == {
        ("my-pod-container", child_image["digest"]),
        ("my-service-pod-container", child_image["digest"]),
    }
