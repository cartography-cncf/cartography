import json

import pytest

from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.ingress import load_ingresses
from cartography.intel.kubernetes.namespaces import load_namespaces
from cartography.intel.kubernetes.services import load_services
from cartography.util import run_scoped_analysis_job
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_DATA
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_IDS
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA

TEST_UPDATE_TAG = 123456789
TAILNET_SUFFIX = "tailxxxx.ts.net"
OTHER_TAILNET_SUFFIX = "tailyyyy.ts.net"


def _common_job_parameters() -> dict[str, int | str]:
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": KUBERNETES_CLUSTER_IDS[0],
    }


def _tailscale_ingress_data() -> list[dict]:
    return [
        {
            "uid": "ts-ingress-uid",
            "name": "ts-ingress",
            "namespace": "my-namespace",
            "creation_timestamp": 1234567890,
            "deletion_timestamp": None,
            "annotations": json.dumps({}),
            "ingress_class_name": "nginx",
            "rules": json.dumps([]),
            "default_backend": json.dumps({}),
            "host_names": [f"node.{TAILNET_SUFFIX}"],
            "target_services": ["ts-service"],
            "ingress_group_name": None,
            "load_balancer_dns_names": [f"app.{TAILNET_SUFFIX}"],
        },
    ]


def _tailscale_service_data() -> list[dict]:
    load_balancer_dns_names = [
        f"app.{TAILNET_SUFFIX}",
        f"node.{TAILNET_SUFFIX}",
    ]
    return [
        {
            "uid": "ts-service-uid",
            "name": "ts-service",
            "qualified_name": "my-namespace/ts-service",
            "creation_timestamp": 1234567890,
            "deletion_timestamp": None,
            "namespace": "my-namespace",
            "selector": json.dumps({}),
            "type": "LoadBalancer",
            "cluster_ip": "10.0.0.1",
            "load_balancer_ip": None,
            "load_balancer_ingress": json.dumps(
                [{"hostname": hostname} for hostname in load_balancer_dns_names],
            ),
            "load_balancer_dns_names": load_balancer_dns_names,
            "pod_ids": [],
        },
    ]


@pytest.fixture
def _create_test_cluster(neo4j_session):
    load_kubernetes_cluster(
        neo4j_session,
        KUBERNETES_CLUSTER_DATA,
        TEST_UPDATE_TAG,
    )
    load_namespaces(
        neo4j_session,
        KUBERNETES_CLUSTER_1_NAMESPACES_DATA,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    yield

    neo4j_session.run(
        """
        MATCH (n)
        WHERE n:KubernetesIngress
           OR n:KubernetesService
           OR n:KubernetesNamespace
           OR n:KubernetesCluster
           OR n:TailscaleTailnet
           OR n:TailscaleService
           OR n:TailscaleDevice
        DETACH DELETE n
        """,
    )


def _load_tailscale_endpoints(neo4j_session) -> None:
    neo4j_session.run(
        """
        MERGE (tailnet:TailscaleTailnet{id: 'simpson.corp'})
        SET tailnet.lastupdated = $update_tag
        MERGE (other_tailnet:TailscaleTailnet{id: 'flanders.corp'})
        SET other_tailnet.lastupdated = $update_tag
        MERGE (svc:TailscaleService{id: 'svc:app'})
        SET svc.name = 'app', svc.lastupdated = $update_tag
        MERGE (tailnet)-[:RESOURCE]->(svc)
        MERGE (device:TailscaleDevice{id: 'node-1'})
        SET device.name = $device_name,
            device.hostname = 'node',
            device.lastupdated = $update_tag
        MERGE (tailnet)-[:RESOURCE]->(device)
        MERGE (other_device:TailscaleDevice{id: 'node-2'})
        SET other_device.name = $other_device_name,
            other_device.hostname = 'node',
            other_device.lastupdated = $update_tag
        MERGE (other_tailnet)-[:RESOURCE]->(other_device)
        """,
        update_tag=TEST_UPDATE_TAG,
        device_name=f"node.{TAILNET_SUFFIX}",
        other_device_name=f"node.{OTHER_TAILNET_SUFFIX}",
    )


def _run_tailscale_linking(neo4j_session) -> None:
    run_scoped_analysis_job(
        "k8s_tailscale_endpoint_linking.json",
        neo4j_session,
        _common_job_parameters(),
    )


def test_kubernetes_ingress_and_service_link_to_tailscale_endpoints(
    neo4j_session,
    _create_test_cluster,
):
    _load_tailscale_endpoints(neo4j_session)
    load_services(
        neo4j_session,
        _tailscale_service_data(),
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_ingresses(
        neo4j_session,
        _tailscale_ingress_data(),
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    _run_tailscale_linking(neo4j_session)

    result = neo4j_session.run(
        """
        MATCH (c:KubernetesCluster {name: $cluster})-[:RESOURCE]->(ing:KubernetesIngress)
        MATCH (ing)-[r:USES_TAILSCALE_SERVICE|USES_TAILSCALE_DEVICE]->(ts)
        RETURN ing.name AS ingress_name,
               ing.namespace AS namespace,
               type(r) AS rel_type,
               ts.name AS tailscale_name,
               r.matched_hostname AS matched_hostname
        """,
        cluster=KUBERNETES_CLUSTER_NAMES[0],
    )
    assert {
        (
            record["ingress_name"],
            record["namespace"],
            record["rel_type"],
            record["tailscale_name"],
            record["matched_hostname"],
        )
        for record in result
    } == {
        (
            "ts-ingress",
            "my-namespace",
            "USES_TAILSCALE_SERVICE",
            "app",
            f"app.{TAILNET_SUFFIX}",
        ),
        (
            "ts-ingress",
            "my-namespace",
            "USES_TAILSCALE_DEVICE",
            f"node.{TAILNET_SUFFIX}",
            f"node.{TAILNET_SUFFIX}",
        ),
    }

    result = neo4j_session.run(
        """
        MATCH (k8ssvc:KubernetesService {name: 'ts-service'})
        MATCH (k8ssvc)-[r:USES_TAILSCALE_SERVICE|USES_TAILSCALE_DEVICE]->(ts)
        RETURN type(r) AS rel_type,
               ts.name AS tailscale_name,
               r.matched_hostname AS matched_hostname,
               r.match_type AS match_type,
               r.source_field AS source_field
        """,
    )
    assert {
        (
            record["rel_type"],
            record["tailscale_name"],
            record["matched_hostname"],
            record["match_type"],
            record["source_field"],
        )
        for record in result
    } == {
        (
            "USES_TAILSCALE_SERVICE",
            "app",
            f"app.{TAILNET_SUFFIX}",
            "service_name",
            "service.load_balancer_dns_names",
        ),
        (
            "USES_TAILSCALE_DEVICE",
            f"node.{TAILNET_SUFFIX}",
            f"node.{TAILNET_SUFFIX}",
            "exact_device_fqdn",
            "service.load_balancer_dns_names",
        ),
    }

    other_tailnet_result = neo4j_session.run(
        """
        MATCH (:KubernetesIngress|KubernetesService)-[:USES_TAILSCALE_DEVICE]->(
            other_device:TailscaleDevice {name: $other_device_name}
        )
        RETURN count(other_device) AS count
        """,
        other_device_name=f"node.{OTHER_TAILNET_SUFFIX}",
    ).single()
    assert other_tailnet_result["count"] == 0


def test_kubernetes_tailscale_endpoint_linking_does_not_link_without_tailscale_nodes(
    neo4j_session,
    _create_test_cluster,
):
    load_services(
        neo4j_session,
        _tailscale_service_data(),
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )
    load_ingresses(
        neo4j_session,
        _tailscale_ingress_data(),
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    _run_tailscale_linking(neo4j_session)

    result = neo4j_session.run(
        """
        MATCH (:KubernetesIngress|KubernetesService)-[
            r:USES_TAILSCALE_SERVICE|USES_TAILSCALE_DEVICE
        ]->()
        RETURN count(r) AS count
        """,
    ).single()
    assert result["count"] == 0


def test_kubernetes_service_tailscale_linking_uses_load_balancer_ingress_json_fallback(
    neo4j_session,
    _create_test_cluster,
):
    _load_tailscale_endpoints(neo4j_session)
    service_data = _tailscale_service_data()
    service_data[0]["load_balancer_dns_names"] = []
    load_services(
        neo4j_session,
        service_data,
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    _run_tailscale_linking(neo4j_session)

    result = neo4j_session.run(
        """
        MATCH (:KubernetesService {name: 'ts-service'})-[r:USES_TAILSCALE_SERVICE]->(
            :TailscaleService {name: 'app'}
        )
        RETURN r.matched_hostname AS matched_hostname,
               r.source_field AS source_field
        """,
    ).single()
    assert result["matched_hostname"] == f"app.{TAILNET_SUFFIX}"
    assert result["source_field"] == "service.load_balancer_ingress.hostname"


def test_tailscale_endpoint_links_do_not_mark_kubernetes_resources_internet_exposed(
    neo4j_session,
    _create_test_cluster,
):
    _load_tailscale_endpoints(neo4j_session)
    load_services(
        neo4j_session,
        _tailscale_service_data(),
        update_tag=TEST_UPDATE_TAG,
        cluster_id=KUBERNETES_CLUSTER_IDS[0],
        cluster_name=KUBERNETES_CLUSTER_NAMES[0],
    )

    _run_tailscale_linking(neo4j_session)
    run_scoped_analysis_job(
        "k8s_compute_asset_exposure.json",
        neo4j_session,
        _common_job_parameters(),
    )

    result = neo4j_session.run(
        """
        MATCH (svc:KubernetesService {name: 'ts-service'})
        RETURN svc.exposed_internet AS exposed_internet
        """,
    ).single()
    assert result["exposed_internet"] is None
