import copy
from types import SimpleNamespace

import cartography.intel.tailscale.devices
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.ingress import load_ingresses
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.pods import load_pods
from cartography.intel.kubernetes.pods import transform_pods
from cartography.intel.kubernetes.services import load_services
from cartography.intel.tailscale.devices import load_devices
from cartography.intel.tailscale.tailnets import load_tailnets
from cartography.util import run_scoped_analysis_job
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.tailscale_operator import TAILSCALE_OPERATOR_INGRESS_DATA
from tests.data.kubernetes.tailscale_operator import TAILSCALE_OPERATOR_NAMESPACES
from tests.data.kubernetes.tailscale_operator import TAILSCALE_OPERATOR_POD_DATA
from tests.data.kubernetes.tailscale_operator import TAILSCALE_OPERATOR_SERVICE_DATA
from tests.data.tailscale.operator import TAILSCALE_OPERATOR_DEVICES
from tests.data.tailscale.operator import TAILSCALE_OPERATOR_TAILNET
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG = "example.com"


def _load_kubernetes_tailscale_operator_fixture(neo4j_session) -> None:
    load_kubernetes_cluster(
        neo4j_session,
        KUBERNETES_CLUSTER_DATA,
        TEST_UPDATE_TAG,
    )
    load_namespaces(
        neo4j_session,
        TAILSCALE_OPERATOR_NAMESPACES,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_services(
        neo4j_session,
        TAILSCALE_OPERATOR_SERVICE_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_ingresses(
        neo4j_session,
        TAILSCALE_OPERATOR_INGRESS_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_pods(
        neo4j_session,
        TAILSCALE_OPERATOR_POD_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )


def _load_tailscale_api_fixture(neo4j_session) -> None:
    devices = copy.deepcopy(TAILSCALE_OPERATOR_DEVICES)
    cartography.intel.tailscale.devices.transform(devices)
    load_tailnets(
        neo4j_session,
        [TAILSCALE_OPERATOR_TAILNET],
        TEST_ORG,
        TEST_UPDATE_TAG,
    )
    load_devices(
        neo4j_session,
        devices,
        TEST_ORG,
        TEST_UPDATE_TAG,
    )


def test_tailscale_operator_proxy_pods_link_to_parent_kubernetes_resources(
    neo4j_session,
):
    _load_kubernetes_tailscale_operator_fixture(neo4j_session)

    assert check_nodes(
        neo4j_session,
        "KubernetesPod",
        [
            "name",
            "tailscale_managed",
            "tailscale_parent_resource_type",
            "tailscale_parent_resource_namespace",
            "tailscale_parent_resource_name",
        ],
    ) >= {
        ("operator-bbb7d9c75-hwmw7", False, None, None, None),
        ("ts-demo-app-nr7d8-0", True, "ingress", "demo-app", "demo-app"),
        (
            "ts-private-gateway-f-nx2j4-0",
            True,
            "svc",
            "gateway-system",
            "private-gateway",
        ),
    }

    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesIngress",
        "name",
        "TAILSCALE_PROXY_FOR",
        rel_direction_right=True,
    ) == {("ts-demo-app-nr7d8-0", "demo-app")}
    assert check_rels(
        neo4j_session,
        "KubernetesPod",
        "name",
        "KubernetesService",
        "name",
        "TAILSCALE_PROXY_FOR",
        rel_direction_right=True,
    ) == {("ts-private-gateway-f-nx2j4-0", "private-gateway")}


def test_tailscale_operator_dns_names_do_not_link_without_tailscale_devices(
    neo4j_session,
):
    _load_kubernetes_tailscale_operator_fixture(neo4j_session)

    assert (
        check_rels(
            neo4j_session,
            "KubernetesIngress",
            "name",
            "TailscaleDevice",
            "name",
            "USES_TAILSCALE_DEVICE",
            rel_direction_right=True,
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "KubernetesService",
            "name",
            "TailscaleDevice",
            "name",
            "USES_TAILSCALE_DEVICE",
            rel_direction_right=True,
        )
        == set()
    )


def test_tailscale_operator_dns_names_link_to_tailscale_devices(neo4j_session):
    _load_tailscale_api_fixture(neo4j_session)
    _load_kubernetes_tailscale_operator_fixture(neo4j_session)

    assert check_rels(
        neo4j_session,
        "KubernetesIngress",
        "name",
        "TailscaleDevice",
        "name",
        "USES_TAILSCALE_DEVICE",
        rel_direction_right=True,
    ) == {("demo-app", "demo-app-cluster-a.tailabc123.ts.net")}
    assert check_rels(
        neo4j_session,
        "KubernetesService",
        "name",
        "TailscaleDevice",
        "name",
        "USES_TAILSCALE_DEVICE",
        rel_direction_right=True,
    ) == {("private-gateway", "private-gateway.tailabc123.ts.net")}

    result = neo4j_session.run(
        """
        MATCH (:KubernetesIngress|KubernetesService)-[:USES_TAILSCALE_DEVICE]->(
            device:TailscaleDevice {name: 'demo-app-cluster-a.tail000000.ts.net'}
        )
        RETURN count(device) AS count
        """,
    ).single()
    assert result["count"] == 0


def test_tailscale_operator_dns_names_do_not_mark_resources_internet_exposed(
    neo4j_session,
):
    _load_tailscale_api_fixture(neo4j_session)
    _load_kubernetes_tailscale_operator_fixture(neo4j_session)

    run_scoped_analysis_job(
        "k8s_compute_asset_exposure.json",
        neo4j_session,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
        },
    )

    assert check_nodes(
        neo4j_session,
        "KubernetesService",
        ["name", "exposed_internet", "exposed_internet_type"],
    ) == {
        ("demo-app", None, None),
        ("private-gateway", None, None),
    }
    assert check_nodes(
        neo4j_session,
        "KubernetesPod",
        ["name", "exposed_internet", "exposed_internet_type"],
    ) == {
        ("operator-bbb7d9c75-hwmw7", None, None),
        ("ts-demo-app-nr7d8-0", None, None),
        ("ts-private-gateway-f-nx2j4-0", None, None),
    }


def test_transform_pods_extracts_tailscale_operator_parent_labels():
    raw_pod = SimpleNamespace(
        metadata=SimpleNamespace(
            uid="raw-tailscale-proxy-uid",
            name="ts-hello-world-dgqdc-0",
            namespace="tailscale",
            creation_timestamp=None,
            deletion_timestamp=None,
            labels={
                "tailscale.com/managed": "true",
                "tailscale.com/parent-resource": "hello-world",
                "tailscale.com/parent-resource-ns": "apps",
                "tailscale.com/parent-resource-type": "ingress",
            },
        ),
        spec=SimpleNamespace(
            containers=[],
            volumes=[],
            node_name="node-1",
            service_account_name="proxies",
            automount_service_account_token=None,
            host_pid=None,
            host_ipc=None,
            host_network=None,
            security_context=None,
        ),
        status=SimpleNamespace(phase="running", container_statuses=[]),
    )

    transformed = transform_pods([raw_pod], KUBERNETES_CLUSTER_NAMES[0])[0]

    assert transformed["tailscale_managed"] is True
    assert transformed["tailscale_parent_resource_type"] == "ingress"
    assert transformed["tailscale_parent_resource_namespace"] == "apps"
    assert transformed["tailscale_parent_resource_name"] == "hello-world"
    assert transformed["tailscale_parent_ingress_name"] == "hello-world"
    assert transformed["tailscale_parent_service_name"] is None
