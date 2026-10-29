from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AddToSet
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperty

K8S_SERVICE_ASSET_EXPOSURE = AnalysisJob(
    name="Kubernetes service internet exposure",
    short_name="k8s_service_asset_exposure",
    scope=ScopeById(
        "KubernetesCluster",
        "CLUSTER_ID",
        scope_on=("svc", "ing"),
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') WITH DISTINCT svc",
            effects=(
                SetProperty("svc", "exposed_internet", True, label="KubernetesService"),
                AddToSet(
                    "svc", "exposed_internet_type", "lb", label="KubernetesService"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService) WITH DISTINCT svc",
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
        scope_on=("svc", "ing"),
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (svc)-[:TARGETS]->(pod:KubernetesPod)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "pod",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="AWSLoadBalancerV2",
                    target_label="KubernetesPod",
                    scoped_to="target",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "pod",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="AWSLoadBalancerV2",
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
        scope_on=("svc", "ing"),
    ),
    statements=(
        AnalysisStatement(
            match="MATCH (svc:KubernetesService)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (svc)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "c",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="AWSLoadBalancerV2",
                    target_label="KubernetesContainer",
                    scoped_to="target",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (ing:KubernetesIngress)-[:USES_LOAD_BALANCER]->(lb:AWSLoadBalancerV2) WHERE lb.exposed_internet = true OR (lb.scheme = 'internet-facing' AND lb.type = 'network') MATCH (ing)-[:TARGETS]->(svc:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(c:KubernetesContainer)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "c",
                    properties={"exposure_type": "via_lb_only"},
                    source_label="AWSLoadBalancerV2",
                    target_label="KubernetesContainer",
                    scoped_to="target",
                ),
            ),
        ),
    ),
)
K8S_LB_EXPOSURE_JOBS = (K8S_LB_POD_EXPOSURE, K8S_LB_CONTAINER_EXPOSURE)
