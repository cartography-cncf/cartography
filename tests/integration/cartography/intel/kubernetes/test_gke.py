from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import cartography.intel.kubernetes.nodes as nodes_module
from cartography.analysis.kubernetes.analysis import K8S_GKE_JOBS
from cartography.intel.gcp.compute import load_gcp_forwarding_rules
from cartography.intel.gcp.compute import transform_gcp_forwarding_rules
from cartography.intel.gcp.gke import sync_gke_clusters
from cartography.intel.gcp.iam import load_gcp_service_accounts
from cartography.intel.gcp.iam import transform_gcp_service_accounts
from cartography.intel.gcp.network_endpoint_group import (
    load_gcp_network_endpoint_groups,
)
from cartography.intel.gcp.network_endpoint_group import (
    transform_gcp_network_endpoint_groups,
)
from cartography.intel.gcp.policy_bindings import cleanup as cleanup_policy_bindings
from cartography.intel.gcp.policy_bindings import load_bindings
from cartography.intel.gcp.policy_bindings import transform_bindings
from cartography.intel.gcp.workload_identity import load_pools
from cartography.intel.gcp.workload_identity import transform_pools
from cartography.intel.kubernetes.clusters import load_kubernetes_cluster
from cartography.intel.kubernetes.ingress import load_ingresses
from cartography.intel.kubernetes.ingress import transform_ingresses
from cartography.intel.kubernetes.nodes import sync_nodes
from cartography.intel.kubernetes.rbac import load_service_accounts
from cartography.intel.kubernetes.rbac import load_users
from cartography.intel.kubernetes.rbac import transform_service_accounts
from cartography.intel.kubernetes.rbac import transform_users
from cartography.intel.kubernetes.services import load_services
from cartography.intel.kubernetes.services import transform_services
from cartography.intel.kubernetes.util import GKENetworkScope
from cartography.util import run_typed_analysis_job
from tests.data.kubernetes.gke import GKE_CLUSTER
from tests.data.kubernetes.gke import GKE_CLUSTER_ID
from tests.data.kubernetes.gke import GKE_CLUSTER_NAME
from tests.data.kubernetes.gke import GKE_FORWARDING_RULES
from tests.data.kubernetes.gke import GKE_GCP_SERVICE_ACCOUNTS
from tests.data.kubernetes.gke import GKE_GSA_EMAIL
from tests.data.kubernetes.gke import GKE_INGRESSES
from tests.data.kubernetes.gke import GKE_NEG_NAME
from tests.data.kubernetes.gke import GKE_NEGS
from tests.data.kubernetes.gke import GKE_NETWORK
from tests.data.kubernetes.gke import GKE_NODES
from tests.data.kubernetes.gke import GKE_OTHER_PROJECT_ID
from tests.data.kubernetes.gke import gke_policy_results
from tests.data.kubernetes.gke import GKE_POOL_ID
from tests.data.kubernetes.gke import GKE_PROJECT_ID
from tests.data.kubernetes.gke import GKE_RESOURCE_NAME
from tests.data.kubernetes.gke import GKE_SELF_LINK
from tests.data.kubernetes.gke import GKE_SERVICE_ACCOUNTS
from tests.data.kubernetes.gke import GKE_SERVICES
from tests.data.kubernetes.gke import GKE_WORKLOAD_POOLS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TAG = 1
COMMON = {"UPDATE_TAG": TAG, "CLUSTER_ID": GKE_CLUSTER_ID}


def _load_gcp(session, update_tag: int, include_impersonation: bool = True) -> None:
    common = {"UPDATE_TAG": update_tag, "PROJECT_ID": GKE_PROJECT_ID}
    load_gcp_service_accounts(
        session,
        transform_gcp_service_accounts(GKE_GCP_SERVICE_ACCOUNTS, GKE_PROJECT_ID),
        GKE_PROJECT_ID,
        update_tag,
    )
    load_pools(
        session,
        transform_pools(GKE_WORKLOAD_POOLS, GKE_PROJECT_ID),
        GKE_PROJECT_ID,
        update_tag,
    )
    container = MagicMock()
    container.projects.return_value.zones.return_value.clusters.return_value.list.return_value.execute.return_value = {
        "clusters": [GKE_CLUSTER],
    }
    sync_gke_clusters(session, container, GKE_PROJECT_ID, update_tag, common)
    for project_id, response in GKE_FORWARDING_RULES.items():
        load_gcp_forwarding_rules(
            session,
            transform_gcp_forwarding_rules(response),
            update_tag,
            project_id,
        )
    for project_id, response in GKE_NEGS.items():
        load_gcp_network_endpoint_groups(
            session,
            transform_gcp_network_endpoint_groups(response, project_id),
            update_tag,
            project_id,
        )
    load_bindings(
        session,
        transform_bindings(gke_policy_results(include_impersonation)),
        GKE_PROJECT_ID,
        update_tag,
    )
    cleanup_policy_bindings(session, common)


def _load_kubernetes(session, monkeypatch, update_tag: int) -> None:
    client = MagicMock()
    client.name = GKE_CLUSTER_NAME
    client.gke_cluster = {**GKE_CLUSTER, "resource_name": GKE_RESOURCE_NAME}
    load_kubernetes_cluster(
        session,
        [
            {
                "id": GKE_CLUSTER_ID,
                "name": GKE_CLUSTER_NAME,
                "gke_resource_name": GKE_RESOURCE_NAME,
            },
        ],
        update_tag,
    )
    monkeypatch.setattr(nodes_module, "get_nodes", lambda _: GKE_NODES)
    sync_nodes(session, client, update_tag, {**COMMON, "UPDATE_TAG": update_tag})
    load_service_accounts(
        session,
        transform_service_accounts(GKE_SERVICE_ACCOUNTS, GKE_CLUSTER_NAME),
        update_tag,
        GKE_CLUSTER_ID,
        GKE_CLUSTER_NAME,
    )
    reader_binding = SimpleNamespace(
        subjects=[SimpleNamespace(kind="User", name=GKE_GSA_EMAIL)],
    )
    load_users(
        session,
        transform_users([], [reader_binding], GKE_CLUSTER_NAME),
        update_tag,
        GKE_CLUSTER_ID,
        GKE_CLUSTER_NAME,
    )
    load_services(
        session,
        transform_services(
            GKE_SERVICES, [], GKENetworkScope(GKE_PROJECT_ID, GKE_NETWORK)
        ),
        update_tag,
        GKE_CLUSTER_ID,
        GKE_CLUSTER_NAME,
    )
    load_ingresses(
        session,
        transform_ingresses(
            GKE_INGRESSES, GKENetworkScope(GKE_PROJECT_ID, GKE_NETWORK)
        ),
        update_tag,
        GKE_CLUSTER_ID,
        GKE_CLUSTER_NAME,
    )


def _run_gke_jobs(session, update_tag: int) -> None:
    for job in K8S_GKE_JOBS:
        run_typed_analysis_job(job, session, {**COMMON, "UPDATE_TAG": update_tag})


@pytest.fixture
def gke_graph(neo4j_session, monkeypatch):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    for project_id in (GKE_PROJECT_ID, GKE_OTHER_PROJECT_ID):
        neo4j_session.run("CREATE (:GCPProject {id: $id})", id=project_id)
    _load_gcp(neo4j_session, TAG)
    _load_kubernetes(neo4j_session, monkeypatch, TAG)
    return neo4j_session


def test_gke_cloud_resources_map_to_kubernetes_inventory(gke_graph):
    # Arrange
    session = gke_graph

    # Act
    _run_gke_jobs(session, TAG)

    # Assert
    assert check_rels(
        session, "GKECluster", "id", "KubernetesCluster", "id", "MAPS_TO"
    ) == {(GKE_SELF_LINK, GKE_CLUSTER_ID)}
    assert check_nodes(session, "GKENodePool", ["id", "workload_metadata_mode"]) == {
        (f"{GKE_RESOURCE_NAME}/nodePools/pool", "GKE_METADATA"),
    }
    assert check_rels(
        session, "GKECluster", "id", "GKENodePool", "id", "HAS_NODE_POOL"
    ) == {(GKE_SELF_LINK, f"{GKE_RESOURCE_NAME}/nodePools/pool")}
    assert check_rels(
        session, "KubernetesNode", "name", "GKENodePool", "name", "MEMBER_OF"
    ) == {("node", "pool")}
    assert check_rels(
        session, "GKENodePool", "name", "GCPServiceAccount", "email", "RUNS_AS"
    ) == {("pool", GKE_GSA_EMAIL)}
    assert check_rels(
        session,
        "GKECluster",
        "id",
        "GCPWorkloadIdentityPool",
        "id",
        "USES_WORKLOAD_IDENTITY_POOL",
    ) == {(GKE_SELF_LINK, GKE_POOL_ID)}
    assert check_rels(
        session, "GCPPrincipal", "email", "KubernetesUser", "name", "MAPS_TO"
    ) == {(GKE_GSA_EMAIL, GKE_GSA_EMAIL)}


def test_gke_service_uses_forwarding_rule_in_cluster_project_and_network(gke_graph):
    # Arrange
    session = gke_graph

    # Act
    result = check_rels(
        session,
        "KubernetesService",
        "name",
        "GCPForwardingRule",
        "name",
        "USES_LOAD_BALANCER",
    )

    # Assert: the private address also exists in another project and another VPC of
    # the same project; neither of those rules matches.
    assert result == {("ilb", "gke-ilb"), ("public", "gke-external-lb")}


def test_gke_service_targeted_by_neg_in_cluster_project(gke_graph):
    # Arrange
    session = gke_graph

    # Act
    result = check_rels(
        session,
        "GCPNetworkEndpointGroup",
        "id",
        "KubernetesService",
        "name",
        "TARGETS",
    )

    # Assert: one edge per zone in neg-status; the same-named NEG in another project
    # does not match.
    assert result == {
        (
            f"projects/{GKE_PROJECT_ID}/zones/us-central1-a/networkEndpointGroups/{GKE_NEG_NAME}",
            "neg",
        ),
        (
            f"projects/{GKE_PROJECT_ID}/zones/us-central1-b/networkEndpointGroups/{GKE_NEG_NAME}",
            "neg",
        ),
    }


def test_gke_ingress_uses_internal_forwarding_rule_in_cluster_network(gke_graph):
    # Arrange
    session = gke_graph

    # Act
    result = check_rels(
        session,
        "KubernetesIngress",
        "name",
        "GCPForwardingRule",
        "name",
        "USES_LOAD_BALANCER",
    )

    # Assert: same-IP rules in another VPC and another project do not match.
    assert result == {("internal", "gke-ilb")}


def test_gke_workload_identity_policies_and_bindings(gke_graph):
    # Arrange
    session = gke_graph

    # Act
    _run_gke_jobs(session, TAG)

    # Assert
    assert check_rels(
        session,
        "KubernetesServiceAccount",
        "name",
        "GCPPolicyBinding",
        "role",
        "HAS_ALLOW_POLICY",
    ) == {
        ("direct", "roles/storage.objectViewer"),
        ("linked", "roles/iam.workloadIdentityUser"),
        ("conditional", "roles/iam.workloadIdentityUser"),
    }
    matched = session.run(
        "MATCH (:KubernetesServiceAccount {name: 'direct'})-[r:HAS_ALLOW_POLICY]->() "
        "RETURN r.matched_members AS members",
    ).single()["members"]
    assert matched == [
        f"principal://iam.googleapis.com/{GKE_POOL_ID}/subject/ns/ns/sa/direct",
    ]
    # The annotation is recorded separately from verified impersonation.
    assert check_rels(
        session,
        "KubernetesServiceAccount",
        "name",
        "GCPServiceAccount",
        "email",
        "ANNOTATED_SERVICE_ACCOUNT",
    ) == {
        ("linked", GKE_GSA_EMAIL),
        ("conditional", GKE_GSA_EMAIL),
        ("annotation-only", GKE_GSA_EMAIL),
    }
    assert check_rels(
        session,
        "KubernetesServiceAccount",
        "name",
        "GCPServiceAccount",
        "email",
        "WORKLOAD_IDENTITY_BINDING",
    ) == {("linked", GKE_GSA_EMAIL)}


def test_gke_workload_identity_binding_removed_with_grant(gke_graph, monkeypatch):
    # Arrange
    session = gke_graph
    _run_gke_jobs(session, TAG)
    # A pre-existing annotation-only edge from older Cartography versions.
    session.run(
        "MATCH (s:KubernetesServiceAccount {name: 'annotation-only'}), "
        "(g:GCPServiceAccount {email: $email}) "
        "MERGE (s)-[:WORKLOAD_IDENTITY_BINDING {lastupdated: 0}]->(g)",
        email=GKE_GSA_EMAIL,
    )
    _load_gcp(session, TAG + 1, include_impersonation=False)
    _load_kubernetes(session, monkeypatch, TAG + 1)

    # Act
    _run_gke_jobs(session, TAG + 1)

    # Assert
    assert (
        check_rels(
            session,
            "KubernetesServiceAccount",
            "name",
            "GCPServiceAccount",
            "email",
            "WORKLOAD_IDENTITY_BINDING",
        )
        == set()
    )
    assert check_rels(
        session,
        "KubernetesServiceAccount",
        "name",
        "GCPPolicyBinding",
        "role",
        "HAS_ALLOW_POLICY",
    ) == {
        ("direct", "roles/storage.objectViewer"),
        ("conditional", "roles/iam.workloadIdentityUser"),
    }
