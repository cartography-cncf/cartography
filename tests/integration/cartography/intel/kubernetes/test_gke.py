from copy import deepcopy
from unittest.mock import MagicMock

import pytest

from cartography.intel.gcp.gke import sync_gke_clusters
from cartography.intel.gcp.policy_bindings import load_bindings
from cartography.intel.kubernetes.gke import sync
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

PROJECT = "example-project"
RESOURCE = f"projects/{PROJECT}/locations/us-central1/clusters/example"
CLOUD_ID = "https://container.googleapis.com/v1/" + RESOURCE
POOL = f"projects/111122223333/locations/global/workloadIdentityPools/{PROJECT}.svc.id.goog"
NETWORK = f"projects/{PROJECT}/global/networks/example"
EMAIL = f"workload@{PROJECT}.iam.gserviceaccount.com"
CLUSTER = {
    "name": "example",
    "selfLink": CLOUD_ID,
    "resource_name": RESOURCE,
    "networkConfig": {"network": NETWORK},
    "workloadIdentityConfig": {"workloadPool": f"{PROJECT}.svc.id.goog"},
    "nodePools": [
        {
            "name": "pool",
            "config": {
                "serviceAccount": EMAIL,
                "workloadMetadataConfig": {"mode": "GKE_METADATA"},
            },
        }
    ],
}


@pytest.fixture
def seeded(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        "CREATE (:GCPProject {id: $project}), (:GCPServiceAccount {id: 'gsa', email: $email}), (:GCPWorkloadIdentityPool {id: $pool, pool_id: $pool_name, project_id: $project})",
        project=PROJECT,
        email=EMAIL,
        pool=POOL,
        pool_name=f"{PROJECT}.svc.id.goog",
    )
    api = MagicMock()
    api.projects.return_value.locations.return_value.clusters.return_value.list.return_value.execute.return_value = {
        "clusters": [deepcopy(CLUSTER)]
    }
    sync_gke_clusters(
        neo4j_session, api, PROJECT, 1, {"PROJECT_ID": PROJECT, "UPDATE_TAG": 1}
    )
    neo4j_session.run(
        "CREATE (c:KubernetesCluster {id: 'cluster'}), (other:KubernetesCluster {id: 'other'}), (recreated:KubernetesCluster {id: 'recreated'}) WITH c CREATE (c)-[:RESOURCE]->(:KubernetesNode {id: 'node', gke_node_pool: 'pool', lastupdated: 1})"
    )
    neo4j_session.run(
        "MATCH (c:KubernetesCluster {id: 'cluster'}) UNWIND ['direct', 'linked', 'annotation-only'] AS name CREATE (c)-[:RESOURCE]->(s:KubernetesServiceAccount {id: name, name: name, namespace: 'ns', uid: name + '-uid', lastupdated: 1}) SET s.gcp_service_account = CASE WHEN name <> 'direct' THEN $email ELSE null END",
        email=EMAIL,
    )
    load_bindings(
        neo4j_session,
        [
            {
                "id": "direct-binding",
                "role": "roles/storage.objectViewer",
                "resource": "//storage.googleapis.com/buckets/example-bucket",
                "raw_members": [
                    f"principal://iam.googleapis.com/{POOL}/subject/ns/ns/sa/direct"
                ],
                "wif_pools": [POOL],
                "has_condition": False,
            },
            {
                "id": "impersonation-binding",
                "role": "roles/iam.workloadIdentityUser",
                "resource": f"//iam.googleapis.com/projects/{PROJECT}/serviceAccounts/{EMAIL}",
                "raw_members": [f"serviceAccount:{PROJECT}.svc.id.goog[ns/linked]"],
                "has_condition": False,
            },
        ],
        PROJECT,
        1,
    )
    neo4j_session.run(
        "MATCH (s:KubernetesServiceAccount {id: 'annotation-only'}), (g:GCPServiceAccount) CREATE (s)-[:WORKLOAD_IDENTITY_BINDING {lastupdated: 0}]->(g)"
    )
    neo4j_session.run(
        "MATCH (c:KubernetesCluster {id: 'cluster'}) CREATE (c)-[:RESOURCE]->(:KubernetesService {id: 'svc', load_balancer_ips: ['10.0.0.2'], lastupdated: 1}), (c)-[:RESOURCE]->(:KubernetesIngress {id: 'ing', load_balancer_ips: ['10.0.0.2'], lastupdated: 1}), (c)-[:RESOURCE]->(:KubernetesGateway {id: 'gateway', load_balancer_ips: ['10.0.0.2'], lastupdated: 1}), (:GCPForwardingRule {id: 'lb', ip_address: '10.0.0.2', project_id: $project, network: $network, load_balancing_scheme: 'INTERNAL'})",
        project=PROJECT,
        network=NETWORK,
    )
    return neo4j_session, api


def test_gke_bridge_and_annotation_evidence(seeded):
    # Arrange
    session, _ = seeded
    # Act
    sync(session, CLUSTER, "cluster", 1)
    # Assert
    assert check_nodes(session, "GKENodePool", ["id", "workload_metadata_mode"]) == {
        (RESOURCE + "/nodePools/pool", "GKE_METADATA")
    }
    assert check_rels(
        session,
        "GKECluster",
        "id",
        "KubernetesCluster",
        "id",
        "MAPS_TO",
        rel_direction_right=True,
    ) == {(CLOUD_ID, "cluster")}
    assert check_rels(
        session,
        "KubernetesServiceAccount",
        "id",
        "GCPPolicyBinding",
        "id",
        "HAS_ALLOW_POLICY",
        rel_direction_right=True,
    ) == {("direct", "direct-binding"), ("linked", "impersonation-binding")}
    assert check_rels(
        session,
        "KubernetesServiceAccount",
        "id",
        "GCPServiceAccount",
        "email",
        "WORKLOAD_IDENTITY_BINDING",
        rel_direction_right=True,
    ) == {("linked", EMAIL)}
    assert check_rels(
        session,
        "KubernetesNode",
        "id",
        "GKENodePool",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {("node", RESOURCE + "/nodePools/pool")}
    for label, id_ in [
        ("KubernetesService", "svc"),
        ("KubernetesIngress", "ing"),
        ("KubernetesGateway", "gateway"),
    ]:
        assert check_rels(
            session,
            label,
            "id",
            "GCPForwardingRule",
            "id",
            "USES_LOAD_BALANCER",
            rel_direction_right=True,
        ) == {(id_, "lb")}


def test_removed_grants_addresses_and_cluster_recreation_cleanup(seeded):
    # Arrange
    session, _ = seeded
    sync(session, CLUSTER, "cluster", 1)
    session.run("MATCH (b:GCPPolicyBinding) SET b.raw_members = [], b.lastupdated = 2")
    session.run(
        "MATCH (:KubernetesCluster {id: 'cluster'})-[:RESOURCE]->(n) SET n.lastupdated = 2, n.load_balancer_ips = []"
    )
    session.run(
        "MATCH (c:KubernetesCluster {id: 'other'}), (lb:GCPForwardingRule) CREATE (c)-[:RESOURCE]->(s:KubernetesService {id: 'other-svc'}), (s)-[:USES_LOAD_BALANCER {_sub_resource_label: 'KubernetesCluster', _sub_resource_id: 'other', lastupdated: 1}]->(lb)"
    )
    # Act
    sync(session, CLUSTER, "cluster", 2)
    sync(session, CLUSTER, "recreated", 2)
    # Assert
    assert check_rels(
        session,
        "GKECluster",
        "id",
        "KubernetesCluster",
        "id",
        "MAPS_TO",
        rel_direction_right=True,
    ) == {(CLOUD_ID, "recreated")}
    assert (
        check_rels(
            session,
            "KubernetesServiceAccount",
            "id",
            "GCPServiceAccount",
            "email",
            "WORKLOAD_IDENTITY_BINDING",
            rel_direction_right=True,
        )
        == set()
    )
    assert check_rels(
        session,
        "KubernetesService",
        "id",
        "GCPForwardingRule",
        "id",
        "USES_LOAD_BALANCER",
        rel_direction_right=True,
    ) == {("other-svc", "lb")}


def test_gateway_denied_preserves_links(seeded):
    # Arrange
    session, _ = seeded
    sync(session, CLUSTER, "cluster", 1)
    # Act
    sync(session, CLUSTER, "cluster", 2, gateway_complete=False)
    # Assert
    assert check_rels(
        session,
        "KubernetesGateway",
        "id",
        "GCPForwardingRule",
        "id",
        "USES_LOAD_BALANCER",
        rel_direction_right=True,
    ) == {("gateway", "lb")}


def test_cloud_incomplete_preserves_but_empty_cleans(seeded):
    # Arrange
    session, api = seeded
    api.projects.return_value.locations.return_value.clusters.return_value.list.return_value.execute.return_value = {
        "clusters": [],
        "missingZones": ["us-central1-a"],
    }
    # Act and assert
    with pytest.raises(RuntimeError):
        sync_gke_clusters(
            session, api, PROJECT, 2, {"PROJECT_ID": PROJECT, "UPDATE_TAG": 2}
        )
    assert check_nodes(session, "GKECluster", ["id"]) == {(CLOUD_ID,)}
    # Arrange
    api.projects.return_value.locations.return_value.clusters.return_value.list.return_value.execute.return_value = (
        {}
    )
    # Act
    sync_gke_clusters(
        session, api, PROJECT, 3, {"PROJECT_ID": PROJECT, "UPDATE_TAG": 3}
    )
    # Assert
    assert check_nodes(session, "GKECluster", ["id"]) == set()
    assert check_nodes(session, "GKENodePool", ["id"]) == set()


@pytest.mark.parametrize(
    "entry", ["KubernetesService", "KubernetesIngress", "KubernetesGateway"]
)
def test_gcp_load_balancer_exposure_paths_and_cleanup(seeded, entry):
    # Arrange
    from cartography.analysis.kubernetes.analysis import K8S_COMPUTE_ASSET_EXPOSURE_JOBS
    from cartography.analysis.kubernetes.analysis import K8S_LB_EXPOSURE_JOBS
    from cartography.util import run_typed_analysis_job

    session, _ = seeded
    session.run(
        "MATCH (lb:GCPForwardingRule) SET lb:LoadBalancer, lb.exposed_internet = true"
    )
    session.run(
        "MATCH (c:KubernetesCluster {id: 'cluster'}), (s:KubernetesService {id: 'svc'}) CREATE (c)-[:RESOURCE]->(p:KubernetesPod {id: 'pod'}), (p)-[:CONTAINS]->(:KubernetesContainer {id: 'container'}), (s)-[:TARGETS]->(p)"
    )
    session.run(
        "MATCH (i:KubernetesIngress), (s:KubernetesService {id: 'svc'}), (g:KubernetesGateway), (c:KubernetesCluster {id: 'cluster'}) CREATE (i)-[:TARGETS]->(s), (g)-[:ROUTES]->(r:KubernetesHTTPRoute {id: 'route'}), (c)-[:RESOURCE]->(r), (r)-[:TARGETS]->(s)"
    )
    sync(session, CLUSTER, "cluster", 1)
    session.run(
        f"MATCH (s)-[r:USES_LOAD_BALANCER]->(:GCPForwardingRule) WHERE NOT s:{entry} DELETE r"
    )
    jobs = (*K8S_COMPUTE_ASSET_EXPOSURE_JOBS, *K8S_LB_EXPOSURE_JOBS)
    # Act
    for job in jobs:
        run_typed_analysis_job(job, session, {"UPDATE_TAG": 1, "CLUSTER_ID": "cluster"})
    # Assert
    assert check_rels(
        session,
        "GCPForwardingRule",
        "id",
        "KubernetesPod",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {("lb", "pod")}
    assert check_rels(
        session,
        "GCPForwardingRule",
        "id",
        "KubernetesContainer",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {("lb", "container")}
    # Arrange: internal / no longer exposed must remove derived exposure on the next tag.
    session.run("MATCH (lb:GCPForwardingRule) SET lb.exposed_internet = false")
    # Act
    for job in jobs:
        run_typed_analysis_job(job, session, {"UPDATE_TAG": 2, "CLUSTER_ID": "cluster"})
    # Assert
    assert (
        check_rels(
            session,
            "GCPForwardingRule",
            "id",
            "KubernetesPod",
            "id",
            "EXPOSE",
            rel_direction_right=True,
        )
        == set()
    )
    assert (
        session.run(
            "MATCH (p:KubernetesPod {id: 'pod'}) RETURN coalesce(p.exposed_internet, false) AS exposed"
        ).single()["exposed"]
        is False
    )
