import json

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.endpoint_slices import cleanup
from cartography.intel.kubernetes.endpoint_slices import load_endpoint_slices
from cartography.intel.kubernetes.endpoint_slices import transform_endpoint_slices
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import load_pods
from cartography.intel.kubernetes.services import load_services
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.endpoint_slices import KUBERNETES_ENDPOINT_SLICES_RAW
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA
from tests.data.kubernetes.services import KUBERNETES_SERVICES_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def test_load_endpoint_slices_maps_services_to_ready_pods(neo4j_session):
    load_kubernetes_cluster(neo4j_session, KUBERNETES_CLUSTER_DATA, TEST_UPDATE_TAG)
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_1_NAMESPACES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_pods(
        neo4j_session,
        KUBERNETES_PODS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_services(
        neo4j_session,
        KUBERNETES_SERVICES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    transformed = transform_endpoint_slices(KUBERNETES_ENDPOINT_SLICES_RAW)
    load_endpoint_slices(
        neo4j_session,
        transformed,
        TEST_UPDATE_TAG,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )

    assert check_nodes(
        neo4j_session,
        "KubernetesEndpointSlice",
        ["name", "address_type"],
    ) == {("my-service-abc12", "IPv4")}
    assert neo4j_session.run(
        "MATCH (slice:KubernetesEndpointSlice {name: 'my-service-abc12'}) "
        "RETURN slice.port_numbers AS ports"
    ).single()["ports"] == [8080]
    assert json.loads(transformed[0]["endpoints"])[0]["ready"] is True
    assert check_rels(
        neo4j_session,
        "KubernetesEndpointSlice",
        "name",
        "KubernetesService",
        "name",
        "FOR_SERVICE",
        rel_direction_right=True,
    ) == {("my-service-abc12", "my-service")}
    assert check_rels(
        neo4j_session,
        "KubernetesEndpointSlice",
        "name",
        "KubernetesPod",
        "name",
        "TARGETS",
        rel_direction_right=True,
    ) == {("my-service-abc12", KUBERNETES_PODS_DATA[0]["name"])}

    transformed[0]["ready_pod_ids"] = []
    load_endpoint_slices(
        neo4j_session,
        transformed,
        TEST_UPDATE_TAG + 1,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    cleanup(
        neo4j_session,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG + 1,
            "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
        },
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesEndpointSlice",
            "name",
            "KubernetesPod",
            "name",
            "TARGETS",
            rel_direction_right=True,
        )
        == set()
    )

    load_endpoint_slices(
        neo4j_session,
        [],
        TEST_UPDATE_TAG + 2,
        KUBERNETES_CLUSTER_IDS[0],
        KUBERNETES_CLUSTER_NAMES[0],
    )
    cleanup(
        neo4j_session,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG + 2,
            "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
        },
    )
    assert check_nodes(neo4j_session, "KubernetesEndpointSlice", ["name"]) == set()
