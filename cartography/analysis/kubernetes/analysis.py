from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperty
from cartography.graph.analysis import Var

K8S_SERVICE_ASSET_EXPOSURE = AnalysisJob(
    name="Kubernetes service internet exposure",
    short_name="k8s_service_asset_exposure",
    scope=ScopeById(
        "KubernetesCluster",
        "CLUSTER_ID",
        scope_on=("svc", "ing", "gw"),
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') WITH DISTINCT svc",
            effects=(
                SetProperty("svc", "exposed_internet", True, label="KubernetesService"),
                AddToSet(
                    "svc", "exposed_internet_type", "lb", label="KubernetesService"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService) WITH DISTINCT svc",
            effects=(
                SetProperty("svc", "exposed_internet", True, label="KubernetesService"),
                AddToSet(
                    "svc", "exposed_internet_type", "lb", label="KubernetesService"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (gw:KubernetesGateway)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (gw)-[:ROUTES]->(:KubernetesHTTPRoute)-[:TARGETS]->(svc:KubernetesService) WITH DISTINCT svc",
            effects=(
                SetProperty("svc", "exposed_internet", True, label="KubernetesService"),
                AddToSet(
                    "svc", "exposed_internet_type", "lb", label="KubernetesService"
                ),
            ),
        ),
    ),
)
K8S_POD_ASSET_EXPOSURE = AnalysisJob(
    name="Kubernetes pod internet exposure",
    short_name="k8s_pod_asset_exposure",
    scope=ScopeById("KubernetesCluster", "CLUSTER_ID", scope_on="svc"),
    statements=(
        AnalysisStatement(
            match="MATCH (svc:KubernetesService{exposed_internet: true})-[:TARGETS]->(pod:KubernetesPod) WITH DISTINCT pod",
            effects=(
                SetProperty("pod", "exposed_internet", True, label="KubernetesPod"),
                AddToSet("pod", "exposed_internet_type", "lb", label="KubernetesPod"),
            ),
        ),
    ),
)
K8S_CONTAINER_ASSET_EXPOSURE = AnalysisJob(
    name="Kubernetes container internet exposure",
    short_name="k8s_container_asset_exposure",
    scope=ScopeById("KubernetesCluster", "CLUSTER_ID", scope_on="pod"),
    statements=(
        AnalysisStatement(
            match="MATCH (pod:KubernetesPod{exposed_internet: true})-[:CONTAINS]->(c:KubernetesContainer)",
            effects=(
                SetProperty("c", "exposed_internet", True, label="KubernetesContainer"),
                AddToSet(
                    "c", "exposed_internet_type", "lb", label="KubernetesContainer"
                ),
            ),
        ),
    ),
)
K8S_COMPUTE_ASSET_EXPOSURE_JOBS = (
    K8S_SERVICE_ASSET_EXPOSURE,
    K8S_POD_ASSET_EXPOSURE,
    K8S_CONTAINER_ASSET_EXPOSURE,
)
K8S_LB_POD_EXPOSURE = AnalysisJob(
    name="Kubernetes LoadBalancer to pod EXPOSE relationships",
    short_name="k8s_lb_pod_exposure",
    scope=ScopeById(
        "KubernetesCluster",
        "CLUSTER_ID",
        scope_on=("svc", "ing", "gw"),
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (svc)-[:TARGETS]->(pod:KubernetesPod)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "pod",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="LoadBalancer",
                    target_label="KubernetesPod",
                    scoped_to="target",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "pod",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="LoadBalancer",
                    target_label="KubernetesPod",
                    scoped_to="target",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (gw:KubernetesGateway)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (gw)-[:ROUTES]->(:KubernetesHTTPRoute)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "pod",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="LoadBalancer",
                    target_label="KubernetesPod",
                    scoped_to="target",
                ),
            ),
        ),
    ),
)
K8S_LB_CONTAINER_EXPOSURE = AnalysisJob(
    name="Kubernetes LoadBalancer to container EXPOSE relationships",
    short_name="k8s_lb_container_exposure",
    scope=ScopeById(
        "KubernetesCluster",
        "CLUSTER_ID",
        scope_on=("svc", "ing", "gw"),
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (svc)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "c",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="LoadBalancer",
                    target_label="KubernetesContainer",
                    scoped_to="target",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "c",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="LoadBalancer",
                    target_label="KubernetesContainer",
                    scoped_to="target",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (gw:KubernetesGateway)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (gw)-[:ROUTES]->(:KubernetesHTTPRoute)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "c",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="LoadBalancer",
                    target_label="KubernetesContainer",
                    scoped_to="target",
                ),
            ),
        ),
    ),
)
K8S_LB_EXPOSURE_JOBS = (K8S_LB_POD_EXPOSURE, K8S_LB_CONTAINER_EXPOSURE)

# GKE Workload Identity Federation: match Kubernetes service accounts against the
# documented IAM member forms for their cluster's workload pool. The GKE workload pool
# is shared by every cluster in the project, so namespace/name subjects and namespace
# principal sets intentionally match same-named service accounts in other clusters.
# https://cloud.google.com/kubernetes-engine/docs/concepts/workload-identity#principal-id
K8S_GKE_WORKLOAD_IDENTITY_POLICY = AnalysisJob(
    name="GKE Kubernetes service account IAM allow policies",
    short_name="k8s_gke_workload_identity_policy",
    scope=ScopeById("KubernetesCluster", "CLUSTER_ID", scope_on="sa"),
    statements=(
        AnalysisStatement(
            # Collect accounts first so policy bindings are scanned once per cluster.
            match="""
            MATCH (k:KubernetesCluster)-[:RESOURCE]->(sa:KubernetesServiceAccount)
            WITH k, collect(sa) AS accounts
            MATCH (k)<-[:MAPS_TO]-(:GKECluster)
                  -[:USES_WORKLOAD_IDENTITY_POOL]->(pool:GCPWorkloadIdentityPool)
            MATCH (b:GCPPolicyBinding)
            WHERE pool.id IN b.wif_pools
               OR any(m IN b.raw_members WHERE m STARTS WITH 'serviceAccount:' + pool.pool_id + '[')
            WITH accounts, k, pool, b,
                 'principal://iam.googleapis.com/' + pool.id AS principal,
                 'principalSet://iam.googleapis.com/' + pool.id AS principal_set
            UNWIND accounts AS sa
            WITH sa, b, [
                principal + '/subject/ns/' + sa.namespace + '/sa/' + sa.name,
                principal + '/kubernetes.serviceaccount.uid/' + sa.uid,
                principal_set + '/kubernetes.serviceaccount.uid/' + sa.uid,
                principal_set + '/namespace/' + sa.namespace,
                principal_set + '/kubernetes.cluster/https://container.googleapis.com/v1/' + k.gke_resource_name,
                principal_set + '/*',
                'serviceAccount:' + pool.pool_id + '[' + sa.namespace + '/' + sa.name + ']'
            ] AS candidates
            WITH sa, b, [m IN candidates WHERE m IN b.raw_members] AS matched_members
            WHERE size(matched_members) > 0
            """,
            effects=(
                AddRelationship(
                    "sa",
                    "HAS_ALLOW_POLICY",
                    "b",
                    source_label="KubernetesServiceAccount",
                    target_label="GCPPolicyBinding",
                    properties={"matched_members": Var("matched_members")},
                ),
            ),
        ),
    ),
)
# Runs after K8S_GKE_WORKLOAD_IDENTITY_POLICY so it only reads current HAS_ALLOW_POLICY edges.
K8S_GKE_WORKLOAD_IDENTITY_BINDING = AnalysisJob(
    name="GKE Kubernetes service account Google service account impersonation",
    short_name="k8s_gke_workload_identity_binding",
    scope=ScopeById("KubernetesCluster", "CLUSTER_ID", scope_on="sa"),
    statements=(
        AnalysisStatement(
            match="""
            MATCH (sa:KubernetesServiceAccount)-[:HAS_ALLOW_POLICY]->(b:GCPPolicyBinding)
                  -[:APPLIES_TO]->(gsa:GCPServiceAccount)
            WHERE b.role = 'roles/iam.workloadIdentityUser'
              AND b.has_condition = false
              AND gsa.email = sa.gcp_service_account
            WITH DISTINCT sa, gsa
            """,
            effects=(
                AddRelationship(
                    "sa",
                    "WORKLOAD_IDENTITY_BINDING",
                    "gsa",
                    source_label="KubernetesServiceAccount",
                    target_label="GCPServiceAccount",
                ),
            ),
        ),
    ),
)
K8S_GKE_JOBS = (K8S_GKE_WORKLOAD_IDENTITY_POLICY, K8S_GKE_WORKLOAD_IDENTITY_BINDING)
