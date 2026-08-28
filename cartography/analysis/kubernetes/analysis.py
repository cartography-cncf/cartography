from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperty

INTERNET_FACING_LOAD_BALANCER = """
lb.exposed_internet = true OR (
  lb._ont_source = 'aws'
  AND lb._ont_scheme = 'internet_facing'
  AND lb._ont_lb_type = 'network'
)
"""

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
            match=f"MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE {INTERNET_FACING_LOAD_BALANCER} WITH DISTINCT svc",
            effects=(
                SetProperty("svc", "exposed_internet", True, label="KubernetesService"),
                AddToSet(
                    "svc", "exposed_internet_type", "lb", label="KubernetesService"
                ),
            ),
        ),
        AnalysisStatement(
            match=f"MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE {INTERNET_FACING_LOAD_BALANCER} MATCH (ing)-[:TARGETS]->(svc:KubernetesService) WITH DISTINCT svc",
            effects=(
                SetProperty("svc", "exposed_internet", True, label="KubernetesService"),
                AddToSet(
                    "svc", "exposed_internet_type", "lb", label="KubernetesService"
                ),
            ),
        ),
        AnalysisStatement(
            comment=(
                "Only propagate Gateway API exposure through a programmed Gateway and "
                "an HTTPRoute that its controller currently reports as accepted."
            ),
            match=f"""
            MATCH (gw:KubernetesGateway {{programmed: true}})-[:USES_LOAD_BALANCER]->(lb:LoadBalancer)
            WHERE {INTERNET_FACING_LOAD_BALANCER}
            MATCH (gw)-[:ROUTES]->(route:KubernetesHTTPRoute)-[:TARGETS]->(svc:KubernetesService)
            WHERE gw.qualified_name IN route.accepted_parent_gateway_qualified_names
            WITH DISTINCT svc
            """,
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
            match=f"MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE {INTERNET_FACING_LOAD_BALANCER} MATCH (svc)-[:TARGETS]->(pod:KubernetesPod)",
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
            match=f"MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE {INTERNET_FACING_LOAD_BALANCER} MATCH (ing)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)",
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
            comment=(
                "Only create Gateway API exposure edges for programmed Gateways and "
                "controller-accepted HTTPRoute parents."
            ),
            match=f"""
            MATCH (gw:KubernetesGateway {{programmed: true}})-[:USES_LOAD_BALANCER]->(lb:LoadBalancer)
            WHERE {INTERNET_FACING_LOAD_BALANCER}
            MATCH (gw)-[:ROUTES]->(route:KubernetesHTTPRoute)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)
            WHERE gw.qualified_name IN route.accepted_parent_gateway_qualified_names
            """,
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
            match=f"MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE {INTERNET_FACING_LOAD_BALANCER} MATCH (svc)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer)",
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
            match=f"MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:LoadBalancer) WHERE {INTERNET_FACING_LOAD_BALANCER} MATCH (ing)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer)",
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
            comment=(
                "Only create Gateway API exposure edges for programmed Gateways and "
                "controller-accepted HTTPRoute parents."
            ),
            match=f"""
            MATCH (gw:KubernetesGateway {{programmed: true}})-[:USES_LOAD_BALANCER]->(lb:LoadBalancer)
            WHERE {INTERNET_FACING_LOAD_BALANCER}
            MATCH (gw)-[:ROUTES]->(route:KubernetesHTTPRoute)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer)
            WHERE gw.qualified_name IN route.accepted_parent_gateway_qualified_names
            """,
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
